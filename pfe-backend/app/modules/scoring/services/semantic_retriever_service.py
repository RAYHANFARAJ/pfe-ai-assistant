from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

MIN_SIMILARITY = 0.25
TOP_K = 5


class SemanticRetrieverService:
    """
    Hybrid retriever: cosine similarity (dense) + BM25 (keyword, French-aware).
    Document chunks get an extra BM25 pass so keyword matches aren't missed
    when semantic embeddings diverge (e.g. "effectif" vs "Effectifs").
    """

    def retrieve(
        self,
        query_embedding: Optional[np.ndarray],
        query_text: str,
        chunks: List[Dict[str, Any]],
        top_k: int = TOP_K,
    ) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        embedded = [c for c in chunks if c.get("embedding") is not None]

        if query_embedding is not None and embedded:
            semantic = self._cosine_retrieve(query_embedding, embedded, top_k)
            # Hybrid boost: BM25 on document chunks to catch stemming mismatches
            doc_chunks = [c for c in chunks if c.get("source_type") == "document"]
            if doc_chunks:
                keyword = self._bm25_retrieve(query_text, doc_chunks, top_k)
                seen = {c["text"] for c in semantic}
                for kc in keyword:
                    if kc["text"] not in seen:
                        # Dampen BM25 score so semantic results still lead
                        kc["similarity"] = min(kc["similarity"] * 0.65, 0.62)
                        semantic.append(kc)
                        seen.add(kc["text"])
            return semantic[:top_k + 3]

        logger.debug("SemanticRetriever: no embeddings — using BM25 fallback.")
        return self._bm25_retrieve(query_text, chunks, top_k)

    # ── Dense retrieval ───────────────────────────────────────────────────────

    @staticmethod
    def _cosine_retrieve(
        query_emb: np.ndarray,
        chunks: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        matrix = np.stack([c["embedding"] for c in chunks])
        q = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
        scores = (matrix / norms) @ q
        order = np.argsort(scores)[::-1]
        results = []
        for idx in order:
            sim = float(scores[idx])
            if sim < MIN_SIMILARITY:
                break
            results.append({**chunks[idx], "similarity": round(sim, 4)})
            if len(results) >= top_k:
                break
        return results

    # ── BM25 with French stemming ─────────────────────────────────────────────

    @staticmethod
    def _stem_fr(text: str) -> List[str]:
        """Tokenize + light French stemming (strip plurals, remove accents)."""
        # Normalize unicode / remove accents
        normalized = unicodedata.normalize("NFD", text.lower())
        normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        tokens = re.findall(r"[a-z0-9]+", normalized)
        stemmed = []
        for t in tokens:
            if len(t) <= 3:
                continue  # skip stopwords
            # Strip French plural -s and -x endings
            if len(t) > 4 and t.endswith("aux"):
                t = t[:-2]
            elif len(t) > 3 and t.endswith("s"):
                t = t[:-1]
            stemmed.append(t)
        return stemmed

    @staticmethod
    def _bm25_retrieve(
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning("rank_bm25 not installed; returning all chunks unsorted.")
            return [{"similarity": 0.0, **c} for c in chunks[:top_k]]

        stem = SemanticRetrieverService._stem_fr
        tokenized_corpus = [stem(c["text"]) for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(stem(query))

        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [
            {**chunks[i], "similarity": round(float(scores[i]), 4)}
            for i in order[:top_k]
            if scores[i] > 0
        ]
