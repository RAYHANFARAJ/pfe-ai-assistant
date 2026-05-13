"""Explanation service — enriches criteria with French explanations.

Key design: ONE batch LLM call per product (not one per criterion).
Société Générale with 15 products → max 15 LLM calls, not 50+.
Parallel enrichment across products reduces total time further.
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MIN_WORDS = 15  # reasoning word count threshold to skip LLM


# ── Public API ─────────────────────────────────────────────────────────────────

def enrich_all_products(
    products: List[Dict[str, Any]],
    client_name: str,
    max_workers: int = 4,
) -> List[Dict[str, Any]]:
    """Enrich all products' criteria in parallel — one LLM call per product."""
    if not products:
        return products

    results: List[Optional[Dict]] = [None] * len(products)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_to_idx = {
            ex.submit(
                enrich_criteria_explanations,
                pr.get("criteria_results", []),
                client_name,
                pr.get("product_name", pr.get("product_id", "")),
            ): i
            for i, pr in enumerate(products)
        }
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            try:
                enriched_criteria = fut.result()
            except Exception as exc:
                logger.warning("Enrichment failed for product index %d: %s", idx, exc)
                enriched_criteria = products[idx].get("criteria_results", [])
            results[idx] = {**products[idx], "criteria_results": enriched_criteria}

    return results  # type: ignore[return-value]


def enrich_criteria_explanations(
    criteria: List[Dict[str, Any]],
    client_name: str,
    product_name: str,
) -> List[Dict[str, Any]]:
    """Add 'explanation' key to each criterion. Uses ONE batch LLM call for all that need it."""
    enriched: List[Dict[str, Any]] = []
    needs_llm: List[int] = []          # indices that need LLM

    # ── Pass 1: apply templates / existing reasoning ──────────────────────────
    for i, c in enumerate(criteria):
        answer    = c.get("predicted_answer") or "unknown"
        reasoning = ((c.get("justification") or {}).get("reasoning") or "").strip()

        if answer == "unknown" or not answer.strip():
            expl = _template_missing(c.get("label", "ce critère"), client_name)
        elif reasoning and len(reasoning.split()) >= _MIN_WORDS:
            expl = _format_existing(
                reasoning, answer,
                c.get("score", 0), c.get("max_score", 0),
                c.get("label", ""), client_name,
            )
        else:
            expl = None          # will be filled by LLM
            needs_llm.append(i)

        enriched.append({**c, "explanation": expl})

    # ── Pass 2: single batch LLM call for all remaining ───────────────────────
    if needs_llm:
        batch_criteria = [criteria[i] for i in needs_llm]
        try:
            batch_explanations = _batch_llm(batch_criteria, client_name, product_name)
            for list_pos, criterion_idx in enumerate(needs_llm):
                enriched[criterion_idx]["explanation"] = batch_explanations[list_pos]
        except Exception as exc:
            logger.warning("Batch LLM call failed (%s) — using templates", exc)
            for criterion_idx in needs_llm:
                c = criteria[criterion_idx]
                enriched[criterion_idx]["explanation"] = _template_fallback(
                    c.get("label", ""), c.get("predicted_answer", ""),
                    c.get("score", 0), c.get("max_score", 0), client_name,
                )

    return enriched


# ── Batch LLM (single call for N criteria) ────────────────────────────────────

