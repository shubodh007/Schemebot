from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.core.config import settings
from app.core.logging import logger


class SupabaseClient:
    def __init__(self) -> None:
        self._client: Optional[Client] = None

    def initialize(self) -> Client:
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key,
            )
        return self._client

    @property
    def client(self) -> Client:
        return self.initialize()

    @property
    def auth(self):
        return self.client.auth

    @property
    def storage(self):
        return self.client.storage


class SupabaseStorage:
    def __init__(self) -> None:
        self._supabase = SupabaseClient()
        self._bucket = "documents"

    async def upload(
        self,
        path: str,
        file: bytes,
        file_type: str,
    ) -> Dict[str, Any]:
        return self._supabase.storage.from_(self._bucket).upload(
            path=path,
            file=io.BytesIO(file),
            file_options={"content-type": file_type},
        )

    async def download(self, path: str) -> bytes:
        result = self._supabase.storage.from_(self._bucket).download(path)
        return result

    async def delete(self, path: str) -> None:
        self._supabase.storage.from_(self._bucket).remove([path])

    async def list_files(self, prefix: str) -> List[Dict[str, Any]]:
        return self._supabase.storage.from_(self._bucket).list(prefix)


supabase_storage = SupabaseStorage()
