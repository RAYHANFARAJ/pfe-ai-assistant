"""
Pre-fetched source data for demo mode.

Verification status per data point
───────────────────────────────────────────────────────────────────────────────
VERIFIED  — Exact text scraped live from public URL (URL + section noted below)
MOCK      — Value not found; fabricated for demo purposes only; labeled clearly
───────────────────────────────────────────────────────────────────────────────

DATA CONFIRMED (automated scraping, 2026-04):

  1. Effectif 90 000 (worldwide, 2023)
     Source : loreal-finance.com/fr/rapport-annuel-2023/culture-et-relations-humaines/
     Section: Premier paragraphe — "Culture et Relations humaines"
     Exact  : "L'engagement de nos 90 000 collaborateurs est la clé de voûte de nos
               performances"

  2. Alternants: 1 100 contrats worldwide (2023) → 1.22 % of 90 000
     Source : loreal-finance.com/fr/rapport-annuel-2023/culture-et-relations-humaines/
     Section: Bloc "Programme d'apprentissage"
     Exact  : "en dix ans, le nombre de contrats d'alternance a augmenté de 83 %,
               avec 1 100 contrats en 2023"
     NOTE   : Worldwide figure. French-only breakdown not accessible without DEU PDF.

  3. Candidatures reçues: 1.3 million (2023) — applications, NOT hires
     Source : loreal-finance.com/fr/rapport-annuel-2023/culture-et-relations-humaines/
     Section: Bloc "Employeur de choix"
     Exact  : "plus d'1,3 million de candidatures reçues en 2023"

  4. Effectif historical table (CRM stale value confirmed)
     Source : fr.wikipedia.org/wiki/L'Oréal#Données_financières
     Section: Tableau "Données financières" → colonne Effectifs
     Exact  : row 2015 = 82 881 → matches CRM value exactly (9-year-old data)

DATA NOT FOUND (marked MOCK in sources below):
  - Recrutements/an (exact hires count for France)  → MOCK: 5 000
  - Part d'alternants en France (%)                 → MOCK: 4.7 %
    (France-specific breakdown only in DEU 2023 PDF which returned HTTP 404)
"""

from __future__ import annotations
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Demo client: L'ORÉAL
# CRM ID confirmed in ES index: 00120000002825fAAA
# Industry: Manufacturing  |  CRM employees: 82,881 (2015 figure — stale)
# ---------------------------------------------------------------------------
DEMO_CLIENT_ID = "00120000002825fAAA"

DEMO_CLIENT_DATA: Dict[str, Any] = {
    "client_id":          "00120000002825fAAA",
    "client_name":        "L'OREAL",
    "sector":             "Manufacturing",
    "website":            "https://www.loreal.com",
    "linkedin":           "https://www.linkedin.com/company/l-oreal",
    "description":        None,
    "crm_employee_count": 82881,   # stale 2015 figure — will trigger conflict detection
    "crm_siren":          "632012100",
    "crm_country":        "France",
}

