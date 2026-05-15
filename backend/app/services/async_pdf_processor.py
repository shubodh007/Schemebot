from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from app.core.logging import logger

_pdf_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pdf")


class AsyncPDFProcessor:
    _executor = _pdf_executor

    async def extract_text(self, pdf_bytes: bytes, max_pages: int = 200) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._sync_extract,
            pdf_bytes,
            max_pages,
        )

    def _sync_extract(self, pdf_bytes: bytes, max_pages: int) -> str:
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            pages = []
            for i, page in enumerate(reader.pages):
                if i >= max_pages:
                    break
                text = page.extract_text() or ""
                pages.append(text)
            return "\n\n".join(pages)
        except Exception as exc:
            logger.error("pdf.extraction_failed", error=str(exc))
            raise

    async def extract_chunks(
        self,
        pdf_bytes: bytes,
        chunk_size: int = 512,
        overlap: int = 50,
        max_pages: int = 200,
    ) -> List[dict]:
        text = await self.extract_text(pdf_bytes, max_pages)
        loop = asyncio.get_running_loop()
        from app.ai.rag.chunker import TextChunker
        chunker = TextChunker(target_size=chunk_size, overlap=overlap)
        return await loop.run_in_executor(
            self._executor,
            chunker.chunk_text,
            text,
        )
