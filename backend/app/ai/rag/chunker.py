from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


class TextChunker:
    def __init__(
        self,
        target_size: int = 512,
        overlap: int = 50,
    ) -> None:
        self.target_size = target_size
        self.overlap = overlap

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        cleaned = self._clean_text(text)
        paragraphs = self._split_paragraphs(cleaned)
        chunks: List[Dict[str, Any]] = []
        current: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._count_tokens(para)
            is_table = self._is_table(para)

            if is_table:
                if current:
                    chunks.append(self._make_chunk(current, metadata))
                    current = []
                    current_tokens = 0
                chunks.append(self._make_chunk([para], {**(metadata or {}), "is_table": True}))
                continue

            if current_tokens + para_tokens > self.target_size and current:
                chunks.append(self._make_chunk(current, metadata))
                overlap_text = self._get_overlap(current, self.overlap)
                current = [overlap_text] if overlap_text else []
                current_tokens = self._count_tokens(overlap_text) if overlap_text else 0

            current.append(para)
            current_tokens += para_tokens

        if current:
            chunks.append(self._make_chunk(current, metadata))

        for i, chunk in enumerate(chunks):
            chunk["chunk_index"] = i
            chunk["token_count"] = self._count_tokens(chunk["content"])

        return chunks

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text

    def _split_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r"\n\n+", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _is_table(self, text: str) -> bool:
        lines = text.split("\n")
        if len(lines) < 2:
            return False
        pipe_count = sum(line.count("|") for line in lines)
        tab_count = sum(line.count("\t") for line in lines)
        return (pipe_count > len(lines) * 2) or (tab_count > len(lines))

    def _count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(text.split())

    def _make_chunk(
        self,
        paragraphs: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "content": "\n\n".join(paragraphs),
            "chunk_metadata": metadata or {},
        }

    def _get_overlap(self, paragraphs: List[str], token_count: int) -> str:
        overlap_parts: List[str] = []
        current = 0
        for para in reversed(paragraphs):
            tokens = self._count_tokens(para)
            if current + tokens > token_count:
                words = para.split()
                remaining = token_count - current
                overlap_parts.insert(0, " ".join(words[-remaining:]))
                break
            overlap_parts.insert(0, para)
            current += tokens
        return "\n\n".join(overlap_parts)

    def chunk_scheme(
        self,
        title: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        full_text = f"{title}\n\n{description}"
        return self.chunk_text(full_text, metadata)
