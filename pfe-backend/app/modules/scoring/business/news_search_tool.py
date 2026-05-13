from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Trusted news / press-release domains.
# Results from these domains are accepted unconditionally.
# Results from unknown domains are accepted only if they mention the company.
# ---------------------------------------------------------------------------
_TRUSTED_DOMAINS = {
    # French business press
    "lesechos.fr", "lefigaro.fr", "lemonde.fr", "latribune.fr",
    "challenges.fr", "bfmtv.com", "capital.fr", "leparisien.fr",
    "usinenouvelle.com", "linformaticien.com", "journaldunet.com",
    # Press release wires
    "businesswire.com", "prnewswire.com", "globenewswire.com",
    "accesswire.com", "newswire.com",
    # International
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com",
    # Public / institutional
    "bpifrance.fr", "gouvernement.fr", "economie.gouv.fr",
}

# Noise patterns to strip from article text
_NOISE_RE = re.compile(
    r"s'inscrire|se connecter|connexion|sign in|sign up|log in|"
    r"abonnez-vous|subscribe|newsletter|cookie|mentions légales|"
    r"politique de confidentialit|terms of service|"
    r"télécharger l.application|download the app",
    re.IGNORECASE,
)

# Minimum words for an article to be worth keeping
_MIN_WORDS = 60

# Fetch timeout per article (seconds)
_FETCH_TIMEOUT = 10

# Max characters kept per article
_MAX_CHARS = 3000

# Max articles fetched per company
_MAX_ARTICLES = 5


class NewsSearchTool:
    """
    Retrieves recent news articles about a company via DuckDuckGo.

    Strategy:
      1. Build 2 focused queries (general news + HR/R&D specific)
      2. Search DDG with timelimit='y' (last 12 months), region fr-fr
      3. Deduplicate and rank by domain trust
      4. Fetch and extract article body from the top results
      5. Return structured page dicts — same format as WebsiteCrawlTool
    """

    def run(
        self,
        company_name: Optional[str],
        website_domain: Optional[str] = None,
    ) -> Dict:
        empty: Dict = {"company_name": company_name, "pages": []}
        if not company_name:
            return empty

        queries = self._build_queries(company_name)
        seen_urls: set = set()
        candidates: List[Dict] = []

        for query in queries:
            results = self._ddg_search(query)
            for r in results:
                url = r.get("href") or ""
                if url in seen_urls:
                    continue
                # Skip the company's own website (already crawled separately)
                if website_domain and website_domain in urlparse(url).netloc:
                    continue
                seen_urls.add(url)
                candidates.append(r)

        # Sort: trusted domains first
        candidates.sort(
            key=lambda r: (0 if self._is_trusted(r.get("href", "")) else 1)
        )

        pages: List[Dict] = []
        for candidate in candidates:
            if len(pages) >= _MAX_ARTICLES:
                break
            page = self._fetch_article(
                url=candidate["href"],
                title=candidate.get("title", ""),
                snippet=candidate.get("body", ""),
                company_name=company_name,
            )
            if page:
                pages.append(page)
                logger.info(
                    "News: accepted article '%s' from %s",
                    page["title"][:60],
                    urlparse(page["url"]).netloc,
                )

        logger.info("News: %d article(s) retrieved for '%s'", len(pages), company_name)
        return {"company_name": company_name, "pages": pages}

    # ── Query builder ────────────────────────────────────────────────────────

    @staticmethod
    def _build_queries(company_name: str) -> List[str]:
        name = company_name.strip().strip('"')
        return [
            # General recent news (press releases, announcements)
            f'"{name}" actualités OR annonce OR communiqué OR résultats',
            # HR / R&D / training criteria — most relevant for scoring
            f'"{name}" recrutement OR effectif OR alternance OR innovation OR R&D',
        ]

    # ── DuckDuckGo search ────────────────────────────────────────────────────

    @staticmethod
    def _ddg_search(query: str, max_results: int = 6) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                results = list(
                    ddgs.text(
                        keywords=query,
                        region="fr-fr",
                        safesearch="off",
                        timelimit="y",      # last 12 months only
                        max_results=max_results,
                    )
                )
            return results
        except Exception as exc:
            logger.warning("DDG search failed for query '%s': %s", query[:80], exc)
            return []

    # ── Article fetcher ──────────────────────────────────────────────────────

    def _fetch_article(
        self,
        url: str,
        title: str,
        snippet: str,
        company_name: str,
    ) -> Optional[Dict]:
        try:
            resp = httpx.get(
                url,
                timeout=_FETCH_TIMEOUT,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                },
            )
            resp.raise_for_status()
        except Exception as exc:
            # Fall back to the DDG snippet if the page can't be fetched
            logger.debug("News: could not fetch %s (%s) — using snippet only", url, exc)
            return self._from_snippet(url, title, snippet, company_name)

        text = self._extract_article_text(resp.text)
        if not text:
            return self._from_snippet(url, title, snippet, company_name)

        # Reject if the article doesn't mention the company at all
        if not self._mentions_company(text, company_name):
            logger.debug("News: rejected '%s' — company '%s' not mentioned", url, company_name)
            return None

        return {
            "url":       url,
            "title":     title or urlparse(url).netloc,
            "snippet":   text[:400],
            "full_text": text[:_MAX_CHARS],
            "sections":  self._build_sections(text),
            "anchors":   {},
            "source_date": None,   # DDG timelimit ensures recency; exact date not parsed
        }

    def _from_snippet(
        self, url: str, title: str, snippet: str, company_name: str
    ) -> Optional[Dict]:
        """Use the DDG snippet when the full article cannot be fetched."""
        clean = self._clean(snippet)
        if not clean or len(clean.split()) < 10:
            return None
        if not self._mentions_company(clean, company_name):
            return None
        return {
            "url":       url,
            "title":     title or urlparse(url).netloc,
            "snippet":   clean[:400],
            "full_text": clean,
            "sections":  [{"heading": "Article snippet", "text": clean}],
            "anchors":   {},
            "source_date": None,
        }

    # ── Text extraction ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_article_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # Remove boilerplate tags
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "noscript", "iframe"]):
            tag.decompose()

        # Priority: <article> → <main> → all <p> tags
        container = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_=re.compile(r"article|content|body|post", re.I))
        )
        if container:
            paragraphs = container.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        parts = [
            re.sub(r"\s+", " ", p.get_text(" ", strip=True))
            for p in paragraphs
            if len(p.get_text(strip=True)) > 40
        ]
        # Filter noise lines
        parts = [p for p in parts if not _NOISE_RE.search(p)]
        return " ".join(parts).strip()

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        lines = [l for l in text.split(". ") if not _NOISE_RE.search(l)]
        return ". ".join(lines)

    @staticmethod
    def _build_sections(text: str) -> List[Dict]:
        sections = []
        for para in re.split(r"\. {2,}|\n{2,}", text):
            para = para.strip()
            if len(para.split()) >= 10:
                sections.append({"heading": "Article", "text": para[:600]})
            if len(sections) >= 6:
                break
        return sections or [{"heading": "Article", "text": text[:600]}]

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_trusted(url: str) -> bool:
        netloc = urlparse(url).netloc.lower().lstrip("www.")
        return any(netloc == d or netloc.endswith("." + d) for d in _TRUSTED_DOMAINS)

    @staticmethod
    def _mentions_company(text: str, company_name: str) -> bool:
        name_words = [w for w in company_name.lower().split() if len(w) > 3]
        if not name_words:
            return True
        text_lower = text.lower()
        return any(w in text_lower for w in name_words)
