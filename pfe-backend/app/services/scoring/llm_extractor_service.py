from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.services.scoring.semantic_validator import SemanticValidator

logger = logging.getLogger(__name__)
_semantic_validator = SemanticValidator()

# Maximum characters from all passages combined sent to the LLM.
# Raised to 4000 to accommodate full PDF sections (Q&A blocks can be 1200 chars each).
# gpt-4o-mini supports 128K tokens so this adds negligible cost (~$0.0001 per call).
MAX_CONTEXT_CHARS = 4000

# ── JSON output schemas ──────────────────────────────────────────────────────

_NUMERIC_SCHEMA = """{
  "found": true or false,
  "extracted_value": <number, or null>,
  "evidence_sentence": "<verbatim sentence from PASSAGES that contains the number>",
  "context_before": "<sentence immediately before, or empty>",
  "context_after": "<sentence immediately after, or empty>",
  "section": "<section heading, or empty>",
  "confidence": <float 0.0–1.0>,
  "is_valid": true or false,
  "reasoning": "<one sentence explaining why the value is or is not valid>"
}"""

_CHOICE_SCHEMA = """{
  "found": true or false,
  "selected_labels": ["<exact label from OPTIONS>"],
  "evidence_sentence": "<verbatim sentence from PASSAGES that supports the selection>",
  "context_before": "<sentence before, or empty>",
  "context_after": "<sentence after, or empty>",
  "section": "<section heading, or empty>",
  "confidence": <float 0.0–1.0>,
  "is_valid": true or false,
  "reasoning": "<one sentence explaining the selection>"
}"""

_TEXT_SCHEMA = """{
  "found": true or false,
  "extracted_text": "<passage that answers the criterion, or null>",
  "evidence_sentence": "<verbatim sentence from PASSAGES>",
  "context_before": "<sentence before, or empty>",
  "context_after": "<sentence after, or empty>",
  "section": "<section heading, or empty>",
  "confidence": <float 0.0–1.0>,
  "is_valid": true or false,
  "reasoning": "<one sentence explaining validity>"
}"""

# ── Business validation constants (FR + ES + EN) ─────────────────────────────

_PCT_KEYWORDS = {
    # French
    "part", "taux", "pourcent", "proportion", "alternant", "%",
    # Spanish
    "porcentaje", "tasa", "proporción",
    # English
    "ratio", "percent", "percentage",
}
_RECRUIT_KEYWORDS = {
    # French
    "recrutement", "recrut", "embauche",
    # Spanish
    "contratación", "contratar", "reclutamiento", "selección",
    # English
    "hiring", "recruit",
}
_EMPLOYEE_KEYWORDS = {
    # French
    "effectif", "salarié", "employé", "collaborateur",
    # Spanish
    "empleado", "trabajador", "plantilla", "empleados", "trabajadores",
    # English
    "employee", "staff", "headcount", "workforce", "personnel",
}

# Evidence sentence quality: anchored UI/nav patterns at start of sentence
_JUNK_PATTERNS = re.compile(
    r"^(?:"
    # French nav
    r"accueil|retour|suivant|mentions légales|cgv|"
    # Spanish nav
    r"inicio|volver|siguiente|política de privacidad|aviso legal|"
    r"condiciones de uso|mapa del sitio|"
    # English nav
    r"home|back|next|"
    # Generic
    r"menu|navigation|footer|header|cookies?|copyright|©|\d{4}\s*[-–]\s*\d{4}"
    r")",
    re.I,
)

# UI noise anywhere in the evidence sentence
_NOISE_IN_EVIDENCE = re.compile(
    r"s'inscrire|se connecter|connexion|"                          # FR auth
    r"registrarse|iniciar.?sesión|cerrar.?sesión|"                 # ES auth
    r"sign in|sign up|log in|log out|"                             # EN auth
    r"check your spam|vérifiez vos spams|compruebe su spam|"       # spam
    r"cookie|privacy policy|politique de confidentialit|"
    r"política de privacidad|aviso legal|"
    r"terms of service|conditions d.utilisation|términos de uso|"
    r"renvoyer l.e-mail|resend|reenviar|forgot password|"
    r"télécharger l.application|download the app|descargar la app|"
    r"mot de passe|contraseña|password|e-mail address",
    re.IGNORECASE,
)

