from __future__ import annotations

import re
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Patterns that ALWAYS invalidate a numeric extraction regardless of context.
# A number is rejected if any of these appear within 60 chars before/after it.
# ---------------------------------------------------------------------------
_NUMERIC_BLOCKLIST: List[str] = [
    r"%\s*off",
    r"off\b",
    r"discount",
    r"remise",
    r"réduction",
    r"promo(?:tion)?",
    r"coupon",
    r"voucher",
    r"rabais",
    r"soldes?",
    r"newsletter",
    r"sign\s+up",
    r"inscri[a-z]+",
    r"first\s+purchase",
    r"premier\s+achat",
    r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}",    # date pattern
    r"\+\d{6,}",                               # phone number
    r"\b\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}",    # French phone  06 12 34 56
    r"€|£|\$|USD|EUR",                         # currency
    r"prix|price|cost|tarif|forfait",
    r"tél(?:éphone)?|phone|mobile|fax",
    r"code\s+postal|zip",
    r"siret|siren|tva",
]

_COMPILED_BLOCKLIST = [re.compile(p, re.IGNORECASE) for p in _NUMERIC_BLOCKLIST]


# ---------------------------------------------------------------------------
# Domain anchor vocabulary.
# For a given criterion label, derive which context words MUST appear near
# a valid extracted number.
# ---------------------------------------------------------------------------

_DOMAIN_ANCHORS: List[Tuple[List[str], List[str]]] = [
    # People / headcount
    (
        ["personnes", "people", "effectif", "salarié", "employé", "collaborateur",
         "staff", "workforce", "équipe", "team", "travaill", "member"],
        ["personnes?", "people", "effectifs?", "salariés?", "employés?",
         "collaborateurs?", "staff", "workforce", "équipe", "team",
         "travaill\w*", "membres?", "individus?", "chercheurs?", "ingénieurs?",
         "experts?", "ressources?"],
    ),
    # Project / R&D
    (
        ["projet", "project", "r&d", "recherche", "innovation", "développement",
         "travaux", "programme"],
        ["projets?", "project", "r&d", "recherch\w*", "innovation",
         "développement", "travaux", "programme\w*", "activit\w*"],
    ),
    # Recruitment / hiring
    (
        ["recrutement", "recrut", "embauche", "hire", "poste", "profil", "candidat"],
        ["recrut\w*", "embauch\w*", "hir\w*", "postes?", "profils?",
         "candidats?", "offres?", "emploi\w*"],
    ),
    # Apprenticeship / alternance
    (
        ["alternant", "apprenti", "alternance", "apprentissage", "contrat"],
        ["alternants?", "apprentis?", "alternance", "apprentissage",
         "contrats?", "cfa"],
    ),
    # Training / formation
    (
        ["formation", "train", "plan", "collaborateurs"],
        ["formations?", "train\w*", "plans?", "collaborateurs?", "programme\w*"],
    ),
    # Contact / account details
    (
        ["contact", "coordonnées", "account", "details", "disponible", "créneau",
         "date", "échange", "rendez"],
        ["contact\w*", "coordonnées?", "compte\w*", "détails?", "disponib\w*",
         "créneau\w*", "dates?", "échange\w*", "rendez.vous", "réunion\w*"],
    ),
]


def _derive_anchors(label: str) -> List[str]:
    """
    Return a list of regex patterns that must appear near a numeric value
    for the extraction to be considered semantically valid.
    """
    label_lower = label.lower()
    anchors: List[str] = []
    for trigger_kws, anchor_patterns in _DOMAIN_ANCHORS:
        if any(kw in label_lower for kw in trigger_kws):
            anchors.extend(anchor_patterns)
    return anchors


class SemanticValidator:
    """
    Validates extracted answers against the criterion label semantics.
    Operates entirely on the text window around the match — no LLM call needed.
    """

    # Window size (chars) to look around a matched number
    CONTEXT_WINDOW = 120

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def validate_numeric(
        self,
        criterion_label: str,
        value: float,
        match_text: str,
        match_start: int,
        match_end: int,
        full_text: str,
    ) -> Tuple[bool, str]:
        """
        Return (True, "") if the extraction is semantically valid.
        Return (False, reason) if it must be rejected.
        """
        window = self._context_window(full_text, match_start, match_end)

        # 1 — Block if a known bad pattern is present near the number
        for pattern in _COMPILED_BLOCKLIST:
            if pattern.search(window):
                return False, (
                    f"Rejected: the number appears near a blocked pattern "
                    f"({pattern.pattern!r}) in context: «{window[:120]}»"
                )

        # 2 — Check that at least one semantic anchor word is near the number
        required_anchors = _derive_anchors(criterion_label)
        if required_anchors:
            combined = "|".join(required_anchors)
            if not re.search(combined, window, re.IGNORECASE):
                return False, (
                    f"Rejected: no semantic anchor for criterion «{criterion_label}» "
                    f"found near the value {value} in context: «{window[:120]}»"
                )

        return True, ""

    def validate_text(
        self,
        criterion_label: str,
        extracted_text: str,
    ) -> Tuple[bool, str]:
        """
        Return (True, "") if the extracted text plausibly answers the criterion.
        Return (False, reason) if the text is semantically unrelated.
        """
        if not extracted_text or not extracted_text.strip():
            return False, "Empty extracted text."

        required_anchors = _derive_anchors(criterion_label)
        if not required_anchors:
            # No domain defined → accept any non-empty text (unclassified criterion)
            return True, ""

        combined = "|".join(required_anchors)
        if re.search(combined, extracted_text, re.IGNORECASE):
            return True, ""

        return False, (
            f"Extracted text does not address the criterion «{criterion_label}». "
            f"No relevant keyword found in: «{extracted_text[:120]}»"
        )

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _context_window(
        self, text: str, start: int, end: int
    ) -> str:
        w = self.CONTEXT_WINDOW
        left = max(0, start - w)
        right = min(len(text), end + w)
        return text[left:right]
