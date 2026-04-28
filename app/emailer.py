from email.message import EmailMessage
import base64
import json
from pathlib import Path
import re
import smtplib
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import ENV_PATH, get_settings


PLACEHOLDER_VALUES = {
    "your-email@gmail.com",
    "recipient@gmail.com",
    "your-gmail-app-password",
    "your-16-character-app-password",
}


def send_gmail_with_attachment(
    subject: str,
    body: str,
    attachment_path: Path,
    recipient: str | None = None,
) -> str:
    settings = get_settings()
    provider = _selected_provider(settings)
    if provider == "resend":
        return _send_resend_with_attachment(subject, body, attachment_path, recipient)
    if provider != "gmail":
        raise ValueError("EMAIL_PROVIDER must be one of: auto, gmail, resend.")

    return _send_gmail_smtp_with_attachment(subject, body, attachment_path, recipient)


def _send_gmail_smtp_with_attachment(
    subject: str,
    body: str,
    attachment_path: Path,
    recipient: str | None = None,
) -> str:
    to_address, sender, app_password = _gmail_credentials(recipient)

    if not to_address:
        raise ValueError("No Gmail recipient configured. Set GMAIL_RECIPIENT or enter a recipient in the Streamlit sidebar.")
    if not sender:
        raise ValueError("No Gmail sender configured. Set GMAIL_SENDER in .env.")
    if not app_password:
        raise ValueError("No Gmail app password configured. Set GMAIL_APP_PASSWORD in .env.")
    _reject_placeholder_config(to_address, sender, app_password)

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    message.add_attachment(
        attachment_path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=attachment_path.name,
    )

    try:
        settings = get_settings()
        with smtplib.SMTP_SSL(settings.gmail_smtp_host, settings.gmail_smtp_port, timeout=30) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(_gmail_auth_help(sender)) from exc
    except (smtplib.SMTPException, OSError, socket.timeout) as exc:
        raise RuntimeError(f"Gmail SMTP send failed: {exc}") from exc

    return to_address


def _send_resend_with_attachment(
    subject: str,
    body: str,
    attachment_path: Path,
    recipient: str | None = None,
) -> str:
    settings = get_settings()
    to_address = (recipient or settings.gmail_recipient).strip()
    from_address = (settings.email_from or settings.gmail_sender).strip()
    api_key = settings.resend_api_key.strip()

    if not api_key:
        raise ValueError("RESEND_API_KEY is required when EMAIL_PROVIDER is resend or auto on Railway.")
    if not from_address:
        raise ValueError("EMAIL_FROM is required for Resend. Use a verified sender such as reports@yourdomain.com.")
    if not to_address:
        raise ValueError("No recipient configured. Set GMAIL_RECIPIENT or enter a recipient in the Streamlit sidebar.")

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


def test_gmail_login() -> str:
    settings = get_settings()
    provider = _selected_provider(settings)
    if provider == "resend":
        return test_resend_config()

    to_address, sender, app_password = _gmail_credentials()
    if not to_address:
        raise ValueError("No Gmail recipient configured. Set GMAIL_RECIPIENT in .env.")
    if not sender:
        raise ValueError("No Gmail sender configured. Set GMAIL_SENDER in .env.")
    if not app_password:
        raise ValueError("No Gmail app password configured. Set GMAIL_APP_PASSWORD in .env.")
    _reject_placeholder_config(to_address, sender, app_password)

    settings = get_settings()
    try:
        with smtplib.SMTP_SSL(settings.gmail_smtp_host, settings.gmail_smtp_port, timeout=30) as smtp:
            smtp.login(sender, app_password)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(_gmail_auth_help(sender)) from exc
    except (smtplib.SMTPException, OSError, socket.timeout) as exc:
        raise RuntimeError(f"Gmail SMTP login test failed: {exc}") from exc
    return sender


def test_resend_config() -> str:
    settings = get_settings()
    if not settings.resend_api_key.strip():
        raise ValueError("RESEND_API_KEY is not configured.")
    from_address = (settings.email_from or settings.gmail_sender).strip()
    if not from_address:
        raise ValueError("EMAIL_FROM is not configured.")
    return from_address


def gmail_debug_summary() -> dict[str, str | int]:
    settings = get_settings()
    _, sender, app_password = _gmail_credentials()
    provider = _selected_provider(settings)
    return {
        "email_provider": provider,
        "sender": _mask_email(sender),
        "email_from": _mask_email((settings.email_from or sender).strip()),
        "recipient": _mask_email(settings.gmail_recipient.strip()),
        "app_password_length_after_cleanup": len(app_password),
        "resend_api_key_configured": "yes" if settings.resend_api_key.strip() else "no",
        "smtp_host": settings.gmail_smtp_host,
        "smtp_port": settings.gmail_smtp_port,
    }


def _gmail_credentials(recipient: str | None = None) -> tuple[str, str, str]:
    settings = get_settings()
    to_address = (recipient or settings.gmail_recipient).strip()
    sender = settings.gmail_sender.strip()
    app_password = re.sub(r"\s+", "", settings.gmail_app_password)
    return to_address, sender, app_password


def _gmail_auth_help(sender: str) -> str:
    return (
        f"Gmail rejected SMTP login for {sender}. This usually means the value in "
        "GMAIL_APP_PASSWORD is not a current Gmail App Password for this exact sender account. "
        "Create a new app password in Google Account -> Security -> 2-Step Verification -> App passwords, "
        "update .env, then fully restart Streamlit."
    )


def _selected_provider(settings) -> str:
    provider = settings.email_provider.strip().lower()
    if provider == "auto":
        return "resend" if settings.resend_api_key.strip() else "gmail"
    return provider


def _reject_placeholder_config(to_address: str, sender: str, app_password: str) -> None:
    if sender in PLACEHOLDER_VALUES:
        raise ValueError(
            f"GMAIL_SENDER is still set to the placeholder value. Update GMAIL_SENDER in {ENV_PATH}, "
            "then click 'Reload .env' in Streamlit or restart it."
        )
    if to_address in PLACEHOLDER_VALUES:
        raise ValueError(
            f"GMAIL_RECIPIENT is still set to the placeholder value. Update GMAIL_RECIPIENT in {ENV_PATH} "
            "or enter a recipient in the sidebar."
        )
    if app_password in PLACEHOLDER_VALUES:
        raise ValueError(
            f"GMAIL_APP_PASSWORD is still set to the placeholder value. Update GMAIL_APP_PASSWORD in {ENV_PATH}. "
            "Replace it with a real Gmail App Password."
        )


def _mask_email(value: str) -> str:
    if "@" not in value:
        return value
    name, domain = value.split("@", 1)
    if len(name) <= 2:
        return f"{name[:1]}***@{domain}"
    return f"{name[:2]}***@{domain}"