def _batch_llm(
    criteria_list: List[Dict[str, Any]],
    client_name: str,
    product_name: str,
) -> List[str]:
    """One OpenAI call → explanations for all criteria in the list."""
    from openai import OpenAI
    from app.core.config import settings

    oai = OpenAI(api_key=settings.openai_api_key)

    items: List[Dict] = []
    for i, c in enumerate(criteria_list):
        score   = c.get("score", 0)
        max_sc  = c.get("max_score", 0)
        answer  = c.get("predicted_answer", "")
        conf    = round((c.get("confidence") or 0) * 100)
        reason  = ((c.get("justification") or {}).get("reasoning") or "").strip()
        quote   = ((c.get("evidence") or {}).get("exact_quote") or "").strip()[:200]

        if score == max_sc:
            score_status = "entièrement satisfait"
        elif score > 0:
            score_status = "partiellement satisfait"
        else:
            score_status = "non satisfait"

        items.append({
            "id":         i,
            "critere":    c.get("label", ""),
            "reponse":    answer,
            "score":      f"{score}/{max_sc} pts ({score_status})",
            "confiance":  f"{conf}%",
            "analyse_ia": reason,
            "source":     quote,
        })

    prompt = (
        f"Tu es un analyste métier chez Leyton, cabinet de conseil en financement public.\n"
        f"Client : {client_name} | Produit : {product_name}\n\n"
        f"Pour chacun des {len(items)} critères ci-dessous, rédige une explication de 2 à 3 phrases "
        f"en français, professionnelle et précise.\n\n"
        f"Règles :\n"
        f"- Expliquer ce que signifie la réponse pour ce critère\n"
        f"- Indiquer pourquoi cette réponse conduit au score obtenu\n"
        f"- Compréhensible pour un directeur non technique\n"
        f"- Liée à la valeur réelle, pas générique\n"
        f"- Prudente si les données sont incertaines\n\n"
        f"Critères :\n"
        f"{json.dumps(items, ensure_ascii=False, indent=2)}\n\n"
        f'Réponds UNIQUEMENT avec un JSON valide : {{"0": "explication...", "1": "explication...", ...}}\n'
        f"Les clés sont les valeurs du champ \"id\"."
    )

    response = oai.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=min(150 * len(criteria_list), 2000),
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw: Dict[str, str] = json.loads(response.choices[0].message.content)

    # Return in original order, with template fallback for any missing key
    out: List[str] = []
    for i, c in enumerate(criteria_list):
        expl = raw.get(str(i)) or raw.get(i)  # type: ignore[call-overload]
        if not expl:
            expl = _template_fallback(
                c.get("label", ""), c.get("predicted_answer", ""),
                c.get("score", 0), c.get("max_score", 0), client_name,
            )
        out.append(str(expl).strip())
    return out


# ── Template helpers ──────────────────────────────────────────────────────────

def _format_existing(
    reasoning: str, answer: str, score: int, max_score: int,
    label: str, client_name: str,
) -> str:
    pct = round((score / max_score) * 100) if max_score else 0
    if score == max_score:
        suffix = f" Ce résultat confirme que {client_name} satisfait pleinement ce critère ({pct}% du score maximal)."
    elif score > 0:
        suffix = f" Ce résultat indique une conformité partielle ({pct}% du score maximal)."
    else:
        suffix = f" Ce résultat indique que le critère n'est pas satisfait pour {client_name}."
    return reasoning.rstrip(".") + "." + suffix


def _template_missing(label: str, client_name: str) -> str:
    return (
        f"Le critère « {label} » n'a pas pu être vérifié lors de l'analyse automatique. "
        f"Aucune information suffisamment fiable n'a été trouvée dans les sources consultées "
        f"(site web, LinkedIn, actualités, documents) pour confirmer ou infirmer ce point "
        f"pour {client_name}. Une vérification manuelle est recommandée."
    )


def _template_fallback(
    label: str, answer: str, score: int, max_score: int, client_name: str,
) -> str:
    pct = round((score / max_score) * 100) if max_score else 0
    if score == max_score:
        return (
            f"Pour le critère « {label} », la valeur identifiée est « {answer} ». "
            f"Cette réponse satisfait pleinement les conditions requises et contribue "
            f"à hauteur de {score}/{max_score} points au score de {client_name}."
        )
    if score > 0:
        return (
            f"Pour le critère « {label} », la valeur identifiée est « {answer} ». "
            f"Cette réponse satisfait partiellement les conditions requises ({pct}% du score maximal), "
            f"ce qui représente {score} point(s) sur {max_score} possibles."
        )
    return (
        f"Pour le critère « {label} », la valeur identifiée est « {answer} ». "
        f"Cette réponse ne satisfait pas les conditions requises pour ce critère, "
        f"ce qui explique un score de 0/{max_score} points pour {client_name}."
    )
