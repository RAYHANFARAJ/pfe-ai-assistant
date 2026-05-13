from __future__ import annotations

import json
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup


class SocialExtractor:
    """
    Multi-strategy LinkedIn resolver.

    Resolution order (most reliable → least reliable):
      1. <a href> links containing linkedin.com/company  (website HTML)
      2. Meta tags (og:see_also, twitter:site, etc.)
      3. JSON-LD / schema.org sameAs markup
      4. Any linkedin.com/company pattern anywhere in the page source
      5. Company-name slug inference (heuristic — lowest confidence)
    """

    _COMPANY_PATTERN = re.compile(
        r"https?://(?:www\.)?linkedin\.com/company/([\w\-\.]+)/?",
        re.IGNORECASE,
    )
    _ANY_LINKEDIN = re.compile(
        r"linkedin\.com/company/([\w\-\.]+)/?",
        re.IGNORECASE,
    )

    def extract_linkedin(self, website: str) -> Optional[str]:
        """
        Fetch a website and apply all four HTML-based strategies.
        Returns a normalised linkedin.com/company/… URL or None.
        """
        if not website:
            return None
        if not website.startswith("http"):
            website = "https://" + website

        try:
            response = requests.get(
                website,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PFE-bot/1.0)"},
                allow_redirects=True,
            )
            response.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Strategy 1 — <a href>
        for a in soup.find_all("a", href=True):
            m = self._COMPANY_PATTERN.search(a["href"])
            if m:
                return self._normalise(m.group(0))

        # Strategy 2 — meta tags
        for meta in soup.find_all("meta"):
            for attr in ("content", "value"):
                val = meta.get(attr, "") or ""
                m = self._ANY_LINKEDIN.search(val)
                if m:
                    return f"https://www.linkedin.com/company/{m.group(1)}/"

        # Strategy 3 — JSON-LD schema.org
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = json.loads(script.string or "{}")
                flat = json.dumps(raw)
                m = self._ANY_LINKEDIN.search(flat)
                if m:
                    return f"https://www.linkedin.com/company/{m.group(1)}/"
            except Exception:
                pass

        # Strategy 4 — raw page source (catches inline JS / data attributes)
        m = self._ANY_LINKEDIN.search(response.text)
        if m:
            return f"https://www.linkedin.com/company/{m.group(1)}/"

        return None

    def infer_linkedin_from_name(self, company_name: str) -> Optional[str]:
        """
        Build a probable LinkedIn company URL by slugifying the company name.
        This is a heuristic — it may not always be correct, but it is the
        best we can do when neither the CRM nor the website exposes a link.
        """
        if not company_name:
            return None
        slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
        if not slug:
            return None
        return f"https://www.linkedin.com/company/{slug}/"

    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(url: str) -> str:
        url = url.strip()
        if not url.startswith("http"):
            return "https://www.linkedin.com/company/" + url.lstrip("/")
        if "://linkedin" in url and "www." not in url:
            url = url.replace("://linkedin", "://www.linkedin")
        return url
