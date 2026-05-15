from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.core.logging import logger


class SchemeParser:
    def parse_html(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        schemes = []

        schemes.extend(self._parse_myscheme(soup, base_url))
        schemes.extend(self._parse_india_gov(soup, base_url))

        return schemes

    def _parse_myscheme(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        schemes = []
        cards = soup.select("[class*='scheme-card'], [class*='card'], article, .scheme-item")

        for card in cards:
            title_el = card.select_one(
                "h2, h3, [class*='title'], [class*='heading'], [class*='name']"
            )
            desc_el = card.select_one(
                "p, [class*='description'], [class*='desc'], [class*='summary']"
            )
            link_el = card.select_one("a[href]")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            scheme = {
                "title": title,
                "description": desc_el.get_text(strip=True) if desc_el else "",
                "source_url": urljoin(base_url, link_el["href"]) if link_el and link_el.get("href") else base_url,
                "tags": self._extract_tags(card),
                "status": "active",
            }

            if self._is_valid_scheme(scheme):
                scheme["slug"] = self._make_slug(title)
                schemes.append(scheme)

        return schemes

    def _parse_india_gov(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        schemes = []
        items = soup.select("li a[href], .views-row a, .node a")

        for item in items:
            title = item.get_text(strip=True)
            href = item.get("href", "")

            if not title or len(title) < 5:
                continue
            if not href or href.startswith("#") or "javascript" in href:
                continue

            description = ""
            parent = item.parent
            if parent:
                desc_el = parent.select_one("p, .description, .summary")
                if desc_el:
                    description = desc_el.get_text(strip=True)

            scheme = {
                "title": title,
                "description": description,
                "source_url": urljoin(base_url, href),
                "tags": [],
                "status": "active",
            }

            if self._is_valid_scheme(scheme):
                scheme["slug"] = self._make_slug(title)
                schemes.append(scheme)

        return schemes

    def _extract_tags(self, element) -> List[str]:
        tags = []
        for tag_el in element.select("[class*='tag'], [class*='badge'], [class*='category']"):
            text = tag_el.get_text(strip=True)
            if text and len(text) < 50:
                tags.append(text.lower())
        return tags

    def _is_valid_scheme(self, scheme: Dict[str, Any]) -> bool:
        title = scheme.get("title", "")
        skip_keywords = [
            "privacy", "terms", "sitemap", "copyright", "contact us",
            "login", "register", "sign up",
        ]
        title_lower = title.lower()
        for kw in skip_keywords:
            if kw in title_lower:
                return False
        return True

    def _make_slug(self, title: str) -> str:
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        slug = slug.strip("-")
        if not slug or len(slug) < 3:
            slug = f"scheme-{abs(hash(title)) % 100000}"
        return slug
