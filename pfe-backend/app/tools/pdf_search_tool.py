from __future__ import annotations

import io
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# PDF search queries — ordered by relevance for scoring criteria
_PDF_QUERIES = [
    '"{name}" rapport annuel filetype:pdf',
    '"{name}" document enregistrement universel filetype:pdf',
    '"{name}" rapport RSE développement durable filetype:pdf',
    '"{name}" annual report filetype:pdf',
    '"{name}" bilan carbone emballage filetype:pdf',
    '"{name}" chiffres clés effectifs filetype:pdf',
]

# Max PDFs to download and process
_MAX_PDFS = 3

# Max characters kept per PDF
_MAX_CHARS = 8000

# Download timeout in seconds
_FETCH_TIMEOUT = 20


class PDFSearchTool:
    """
    Automatically finds and extracts text from public PDFs related to a company.

    Searches DuckDuckGo for annual reports, CSR reports, DEU, and other
    official company documents in PDF format. Extracts and returns their
    text as source dicts — same format as WebsiteCrawlTool pages.

    This runs in parallel with website and LinkedIn crawling so it adds
    no extra wall-clock time to the pipeline.
    """

    def run(
        self,
        company_name: Optional[str],
        website_domain: Optional[str] = None,
    ) -> Dict:
        empty: Dict = {"company_name": company_name, "pages": []}
        if not company_name:
            return empty

        pdf_urls = self._find_pdf_urls(company_name, website_domain)
        pages: List[Dict] = []

        for url in pdf_urls:
            if len(pages) >= _MAX_PDFS:
                break
            page = self._fetch_and_extract(url, company_name)
            if page:
                pages.append(page)
                logger.info("PDF: extracted '%s' (%d chars)", url[:80], len(page["full_text"]))

        logger.info("PDF: %d document(s) extracted for '%s'", len(pages), company_name)
        return {"company_name": company_name, "pages": pages}

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _find_pdf_urls(
        self, company_name: str, website_domain: Optional[str]
    ) -> List[str]:
        name = company_name.strip().strip('"')
        seen: set = set()
        pdf_urls: List[str] = []

        for query_tpl in _PDF_QUERIES:
            if len(pdf_urls) >= _MAX_PDFS * 2:
                break
            query = query_tpl.format(name=name)
            results = self._ddg_search(query)
            for r in results:
                url = (r.get("href") or "").strip()
                if not url or url in seen:
                    continue
                # Accept only PDFs hosted on company website or trusted document hosts
                if not self._is_relevant_pdf_url(url, website_domain):
                    continue
                seen.add(url)
                pdf_urls.append(url)
                logger.debug("PDF candidate: %s", url)

        return pdf_urls

    @staticmethod
    def _ddg_search(query: str, max_results: int = 5) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(
                    keywords=query,
                    region="fr-fr",
                    safesearch="off",
                    max_results=max_results,
                ))
        except Exception as exc:
            logger.warning("PDF DDG search failed: %s", exc)
            return []

    @staticmethod
    def _is_relevant_pdf_url(url: str, website_domain: Optional[str]) -> bool:
        url_lower = url.lower()
        # Must end with .pdf or contain /pdf/ in path
        if not (url_lower.endswith(".pdf") or "/pdf/" in url_lower
                or "filetype=pdf" in url_lower):
            return False
        # Prefer company's own domain or well-known document hosts
        netloc = urlparse(url).netloc.lower()
        trusted_hosts = {
            "loreal-finance.com", "total.com", "sncf.com", "airfrance.com",
            "elysee.fr", "legifrance.gouv.fr", "amf-france.org",
            "sec.gov", "annualreports.com", "ir.company",
        }
        if website_domain and website_domain in netloc:
            return True
        if any(h in netloc for h in trusted_hosts):
            return True
        # Accept any .pdf from a non-social domain
        excluded = {"facebook", "twitter", "instagram", "youtube", "tiktok", "linkedin"}
        return not any(ex in netloc for ex in excluded)

    # ------------------------------------------------------------------
    # Fetch and extract
    # ------------------------------------------------------------------

    def _fetch_and_extract(self, url: str, company_name: str) -> Optional[Dict]:
        try:
            resp = httpx.get(
                url,
                timeout=_FETCH_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SellynxBot/1.0)"},
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                logger.debug("PDF: skipping non-PDF response from %s", url)
                return None

            text = self._extract_pdf_text(resp.content)
            if not text or len(text.split()) < 50:
                return None

            # Verify the document actually mentions the company
            name_words = [w for w in company_name.lower().split() if len(w) > 3]
            if name_words and not any(w in text.lower() for w in name_words):
                logger.debug("PDF: rejected '%s' — company not mentioned", url[:60])
                return None

            title = self._infer_title(url, text)
            return {
                "url":       url,
                "title":     title,
                "snippet":   text[:400],
                "full_text": text[:_MAX_CHARS],
                "sections":  self._build_sections(text),
                "anchors":   {},
            }
        except Exception as exc:
            logger.debug("PDF: could not fetch/extract %s: %s", url[:80], exc)
            return None

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = []
            for page in reader.pages:
                t = (page.extract_text() or "").strip()
                if t:
                    pages.append(t)
            return re.sub(r"\s+", " ", "\n\n".join(pages)).strip()
        except Exception as exc:
            logger.debug("PDF text extraction failed: %s", exc)
            return ""

    @staticmethod
    def _infer_title(url: str, text: str) -> str:
        # Try to get a meaningful title from the first line of text
        first_line = text.split("\n")[0].strip()[:120]
        if len(first_line.split()) > 3:
            return first_line
        # Fall back to URL filename
        path = urlparse(url).path
        filename = path.split("/")[-1].replace("-", " ").replace("_", " ")
        return filename or "Document PDF"

    @staticmethod
    def _build_sections(text: str) -> List[Dict]:
        sections = []
        for para in re.split(r"\n{2,}", text):
            para = para.strip()
            if len(para.split()) >= 10:
                sections.append({"heading": "", "text": para[:600]})
            if len(sections) >= 15:
                break
        return sections or [{"heading": "", "text": text[:600]}]
