from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UpdateUserRequest(BaseModel):
    role: Optional[str] = Field(None, pattern=r"^(citizen|admin|superadmin)$")
    status: Optional[str] = Field(None, pattern=r"^(pending_verification|active|suspended|deleted)$")


class TriggerScrapeRequest(BaseModel):
    source: str = Field(default="myscheme", pattern=r"^(myscheme|india_gov|ap_portal|telangana_portal)$")
