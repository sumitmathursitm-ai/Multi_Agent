from email.message import EmailMessage
from pathlib import Path
import re
import smtplib
import socket

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


def test_gmail_login() -> str:
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


def gmail_debug_summary() -> dict[str, str | int]:
    settings = get_settings()
    _, sender, app_password = _gmail_credentials()
    return {
        "sender": _mask_email(sender),
        "recipient": _mask_email(settings.gmail_recipient.strip()),
        "app_password_length_after_cleanup": len(app_password),
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