# ── Domain relevance keywords (FR + ES + EN) ─────────────────────────────────
# Evidence must contain at least one of these substrings to be considered
# semantically relevant to an eligibility criterion.
_DOMAIN_SUBSTRINGS: List[str] = [
    # ── Headcount / staffing ──────────────────────────────────────────────────
    # FR
    "effectif", "salari", "employé", "collaborateur",
    # ES
    "empleado", "trabajador", "plantilla", "personal",
    # EN
    "employee", "staff", "headcount", "workforce",
    # ── Recruitment ──────────────────────────────────────────────────────────
    # FR
    "recrutement", "recrut", "embauche", "embaucher",
    # ES
    "contratación", "contratar", "reclutamiento", "selección de personal",
    # EN
    "hiring", "hire",
    # ── Apprenticeship / alternance ───────────────────────────────────────────
    # FR
    "alternant", "alternance", "apprenti", "apprentissage", "professionnalis",
    # ES
    "aprendiz", "prácticas", "formación dual", "becario",
    # ── Training ─────────────────────────────────────────────────────────────
    # FR
    "formation", "plan de formation", "cpf", "opco",
    # ES
    "capacitación", "formación profesional", "curso",
    # EN
    "training",
    # ── HR / company structure ────────────────────────────────────────────────
    # FR
    "ressources humaines",
    # ES
    "recursos humanos", "rrhh",
    # EN
    "human resources",
    # ── R&D / innovation ─────────────────────────────────────────────────────
    # FR
    "recherche", "développement",
    # ES
    "investigación", "desarrollo", "i+d",
    # EN/Universal
    "innovation", "r&d", "technologie", "tecnología", "technology",
    # ── Finance / revenue ─────────────────────────────────────────────────────
    # FR
    "chiffre d'affaires", "revenus", "bénéfice",
    # ES
    "facturación", "ingresos", "beneficio", "cifra de negocios", "ventas",
    # EN
    "revenue", "turnover", "profit",
    # ── Energy / environment ──────────────────────────────────────────────────
    # FR
    "énergie", "consommation", "émissions", "carbone",
    # ES
    "energía", "consumo", "emisiones", "carbono", "huella",
    # EN
    "energy", "carbon", "emissions",
    # ── Tax / fiscal ──────────────────────────────────────────────────────────
    # FR
    "fiscalité", "taxe", "impôt", "déduction",
    # ES
    "impuesto", "tributario", "fiscal", "deducción", "hacienda",
    # EN
    "tax", "deduction",
    # ── Size / growth ─────────────────────────────────────────────────────────
    # FR
    "croissance", "taille", "entreprise", "société",
    # ES
    "crecimiento", "tamaño", "empresa", "sociedad",
    # EN
    "growth", "company", "organization",
]


class ExtractionResult(BaseModel):
    found: bool = False
    extracted_value: Optional[Any] = None
    evidence_sentence: str = ""
    context_before: str = ""
    context_after: str = ""
    section: str = ""
    confidence: float = 0.0
    is_valid: bool = False
    reasoning: str = ""
    source_type: str = ""
    source_url: Optional[str] = None
    source_label: str = ""
    clickable_url: Optional[str] = None


