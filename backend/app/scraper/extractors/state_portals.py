from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from app.core.logging import logger


class APPortalExtractor:
    source_name = "AP Government Portal"
    base_url = "https://www.ap.gov.in"

    def extract(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        schemes = []

        items = soup.select(".scheme-item, .service-card, .node-scheme, [class*='scheme']")
        for item in items:
            title_el = item.select_one("h2, h3, .title, .field-title")
            desc_el = item.select_one("p, .description, .field-body")
            link_el = item.select_one("a[href]")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            scheme = {
                "title": title,
                "title_te": None,
                "description": desc_el.get_text(strip=True) if desc_el else "",
                "description_te": None,
                "source_url": link_el["href"] if link_el and link_el.get("href") else self.base_url,
                "level": "state",
                "state_code": "AP",
                "tags": self._extract_tags(item),
                "status": "active",
                "slug": self._make_slug(title),
            }

            if self._is_valid(scheme):
                schemes.append(scheme)

        logger.info("scraper.ap_portal.extracted", count=len(schemes))
        return schemes

    def _extract_tags(self, element) -> List[str]:
        tags = []
        for el in element.select(".category, .tag, .badge, .field-tags"):
            text = el.get_text(strip=True)
            if text and len(text) < 50:
                tags.append(text.lower())
        return tags

    def _is_valid(self, scheme: Dict[str, Any]) -> bool:
        skip = ["privacy", "terms", "sitemap", "copyright"]
        title = scheme.get("title", "").lower()
        return not any(kw in title for kw in skip)

    def _make_slug(self, title: str) -> str:
        import re
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-") or f"ap-scheme-{abs(hash(title)) % 100000}"


class TelanganaPortalExtractor:
    source_name = "Telangana Government Portal"
    base_url = "https://www.telangana.gov.in"

    def extract(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        schemes = []

        items = soup.select(
            ".scheme-listing li, .panchayat-services li, "
            ".views-row, .node--type-scheme, [class*='scheme']"
        )
        for item in items:
            title_el = item.select_one("a, h3, .title, .field--name-title")
            desc_el = item.select_one("p, .field--name-body, .description")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = ""
            if title_el.name == "a" and title_el.get("href"):
                href = title_el["href"]
            elif item.select_one("a[href]"):
                href = item.select_one("a[href]")["href"]  # type: ignore

            if not title or len(title) < 3:
                continue

            scheme = {
                "title": title,
                "title_te": None,
                "description": desc_el.get_text(strip=True) if desc_el else "",
                "description_te": None,
                "source_url": href if href.startswith("http") else f"{self.base_url}{href}",
                "level": "state",
                "state_code": "TS",
                "tags": ["telangana"],
                "status": "active",
                "slug": self._make_slug(title),
            }

            if self._is_valid(scheme):
                schemes.append(scheme)

        logger.info("scraper.telangana_portal.extracted", count=len(schemes))
        return schemes

    def _is_valid(self, scheme: Dict[str, Any]) -> bool:
        skip = ["privacy", "terms", "copyright", "contact"]
        title = scheme.get("title", "").lower()
        return not any(kw in title for kw in skip)

    def _make_slug(self, title: str) -> str:
        import re
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-") or f"ts-scheme-{abs(hash(title)) % 100000}"
