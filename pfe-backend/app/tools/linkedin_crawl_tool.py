from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FETCH_TIMEOUT   = 10
_SEARCH_TIMEOUT = 10
_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# ── Auth-wall detection ──────────────────────────────────────────────────────
_AUTHWALL_URL_FRAGMENTS = ("linkedin.com/login", "authwall", "/uas/login")

# ── Sentence-level noise filter ──────────────────────────────────────────────
_NOISE_PHRASES: List[str] = [
    "s'inscrire", "se connecter", "connexion", "sign in", "sign up",
    "log in", "register", "mot de passe", "password", "email address",
    "renvoyer l'e-mail", "renvoyer", "resend", "check your spam",
    "vérifiez vos spams", "spam folder", "dossier spam",
    "forgot password", "mot de passe oublié",
    "accepter les cookies", "accept cookies", "cookie policy",
    "politique de confidentialité", "privacy policy", "conditions d'utilisation",
    "terms of service", "terms of use", "mentions légales",
    "paramètres des cookies", "cookie settings", "gérer les préférences",
    "nous utilisons des cookies", "we use cookies",
    "voir plus", "see more", "afficher plus",
    "suivre", "follow", "se connecter à", "connect with",
    "envoyer un message", "send message", "signaler", "report this",
    "partager", "share", "accueil", "retour", "back to", "fermer", "close",
    "télécharger l'application", "download the app", "get the app",
    "disponible sur", "available on", "app store", "google play",
    "linkedin corporation", "© linkedin", "tous droits réservés",
    "all rights reserved", "copyright",
]
_NOISE_RE = re.compile(
    "|".join(re.escape(p) for p in _NOISE_PHRASES),
    re.IGNORECASE,
)

_MIN_WORDS           = 6
_MAX_NOISE_RATIO     = 0.50
_MIN_CLEAN_SENTENCES = 3

