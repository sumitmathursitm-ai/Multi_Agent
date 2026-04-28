import base64
import json
from pathlib import Path
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings


def send_email_with_attachment(
    subject: str,
    body: str,
    attachment_path: Path,
    recipient: str | None = None,
) -> str:
    settings = get_settings()
    to_address = (recipient or settings.email_recipient).strip()
    from_address = settings.email_from.strip()
    api_key = settings.resend_api_key.strip()

    if not api_key:
        raise ValueError("RESEND_API_KEY is required.")
    if not from_address:
        raise ValueError("EMAIL_FROM is required. Use a verified Resend sender such as reports@yourdomain.com.")
    if not to_address:
        raise ValueError("EMAIL_RECIPIENT is required, or enter a recipient in the Streamlit sidebar.")

    attachment_content = base64.b64encode(attachment_path.read_bytes()).decode("ascii")
    payload = {
        "from": from_address,
        "to": [to_address],
        "subject": subject,
        "text": body,
        "attachments": [
            {
                "filename": attachment_path.name,
                "content": attachment_content,
            }
        ],
    }

    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError(f"Resend API failed with HTTP {response.status}.")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend API failed with HTTP {exc.code}: {details}") from exc
    except (URLError, socket.timeout, OSError) as exc:
        raise RuntimeError(f"Resend HTTPS email send failed: {exc}") from exc

    return to_address


def test_email_provider() -> str:
    settings = get_settings()
    if not settings.resend_api_key.strip():
        raise ValueError("RESEND_API_KEY is not configured.")
    if not settings.email_from.strip():
        raise ValueError("EMAIL_FROM is not configured.")
    return settings.email_from.strip()


def email_debug_summary() -> dict[str, str]:
    settings = get_settings()
    return {
        "email_provider": "resend",
        "email_from": _mask_email(settings.email_from.strip()),
        "recipient": _mask_email(settings.email_recipient.strip()),
        "resend_api_key_configured": "yes" if settings.resend_api_key.strip() else "no",
    }


def _mask_email(value: str) -> str:
    if "@" not in value:
        return value
    name, domain = value.split("@", 1)
    if len(name) <= 2:
        return f"{name[:1]}***@{domain}"
    return f"{name[:2]}***@{domain}"
