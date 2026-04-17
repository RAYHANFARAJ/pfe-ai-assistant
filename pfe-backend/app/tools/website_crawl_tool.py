from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class WebsiteCrawlTool:
    def __init__(self) -> None:
        self.timeout = 15
        self.max_pages = 4
        self.page_keywords = ["about", "service", "contact", "company", "solution"]

    def run(self, website_url: str | None) -> Dict[str, object]:
        if not website_url:
            return {
                "website_url": None,
                "pages": [],
                "social_links": {},
            }

        visited_pages: List[Dict[str, str]] = []
        social_links: Dict[str, str] = {}

        homepage = self._fetch_page(website_url)
        if homepage:
            visited_pages.append(homepage)
            social_links.update(self._extract_social_links(homepage.get("html", ""), website_url))
            candidate_links = self._extract_candidate_links(homepage.get("html", ""), website_url)

            for link in candidate_links[: self.max_pages - 1]:
                page = self._fetch_page(link)
                if page:
                    visited_pages.append(page)

        for page in visited_pages:
            page.pop("html", None)

        return {
            "website_url": website_url,
            "pages": visited_pages,
            "social_links": social_links,
        }

    def _fetch_page(self, url: str) -> Dict[str, str] | None:
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        return {
            "url": url,
            "title": title,
            "snippet": text[:1500],
            "html": response.text,
        }

    def _extract_candidate_links(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            absolute = urljoin(base_url, href)

            if not absolute.startswith(("http://", "https://")):
                continue

            if urlparse(absolute).netloc != urlparse(base_url).netloc:
                continue

            absolute_lower = absolute.lower()
            if any(keyword in absolute_lower for keyword in self.page_keywords):
                if absolute not in seen:
                    seen.add(absolute)
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
            href_lower = href.lower()

            for social_name, marker in patterns.items():
                if marker in href_lower and social_name not in social_links:
                    social_links[social_name] = href

        return social_links