_ABOUT_SELECTORS = [
    "section.artdeco-card p",
    "div.core-section-container p",
    "section[data-test-id='about-us'] p",
    "div[class*='about-us'] p",
    "p[class*='description']",
    ".org-top-card-summary__tagline",
]
_EMPLOYEE_PATTERNS = [
    re.compile(r"(\d[\d\s,\.]+)\s*(?:employés?|salariés?|employees?|staff|collaborateurs?)", re.I),
    re.compile(r"(?:effectif|workforce|headcount)[^\d]*(\d[\d\s,\.]+)", re.I),
]
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class LinkedInCrawlTool:
    """
    Treats LinkedIn/public company content as a full semantic evidence source.

    Fetch strategy (tried in order, first success wins):
      1. Direct fetch of linkedin.com/company/…/about
         → fast but almost always blocked by LinkedIn's auth wall
      2. Wikipedia API (FR then EN)
         → free, no key, JSON API, excellent coverage of mid/large companies,
           returns structured plain text with headcount, sector, activities
      3. DuckDuckGo HTML endpoint
         → searches for the company name + linkedin/description keywords,
           collects search result snippets that often include About text

    All three paths produce the same page-dict so the downstream
    chunker/embedder works identically regardless of which won.
    """

    def run(self, linkedin_url: Optional[str], company_name: Optional[str] = None) -> Dict:
        empty = {"linkedin_url": linkedin_url, "pages": []}

        # ── Path 1: LinkedIn direct ──────────────────────────────────────────
        if linkedin_url:
            about_url = self._about_url(linkedin_url)
            page = self._fetch_page(about_url) or self._fetch_page(linkedin_url)
            if page:
                logger.info("LinkedIn: direct fetch succeeded for %s", linkedin_url)
                return {"linkedin_url": linkedin_url, "pages": [page]}
            logger.info("LinkedIn: direct fetch blocked — trying fallbacks")

        if not company_name:
            return empty

        # ── Path 2: Wikipedia API ────────────────────────────────────────────
        page = self._wikipedia_lookup(company_name)
        if page:
            logger.info("LinkedIn fallback: Wikipedia content found for '%s'", company_name)
            return {"linkedin_url": linkedin_url, "pages": [page]}

        # ── Path 3: DuckDuckGo HTML search ──────────────────────────────────
        page = self._ddg_search_fallback(linkedin_url, company_name)
        if page:
            logger.info("LinkedIn fallback: DDG search content found for '%s'", company_name)
            return {"linkedin_url": linkedin_url, "pages": [page]}

        logger.info("LinkedIn: no content from any strategy (%s / %s)",
                    linkedin_url, company_name)
        return empty

    # ── URL helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _about_url(url: str) -> str:
        url = url.rstrip("/")
        return url if url.endswith("/about") else url + "/about"

    # ── Path 1: Direct fetch ─────────────────────────────────────────────────

    def _fetch_page(self, url: str) -> Optional[Dict]:
        try:
            resp = requests.get(url, timeout=FETCH_TIMEOUT, headers=_HEADERS, allow_redirects=True)
        except Exception as exc:
            logger.debug("LinkedIn fetch error %s: %s", url, exc)
            return None
        if any(f in resp.url for f in _AUTHWALL_URL_FRAGMENTS):
            return None
        if not resp.ok:
            return None
        return self._parse_page(resp.text, url)

    # ── Path 2: Wikipedia API ────────────────────────────────────────────────

    def _wikipedia_lookup(self, company_name: str) -> Optional[Dict]:
        """
        Query the Wikipedia REST API (no key required) for a company extract.

        Tries French Wikipedia first (better coverage of FR companies), then
        English. The introductory section typically contains headcount,
        sector, founding date, and key activities — exactly what our criteria
        evaluate. Returns a page-dict compatible with the website/LinkedIn schema.
        """
        for lang in ("fr", "en"):
            base = f"https://{lang}.wikipedia.org/w/api.php"

            # Step 1: Search
            try:
                search = requests.get(
                    base,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": company_name,
                        "srlimit": 3,
                        "format": "json",
                        "utf8": 1,
                    },
                    timeout=_SEARCH_TIMEOUT,
                    headers={"User-Agent": "PFE-scoring-bot/1.0 (research project)"},
                )
                hits = search.json().get("query", {}).get("search", [])
            except Exception as exc:
                logger.debug("Wikipedia search error (%s): %s", lang, exc)
                continue

            # Only accept results whose title closely matches the company name.
            # Never fall back to hits[0] — an unrelated top result (e.g. a film
            # with a similar word) would silently poison the evidence pool.
            name_lower = company_name.lower()
            name_words = [w for w in name_lower.split() if len(w) > 3]
            candidate = next(
                (h for h in hits if name_lower in h["title"].lower()
                 or h["title"].lower() in name_lower),
                None,
            )
            if not candidate:
                logger.debug(
                    "Wikipedia (%s): no title match for %r among %s",
                    lang, company_name, [h["title"] for h in hits],
                )
                continue

            page_title = candidate["title"]
            logger.debug("Wikipedia (%s): matched %r → %r", lang, company_name, page_title)

            # Step 2: Fetch plain-text intro extract
            try:
                extract_resp = requests.get(
                    base,
                    params={
                        "action": "query",
                        "titles": page_title,
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "format": "json",
                        "utf8": 1,
                    },
                    timeout=_SEARCH_TIMEOUT,
                    headers={"User-Agent": "PFE-scoring-bot/1.0 (research project)"},
                )
                pages = extract_resp.json().get("query", {}).get("pages", {})
            except Exception as exc:
                logger.debug("Wikipedia extract error (%s, %s): %s", lang, page_title, exc)
                continue

            for page in pages.values():
                extract = page.get("extract", "").strip()
                if not extract or len(extract.split()) < 30:
                    continue
                # Content-level guard: the extract must mention at least one
                # significant word from the company name to be kept.
                extract_lower = extract.lower()
                if name_words and not any(w in extract_lower for w in name_words):
                    logger.debug(
                        "Wikipedia (%s): extract for %r contains none of %s — discarded",
                        lang, page_title, name_words,
                    )
                    continue
                wiki_url = f"https://{lang}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                clean    = re.sub(r"\n{3,}", "\n\n", extract)
                return {
                    "url":      wiki_url,
                    "title":    f"{page_title} — Wikipedia ({lang.upper()})",
                    "snippet":  clean[:400],
                    "full_text": clean,
                    "sections": self._wikipedia_sections(clean),
                    "anchors":  {},
                }

        return None

    @staticmethod
    def _wikipedia_sections(text: str) -> List[Dict]:
        """Split Wikipedia extract into paragraph-level sections."""
        sections = []
        for para in re.split(r"\n{2,}", text):
            para = para.strip()
            if para and len(para.split()) >= 10:
                sections.append({"heading": "", "text": para[:600]})
            if len(sections) >= 6:
                break
        return sections or [{"heading": "Company Info", "text": text[:800]}]

    # ── Path 3: DuckDuckGo HTML search ──────────────────────────────────────

    def _ddg_search_fallback(
        self,
        linkedin_url: Optional[str],
        company_name: str,
    ) -> Optional[Dict]:
        """
        POST to DuckDuckGo's HTML endpoint and collect search result snippets.
        DDG indexes LinkedIn pages and stores their text in snippets.
        """
        queries: List[str] = []
        if linkedin_url:
            slug = linkedin_url.rstrip("/").split("/")[-1]
            queries.append(f'{slug} linkedin company about employees')
        queries.append(f'"{company_name}" linkedin effectif OR employés OR recrutement')

        # Relevance guard: snippet must contain at least one significant word
        # from the company name to avoid polluting evidence with random results.
        name_words = [w for w in company_name.lower().split() if len(w) > 3]

        seen: set = set()
        snippets: List[str] = []

        for query in queries[:2]:
            for hit in self._ddg_html_search(query, max_results=5):
                body  = hit.get("body", "").strip()
                title = hit.get("title", "").strip()
                if not body or body in seen or len(body.split()) < _MIN_WORDS:
                    continue
                combined = (title + " " + body).lower()
                if name_words and not any(w in combined for w in name_words):
                    logger.debug("DDG: snippet irrelevant to %r — skipped: %.60s", company_name, body)
                    continue
                seen.add(body)
                snippets.append(f"[{title}]\n{body}" if title else body)

        if not snippets:
            return None

        full_text = "\n\n".join(snippets)
        clean = self._clean_text(full_text)
        if not clean:
            return None

        return {
            "url": linkedin_url or f"https://duckduckgo.com/?q={company_name}+linkedin",
            "title": f"{company_name} — public profile (search)",
            "snippet": clean[:400],
            "full_text": clean,
            "sections": [{"heading": "Public Profile", "text": clean[:800]}],
            "anchors": {},
        }

    @staticmethod
    def _ddg_html_search(query: str, max_results: int = 5) -> List[Dict]:
        try:
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "kl": "fr-fr"},
                headers=_SEARCH_HEADERS,
                timeout=_SEARCH_TIMEOUT,
                allow_redirects=True,
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.debug("DDG HTML search failed for %r: %s", query[:60], exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[Dict] = []
        for item in soup.find_all("div", class_="result__body")[:max_results]:
            title_el   = item.find("a", class_="result__a")
            snippet_el = item.find("a", class_="result__snippet")
            if snippet_el:
                results.append({
                    "title": title_el.get_text(strip=True) if title_el else "",
                    "body":  snippet_el.get_text(" ", strip=True),
                })
        return results

    # ── Parse + clean (direct-fetch path) ───────────────────────────────────

    def _parse_page(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        raw_text   = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
        clean_text = self._clean_text(raw_text)
        if not clean_text:
            return None
        title    = soup.title.get_text(" ", strip=True) if soup.title else "LinkedIn"
        sections = self._extract_sections(soup, clean_text)
        return {
            "url":      url,
            "title":    title,
            "snippet":  clean_text[:400],
            "full_text": clean_text,
            "sections": sections,
            "anchors":  {},
        }

    def _clean_text(self, raw: str) -> str:
        sentences   = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", raw) if s.strip()]
        clean: List[str] = []
        noise_count = 0
        for sent in sentences:
            if _NOISE_RE.search(sent):
                noise_count += 1
                continue
            if len(sent.split()) < _MIN_WORDS:
                noise_count += 1
                continue
            clean.append(sent)
        total = len(sentences)
        if total == 0:
            return ""
        if noise_count / total > _MAX_NOISE_RATIO:
            return ""
        if len(clean) < _MIN_CLEAN_SENTENCES:
            return ""
        return " ".join(clean)

    def _extract_sections(self, soup: BeautifulSoup, clean_text: str) -> List[Dict]:
        sections: List[Dict] = []
        for sel in _ABOUT_SELECTORS:
            paras = soup.select(sel)
            if paras:
                raw  = " ".join(p.get_text(" ", strip=True) for p in paras)
                text = self._clean_text(re.sub(r"\s+", " ", raw))
                if text:
                    sections.append({"heading": "About", "text": text[:800]})
                break
        emp = self._extract_employee_snippet(clean_text)
        if emp:
            sections.append({"heading": "Headcount", "text": emp})
        if not sections:
            for para in re.split(r"\.\s+", clean_text):
                para = para.strip()
                if len(para.split()) >= _MIN_WORDS:
                    sections.append({"heading": "", "text": para[:600]})
                if len(sections) >= 6:
                    break
        return sections

    @staticmethod
    def _extract_employee_snippet(text: str) -> Optional[str]:
        for pat in _EMPLOYEE_PATTERNS:
            m = pat.search(text)
            if m:
                return re.sub(r"\s+", " ", text[max(0, m.start()-30): m.end()+30]).strip()
        return None
