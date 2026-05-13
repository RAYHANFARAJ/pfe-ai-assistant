from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://nubela.co/proxycurl/api/linkedin/company"
_TIMEOUT  = 20


class LinkedInProxycurlTool:
    """
    Fetches LinkedIn company data via the Proxycurl API.

    Why Proxycurl:
      - Legal — compliant with LinkedIn ToS
      - No credentials needed on your side
      - Shareable across any machine without setup
      - Returns structured JSON: description, headcount, specialities, locations

    Setup:
      1. Sign up at https://nubela.co/proxycurl  (free trial = 10 credits)
      2. Copy your API key
      3. Add to .env.local:  PROXYCURL_API_KEY=your-key-here
    """

    def __init__(self) -> None:
        self.api_key = getattr(settings, "proxycurl_api_key", None)

    def run(self, linkedin_url: Optional[str], company_name: Optional[str] = None) -> Dict:
        empty = {"linkedin_url": linkedin_url, "pages": []}

        if not linkedin_url:
            return empty

        if not self.api_key:
            logger.warning(
                "Proxycurl: no API key configured. "
                "Add PROXYCURL_API_KEY to .env.local — get a free key at https://nubela.co/proxycurl"
            )
            return empty

        try:
            data = self._fetch(linkedin_url)
            if not data:
                return empty

            text = self._build_text(data)
            if not text:
                return empty

            logger.info("LinkedIn Proxycurl: data fetched for '%s'", linkedin_url)
            return {
                "linkedin_url": linkedin_url,
                "pages": [{
                    "url":       linkedin_url,
                    "title":     data.get("name") or company_name or "LinkedIn",
                    "snippet":   text[:400],
                    "full_text": text,
                    "sections":  self._build_sections(data),
                    "anchors":   {},
                }],
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                logger.warning("Proxycurl: credits exhausted. Top up at https://nubela.co/proxycurl")
            elif e.response.status_code == 404:
                logger.warning("Proxycurl: company page not found for '%s'", linkedin_url)
            else:
                logger.error("Proxycurl HTTP error %s: %s", e.response.status_code, e)
        except Exception as exc:
            logger.error("Proxycurl unexpected error: %s", exc)

        return empty

    # ── API call ─────────────────────────────────────────────────────────────

    def _fetch(self, linkedin_url: str) -> Optional[Dict]:
        resp = httpx.get(
            _BASE_URL,
            params={
                "url":                  linkedin_url,
                "categories":           "include",
                "funding_data":         "exclude",
                "extra":                "include",
                "exit_signal_investors": "exclude",
                "use_cache":            "if-present",
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data or data.get("code") == 404:
            return None
        return data

    # ── Text builder ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_text(data: Dict) -> str:
        parts: List[str] = []

        name = data.get("name", "")
        desc = data.get("description", "")
        if desc:
            parts.append(desc)

        # Headcount
        hc = data.get("company_size_on_linkedin") or data.get("employee_count")
        if hc:
            parts.append(f"L'entreprise {name} compte {hc} employés sur LinkedIn.")

        hc_range = data.get("company_size")
        if hc_range and not hc:
            parts.append(f"Taille de l'entreprise : {hc_range} employés.")

        # Sector / industry
        industry = data.get("industry")
        if industry:
            parts.append(f"Secteur d'activité : {industry}.")

        # Specialities
        specialities = data.get("specialities") or []
        if specialities:
            parts.append("Spécialités : " + ", ".join(specialities[:10]) + ".")

        # Locations
        hq = data.get("hq")
        if hq:
            city    = hq.get("city", "")
            country = hq.get("country", "")
            loc     = ", ".join(filter(None, [city, country]))
            if loc:
                parts.append(f"Siège social : {loc}.")

        # Founded
        founded = data.get("founded_year")
        if founded:
            parts.append(f"Fondée en {founded}.")

        # Follower count (signal of company size/visibility)
        followers = data.get("followers_count")
        if followers:
            parts.append(f"Nombre d'abonnés LinkedIn : {followers:,}.")

        return "\n\n".join(parts)

    @staticmethod
    def _build_sections(data: Dict) -> List[Dict]:
        sections: List[Dict] = []

        desc = data.get("description", "")
        if desc:
            sections.append({"heading": "Description", "text": desc[:800]})

        hc = data.get("company_size_on_linkedin") or data.get("employee_count")
        hc_range = data.get("company_size")
        if hc or hc_range:
            val = hc or hc_range
            sections.append({"heading": "Effectif", "text": f"Effectif : {val} employés."})

        specialities = data.get("specialities") or []
        if specialities:
            sections.append({
                "heading": "Spécialités",
                "text": "Spécialités : " + ", ".join(specialities[:10]) + ".",
            })

        updates = data.get("updates") or []
        for post in updates[:3]:
            text = post.get("text") or ""
            if text and len(text.split()) >= 8:
                sections.append({"heading": "Post LinkedIn", "text": text[:600]})

        return sections or [{"heading": "Company Info", "text": data.get("description", "")[:800]}]
