from __future__ import annotations

import pytest
from app.ai.rag.chunker import TextChunker


class TestTextChunker:
    def test_chunk_empty_text(self):
        chunker = TextChunker()
        assert chunker.chunk_text("") == []
        assert chunker.chunk_text("   ") == []

    def test_chunk_short_text(self):
        chunker = TextChunker()
        text = "This is a short text about government schemes."
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0]["content"] == text

    def test_chunk_preserves_paragraphs(self):
        chunker = TextChunker(target_size=20, overlap=5)
        text = "First paragraph about eligibility.\n\nSecond paragraph about benefits.\n\nThird paragraph about application."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2
        assert "First paragraph" in chunks[0]["content"] or "First paragraph" in chunks[0]["content"]

    def test_chunk_overlap(self):
        chunker = TextChunker(target_size=15, overlap=5)
        text = "word " * 50
        chunks = chunker.chunk_text(text)
        if len(chunks) > 1:
            first_words = set(chunks[0]["content"].split())
            second_words = set(chunks[1]["content"].split())
            overlap = first_words & second_words
            assert len(overlap) > 1

    def test_chunk_tables_preserved(self):
        chunker = TextChunker()
        table = "| Name | Amount |\n|------|-------|\n| PM-KISAN | 6000 |\n| Awas | 267000 |"
        chunks = chunker.chunk_text(table)
        assert len(chunks) == 1
        assert "PM-KISAN" in chunks[0]["content"]

    def test_scheme_chunk(self):
        chunker = TextChunker()
        chunks = chunker.chunk_scheme(
            title="PM-KISAN",
            description="PM Kisan Samman Nidhi provides income support of Rs. 6000 per year.",
            metadata={"scheme_id": "123", "source_url": "https://example.com"},
        )
        assert len(chunks) == 1
        assert chunks[0]["chunk_metadata"]["scheme_id"] == "123"
        assert chunks[0]["token_count"] > 0