class LLMExtractorService:
    """
    Extracts a single answer from pre-selected, semantically relevant passages.

    Uses OpenAI API (gpt-4o-mini) when OPENAI_API_KEY is configured — fast and
    accurate. Falls back to local Ollama for offline / no-key environments.
    """

    def __init__(self) -> None:
        if settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key, timeout=60.0, max_retries=1)
            self._model  = settings.openai_model
            logger.info("LLMExtractor: using OpenAI (%s)", self._model)
        else:
            self._client = OpenAI(
                base_url=settings.ollama_base_url,
                api_key="ollama",
                timeout=300.0,
                max_retries=0,
            )
            self._model = settings.ollama_model
            logger.info("LLMExtractor: using Ollama (%s)", self._model)

    # ── Public API ──────────────────────────────────────────────────────────

    def extract(
        self,
        criterion_label: str,
        answer_type: str,
        unit: str,
        choices: List[Dict[str, Any]],
        passages: List[Dict[str, Any]],
    ) -> ExtractionResult:
        """
        Extract an answer from a ranked list of passage dicts.
        Each passage: {text, source_label, source_url, source_type, section, similarity}
        Returns ExtractionResult with is_valid=False when nothing reliable is found.
        """
        if not passages:
            return ExtractionResult(reasoning="No relevant passages retrieved for this criterion.")

        # ── LLM Cache check ──────────────────────────────────────────────────
        _passage_texts = [p.get("text", "") for p in passages[:5]]
        try:
            from app.services.cache.llm_cache import get_extraction, set_extraction as _set_llm
            _cached_extraction = get_extraction(criterion_label, answer_type, _passage_texts)
            if _cached_extraction:
                return ExtractionResult(**{
                    k: v for k, v in _cached_extraction.items()
                    if k in ExtractionResult.model_fields
                })
        except Exception:
            _set_llm = None

        # ── RAG: retrieve few-shot examples for this criterion type ──────────
        _few_shot_block = ""
        try:
            from app.services.rag.knowledge_base import retrieve_examples, format_examples_for_prompt
            _examples = retrieve_examples(criterion_label, answer_type, label_embedding=None)
            if _examples:
                _few_shot_block = format_examples_for_prompt(_examples) + "\n\n"
        except Exception:
            pass

        # Build combined context from top passages (capped at MAX_CONTEXT_CHARS)
        context_blocks: List[str] = []
        used_passages: List[Dict[str, Any]] = []
        total = 0
        for p in passages:
            block = (
                f"[Source: {p.get('source_label', '?')} | "
                f"Section: {p.get('section', '') or 'general'} | "
                f"Relevance: {p.get('similarity', 0):.2f}]\n"
                f"{p['text']}"
            )
            if total + len(block) > MAX_CONTEXT_CHARS:
                break
            context_blocks.append(block)
            used_passages.append(p)
            total += len(block)

        context = _few_shot_block + "\n\n---\n\n".join(context_blocks)

        # Source metadata is resolved AFTER extraction, based on which passage
        # actually contains the evidence sentence (see _resolve_source below).
        # Use top passage as initial fallback.
        base = dict(
            source_type=passages[0].get("source_type", ""),
            source_url=passages[0].get("source_url"),
            source_label=passages[0].get("source_label", ""),
        )

        try:
            if answer_type == "numeric":
                result = self._numeric(criterion_label, unit, context, base)
            elif answer_type in ("single_choice", "multiple_choice"):
                result = self._choice(criterion_label, answer_type, choices, context, base)
            else:
                result = self._text(criterion_label, context, base)
        except Exception as exc:
            exc_str = str(exc)
            if "insufficient_quota" in exc_str or "quota" in exc_str.lower():
                reason = "LLM unavailable: OpenAI quota exhausted. Add credits at platform.openai.com/account/billing."
                logger.warning("LLM quota exhausted for criterion: %s", criterion_label[:60])
            elif "429" in exc_str:
                reason = "LLM unavailable: rate limited. Retry in a few seconds."
                logger.warning("LLM rate limited for criterion: %s", criterion_label[:60])
            else:
                reason = "LLM extraction failed — no answer available."
                logger.error("LLM extraction error | criterion=%s | error=%s", criterion_label[:60], exc)
            return ExtractionResult(reasoning=reason, **base)

        # Resolve source attribution to the passage that actually contains the evidence
        if result.evidence_sentence:
            evidence_source = _resolve_source(result.evidence_sentence, used_passages)
            result.source_type  = evidence_source.get("source_type", result.source_type)
            result.source_url   = evidence_source.get("source_url",  result.source_url)
            result.source_label = evidence_source.get("source_label", result.source_label)
            result.clickable_url = _build_clickable_url(evidence_source, result.evidence_sentence)

        # Business-rule validation (modifies in place)
        result = self._validate(result, criterion_label, unit, answer_type, choices)

        # ── Persist to LLM cache and RAG knowledge base ──────────────────────
        if result.is_valid and result.confidence >= 0.4:
            try:
                from app.services.cache.llm_cache import set_extraction as _set_llm_cache
                _set_llm_cache(criterion_label, answer_type, _passage_texts, result.model_dump())
            except Exception:
                pass
            try:
                from app.services.rag.knowledge_base import store_entry
                store_entry(
                    criterion_id=criterion_label,
                    criterion_label=criterion_label,
                    answer_type=answer_type,
                    predicted_answer=str(result.predicted_answer or ""),
                    confidence=result.confidence,
                    evidence_sentence=result.evidence_sentence or "",
                    reasoning=result.reasoning or "",
                    label_embedding=None,
                )
            except Exception:
                pass

        return result

    # ── Type-specific extractors ────────────────────────────────────────────

    def _numeric(
        self, label: str, unit: str, context: str, base: Dict
    ) -> ExtractionResult:
        label_lower = label.lower()
        is_pct = any(kw in label_lower or kw in (unit or "").lower() for kw in _PCT_KEYWORDS)

        bounds_hint = (
            "The value MUST be between 0 and 100 since this is a percentage."
            if is_pct else
            "Sanity-check: reject if the number is implausibly large (>50 000 for headcount, >100 for percentage)."
        )

        # Build threshold hint if choices provide only range conditions (< X or >= X)
        # This lets the LLM reason from qualitative statements like "several tens of millions"
        threshold_hint = ""
        if choices:
            thresholds = []
            for ch in choices:
                body = (ch.get("condition") or {}).get("body", "")
                import re as _re
                m = _re.search(r"([<>]=?)\s*([\d.]+)", body)
                if m:
                    thresholds.append(f"{m.group(1)} {m.group(2)} {unit or ''} → {ch.get('score',0)} pts")
            if thresholds:
                threshold_hint = (
                    f"\nSCORING THRESHOLDS (use these to interpret qualitative amounts):\n"
                    + "\n".join(f"  • {t}" for t in thresholds)
                    + "\nIf the passages give a qualitative amount (e.g. 'several tens of millions'), "
                    "convert it to the most defensible numeric estimate and use it as extracted_value. "
                    "Set confidence to 0.55 and note the estimation in reasoning.\n"
                )

        prompt = (
            f"You extract company data for an eligibility assessment.\n\n"
            f"CRITERION (in French): {label}\n"
            f"UNIT: {unit or 'not specified'}\n\n"
            f"LANGUAGE NOTE: The criterion is in French but passages may be in French, Spanish, or English. "
            f"Apply the same extraction logic regardless of language. "
            f"Match semantically: 'effectif'='empleados'='employees', 'chiffre d affaires'='facturación'='revenue', etc.\n\n"
            f"PASSAGES (pre-selected as most relevant):\n\"\"\"\n{context}\n\"\"\"\n\n"
            f"TASK: Find the single number that directly and explicitly quantifies '{label}' (in any language).\n"
            f"If no exact number exists but the passage gives a clear qualitative range "
            f"(e.g. 'plusieurs dizaines de millions', 'más de 100', 'more than 100', 'under 50'), "
            f"extract the most conservative defensible estimate.\n\n"
            f"STRICT REJECTION RULES — set found=false, extracted_value=null, is_valid=false if:\n"
            f"• The number comes from a page title, navigation, footer, copyright, or meta text\n"
            f"• The number is a price, phone number, postal code, year, SIRET/SIREN, CIF, NIF, or registration ID\n"
            f"• The number is used in a sentence unrelated to '{label}'\n"
            f"• The evidence_sentence is empty, shorter than 10 words, or identical to the criterion\n"
            f"• No sentence in the passages quantifies or estimates '{label}' in any way\n"
            f"{bounds_hint}"
            f"{threshold_hint}\n"
            f"The evidence_sentence field MUST be a verbatim copy of an existing sentence in PASSAGES.\n"
            f"Do NOT paraphrase or construct a sentence. If you cannot find one, set found=false.\n\n"
            f"Respond with ONLY valid JSON — no markdown, no explanation outside the JSON:\n"
            f"{_NUMERIC_SCHEMA}"
        )
        raw = self._call(prompt)
        return ExtractionResult(
            found=bool(raw.get("found")),
            extracted_value=raw.get("extracted_value"),
            evidence_sentence=str(raw.get("evidence_sentence", "")),
            context_before=str(raw.get("context_before", "")),
            context_after=str(raw.get("context_after", "")),
            section=str(raw.get("section", "")),
            confidence=_safe_float(raw.get("confidence")),
            is_valid=bool(raw.get("is_valid")),
            reasoning=str(raw.get("reasoning", "")),
            **base,
        )

    def _choice(
        self,
        label: str,
        answer_type: str,
        choices: List[Dict[str, Any]],
        context: str,
        base: Dict,
    ) -> ExtractionResult:
        valid_labels = [c.get("label", "") for c in choices if c.get("label")]
        is_multi = answer_type == "multiple_choice"

        # Explain range-style labels (e.g. "< 2", ">= 2") so the LLM understands them
        range_hint = ""
        import re as _re
        range_labels = [l for l in valid_labels if _re.match(r'^[<>]=?\s*\d', l.strip())]
        if range_labels:
            range_hint = (
                f"\nNOTE: The OPTIONS use range labels (e.g. '< 2', '>= 2'). "
                f"They refer to the COUNT or QUANTITY implied by the criterion. "
                f"Read the passage, estimate the count/quantity, then select the matching range label.\n"
            )

        prompt = (
            f"You determine which option applies to a company for an eligibility assessment.\n\n"
            f"CRITERION (in French): {label}\n"
            f"OPTIONS (copy one exactly): {json.dumps(valid_labels, ensure_ascii=False)}\n"
            f"SELECTION TYPE: {'Multiple options allowed' if is_multi else 'Single option only'}"
            f"{range_hint}\n\n"
            f"LANGUAGE NOTE: The criterion is in French but passages may be in French, Spanish, or English. "
            f"Reason semantically across languages to match the criterion's intent to the passage content.\n\n"
            f"PASSAGES (pre-selected as most relevant):\n\"\"\"\n{context}\n\"\"\"\n\n"
            f"TASK: Select an option ONLY when the PASSAGES contain a clear, explicit statement "
            f"that directly answers '{label}' (in any language).\n\n"
            f"STRICT RULES:\n"
            f"• selected_labels must contain only values copied exactly from OPTIONS above\n"
            f"• Do NOT infer from indirect signals (e.g. social media presence, industry type)\n"
            f"• Do NOT select based on absence of evidence\n"
            f"• The evidence_sentence must be verbatim from PASSAGES and directly support the selection\n"
            f"• If evidence is weak, ambiguous, or absent, set found=false and selected_labels=[]\n\n"
            f"Respond with ONLY valid JSON — no markdown, no explanation outside the JSON:\n"
            f"{_CHOICE_SCHEMA}"
        )
        raw = self._call(prompt)

        # Enforce: selected labels must be from the valid list
        raw_selected: List[str] = raw.get("selected_labels") or []
        if not isinstance(raw_selected, list):
            raw_selected = []
        selected = [lbl for lbl in raw_selected if lbl in valid_labels]

        extracted: Any = (
            selected[0] if (selected and not is_multi)
            else (selected or None)
        )
        return ExtractionResult(
            found=bool(raw.get("found")) and bool(selected),
            extracted_value=extracted,
            evidence_sentence=str(raw.get("evidence_sentence", "")),
            context_before=str(raw.get("context_before", "")),
            context_after=str(raw.get("context_after", "")),
            section=str(raw.get("section", "")),
            confidence=_safe_float(raw.get("confidence")),
            is_valid=bool(raw.get("is_valid")) and bool(selected),
            reasoning=str(raw.get("reasoning", "")),
            **base,
        )

    def _text(self, label: str, context: str, base: Dict) -> ExtractionResult:
        prompt = (
            f"You extract company data for an eligibility assessment.\n\n"
            f"CRITERION (in French): {label}\n\n"
            f"LANGUAGE NOTE: The criterion is in French but passages may be in French, Spanish, or English. "
            f"Extract information semantically: understand what the French criterion is asking, "
            f"then find the answer in the passage regardless of its language.\n\n"
            f"PASSAGES (pre-selected as most relevant):\n\"\"\"\n{context}\n\"\"\"\n\n"
            f"TASK: Find the passage that most specifically and directly answers '{label}' (in any language).\n\n"
            f"STRICT RULES:\n"
            f"• Do NOT return generic marketing text, slogans, or page titles\n"
            f"• Do NOT infer or paraphrase — the evidence must be explicit in the text\n"
            f"• If no passage specifically addresses '{label}', set found=false and is_valid=false\n\n"
            f"Respond with ONLY valid JSON — no markdown, no explanation outside the JSON:\n"
            f"{_TEXT_SCHEMA}"
        )
        raw = self._call(prompt)
        return ExtractionResult(
            found=bool(raw.get("found")),
            extracted_value=raw.get("extracted_text"),
            evidence_sentence=str(raw.get("evidence_sentence", "")),
            context_before=str(raw.get("context_before", "")),
            context_after=str(raw.get("context_after", "")),
            section=str(raw.get("section", "")),
            confidence=_safe_float(raw.get("confidence")),
            is_valid=bool(raw.get("is_valid")),
            reasoning=str(raw.get("reasoning", "")),
            **base,
        )

    # ── Business validation ─────────────────────────────────────────────────

    def _validate(
        self,
        result: ExtractionResult,
        label: str,
        unit: str,
        answer_type: str,
        choices: List[Dict[str, Any]],
    ) -> ExtractionResult:
        """
        Apply deterministic business rules after LLM extraction.
        Sets is_valid=False and clears the value when a rule fires.
        Prefers returning "unknown" over a hallucinated answer.
        """
        if not result.found or result.extracted_value is None:
            return result

        label_lower = label.lower()
        unit_lower = (unit or "").lower()

        # ── Evidence quality ────────────────────────────────────────────────
        ev = result.evidence_sentence.strip()
        if not ev or len(ev.split()) < 3:
            return self._invalidate(result, "Evidence sentence too short or missing.")

        # Hard reject: UI/noise phrases inside the evidence sentence
        if _NOISE_IN_EVIDENCE.search(ev):
            return self._invalidate(result, "Evidence contains UI/noise text (login, cookies, spam, etc.).")

        if _JUNK_PATTERNS.match(ev):
            return self._invalidate(result, "Evidence looks like navigation/title text.")

        # Reject if model recycled the criterion label as evidence
        label_words = set(re.sub(r"[^\w\s]", "", label_lower).split())
        ev_words = set(re.sub(r"[^\w\s]", "", ev.lower()).split())
        overlap = len(label_words & ev_words) / max(len(label_words), 1)
        if overlap > 0.75 and len(ev_words) < len(label_words) + 4:
            return self._invalidate(result, "Evidence appears to recycle the criterion text.")

        # ── Domain relevance check ───────────────────────────────────────────
        # For single/multiple choice criteria, the topic-match check below is
        # sufficient — skip the narrow HR/R&D keyword list so that evidence
        # about emballage, énergie, gaz, fiscal, etc. is not wrongly rejected.
        ev_lower = ev.lower()
        if answer_type not in ("single_choice", "multiple_choice"):
            has_domain_keyword = any(kw in ev_lower for kw in _DOMAIN_SUBSTRINGS)
            # Also accept if the criterion's own content words appear in the evidence
            criterion_content_words = {
                w for w in re.sub(r"[^\w]", " ", label_lower).split() if len(w) > 4
            }
            if not has_domain_keyword and not any(w in ev_lower for w in criterion_content_words):
                return self._invalidate(
                    result,
                    "Evidence contains no domain-relevant keywords.",
                )

        # ── Numeric-specific rules ──────────────────────────────────────────
        if answer_type == "numeric":
            try:
                val = float(result.extracted_value)
            except (TypeError, ValueError):
                return self._invalidate(result, f"extracted_value {result.extracted_value!r} is not numeric.")

            is_pct = any(kw in label_lower or kw in unit_lower for kw in _PCT_KEYWORDS)
            if is_pct and not (0.0 <= val <= 100.0):
                return self._invalidate(
                    result,
                    f"Percentage value {val} is outside [0, 100]. Likely a hallucination.",
                )

            is_recruit = any(kw in label_lower for kw in _RECRUIT_KEYWORDS)
            if is_recruit and (val <= 0 or val > 20_000):
                return self._invalidate(
                    result,
                    f"Recruitment count {val} is outside plausible range (1–20 000).",
                )

            is_employee = any(kw in label_lower for kw in _EMPLOYEE_KEYWORDS)
            if is_employee and (val <= 0 or val > 500_000):
                return self._invalidate(
                    result,
                    f"Employee count {val} is outside plausible range (1–500 000).",
                )

            # ── Semantic context validation (blocklist + domain anchors) ────
            ok, sem_reason = _semantic_validator.validate_numeric(
                criterion_label=label,
                value=val,
                match_text=ev,
                match_start=0,
                match_end=len(ev),
                full_text=ev,
            )
            if not ok:
                return self._invalidate(result, sem_reason)

        # ── Choice-specific rules ───────────────────────────────────────────
        if answer_type in ("single_choice", "multiple_choice"):
            valid_labels = {c.get("label", "") for c in choices}
            if isinstance(result.extracted_value, list):
                clean = [v for v in result.extracted_value if v in valid_labels]
                if not clean:
                    return self._invalidate(result, "No selected label matches the valid choices.")
                result.extracted_value = clean
            elif result.extracted_value not in valid_labels:
                return self._invalidate(
                    result,
                    f"Selected label {result.extracted_value!r} is not in the valid options.",
                )

            # For single_choice, require the evidence to explicitly address
            # the criterion topic — not just contain any domain word.
            # Build a reduced set from the criterion label itself.
            criterion_stems = {
                w for w in re.sub(r"[^\w]", " ", label_lower).split()
                if len(w) > 4
            }
            ev_lower_norm = re.sub(r"[^\w]", " ", ev.lower())
            topic_match = any(stem in ev_lower_norm for stem in criterion_stems)
            if not topic_match and result.confidence < 0.75:
                return self._invalidate(
                    result,
                    "Evidence does not directly address the criterion topic. "
                    "Confidence too low to accept indirect inference.",
                )

        # ── Confidence floor ────────────────────────────────────────────────
        if result.confidence < 0.40:
            return self._invalidate(
                result,
                f"Confidence {result.confidence:.2f} is below threshold (0.40).",
            )

        return result

    @staticmethod
    def _invalidate(result: ExtractionResult, reason: str) -> ExtractionResult:
        result.is_valid = False
        result.found = False
        result.extracted_value = None
        result.reasoning = reason
        result.confidence = min(result.confidence, 0.20)
        logger.debug("Extraction invalidated: %s", reason)
        return result

    # ── LLM call ────────────────────────────────────────────────────────────

    def _call(self, prompt: str) -> Dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=300,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict data extraction assistant for company eligibility assessments. "
                        "Criteria are written in French, but passages may be in French, Spanish, English, or any other language. "
                        "You MUST extract information from passages regardless of their language, "
                        "matching the semantic meaning of the French criterion to the content in any language. "
                        "For example, 'effectif' (FR) = 'empleados/plantilla' (ES) = 'employees/headcount' (EN). "
                        "'chiffre d affaires' (FR) = 'facturación/ingresos' (ES) = 'revenue/turnover' (EN). "
                        "'recherche et développement' (FR) = 'investigación y desarrollo/I+D' (ES) = 'R&D' (EN). "
                        "Apply the same reasoning quality regardless of the source language. "
                        "Only extract values explicitly stated in the provided passages. "
                        "Never infer or hallucinate. Respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return _parse_json(response.choices[0].message.content or "{}")


