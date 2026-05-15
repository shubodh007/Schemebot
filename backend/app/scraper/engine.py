from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from app.core.logging import logger
from app.models.scraping import ScrapingJob
from app.scraper.ai_extractor import AIExtractor
from app.scraper.change_detector import ChangeDetector
from app.scraper.extractors.state_portals import APPortalExtractor, TelanganaPortalExtractor
from app.scraper.parser import SchemeParser

ua = UserAgent(browsers=["chrome", "firefox", "edge"], os=["windows", "macos", "linux"])
ROBOTS_TXT_CACHE: Dict[str, bool] = {}
DOMAIN_LAST_FETCH: Dict[str, float] = {}


@dataclass
class SourceCircuitBreaker:
    name: str
    failure_count: int = 0
    max_failures: int = 5
    cooldown_seconds: float = 300.0
    last_failure: float = 0.0
    is_open: bool = False
    total_scrapes: int = 0
    total_errors: int = 0

    def record_success(self) -> None:
        self.total_scrapes += 1
        self.failure_count = 0
        if self.is_open and time.monotonic() - self.last_failure > self.cooldown_seconds:
            self.is_open = False
            logger.info("scraper.circuit_closed", source=self.name)

    def record_failure(self) -> bool:
        self.total_scrapes += 1
        self.total_errors += 1
        self.failure_count += 1
        self.last_failure = time.monotonic()
        if self.failure_count >= self.max_failures:
            self.is_open = True
            logger.warning("scraper.circuit_opened", source=self.name, failures=self.failure_count)
            return True
        return False

    def allow_request(self) -> bool:
        if not self.is_open:
            return True
        if time.monotonic() - self.last_failure > self.cooldown_seconds:
            self.is_open = False
            return True
        return False

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "is_open": self.is_open,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "total_scrapes": self.total_scrapes,
            "total_errors": self.total_errors,
            "health": "healthy" if not self.is_open else "degraded",
        }


