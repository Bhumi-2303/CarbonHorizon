"""
Email service interface and providers for transactional and security alerts.

Supported Providers:
- ResendEmailProvider: Sends via Resend REST API (https://api.resend.com/emails)
- SMTPEmailProvider: Sends via standard SMTP / STARTTLS using asyncio.to_thread
- StubEmailProvider: In-memory tracking for tests
- ConsoleEmailProvider: Logs outgoing alert messages to stdout
"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger("app.security.email")


class EmailProvider(Protocol):
    async def send_security_alert_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:
        """Send a security alert email to the recipient."""
        ...


class StubEmailProvider:
    """In-memory stub provider for testing."""

    def __init__(self) -> None:
        self.sent_emails: List[Dict[str, Any]] = []

    async def send_security_alert_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:
        record = {
            "to_email": to_email,
            "subject": subject,
            "body": body,
        }
        self.sent_emails.append(record)
        logger.info(
            f"[StubEmailProvider] Recorded alert email to {to_email}: {subject}"
        )
        return True

    def clear(self) -> None:
        self.sent_emails.clear()


class ConsoleEmailProvider:
    """Console/logging provider for local development."""

    async def send_security_alert_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:
        logger.warning(
            f"[Security Alert Email]\nTo: {to_email}\nSubject: {subject}\nBody: {body}"
        )
        return True


class ResendEmailProvider:
    """Production provider using Resend API (https://resend.com)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or getattr(settings, "RESEND_API_KEY", "")
        self.from_email = from_email or getattr(
            settings, "EMAIL_FROM", "security@carbonhorizon.app"
        )

    async def send_security_alert_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:
        if not self.api_key:
            logger.error("ResendEmailProvider failed: RESEND_API_KEY is not set")
            return False

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": self.from_email,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    logger.info(
                        "Resend email dispatched to %s [id=%s]",
                        to_email,
                        resp.json().get("id"),
                    )
                    return True
                else:
                    logger.error(
                        f"Resend API error {resp.status_code}: {resp.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Failed to send email via Resend: {e}")
            return False


class SMTPEmailProvider:
    """Production provider using standard SMTP / TLS."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        from_email: Optional[str] = None,
    ) -> None:
        self.host = host or getattr(settings, "SMTP_HOST", "")
        self.port = port or getattr(settings, "SMTP_PORT", 587)
        self.user = user or getattr(settings, "SMTP_USER", "")
        self.password = password or getattr(settings, "SMTP_PASSWORD", "")
        self.use_tls = use_tls
        self.from_email = from_email or getattr(
            settings, "EMAIL_FROM", "security@carbonhorizon.app"
        )

    def _sync_send(self, to_email: str, subject: str, body: str) -> bool:
        if not self.host:
            logger.error("SMTPEmailProvider failed: SMTP_HOST is not set")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))

        try:
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=10)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                if self.use_tls:
                    server.starttls()

            if self.user and self.password:
                server.login(self.user, self.password)

            server.sendmail(self.from_email, [to_email], msg.as_string())
            server.quit()
            logger.info(f"SMTP email dispatched successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False

    async def send_security_alert_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:
        return await asyncio.to_thread(self._sync_send, to_email, subject, body)


_current_email_provider: Optional[EmailProvider] = None


def get_email_service() -> EmailProvider:
    """
    Get or initialize the configured email provider.
    Selectable via settings.EMAIL_PROVIDER: "resend", "smtp", "stub", or "console".
    """
    global _current_email_provider
    if _current_email_provider is not None:
        return _current_email_provider

    provider_name = getattr(settings, "EMAIL_PROVIDER", "console").lower().strip()

    if provider_name == "resend":
        _current_email_provider = ResendEmailProvider()
    elif provider_name == "smtp":
        _current_email_provider = SMTPEmailProvider()
    elif provider_name == "stub" or settings.ENVIRONMENT in ("development", "testing"):
        _current_email_provider = StubEmailProvider()
    else:
        _current_email_provider = ConsoleEmailProvider()

    return _current_email_provider


def set_email_service(provider: Optional[EmailProvider]) -> None:
    """Override email provider (primarily for tests)."""
    global _current_email_provider
    _current_email_provider = provider
