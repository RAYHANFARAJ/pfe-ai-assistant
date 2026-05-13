"""Criterion Knowledge Base — RAG few-shot retrieval.

After each successful LLM extraction, the answer is stored as a knowledge
entry. When scoring the same criterion type for a new client, the top-K
most similar past answers are retrieved via cosine similarity and injected
into the LLM prompt as few-shot examples.

This turns the scoring pipeline into a self-improving RAG:
- First time a criterion is scored → zero-shot
- Subsequent scorings → few-shot with real past examples
- Quality improves organically as the knowledge base grows

Storage: output/rag_knowledge.jsonl (one JSON object per line)
Retrieval: cosine similarity on criterion_label embeddings

Toggle: set RAG_KB_ENABLED=false to disable.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

ENABLED    = os.getenv("RAG_KB_ENABLED", "true").lower() != "false"
TOP_K      = int(os.getenv("RAG_KB_TOP_K", "2"))
MIN_CONF   = float(os.getenv("RAG_KB_MIN_CONFIDENCE", "0.75"))
MAX_ENTRIES= int(os.getenv("RAG_KB_MAX_ENTRIES", "2000"))
_KB_FILE   = Path(__file__).parent.parent.parent.parent / "output" / "rag_knowledge.jsonl"
_lock      = threading.Lock()


# ── Public API ─────────────────────────────────────────────────────────────────

def store_entry(
    criterion_id: str,
    criterion_label: str,
    answer_type: str,
    predicted_answer: str,
    confidence: float,
    evidence_sentence: str,
    reasoning: str,
    label_embedding: Optional[List[float]],
) -> None:
    """Persist a high-confidence extraction as a knowledge entry."""
    if not ENABLED:
        return
    if confidence < MIN_CONF or not predicted_answer or predicted_answer == "unknown":
        return
    entry = {
        "criterion_id":     criterion_id,
        "criterion_label":  criterion_label,
        "answer_type":      answer_type,
        "predicted_answer": predicted_answer,
        "confidence":       round(confidence, 3),
        "evidence":         evidence_sentence[:300] if evidence_sentence else "",
        "reasoning":        reasoning[:200] if reasoning else "",
        "embedding":        label_embedding,
    }
    with _lock:
        _append_entry(entry)
    logger.debug("RAG KB: stored entry for '%s' (conf=%.2f)", criterion_label, confidence)


def retrieve_examples(
    criterion_label: str,
    answer_type: str,
    label_embedding: Optional[List[float]],
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """Return the top-K most similar past examples for this criterion."""
    if not ENABLED or label_embedding is None:
        return []
    entries = _load_entries()
    # Filter by same answer_type to avoid mixing numeric with choice examples
    same_type = [e for e in entries if e.get("answer_type") == answer_type and e.get("embedding")]
    if not same_type:
        return []

    query_vec = np.array(label_embedding, dtype=np.float32)
    scored: List[tuple] = []
    for e in same_type:
        try:
            vec = np.array(e["embedding"], dtype=np.float32)
            sim = float(np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-9))
            scored.append((sim, e))
        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [e for _, e in scored[:top_k] if _ > 0.70]   # similarity threshold
    logger.debug("RAG KB: retrieved %d example(s) for '%s'", len(results), criterion_label)
    return results


def format_examples_for_prompt(examples: List[Dict[str, Any]]) -> str:
    """Format retrieved examples as a human-readable few-shot block."""
    if not examples:
        return ""
    lines = ["--- Past examples for similar criteria ---"]
    for i, ex in enumerate(examples, 1):
        lines.append(
            f"Example {i}: Criterion '{ex['criterion_label']}' → "
            f"Answer: {ex['predicted_answer']} (confidence {ex['confidence']:.0%})"
        )
        if ex.get("evidence"):
            lines.append(f"  Evidence: \"{ex['evidence'][:150]}\"")
        if ex.get("reasoning"):
            lines.append(f"  Reasoning: {ex['reasoning'][:100]}")
    lines.append("---")
    return "\n".join(lines)


def stats() -> Dict[str, Any]:
    entries = _load_entries()
    by_type: Dict[str, int] = {}
    for e in entries:
        t = e.get("answer_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "enabled":     ENABLED,
        "total":       len(entries),
        "by_type":     by_type,
        "top_k":       TOP_K,
        "min_conf":    MIN_CONF,
        "max_entries": MAX_ENTRIES,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_entries() -> List[Dict[str, Any]]:
    if not _KB_FILE.exists():
        return []
    entries = []
    try:
        for line in _KB_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    except Exception as exc:
        logger.warning("RAG KB load error: %s", exc)
    return entries


def _append_entry(entry: Dict[str, Any]) -> None:
    try:
        _KB_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Rotate if too large
        existing = _load_entries()
        if len(existing) >= MAX_ENTRIES:
            # Keep the most recent MAX_ENTRIES entries
            keep = existing[-(MAX_ENTRIES - 1):]
            _KB_FILE.write_text(
                "\n".join(json.dumps(e, ensure_ascii=False) for e in keep) + "\n",
                encoding="utf-8",
            )
        with open(_KB_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.error("RAG KB append error: %s", exc)
