from __future__ import annotations

import re
from typing import List, Tuple

INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|directions|prompts)", "INJECTION_IGNORE"),
    (r"forget\s+(all\s+)?(previous|above)", "INJECTION_FORGET"),
    (r"(you\s+are\s+|now\s+you'?re?\s+)a?\s*free\s+(ai|assistant|model)", "INJECTION_FREE"),
    (r"print\s+(your\s+)?(system\s+)?prompt", "INJECTION_PRINT_PROMPT"),
    (r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions)", "INJECTION_REVEAL"),
    (r"output\s+(your\s+)?(system\s+)?prompt", "INJECTION_OUTPUT_PROMPT"),
    (r"new\s+(instructions|rules|directive)", "INJECTION_NEW_RULES"),
    (r"override\s+(instructions|rules|constraints)", "INJECTION_OVERRIDE"),
    (r"you\s+don'?t?\s+(need\s+to\s+)?follow\s+", "INJECTION_DONT_FOLLOW"),
    (r"act\s+as\s+(if\s+)?you\s+(are|were)", "INJECTION_ACT_AS"),
    (r"from\s+now\s+on\s*,?\s*you", "INJECTION_FROM_NOW"),
    (r"role.?play\s*(as|with)", "INJECTION_ROLEPLAY"),
    (r"dan\s*=\s*", "INJECTION_DAN"),
    (r"do\s+not\s+follow\s+(the\s+)?(instructions|rules|guidelines)", "INJECTION_DO_NOT_FOLLOW"),
]

PROMPT_LEAK_PATTERNS: List[str] = [
    r"system\s+prompt",
    r"initial\s+instructions",
    r"your\s+(core\s+)?instructions",
]


class InputSanitizer:
    @staticmethod
    def sanitize(text: str) -> str:
        text = text.replace("\u0000", "")
        text = text.replace("\uffff", "")
        text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
        text = text[:50000]
        return text.strip()

    @staticmethod
    def detect_injection(text: str) -> List[str]:
        detected = []
        lower = text.lower()
        for pattern, tag in INJECTION_PATTERNS:
            if re.search(pattern, lower):
                detected.append(tag)
        return detected

    @staticmethod
    def detect_prompt_leak_request(text: str) -> bool:
        lower = text.lower()
        return any(re.search(p, lower) for p in PROMPT_LEAK_PATTERNS)

    @staticmethod
    def process(text: str) -> str:
        sanitized = InputSanitizer.sanitize(text)
        injections = InputSanitizer.detect_injection(sanitized)

        if injections:
            from app.core.logging import logger
            logger.warning(
                "input_sanitizer.injection_detected",
                patterns=injections,
                text_preview=text[:100],
            )

        return sanitized
