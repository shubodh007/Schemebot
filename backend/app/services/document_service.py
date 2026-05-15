from __future__ import annotations

import hashlib
import io
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import pytesseract
from PIL import Image
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    FileTypeNotAllowedError,
    FileValidationError,
    NotFoundError,
)
from app.core.logging import logger
from app.models.document import Document, DocumentChunk
from app.models.scheme import Scheme
from app.repositories.scheme_repo import SchemeRepository
from app.schemas.document import SchemeMatchResult
from app.services.async_pdf_processor import AsyncPDFProcessor

ALLOWED_MAGIC_BYTES: Dict[str, bytes] = {
    "application/pdf": b"%PDF",
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
}


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.scheme_repo = SchemeRepository(session)
        self._pdf_processor = AsyncPDFProcessor()

    async def validate_and_upload(
        self,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        mime_type: str,
    ) -> Document:
        if len(file_content) > settings.max_upload_bytes:
            raise FileTooLargeError(
                f"File exceeds maximum size of {settings.max_upload_size_mb}MB"
            )

        if mime_type not in settings.allowed_mime_list:
            raise FileTypeNotAllowedError(f"File type '{mime_type}' is not supported")

        if not self._validate_magic_bytes(file_content, mime_type):
            raise FileValidationError("File content does not match declared type")

        if filename.lower().endswith(".svg"):
            raise FileTypeNotAllowedError("SVG files are not allowed for security reasons")

        storage_key = f"documents/{user_id}/{uuid.uuid4()}/{filename}"

        doc = Document(
            user_id=user_id,
            original_filename=filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size_bytes=len(file_content),
            status="uploading",
        )
        self.session.add(doc)
        await self.session.flush()

        from app.core.supabase_client import supabase_storage

        try:
            await supabase_storage.upload(
                path=storage_key,
                file=file_content,
                file_type=mime_type,
            )
            logger.info("document.uploaded", doc_id=str(doc.id), storage_key=storage_key)
        except Exception as exc:
            doc.status = "failed"
            doc.error_message = f"Storage upload failed: {str(exc)}"
            await self.session.flush()
            raise FileValidationError(f"Failed to upload file to storage: {str(exc)}")

        doc.status = "processing"
        doc.processing_started = datetime.now(timezone.utc)
        await self.session.flush()

        try:
            await self._process_document(doc, file_content)
        except Exception as exc:
            doc.status = "failed"
            doc.error_message = f"Processing failed: {str(exc)}"
            logger.error("document.processing_failed", doc_id=str(doc.id), error=str(exc))

        await self.session.flush()
        return doc

    def _validate_magic_bytes(self, content: bytes, mime_type: str) -> bool:
        expected = ALLOWED_MAGIC_BYTES.get(mime_type)
        if expected is None:
            return True
        return content[: len(expected)] == expected

    async def _process_document(
        self, doc: Document, file_content: bytes
    ) -> None:
        extracted_text = ""
        page_count = 0

        if doc.mime_type == "application/pdf":
            extracted_text, page_count = await self._extract_pdf_text(file_content)
        elif doc.mime_type in ("image/jpeg", "image/png"):
            extracted_text, page_count = await self._extract_image_text(file_content)
            page_count = 1

        doc.extracted_text = extracted_text
        doc.page_count = page_count

        extracted_fields = await self._analyze_fields(doc, extracted_text)
        doc.extracted_fields = extracted_fields
        doc.ocr_confidence = extracted_fields.get("_ocr_confidence", 0.0)

        scheme_matches = await self._find_matching_schemes(extracted_fields, extracted_text)
        doc.scheme_matches = scheme_matches

        doc.status = "ready"
        doc.processing_finished = datetime.now(timezone.utc)

        logger.info(
            "document.processed",
            doc_id=str(doc.id),
            pages=page_count,
            fields=len(extracted_fields),
            scheme_matches=len(scheme_matches),
        )

    async def _extract_pdf_text(self, content: bytes) -> Tuple[str, int]:
        return await self._pdf_processor.extract_text(content), 0

    async def _extract_image_text(self, content: bytes) -> Tuple[str, int]:
        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image, lang="eng+hin+tel")
        return text.strip(), 1

    async def _analyze_fields(
        self, doc: Document, text: str
    ) -> Dict[str, Any]:
        fields: Dict[str, Any] = {
            "_ocr_confidence": 0.85,
            "_word_count": len(text.split()),
            "_char_count": len(text),
            "name": None,
            "date_of_birth": None,
            "gender": None,
            "address": None,
            "id_number": None,
        }

        doc_type = doc.document_type
        if doc_type == "aadhaar":
            import re
            aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
            match = re.search(aadhaar_pattern, text)
            if match:
                fields["id_number"] = match.group().replace(" ", "")
            name_patterns = [
                r"(?:Name|नाम)\s*[:\-]?\s*([A-Za-z\s]+)",
            ]
            for pat in name_patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    fields["name"] = match.group(1).strip()
                    break
        elif doc_type == "pan":
            import re
            pan_pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
            match = re.search(pan_pattern, text.upper())
            if match:
                fields["id_number"] = match.group()

        return fields

    async def _find_matching_schemes(
        self, fields: Dict[str, Any], text: str
    ) -> List[Dict[str, Any]]:
        _ = fields
        schemes, _ = await self.scheme_repo.search(query="", limit=50)
        matches: List[Dict[str, Any]] = []
        for scheme in schemes:
            keywords = scheme.tags + [scheme.title.lower(), scheme.ministry or ""]
            match_count = sum(1 for kw in keywords if kw.lower() in text.lower())
            if match_count > 0:
                confidence = min(match_count / max(len(keywords), 1) * 2, 1.0)
                matches.append({
                    "scheme_id": str(scheme.id),
                    "scheme_title": scheme.title,
                    "match_confidence": round(confidence, 4),
                    "matched_fields": [k for k in keywords[:3] if k.lower() in text.lower()],
                })
        matches.sort(key=lambda m: m["match_confidence"], reverse=True)
        return matches[:5]
