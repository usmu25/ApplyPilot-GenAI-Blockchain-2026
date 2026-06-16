import os
import imaplib
import email
import re
from email.header import decode_header
from html import unescape
from dotenv import load_dotenv

from tools.application_tracker import (
    read_tracker_rows,
    update_reply_status,
    mark_checked_no_reply
)


load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))


def decode_text(value: str) -> str:
    if not value:
        return ""

    decoded_parts = decode_header(value)
    result = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="ignore")
        else:
            result += part

    return result


def clean_html(html_text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html_text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return text.strip()


def extract_email_body(message) -> str:
    plain_text = ""
    html_text = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition.lower():
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="ignore")

                if content_type == "text/plain" and not plain_text:
                    plain_text = decoded.strip()

                elif content_type == "text/html" and not html_text:
                    html_text = clean_html(decoded)

            except Exception:
                continue

    else:
        try:
            payload = message.get_payload(decode=True)
            charset = message.get_content_charset() or "utf-8"

            if payload:
                decoded = payload.decode(charset, errors="ignore")

                if message.get_content_type() == "text/html":
                    html_text = clean_html(decoded)
                else:
                    plain_text = decoded.strip()

        except Exception:
            pass

    body = plain_text if plain_text else html_text

    # Remove excessive whitespace
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip()

    return body


def create_body_preview(body: str, limit: int = 1000) -> str:
    if not body:
        return "No readable email body found."

    # Try to remove quoted previous email sections
    cut_markers = [
        "\nOn ",
        "\nFrom:",
        "\nSent:",
        "\n-----Original Message-----",
        "\n> "
    ]

    preview = body

    for marker in cut_markers:
        index = preview.find(marker)
        if index > 100:
            preview = preview[:index].strip()
            break

    if len(preview) > limit:
        preview = preview[:limit].strip() + "..."

    return preview


def normalize_subject(subject: str) -> str:
    subject = subject.lower().strip()
    subject = re.sub(r"^(re|fwd|fw):\s*", "", subject)
    subject = re.sub(r"\s+", " ", subject)
    return subject


def subject_matches(original_subject: str, reply_subject: str, application_id: str) -> bool:
    original = normalize_subject(original_subject)
    reply = normalize_subject(reply_subject)

    if application_id and application_id.lower() in reply.lower():
        return True

    if original and original in reply:
        return True

    return False


def check_replies_and_update_tracker(limit_messages: int = 100) -> dict:
    if not EMAIL_USER or not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_USER or EMAIL_APP_PASSWORD is missing in .env")

    rows = read_tracker_rows()

    pending_rows = [
        row for row in rows
        if row.get("email_status") == "Sent" and row.get("reply_status") == "No Reply"
    ]

    if not pending_rows:
        return {
            "checked": 0,
            "replies_found": 0,
            "new_replies": [],
            "message": "No pending sent applications to check."
        }

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_APP_PASSWORD)
    mail.select("inbox")

    status, data = mail.search(None, "ALL")

    if status != "OK":
        mail.logout()
        return {
            "checked": len(pending_rows),
            "replies_found": 0,
            "new_replies": [],
            "message": "Could not search inbox."
        }

    message_ids = data[0].split()
    recent_ids = message_ids[-limit_messages:]

    replies_found = 0
    new_replies = []

    for row in pending_rows:
        application_id = row["application_id"]
        original_subject = row["subject"]
        expected_sender = row["recipient_email"].lower()
        found_reply = False

        for msg_id in reversed(recent_ids):
            status, msg_data = mail.fetch(msg_id, "(RFC822)")

            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            message = email.message_from_bytes(raw_email)

            reply_subject = decode_text(message.get("Subject", ""))
            sender = decode_text(message.get("From", ""))
            date = decode_text(message.get("Date", ""))

            sender_lower = sender.lower()

            subject_ok = subject_matches(
                original_subject=original_subject,
                reply_subject=reply_subject,
                application_id=application_id
            )

            sender_ok = expected_sender in sender_lower

            if subject_ok or (sender_ok and normalize_subject(original_subject) in normalize_subject(reply_subject)):
                body = extract_email_body(message)
                body_preview = create_body_preview(body)

                update_reply_status(
                    application_id=application_id,
                    reply_from=sender,
                    reply_received_at=date
                )

                replies_found += 1
                found_reply = True

                new_replies.append({
                    "application_id": application_id,
                    "opportunity_title": row.get("opportunity_title", ""),
                    "organization": row.get("organization", ""),
                    "recipient_email": row.get("recipient_email", ""),
                    "reply_from": sender,
                    "reply_subject": reply_subject,
                    "reply_received_at": date,
                    "reply_body_preview": body_preview
                })

                break

        if not found_reply:
            mark_checked_no_reply(application_id)

    mail.logout()

    return {
        "checked": len(pending_rows),
        "replies_found": replies_found,
        "new_replies": new_replies,
        "message": "Reply check completed."
    }
