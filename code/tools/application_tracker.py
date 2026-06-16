import csv
import os
from datetime import datetime


TRACKER_FILE = "data/application_tracker.csv"


HEADERS = [
    "application_id",
    "session_id",
    "opportunity_number",
    "opportunity_title",
    "organization",
    "recipient_email",
    "subject",
    "email_status",
    "sent_at",
    "reply_status",
    "reply_received_at",
    "reply_from",
    "last_checked_at",
    "cv_file",
    "notes"
]


def ensure_tracker_file():
    os.makedirs("data", exist_ok=True)

    if not os.path.isfile(TRACKER_FILE) or os.path.getsize(TRACKER_FILE) == 0:
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=HEADERS)
            writer.writeheader()


def generate_application_id() -> str:
    return "AP-" + datetime.now().strftime("%Y%m%d-%H%M%S")


def read_tracker_rows() -> list:
    ensure_tracker_file()

    with open(TRACKER_FILE, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_tracker_rows(rows: list):
    ensure_tracker_file()

    with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def log_email_sent(
    application_id: str,
    session_id: str,
    opportunity_number: str,
    opportunity: dict,
    recipient_email: str,
    subject: str,
    cv_file: str,
    notes: str = ""
) -> dict:
    ensure_tracker_file()

    row = {
        "application_id": application_id,
        "session_id": session_id,
        "opportunity_number": opportunity_number,
        "opportunity_title": opportunity.get("title", ""),
        "organization": opportunity.get("organization", ""),
        "recipient_email": recipient_email,
        "subject": subject,
        "email_status": "Sent",
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reply_status": "No Reply",
        "reply_received_at": "",
        "reply_from": "",
        "last_checked_at": "",
        "cv_file": cv_file,
        "notes": notes
    }

    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writerow(row)

    return row


def update_reply_status(application_id: str, reply_from: str, reply_received_at: str):
    rows = read_tracker_rows()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in rows:
        if row["application_id"] == application_id:
            row["reply_status"] = "Replied"
            row["reply_from"] = reply_from
            row["reply_received_at"] = reply_received_at
            row["last_checked_at"] = now
        elif row["reply_status"] == "No Reply":
            row["last_checked_at"] = now

    write_tracker_rows(rows)


def mark_checked_no_reply(application_id: str):
    rows = read_tracker_rows()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in rows:
        if row["application_id"] == application_id:
            row["last_checked_at"] = now

    write_tracker_rows(rows)


def format_status_rows(limit: int = 10) -> str:
    rows = read_tracker_rows()

    if not rows:
        return "No applications tracked yet."

    rows = rows[-limit:]

    text = "Application Tracker Status:\n\n"

    for row in rows:
        text += (
            f"ID: {row['application_id']}\n"
            f"Opportunity: {row['opportunity_title']}\n"
            f"Recipient: {row['recipient_email']}\n"
            f"Email: {row['email_status']} at {row['sent_at']}\n"
            f"Reply: {row['reply_status']}\n"
            f"Reply From: {row['reply_from'] or '-'}\n"
            f"Last Checked: {row['last_checked_at'] or '-'}\n\n"
        )

    return text.strip()

