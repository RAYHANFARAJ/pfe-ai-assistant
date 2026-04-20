from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, urlencode

import requests
from bs4 import BeautifulSoup, Tag


class WebsiteCrawlTool:
    def __init__(self) -> None:
        self.timeout = 15
        self.max_pages = 4
        self.page_keywords = ["about", "service", "contact", "company", "solution",
                               "career", "emploi", "recrutement", "formation", "equipe",
                               "team", "jobs", "alternance", "apprentissage"]

    def run(self, website_url: str | None) -> Dict[str, object]:
        if not website_url:
            return {"website_url": None, "pages": [], "social_links": {}}

        visited_pages: List[Dict] = []
        social_links: Dict[str, str] = {}

        homepage = self._fetch_page(website_url)
        if homepage:
            visited_pages.append(homepage)
            social_links.update(self._extract_social_links(homepage.get("_html", ""), website_url))
            candidate_links = self._extract_candidate_links(homepage.get("_html", ""), website_url)

            for link in candidate_links[: self.max_pages - 1]:
                page = self._fetch_page(link)
                if page:
                    visited_pages.append(page)

        # Strip internal _html before returning (keep rich text fields)
        for page in visited_pages:
            page.pop("_html", None)

        return {
            "website_url": website_url,
            "pages": visited_pages,
            "social_links": social_links,
        }

    def _fetch_page(self, url: str) -> Dict | None:
        try:
            response = requests.get(url, timeout=self.timeout,
                                    headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""

        # Full normalized text (no 1500-char cap — evaluators need the full page)
        full_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

        # Section map: list of {heading, text} blocks for location hints
        sections = self._extract_sections(soup)

        # Anchor map: id → nearby text (for fragment URL generation)
        anchors = self._extract_anchors(soup)

        return {
            "url": url,
            "title": title,
            "snippet": full_text[:1500],   # kept for backward compat
            "full_text": full_text,         # full content for precise extraction
            "sections": sections,           # [{heading, text}]
            "anchors": anchors,             # {anchor_id: nearby_text}
            "_html": response.text,         # stripped before returning
        }

    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract heading → paragraph blocks for section-level location hints."""
        sections: List[Dict[str, str]] = []
        current_heading = ""
        current_text: List[str] = []

        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            tag_name = tag.name
            text = tag.get_text(" ", strip=True)
            if not text:
                continue
            if tag_name in ("h1", "h2", "h3", "h4"):
                if current_text:
                    sections.append({
                        "heading": current_heading,
                        "text": re.sub(r"\s+", " ", " ".join(current_text)).strip()[:600],
                    })
                current_heading = text
                current_text = []
            else:
                current_text.append(text)

        if current_text:
            sections.append({
                "heading": current_heading,
                "text": re.sub(r"\s+", " ", " ".join(current_text)).strip()[:600],
            })

        return sections

    def _extract_anchors(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Return {anchor_id: nearby_text} for fragment URL building."""
        anchors: Dict[str, str] = {}
        for tag in soup.find_all(id=True):
            anchor_id = tag.get("id", "").strip()
            if anchor_id:
                nearby = tag.get_text(" ", strip=True)[:200]
                if nearby:
                    anchors[anchor_id] = re.sub(r"\s+", " ", nearby)
        return anchors

    def _extract_candidate_links(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        seen: set = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            absolute = urljoin(base_url, href)
            if not absolute.startswith(("http://", "https://")):
                continue
            if urlparse(absolute).netloc != urlparse(base_url).netloc:
                continue
            absolute_clean = absolute.split("#")[0]  # strip fragments for dedup
            if absolute_clean not in seen and any(
                kw in absolute.lower() for kw in self.page_keywords
            ):
                seen.add(absolute_clean)
                links.append(absolute)

        return links

    def _extract_social_links(self, html: str, base_url: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        social_links: Dict[str, str] = {}
        patterns = {
            "linkedin": "linkedin.com",
            "facebook": "facebook.com",
            "instagram": "instagram.com",
            "x": "x.com",
            "twitter": "twitter.com",
            "youtube": "youtube.com",
        }
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"].strip())
            for name, marker in patterns.items():
                if marker in href.lower() and name not in social_links:
                    social_links[name] = href
        return social_links
