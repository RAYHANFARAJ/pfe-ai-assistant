from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Chunks below this cosine similarity are discarded as irrelevant
MIN_SIMILARITY = 0.25
# How many chunks to return per criterion
TOP_K = 5


class SemanticRetrieverService:
    """
    Retrieves the most relevant chunks for a given criterion using cosine
    similarity between dense embeddings.

    Falls back to BM25 keyword ranking when embeddings are unavailable.
    """

    # ── Public API ──────────────────────────────────────────────────────────

    def retrieve(
        self,
        query_embedding: Optional[np.ndarray],
        query_text: str,
        chunks: List[Dict[str, Any]],
        top_k: int = TOP_K,
    ) -> List[Dict[str, Any]]:
        """
        Return up to `top_k` chunks most relevant to the query, sorted by
        descending relevance. Each returned chunk gains a 'similarity' key.
        """
        if not chunks:
            return []

        embedded = [c for c in chunks if c.get("embedding") is not None]

        if query_embedding is not None and embedded:
            return self._cosine_retrieve(query_embedding, embedded, top_k)

        # Fallback: BM25
        logger.debug("SemanticRetriever: no embeddings — using BM25 fallback.")
        return self._bm25_retrieve(query_text, chunks, top_k)

    # ── Dense retrieval ─────────────────────────────────────────────────────

    @staticmethod
    def _cosine_retrieve(
        query_emb: np.ndarray,
        chunks: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        matrix = np.stack([c["embedding"] for c in chunks])  # (N, D)

        q = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
        scores = (matrix / norms) @ q  # (N,)

        # Filter below threshold, then sort descending
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

    # ── BM25 fallback ───────────────────────────────────────────────────────

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

        tokenized_corpus = [c["text"].lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(query.lower().split())

        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [
            {**chunks[i], "similarity": round(float(scores[i]), 4)}
            for i in order[:top_k]
            if scores[i] > 0
        ]