class ScrapingEngine:
    def __init__(self) -> None:
        self.parser = SchemeParser()
        self.ai_extractor = AIExtractor()
        self.change_detector = ChangeDetector()
        self._circuit_breakers: Dict[str, SourceCircuitBreaker] = {}

        self.sources: Dict[str, Dict[str, Any]] = {
            "myscheme": {
                "name": "MyScheme.gov.in",
                "url": "https://www.myscheme.gov.in/schemes",
                "type": "central",
                "requires_js": True,
                "rate_limit": 3.0,
                "extractor": "parser",
            },
            "india_gov": {
                "name": "India.gov.in",
                "url": "https://www.india.gov.in/topics/rural",
                "type": "central",
                "requires_js": False,
                "rate_limit": 2.0,
                "extractor": "parser",
            },
            "ap_portal": {
                "name": "AP Government Portal",
                "url": "https://www.ap.gov.in",
                "type": "state",
                "requires_js": False,
                "rate_limit": 2.0,
                "extractor": "ap_portal",
            },
            "telangana_portal": {
                "name": "Telangana Government Portal",
                "url": "https://www.telangana.gov.in",
                "type": "state",
                "requires_js": False,
                "rate_limit": 2.0,
                "extractor": "telangana",
            },
        }

    async def scrape_source(
        self,
        source_key: str,
        job: ScrapingJob,
    ) -> Tuple[int, int, int]:
        source = self.sources.get(source_key)
        if not source:
            raise ValueError(f"Unknown source: {source_key}")

        breaker = self._get_circuit_breaker(source_key)
        if not breaker.allow_request():
            logger.warning("scraper.skipping_circuit_open", source=source_key)
            return 0, 0, 0

        if not await self._check_robots_txt(source["url"]):
            logger.warning("scraper.robots_blocked", url=source["url"])
            return 0, 0, 0

        await self._rate_limit(source["url"], source.get("rate_limit", 2.0))

        try:
            if source.get("requires_js"):
                html = await self._fetch_with_playwright(source["url"])
            else:
                html = await self._fetch_static(source["url"])

            if not html:
                breaker.record_failure()
                return 0, 0, 0

            schemes_data = await self._extract_schemes(html, source)
            logger.info("scraper.parsed", source=source_key, count=len(schemes_data))

            if not schemes_data:
                logger.warning("scraper.no_schemes_found", source=source_key)
                return 0, 0, 0

            created, updated = await self._upsert_schemes(schemes_data, source)
            breaker.record_success()

            return len(schemes_data), created, updated

        except Exception as exc:
            breaker.record_failure()
            logger.error("scraper.source_failed", source=source_key, error=str(exc))
            return 0, 0, 0

    async def _extract_schemes(
        self, html: str, source: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        extractor_type = source.get("extractor", "parser")

        if extractor_type == "ap_portal":
            extractor = APPortalExtractor()
            return extractor.extract(html)
        elif extractor_type == "telangana":
            extractor = TelanganaPortalExtractor()
            return extractor.extract(html)

        schemes = self.parser.parse_html(html, source["url"])

        if not schemes:
            ai_schemes = await self.ai_extractor.extract(html, source["url"])
            if ai_schemes:
                return ai_schemes

        return schemes

    async def _fetch_static(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        }
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0, connect=10.0),
                    follow_redirects=True,
                    headers=headers,
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    wait = (attempt + 1) * 10
                    logger.warning("scraper.rate_limited", url=url, retry_in=wait)
                    await asyncio.sleep(wait)
                    continue
                logger.error("scraper.http_error", url=url, status=exc.response.status_code, attempt=attempt + 1)
                if attempt < 2:
                    await asyncio.sleep((attempt + 1) * 2)
                    continue
                return None
            except httpx.RequestError as exc:
                logger.error("scraper.request_error", url=url, error=str(exc), attempt=attempt + 1)
                if attempt < 2:
                    await asyncio.sleep((attempt + 1) * 5)
                    continue
                return None
        return None

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        for attempt in range(2):
            try:
                from playwright.async_api import async_playwright

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent=ua.random,
                        viewport={"width": 1920, "height": 1080},
                        locale="en-IN",
                    )
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=45000)
                    await asyncio.sleep(3)
                    content = await page.content()
                    await browser.close()
                    return content
            except Exception as exc:
                logger.error("scraper.playwright_error", url=url, error=str(exc), attempt=attempt + 1)
                if attempt < 1:
                    await asyncio.sleep(5)
                    continue
                return None
        return None

    async def _check_robots_txt(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base in ROBOTS_TXT_CACHE:
            return ROBOTS_TXT_CACHE[base]
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.get(f"{base}/robots.txt")
                if resp.status_code == 200:
                    allowed = "Disallow: /" not in resp.text
                    ROBOTS_TXT_CACHE[base] = allowed
                    return allowed
                ROBOTS_TXT_CACHE[base] = True
                return True
        except Exception:
            ROBOTS_TXT_CACHE[base] = True
            return True

    async def _rate_limit(self, url: str, min_interval: float = 2.0) -> None:
        parsed = urlparse(url)
        domain = parsed.netloc
        last = DOMAIN_LAST_FETCH.get(domain, 0.0)
        elapsed = time.monotonic() - last
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        DOMAIN_LAST_FETCH[domain] = time.monotonic()

    def _get_circuit_breaker(self, source_key: str) -> SourceCircuitBreaker:
        if source_key not in self._circuit_breakers:
            self._circuit_breakers[source_key] = SourceCircuitBreaker(name=source_key)
        return self._circuit_breakers[source_key]

    async def _upsert_schemes(
        self,
        schemes_data: List[Dict[str, Any]],
        source: Dict[str, Any],
    ) -> Tuple[int, int]:
        from app.core.database import async_session_factory
        from app.repositories.scheme_repo import SchemeRepository

        created = 0
        updated = 0

        for data in schemes_data:
            data.setdefault("source_url", source["url"])
            data.setdefault("level", source.get("type", "central"))
            content_str = str(sorted(data.items()))
            data["content_hash"] = hashlib.sha256(content_str.encode()).hexdigest()

        async with async_session_factory() as session:
            repo = SchemeRepository(session)
            c, u = await repo.bulk_upsert(schemes_data)
            created += c
            updated += u
            await session.commit()

        return created, updated

    def get_all_source_status(self) -> List[Dict[str, Any]]:
        statuses = []
        for key, source in self.sources.items():
            breaker = self._circuit_breakers.get(key)
            statuses.append({
                "source_key": key,
                "name": source["name"],
                "url": source["url"],
                "type": source["type"],
                "circuit": breaker.status() if breaker else {"is_open": False, "total_scrapes": 0, "total_errors": 0, "health": "unknown"},
            })
        return statuses
