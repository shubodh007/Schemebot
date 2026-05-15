from __future__ import annotations

from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import logger


class EmailService:
    """Transactional email via SendGrid API (async)."""

    def __init__(self) -> None:
        self._api_key = settings.sendgrid_api_key or ""
        self._from_email = settings.sendgrid_from_email or "noreply@govscheme.in"
        self._enabled = bool(self._api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def send(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> None:
        if not self._enabled:
            logger.info("email.disabled", to=to_email, subject=subject)
            return

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": to_email}]}],
                        "from": {"email": self._from_email},
                        "subject": subject,
                        "content": [
                            {"type": "text/plain", "value": text_content or html_content},
                            {"type": "text/html", "value": html_content},
                        ],
                    },
                )
                if response.status_code not in (200, 201, 202):
                    logger.error(
                        "email.send_failed",
                        to=to_email,
                        status=response.status_code,
                        body=response.text[:200],
                    )
                else:
                    logger.info("email.sent", to=to_email, subject=subject)
        except httpx.RequestError as exc:
            logger.error("email.send_error", to=to_email, error=str(exc))

    async def send_password_reset(self, to_email: str, reset_token: str) -> None:
        reset_url = f"{settings.app_base_url}/reset-password?token={reset_token}"
        await self.send(
            to_email=to_email,
            subject="Reset your GovScheme AI password",
            html_content=f"""
            <p>You requested a password reset for your GovScheme AI account.</p>
            <p><a href="{reset_url}">Click here to reset your password</a></p>
            <p>This link expires in 15 minutes. If you didn't request this, ignore this email.</p>
            """,
            text_content=f"Reset your password at: {reset_url}\nThis link expires in 15 minutes.",
        )

    async def send_welcome(self, to_email: str, name: str) -> None:
        await self.send(
            to_email=to_email,
            subject="Welcome to GovScheme AI",
            html_content=f"""
            <p>Welcome to GovScheme AI, {name}!</p>
            <p>Start discovering government schemes you qualify for.</p>
            """,
            text_content=f"Welcome to GovScheme AI, {name}!",
        )


email_service = EmailService()
