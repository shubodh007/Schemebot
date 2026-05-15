from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import logger


class AsyncSupabaseStorage:
    """Async Supabase Storage client using httpx.

    Replaces sync supabase-py with fully async HTTP calls.
    """

    def __init__(self) -> None:
        self._base_url = settings.supabase_url.rstrip("/")
        self._anon_key = settings.supabase_anon_key
        self._service_key = settings.supabase_service_role_key
        self._default_bucket = "documents"

    def _headers(self, service_role: bool = True) -> Dict[str, str]:
        return {
            "apikey": self._service_key if service_role else self._anon_key,
            "Authorization": f"Bearer {self._service_key if service_role else self._anon_key}",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload(
        self,
        path: str,
        file: bytes,
        file_type: str = "application/octet-stream",
        bucket: Optional[str] = None,
        upsert: bool = True,
    ) -> Dict[str, Any]:
        bucket = bucket or self._default_bucket
        url = f"{self._base_url}/storage/v1/object/{bucket}/{path}"
        headers = {
            **self._headers(service_role=True),
            "Content-Type": file_type,
            "x-upsert": "true" if upsert else "false",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.post(url, content=file, headers=headers)
            if response.status_code not in (200, 201):
                logger.error(
                    "storage.upload_failed",
                    path=path,
                    status=response.status_code,
                    body=response.text[:200],
                )
                raise RuntimeError(f"Storage upload failed: {response.status_code}")
            logger.info("storage.uploaded", path=path, bucket=bucket)
            return response.json()

    async def download(self, path: str, bucket: Optional[str] = None) -> bytes:
        bucket = bucket or self._default_bucket
        url = f"{self._base_url}/storage/v1/object/{bucket}/{path}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(url, headers=self._headers(service_role=True))
            if response.status_code != 200:
                raise FileNotFoundError(f"Storage download failed: {path}")
            return response.content

    async def delete(self, path: str, bucket: Optional[str] = None) -> None:
        bucket = bucket or self._default_bucket
        url = f"{self._base_url}/storage/v1/object/{bucket}/{path}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.delete(url, headers=self._headers(service_role=True))
            if response.status_code not in (200, 204):
                logger.error("storage.delete_failed", path=path, status=response.status_code)
                raise RuntimeError(f"Storage delete failed: {response.status_code}")

    async def list_files(self, prefix: str = "", bucket: Optional[str] = None) -> List[Dict[str, Any]]:
        bucket = bucket or self._default_bucket
        url = f"{self._base_url}/storage/v1/object/{bucket}/{prefix}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.get(url, headers=self._headers(service_role=True))
            if response.status_code != 200:
                return []
            return response.json()

    async def create_bucket(self, bucket: str, public: bool = False) -> Dict[str, Any]:
        url = f"{self._base_url}/storage/v1/bucket"

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.post(
                url,
                json={"name": bucket, "public": public, "file_size_limit": 10485760},
                headers=self._headers(service_role=True),
            )
            return response.json()


supabase_storage = AsyncSupabaseStorage()
