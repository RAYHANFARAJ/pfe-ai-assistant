from __future__ import annotations

import json
import logging
import random
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Session storage ──────────────────────────────────────────────────────────
# Cookies are saved here after first login and reused automatically.
_SESSION_FILE = Path(__file__).parent.parent.parent / "linkedin_session.json"

# ── Noise filter (same as original tool) ────────────────────────────────────
_NOISE_PHRASES = [
    "s'inscrire", "se connecter", "connexion", "sign in", "sign up", "log in",
    "register", "mot de passe", "password", "cookie", "privacy policy",
    "terms of service", "mentions légales", "télécharger l'application",
    "download the app", "linkedin corporation", "© linkedin",
]
_NOISE_RE = re.compile("|".join(re.escape(p) for p in _NOISE_PHRASES), re.IGNORECASE)
_MIN_WORDS = 6


class LinkedInPlaywrightTool:
    """
    Real browser LinkedIn scraper using Playwright.

    Anti-detection techniques:
      - Full Chromium browser (not detectable as headless)
      - Random human-like delays between actions
      - Real viewport, locale, timezone
      - Session cookie persistence (login once, reuse forever)
      - Stealth flags: disables webdriver fingerprint
    """

    def __init__(
        self,
        li_email: Optional[str] = None,
        li_password: Optional[str] = None,
    ) -> None:
        from app.core.config import settings
        self.email    = li_email    or getattr(settings, "linkedin_email",    None)
        self.password = li_password or getattr(settings, "linkedin_password", None)

    # ── Public entry point ───────────────────────────────────────────────────

    def run(self, linkedin_url: Optional[str], company_name: Optional[str] = None) -> Dict:
        empty = {"linkedin_url": linkedin_url, "pages": []}
        if not linkedin_url:
            return empty

        try:
            page_data = self._scrape_with_browser(linkedin_url)
            if page_data:
                logger.info("LinkedIn Playwright: scraped '%s' successfully", linkedin_url)
                return {"linkedin_url": linkedin_url, "pages": [page_data]}
            logger.warning("LinkedIn Playwright: no content extracted from '%s'", linkedin_url)
        except Exception as exc:
            logger.error("LinkedIn Playwright error: %s", exc)

        return empty

    # ── Browser scraping ─────────────────────────────────────────────────────

    def _scrape_with_browser(self, linkedin_url: str) -> Optional[Dict]:
        from playwright.sync_api import sync_playwright

        about_url = linkedin_url.rstrip("/")
        if not about_url.endswith("/about"):
            about_url += "/about"

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="fr-FR",
                timezone_id="Europe/Paris",
            )

            # Remove webdriver fingerprint
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en'] });
                window.chrome = { runtime: {} };
            """)

            # Restore saved session if it exists
            if _SESSION_FILE.exists():
                try:
                    cookies = json.loads(_SESSION_FILE.read_text())
                    context.add_cookies(cookies)
                    logger.info("LinkedIn: restored saved session (%d cookies)", len(cookies))
                except Exception as e:
                    logger.warning("LinkedIn: could not load session cookies: %s", e)

            page = context.new_page()

            # Check if we need to login.
            # LinkedIn redirects unauthenticated users to a URL like:
            #   /uas/login?session_redirect=...feed...
            # so checking `"feed" in url` is not reliable — the word "feed"
            # appears in the redirect query parameter. Check the URL path instead.
            try:
                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            except Exception:
                logger.warning("LinkedIn: timeout loading feed page — retrying once")
                try:
                    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    logger.error("LinkedIn: could not reach linkedin.com: %s", e)
                    browser.close()
                    return None
            self._human_delay(1.5, 2.5)

            def _is_logged_in(url: str) -> bool:
                from urllib.parse import urlparse
                path = urlparse(url).path
                return path.startswith("/feed") or path.startswith("/home") or path.startswith("/mynetwork")

            if not _is_logged_in(page.url) and self.email and self.password:
                logger.info("LinkedIn: session expired or missing — logging in")
                # Delete stale session file so next run starts clean
                if _SESSION_FILE.exists():
                    _SESSION_FILE.unlink()
                self._login(page)
                # Save fresh cookies for future use
                cookies = context.cookies()
                _SESSION_FILE.write_text(json.dumps(cookies))
                logger.info("LinkedIn: session saved (%d cookies)", len(cookies))
            elif not _is_logged_in(page.url):
                logger.warning(
                    "LinkedIn: not logged in and no credentials configured. "
                    "Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env.local"
                )
                browser.close()
                return None

            # Navigate to the company About page
            logger.info("LinkedIn: navigating to %s", about_url)
            page.goto(about_url, wait_until="domcontentloaded", timeout=30000)
            self._human_delay(2.0, 3.5)

            # Scroll to trigger lazy-loaded content
            self._scroll_page(page)

            html    = page.content()
            title   = page.title()
            content = self._extract_text(page)

            browser.close()

            if not content:
                return None

            return {
                "url":       about_url,
                "title":     title or "LinkedIn Company",
                "snippet":   content[:400],
                "full_text": content,
                "sections":  self._build_sections(content),
                "anchors":   {},
            }

    # ── Login ────────────────────────────────────────────────────────────────

    def _login(self, page) -> None:
        page.goto("https://www.linkedin.com/login", wait_until="networkidle", timeout=30000)
        self._human_delay(2.0, 3.0)

        # Try multiple selectors for the email field (LinkedIn A/B tests its login form)
        email_selector = None
        for sel in ["#username", "input[name='session_key']", "input[type='email']", "input[autocomplete='username']"]:
            try:
                page.wait_for_selector(sel, timeout=8000, state="visible")
                email_selector = sel
                break
            except Exception:
                continue

        if not email_selector:
            logger.error("LinkedIn: could not find email field on login page (URL: %s)", page.url)
            return

        page.fill(email_selector, self.email)
        self._human_delay(0.6, 1.2)

        # Password field
        for sel in ["#password", "input[name='session_password']", "input[type='password']"]:
            try:
                page.wait_for_selector(sel, timeout=5000, state="visible")
                page.focus(sel)
                break
            except Exception:
                continue

        for char in self.password:
            page.keyboard.type(char, delay=random.randint(50, 150))
        self._human_delay(0.5, 1.0)

        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded", timeout=25000)
        self._human_delay(2.5, 4.0)

        if "checkpoint" in page.url or "security-verification" in page.url:
            logger.warning(
                "LinkedIn: security checkpoint triggered. "
                "Complete the verification manually once, then the session will be saved."
            )

    # ── Text extraction ──────────────────────────────────────────────────────

    def _extract_text(self, page) -> str:
        # Priority selectors for company about section
        selectors = [
            "section.artdeco-card",
            "div.org-top-card-summary",
            "div[data-test-id='about-us']",
            "div.org-about-us-organization-description",
            "p.break-words",
            "main",
        ]
        collected: List[str] = []
        for sel in selectors:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    text = el.inner_text()
                    cleaned = self._clean(text)
                    if cleaned:
                        collected.append(cleaned)
                if collected:
                    break
            except Exception:
                continue

        # Fallback: full page text
        if not collected:
            try:
                body_text = page.inner_text("body")
                cleaned = self._clean(body_text)
                if cleaned:
                    collected.append(cleaned)
            except Exception:
                pass

        return "\n\n".join(collected)

    def _clean(self, raw: str) -> str:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", raw) if s.strip()]
        clean = [
            s for s in sentences
            if len(s.split()) >= _MIN_WORDS and not _NOISE_RE.search(s)
        ]
        return " ".join(clean)

    def _build_sections(self, text: str) -> List[Dict]:
        sections = []
        for para in re.split(r"\.\s+", text):
            para = para.strip()
            if len(para.split()) >= _MIN_WORDS:
                sections.append({"heading": "", "text": para[:600]})
            if len(sections) >= 8:
                break
        return sections or [{"heading": "Company Info", "text": text[:800]}]

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _human_delay(min_s: float = 1.0, max_s: float = 2.5) -> None:
        time.sleep(random.uniform(min_s, max_s))

    @staticmethod
    def _scroll_page(page) -> None:
        for _ in range(3):
            page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
            time.sleep(random.uniform(0.8, 1.5))
