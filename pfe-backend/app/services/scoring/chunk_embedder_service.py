from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

CHUNK_SIZE = 350
MIN_CHUNK_CHARS = 40
_EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# ── Chunk-level junk filter ──────────────────────────────────────────────────
# Chunks where >40% of words match these patterns are discarded before
# embedding — catches LinkedIn/website UI noise that survived HTML stripping.
_JUNK_TOKENS = frozenset([
    "s'inscrire", "connexion", "se", "connecter", "register", "sign", "login",
    "log", "password", "mot", "de", "passe", "cookies", "cookie", "accepter",
    "accept", "privacy", "policy", "terms", "conditions", "spam", "resend",
    "renvoyer", "email", "e-mail", "unsubscribe", "désabonner",
    "follow", "suivre", "partager", "share", "report", "signaler",
    "télécharger", "download", "app", "store", "play", "google", "apple",
    "©", "copyright", "linkedin", "corporation", "all", "rights", "reserved",
    "tous", "droits", "réservés", "mentions", "légales", "legal",
])

# If chunk contains any of these exact substrings it is always junk
_JUNK_PHRASES = re.compile(
    r"s'inscrire|se connecter|connexion|sign in|sign up|log in|"
    r"check your spam|vérifiez vos spams|cookie policy|"
    r"privacy policy|politique de confidentialit|conditions d.utilisation|"
    r"terms of service|terms of use|mentions légales|"
    r"renvoyer l.e-mail|resend|forgot password|mot de passe oublié|"
    r"télécharger l.application|download the app|get the app",
    re.IGNORECASE,
)


class ChunkEmbedderService:
    """
    Splits text sources into overlapping sentence-aware chunks, then generates
    dense embeddings using fastembed (ONNX runtime, no PyTorch).

    Falls back to BM25-compatible text-only chunks when fastembed is unavailable.
    The service is stateless between pipeline runs — no index is persisted.
    """

    def __init__(self) -> None:
        self._model = None
        self._available = False
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(_EMBED_MODEL)
            self._available = True
            logger.info("ChunkEmbedderService: model '%s' loaded", _EMBED_MODEL)
        except Exception as exc:
            logger.warning(
                "ChunkEmbedderService: fastembed unavailable (%s) — will run without embeddings.",
                exc,
            )

    # ── Public API ──────────────────────────────────────────────────────────

    def chunk_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split one evidence source into overlapping chunks with metadata."""
        text = (source.get("text") or "").strip()
        if not text:
            return []

        meta = {
            "source_type":  source.get("type", ""),
            "source_url":   source.get("url"),
            "source_label": source.get("label", ""),
        }

        # Document sources (PDFs) use larger chunks so Q&A pairs are not split.
        # Each section from the loader already holds one complete Q&A block.
        is_document = source.get("type") == "document"

        sections: List[Dict] = source.get("sections") or []
        if sections:
            chunks = []
            for sec in sections:
                heading = sec.get("heading", "")
                body = sec.get("text", "").strip()
                if not body:
                    continue
                if is_document:
                    # Keep the whole section as one chunk — never split PDF Q&A blocks
                    if len(body) >= MIN_CHUNK_CHARS:
                        chunks.append({**meta, "text": body, "section": heading, "embedding": None})
                else:
                    chunks.extend(self._chunk_text(body, meta, section=heading))
            if chunks:
                return [c for c in chunks if not self._is_junk(c["text"])]

        raw = self._chunk_text(text, meta, section="")
        return [c for c in raw if not self._is_junk(c["text"])]

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Return a cached chunk embedding, or None on cache miss."""
        from app.services.cache.embedding_cache import embedding_cache
        return embedding_cache.get("chunk::" + text)

    def _store_embedding(self, text: str, vec: np.ndarray) -> None:
        from app.services.cache.embedding_cache import embedding_cache
        embedding_cache.set("chunk::" + text, vec)

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Attach a numpy float32 embedding to each chunk (in-place).

        Cache strategy:
          1. Check in-memory cache for each chunk text.
          2. Batch-embed only the chunks that are not cached (cache misses).
          3. Store new embeddings in cache for future reuse.
        """
        for c in chunks:
            c["embedding"] = None

        if not self._available or not chunks:
            return chunks

        # ── Step 1: separate hits from misses ────────────────────────────────
        miss_indices: List[int] = []
        hits = 0
        for i, c in enumerate(chunks):
            cached = self.get_embedding(c["text"])
            if cached is not None:
                c["embedding"] = cached
                hits += 1
            else:
                miss_indices.append(i)

        if hits:
            logger.debug(
                "ChunkEmbedderService: %d/%d chunk embedding(s) served from cache",
                hits, len(chunks),
            )

        # ── Step 2: batch-embed only the misses ──────────────────────────────
        if miss_indices:
            miss_texts = [chunks[i]["text"] for i in miss_indices]
            try:
                embeddings = list(self._model.embed(miss_texts))
                for idx, emb in zip(miss_indices, embeddings):
                    vec = np.array(emb, dtype=np.float32)
                    chunks[idx]["embedding"] = vec
                    # ── Step 3: store in cache ────────────────────────────────
                    self._store_embedding(chunks[idx]["text"], vec)
                logger.debug(
                    "ChunkEmbedderService: %d new chunk embedding(s) computed and cached",
                    len(miss_indices),
                )
            except Exception as exc:
                logger.error("Batch embedding failed: %s", exc)

        return chunks

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Return a float32 embedding for a criterion label (query-mode)."""
        if not self._available or not self._model:
            return None
        try:
            from app.services.cache.embedding_cache import embedding_cache
            cached = embedding_cache.get(query)
            if cached is not None:
                return cached
            result = list(self._model.query_embed(query))
            vec = np.array(result[0], dtype=np.float32) if result else None
            embedding_cache.set(query, vec)
            return vec
        except Exception as exc:
            logger.error("Query embedding failed for %r: %s", query[:60], exc)
            return None

    @property
    def embeddings_available(self) -> bool:
        return self._available

    # ── Junk detection ───────────────────────────────────────────────────────

    @staticmethod
    def _is_junk(text: str) -> bool:
        """Return True if the chunk is UI/navigation noise and should be dropped."""
        if _JUNK_PHRASES.search(text):
            return True
        words = re.sub(r"[^\w\s']", " ", text.lower()).split()
        if not words:
            return True
        junk_ratio = sum(1 for w in words if w in _JUNK_TOKENS) / len(words)
        return junk_ratio > 0.40

    # ── Chunking ────────────────────────────────────────────────────────────

    def _chunk_text(
        self, text: str, meta: Dict[str, Any], section: str
    ) -> List[Dict[str, Any]]:
        # Split on sentence boundaries and newlines
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text) if s.strip()]

        chunks: List[Dict[str, Any]] = []
        current_parts: List[str] = []
        current_len = 0

        for sent in sentences:
            if current_len + len(sent) > CHUNK_SIZE and current_parts:
                chunk_text = " ".join(current_parts).strip()
                if len(chunk_text) >= MIN_CHUNK_CHARS:
                    chunks.append({**meta, "text": chunk_text, "section": section, "embedding": None})
                # carry the last sentence as overlap context
                current_parts = [current_parts[-1]] if current_parts else []
                current_len = len(current_parts[0]) if current_parts else 0

            current_parts.append(sent)
            current_len += len(sent) + 1

        # flush remainder
        if current_parts:
            chunk_text = " ".join(current_parts).strip()
            if len(chunk_text) >= MIN_CHUNK_CHARS:
                chunks.append({**meta, "text": chunk_text, "section": section, "embedding": None})

        return chunks