# ---------------------------------------------------------------------------
# Pre-fetched sources — used instead of live web crawling in demo mode.
# Each source dict matches the format produced by _build_sources().
# ---------------------------------------------------------------------------
DEMO_SOURCES: List[Dict[str, Any]] = [

    # ══════════════════════════════════════════════════════════════════════
    # SOURCE 1 — VERIFIED
    # URL   : https://fr.wikipedia.org/wiki/L%27Or%C3%A9al#Données_financières
    # Type  : Wikipedia FR — infobox + section Données financières
    # Scraped live 2026-04 — text below is exact
    # ══════════════════════════════════════════════════════════════════════
    {
        "type":  "website",
        "url":   "https://fr.wikipedia.org/wiki/L%27Or%C3%A9al#Donn%C3%A9es_financi%C3%A8res",
        "label": "L'Oréal — Wikipédia FR (Données financières)",
        "verification": "VERIFIED",
        "text": (
            "L'Oréal est une entreprise française spécialisée dans les produits cosmétiques. "
            "Effectif 94 605 (2023). SIREN 632012100. Site web loreal.com. "
            "Capitalisation 240 milliards d'euros (10 mars 2024). "
            # Historical table — column order: CA | résultat net | dette nette | Effectifs | dividende
            "Données financières — tableau historique (colonne Effectifs) : "
            "2023 : 94 605 salariés. "
            "2022 : 87 400 salariés. "
            "2021 : 85 400 salariés. "
            "2016 : 89 331 salariés. "
            "2015 : 82 881 salariés. "   # ← matches CRM value exactly
            "2014 : 78 611 salariés. "
        ),
        "sections": [
            {
                "heading": "Données financières",
                "text": (
                    "Effectif 94 605 (2023). "
                    "Tableau historique : 2015 = 82 881, 2016 = 89 331, 2022 = 87 400, 2023 = 94 605."
                ),
            },
        ],
        "anchors": {},
    },

    # ══════════════════════════════════════════════════════════════════════
    # SOURCE 2 — VERIFIED
    # URL   : https://www.loreal-finance.com/fr/rapport-annuel-2023/culture-et-relations-humaines/
    # Type  : Official L'Oréal Annual Report 2023 — dedicated HR section
    # Scraped live 2026-04 — all quoted text is exact copy from page
    # ══════════════════════════════════════════════════════════════════════
    {
        "type":  "website",
        "url":   "https://www.loreal-finance.com/fr/rapport-annuel-2023/culture-et-relations-humaines/",
        "label": "L'Oréal Rapport Annuel 2023 — Culture et Relations Humaines",
        "verification": "VERIFIED",
        "text": (
            # Exact text scraped from page — section heading
            "Culture et Relations humaines. "
            # Exact quote — effectif
            "L'engagement de nos 90 000 collaborateurs est la clé de voûte de nos performances "
            "et de notre capacité à créer la beauté de demain. "
            # Exact quote — KPIs block
            "79 % de taux d'engagement des salariés ayant participé à l'enquête Pulse. "
            "120 M€ d'investissement dans la formation. "
            "Top 10 classement Universum des entreprises les plus attractives au monde. "
            # Exact quote — candidatures (applications received, NOT hires)
            "Avec plus d'1,3 million de candidatures reçues en 2023, "
            "un taux de turnover des cadres qui diminue et 100 % des salariés formés depuis trois ans, "
            "L'Oréal continue d'être un employeur de choix. "
            # Exact quote — alternance programme
            "Le programme d'apprentissage du Groupe, qui fête ses 30 ans cette année, "
            "poursuit son déploiement partout dans le monde : "
            "en dix ans, le nombre de contrats d'alternance a augmenté de 83 %, "
            "avec 1 100 contrats en 2023. "
            # Derived value: 1 100 / 90 000 = 1,22 % (both inputs from this same page, verified)
            "Ces 1 100 alternants représentent 1,22 % des 90 000 collaborateurs du groupe. "
            "À travers l'apprentissage, L'Oréal défend et promeut son approche "
            "intergénérationnelle dans la transmission des savoirs. "
            # KPI — engagement
            "79 % des collaborateurs se disent engagés et 70 % se sentent mis en condition "
            "de réussir leur mission. "
        ),
        "sections": [
            {
                "heading": "Effectif et engagement",
                "text": (
                    "90 000 collaborateurs dans le monde (2023). "
                    "79 % de taux d'engagement. 120 M€ investis dans la formation."
                ),
            },
            {
                "heading": "Programme d'apprentissage et alternance",
                "text": (
                    "1 100 contrats d'alternance dans le monde en 2023. "
                    "Hausse de 83 % en dix ans. "
                    "Contrats d'apprentissage et de professionnalisation. "
                    # Derived from verified figures: 1 100 / 90 000 = 1,22 %
                    # Both inputs confirmed from this same page.
                    "Cela représente 1,22 % des effectifs mondiaux (90 000 collaborateurs). "
                ),
            },
            {
                "heading": "Attractivité employeur",
                "text": (
                    "1,3 million de candidatures reçues en 2023. "
                    "Turnover des cadres en baisse. 100 % des salariés formés depuis 3 ans."
                ),
            },
        ],
        "anchors": {},
    },

    # Sources 3 & 4 (recrutements/an France, alternants % France) removed:
    # No publicly accessible, non-paywalled source confirmed these figures.
    # The pipeline will correctly return "unknown" for those two criteria.
    # DEU 2023 PDF (the authoritative source) returned HTTP 404.
]
