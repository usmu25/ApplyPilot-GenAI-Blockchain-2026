import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))


def clean_email_address(address: str) -> str:
    if not address:
        raise ValueError("Email address is empty.")

    address = address.strip()
    address = address.replace("mailto:", "")
    address = address.replace("<", "").replace(">", "")
    address = address.replace("\n", "").replace("\r", "")

    _, parsed_email = parseaddr(address)

    if not parsed_email or "@" not in parsed_email:
        raise ValueError(f"Invalid email address: {address}")

    return parsed_email


def clean_header(text: str) -> str:
    if not text:
        return "Application"

    text = str(text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = " ".join(text.split())

    return text[:180]


def clean_body(text: str) -> str:
    if not text:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text


def send_email_with_attachments(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_paths: list = None
) -> dict:
    if not EMAIL_USER or not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_USER or EMAIL_APP_PASSWORD is missing in .env")

    sender_email = clean_email_address(EMAIL_USER)
    recipient_email = clean_email_address(recipient_email)
    subject = clean_header(subject)
    body = clean_body(body)

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(body, subtype="plain", charset="utf-8")

    attachment_paths = attachment_paths or []

    for attachment_path in attachment_paths:
        if not attachment_path:
            continue

        with open(attachment_path, "rb") as file:
            file_data = file.read()
            file_name = os.path.basename(attachment_path)

        if attachment_path.lower().endswith(".pdf"):
            maintype = "application"
            subtype = "pdf"
        else:
            maintype = "application"
            subtype = "octet-stream"

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=file_name
        )

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(sender_email, EMAIL_APP_PASSWORD)
        server.send_message(message)

    return {
        "status": "sent",
        "recipient": recipient_email,
        "subject": subject,
        "attachments": attachment_paths
    }


def send_email_with_attachment(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str = None
) -> dict:
    attachments = [attachment_path] if attachment_path else []

    return send_email_with_attachments(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        attachment_paths=attachments
    )


def extract_email_body(draft_text: str) -> str:
    if "Email Draft:" in draft_text:
        return draft_text.split("Email Draft:", 1)[1].strip()

    if "Email:" in draft_text:
        return draft_text.split("Email:", 1)[1].strip()

    return draft_text.strip()