# ── Shared utilities ─────────────────────────────────────────────────────────

def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse JSON from model output: %.200s", text)
    return {}


def _safe_float(val: Any) -> float:
    try:
        return max(0.0, min(1.0, float(val)))
    except (TypeError, ValueError):
        return 0.0


def _resolve_source(evidence_sentence: str, passages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return the passage most likely to contain the evidence sentence.
    Word-overlap scoring: the passage whose text shares the most words
    with the evidence sentence wins. Falls back to the top passage.
    """
    if not passages:
        return {}
    ev_words = set(re.sub(r"[^\w\s]", " ", evidence_sentence.lower()).split())
    if not ev_words:
        return passages[0]
    best, best_score = passages[0], 0
    for p in passages:
        p_words = set(re.sub(r"[^\w\s]", " ", p.get("text", "").lower()).split())
        score = len(ev_words & p_words)
        if score > best_score:
            best_score, best = score, p
    return best


def _build_clickable_url(passage: Dict[str, Any], evidence: str) -> Optional[str]:
    """
    Build a URL that opens the source page and jumps directly to the evidence text.

    Uses the Text Fragment API (#:~:text=…) supported by Chrome, Edge, and
    most modern browsers. When the user clicks the link, the browser scrolls to
    and highlights the exact sentence in yellow — no manual searching needed.
    """
    url = passage.get("source_url") or ""
    if not url:
        return None

    # Take the most distinctive 10-word slice from the evidence as the fragment
    words = evidence.strip().split()
    # Use first 8 words as prefix and last 4 words as suffix for precise targeting
    prefix = " ".join(words[:8]) if words else ""
    suffix = " ".join(words[-4:]) if len(words) > 8 else ""

    if not prefix:
        return url

    from urllib.parse import quote
    fragment_prefix = quote(prefix, safe="")
    if suffix and suffix != prefix:
        fragment = f"{fragment_prefix},{quote(suffix, safe='')}"
    else:
        fragment = fragment_prefix

    base = url.split("#")[0].split("?")[0]
    return f"{base}#:~:text={fragment}"
