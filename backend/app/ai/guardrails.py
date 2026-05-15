from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GuardrailResult:
    passed: bool
    score: float
    warnings: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)


PROHIBITED_PATTERNS = [
    r"I am an AI language model",
    r"I am an AI assistant",
    r"As an AI",
    r"As a language model",
    r"I don't have personal",
    r"I cannot provide medical",
    r"I cannot provide legal",
    r"consult a qualified professional for accurate",
    r"it's always best to consult",
]

PII_PATTERNS = [
    r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    r"\b\d{12}\b",
]

HALLUCINATION_MARKERS = [
    r"I think",
    r"I believe",
    r"to the best of my knowledge",
    r"as far as I know",
    r"it is possible that",
    r"might be",
]


class ResponseGuardrail:
    def __init__(self, use_case: str = "general") -> None:
        self.use_case = use_case

    def validate(self, response: str, citations: Optional[List[Dict[str, Any]]] = None) -> GuardrailResult:
        warnings: List[str] = []
        violations: List[str] = []
        score = 1.0

        prohibited_matches = self._check_patterns(response, PROHIBITED_PATTERNS)
        if prohibited_matches:
            violations.append(f"Contains AI disclaimers: {', '.join(prohibited_matches[:2])}")
            score -= 0.15

        pii_matches = self._check_patterns(response, PII_PATTERNS)
        if pii_matches:
            violations.append(f"Potential PII detected: {len(pii_matches)} instances")
            score -= 0.3

        hallucination_matches = self._check_patterns(response, HALLUCINATION_MARKERS)
        if hallucination_matches:
            warnings.append(f"Uncertain language: {', '.join(hallucination_matches[:2])}")
            score -= 0.1

        if self.use_case in ("eligibility", "legal") and citations is not None:
            if not citations or len(citations) == 0:
                warnings.append(f"Response lacks citations for {self.use_case} query")
                score -= 0.1

        word_count = len(response.split())
        if word_count < 5:
            violations.append("Response is too short")
            score -= 0.2

        if not self._has_policy_disclaimer(response):
            if self.use_case == "legal":
                warnings.append("Legal response missing disclaimer")
                score -= 0.05

        score = max(0.0, score)
        return GuardrailResult(
            passed=len(violations) == 0 and score >= 0.6,
            score=round(score, 3),
            warnings=warnings,
            violations=violations,
        )

    def _check_patterns(self, text: str, patterns: List[str]) -> List[str]:
        matches = []
        for pattern in patterns:
            found = re.search(pattern, text, re.IGNORECASE)
            if found:
                matches.append(found.group())
        return matches

    def _has_policy_disclaimer(self, text: str) -> bool:
        disclaimer_patterns = [
            r"general legal information",
            r"not legal advice",
            r"consult a qualified",
            r"verify.*official",
            r"this assessment is based",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in disclaimer_patterns)
