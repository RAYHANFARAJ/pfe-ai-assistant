from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_PAGES = 3
FETCH_TIMEOUT = 8   # tighter timeout — don't wait forever on slow pages

# Pages relevant to R&D / headcount / hiring criteria
_KEYWORDS = [
    "about", "equipe", "team", "career", "recrutement", "formation",
    "r-d", "r&d", "rd", "innovation", "company", "qui-sommes", "notre",
    "alternance", "apprentissage", "jobs", "emploi", "mission", "valeurs",
]


class SemanticCrawlTool:
    """
    Crawls a company website and returns page content for the semantic pipeline.

    Page selection uses keyword URL matching (fast, zero RAM, no LLM call).
    Semantic relevance is handled downstream by ChunkEmbedderService +
    SemanticRetrieverService — no need for an LLM at the crawl stage.
    """

    def run(self, website_url: Optional[str]) -> Dict:
        if not website_url:
            return {"website_url": None, "pages": [], "social_links": {}}

        homepage = self._fetch_page(website_url)
        if not homepage:
            return {"website_url": website_url, "pages": [], "social_links": {}}

        html = homepage.get("_html", "")
        social_links = self._extract_social_links(html, website_url)
        all_links = self._internal_links(html, website_url)
        selected = self._select_pages(all_links)

        pages = [homepage]
        extra_urls = selected[: MAX_PAGES - 1]
        if extra_urls:
            with ThreadPoolExecutor(max_workers=len(extra_urls)) as pool:
                for page in pool.map(self._fetch_page, extra_urls):
                    if page:
                        pages.append(page)

        for p in pages:
            p.pop("_html", None)

        return {"website_url": website_url, "pages": pages, "social_links": social_links}

    # ── Page selection ───────────────────────────────────────────────────────

    @staticmethod
    def _select_pages(links: List[str]) -> List[str]:
        return [
            url for url in links
            if any(kw in url.lower() for kw in _KEYWORDS)
        ][: MAX_PAGES - 1]

    # ── Fetching ─────────────────────────────────────────────────────────────

    def _fetch_page(self, url: str) -> Optional[Dict]:
        try:
            resp = requests.get(
                url,
                timeout=FETCH_TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.debug("Failed to fetch %s: %s", url, exc)
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        full_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

        return {
            "url": url,
            "title": title,
            "snippet": full_text[:400],
            "full_text": full_text,
            "sections": self._extract_sections(soup),
            "anchors": self._extract_anchors(soup),
            "_html": resp.text,
        }

    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        sections: List[Dict[str, str]] = []
        heading, texts = "", []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = tag.get_text(" ", strip=True)
            if not text:
                continue
            if tag.name in ("h1", "h2", "h3", "h4"):
                if texts:
                    sections.append({
                        "heading": heading,
                        "text": re.sub(r"\s+", " ", " ".join(texts))[:600],
                    })
                heading, texts = text, []
            else:
                texts.append(text)
        if texts:
            sections.append({
                "heading": heading,
                "text": re.sub(r"\s+", " ", " ".join(texts))[:600],
            })
        return sections

    @staticmethod
    def _extract_anchors(soup: BeautifulSoup) -> Dict[str, str]:
        anchors: Dict[str, str] = {}
        for tag in soup.find_all(id=True):
            aid = tag.get("id", "").strip()
            if aid:
                nearby = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)[:200])
                if nearby:
                    anchors[aid] = nearby
        return anchors

    @staticmethod
    def _internal_links(html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        base_netloc = urlparse(base_url).netloc
        seen: set = set()
        links: List[str] = []
        for a in soup.find_all("a", href=True):
            abs_url = urljoin(base_url, a["href"].strip()).split("#")[0]
            if not abs_url.startswith(("http://", "https://")):
                continue
            if urlparse(abs_url).netloc != base_netloc:
                continue
            if abs_url not in seen:
                seen.add(abs_url)
                links.append(abs_url)
        return links

    @staticmethod
    def _extract_social_links(html: str, base_url: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        markers = {
            "linkedin": "linkedin.com", "twitter": "twitter.com", "x": "x.com",
            "facebook": "facebook.com", "youtube": "youtube.com",
            "instagram": "instagram.com",
        }
        found: Dict[str, str] = {}
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"].strip())
            for name, marker in markers.items():
                if marker in href.lower() and name not in found:
                    found[name] = href
        return found
