from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.ai.providers.base import Message
from app.ai.providers.factory import ProviderFactory
from app.core.logging import logger

EXTRACTION_PROMPT = """You are a government scheme data extraction engine.
Extract structured scheme information from the raw HTML text below.

Return ONLY valid JSON in this exact format — no explanations, no markdown:
{
  "title": "Scheme Name",
  "title_hi": null or "हिन्दी नाम",
  "title_te": null or "తెలుగు పేరు",
  "description": "Detailed description in English",
  "description_hi": null or "हिन्दी विवरण",
  "description_te": null or "తెలుగు వివరణ",
  "ministry": "Ministry name or null",
  "department": "Department name or null",
  "level": "central" or "state",
  "state_code": null or "AP",
  "category": "education" | "health" | "agriculture" | "housing" | "employment" | "social_welfare" | "other",
  "tags": ["tag1", "tag2"],
  "application_url": null or "https://...",
  "eligibility_rules": [
    {"field_name": "annual_income", "operator": "lte", "value": 300000, "is_mandatory": true}
  ]
}

Rules:
- title is REQUIRED. If you cannot determine a title, return {"title": null}
- description: extract a clear 2-5 sentence summary
- eligibility_rules: extract any income limits, age limits, category restrictions you find
- tags: include category, target audience (women/farmers/students/etc), and state
- If the text contains Hindi or Telugu text, populate the _hi / _te fields
- Never hallucinate data. Use null for unknown fields."""


class AIExtractor:
    async def extract(self, html_text: str, source_url: str) -> List[Dict[str, Any]]:
        try:
            text_sample = self._prepare_text(html_text)
            if not text_sample:
                return []

            provider = await ProviderFactory.get_provider_for_use_case("document")
            result = await provider.complete(
                messages=[Message(
                    role="user",
                    content=f"Source URL: {source_url}\n\nHTML text:\n{text_sample}",
                )],
                system=EXTRACTION_PROMPT,
                temperature=0.1,
                max_tokens=1024,
            )

            schemes = self._parse_response(result.content, source_url)
            return schemes

        except Exception as exc:
            logger.error("scraper.ai_extraction.failed", url=source_url, error=str(exc))
            return []

    def _prepare_text(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean = "\n".join(lines[:200])
        return clean[:8000]

    def _parse_response(self, content: str, source_url: str) -> List[Dict[str, Any]]:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            logger.warning("scraper.ai_extraction.no_json", url=source_url)
            return []

        try:
            data = json.loads(json_match.group())
            if not data.get("title"):
                return []

            title = data["title"].strip()
            if len(title) < 3:
                return []

            slug = title.lower()
            slug = re.sub(r"[^\w\s-]", "", slug)
            slug = re.sub(r"[-\s]+", "-", slug).strip("-")

            scheme = {
                "title": title,
                "title_hi": data.get("title_hi"),
                "title_te": data.get("title_te"),
                "description": data.get("description", "")[:2000],
                "description_hi": data.get("description_hi"),
                "description_te": data.get("description_te"),
                "ministry": data.get("ministry"),
                "department": data.get("department"),
                "level": data.get("level", "central"),
                "state_code": data.get("state_code"),
                "category": data.get("category", "other"),
                "tags": data.get("tags", []),
                "application_url": data.get("application_url"),
                "source_url": source_url,
                "slug": slug or f"scheme-{abs(hash(title)) % 100000}",
                "status": "active",
            }

            eligibility = data.get("eligibility_rules", [])
            if eligibility:
                scheme["_eligibility_rules"] = eligibility

            return [scheme]

        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("scraper.ai_extraction.parse_error", url=source_url, error=str(exc))
            return []
