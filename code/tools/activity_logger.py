import os
import json
import re
from datetime import datetime, date

TELEGRAM_LOG_FILE = "data/logs/telegram_activity.jsonl"
ACTION_LOG_FILE = "data/logs/agent_actions.jsonl"
USAGE_LOG_FILE = "usage_log/USAGE_LOG.md"
USAGE_DAY_STATE_FILE = "usage_log/.usage_day_state.json"


SENSITIVE_PATTERNS = [
    r"EMAIL_APP_PASSWORD\s*=\s*[^\s]+",
    r"TELEGRAM_BOT_TOKEN\s*=\s*[^\s]+",
    r"TAVILY_API_KEY\s*=\s*[^\s]+",
    r"GEMINI_API_KEY\s*=\s*[^\s]+",
    r"sk-[A-Za-z0-9_\-]+",
]


def ensure_dirs():
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("usage_log", exist_ok=True)


def redact_sensitive(text: str) -> str:
    if not text:
        return ""

    text = str(text)

    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(pattern, "[REDACTED_SECRET]", text, flags=re.IGNORECASE)

    # Redact long app-password-like strings
    text = re.sub(r"\b[a-zA-Z0-9]{16,}\b", "[REDACTED_LONG_TOKEN]", text)

    return text


def clean_preview(text: str, limit: int = 250) -> str:
    if not text:
        return ""

    text = redact_sensitive(text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = " ".join(text.split())

    if len(text) > limit:
        return text[:limit] + "..."

    return text


def write_jsonl(file_path: str, payload: dict):
    ensure_dirs()

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def ensure_usage_log():
    ensure_dirs()

    if not os.path.exists(USAGE_LOG_FILE) or os.path.getsize(USAGE_LOG_FILE) == 0:
        with open(USAGE_LOG_FILE, "w", encoding="utf-8") as file:
            file.write("# ApplyPilot Usage Log\n\n")
            file.write("| Date/Time | Channel | Task | Outcome | Notes |\n")
            file.write("|---|---|---|---|---|\n")


def clean_md_cell(text: str) -> str:
    text = clean_preview(text, limit=180)
    text = text.replace("|", "/")
    return text

def load_usage_day_state() -> dict:
    ensure_dirs()

    if not os.path.exists(USAGE_DAY_STATE_FILE):
        return {
            "current_date": "",
            "day_number": 0
        }

    try:
        with open(USAGE_DAY_STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {
            "current_date": "",
            "day_number": 0
        }


def save_usage_day_state(state: dict):
    ensure_dirs()

    with open(USAGE_DAY_STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)


def add_day_separator_if_needed():
    ensure_usage_log()

    today = date.today().isoformat()
    state = load_usage_day_state()

    if state.get("current_date") == today:
        return

    previous_day_number = int(state.get("day_number", 0))
    new_day_number = previous_day_number + 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    separator_row = (
        f"| {timestamp} "
        f"| --- "
        f"| **DAY {new_day_number} START** "
        f"| --- "
        f"| New usage day started |\n"
    )

    with open(USAGE_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(separator_row)

    save_usage_day_state({
        "current_date": today,
        "day_number": new_day_number
    })

def log_usage_markdown(channel: str, task: str, outcome: str, notes: str = ""):
    ensure_usage_log()
    add_day_separator_if_needed()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    row = (
        f"| {timestamp} "
        f"| {clean_md_cell(channel)} "
        f"| {clean_md_cell(task)} "
        f"| {clean_md_cell(outcome)} "
        f"| {clean_md_cell(notes)} |\n"
    )

    with open(USAGE_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(row)


def log_telegram_event(
    user_id: str = "",
    username: str = "",
    chat_id: str = "",
    message_type: str = "",
    command: str = "",
    text: str = "",
    file_name: str = "",
):
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": "telegram",
        "user_id": str(user_id),
        "username": username or "",
        "chat_id": str(chat_id),
        "message_type": message_type,
        "command": command,
        "text_preview": clean_preview(text),
        "file_name": file_name or ""
    }

    write_jsonl(TELEGRAM_LOG_FILE, payload)

    # Only high-level Markdown log, not every normal text message
    if command:
        log_usage_markdown(
            channel="Telegram",
            task=command,
            outcome="RECEIVED",
            notes=f"User command received. Type: {message_type}"
        )


def log_agent_action(
    agent: str,
    action: str,
    outcome: str,
    notes: str = "",
    metadata: dict = None,
    write_usage: bool = True
):
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "agent": agent,
        "action": action,
        "outcome": outcome,
        "notes": clean_preview(notes, limit=500),
        "metadata": metadata or {}
    }

    write_jsonl(ACTION_LOG_FILE, payload)

    if write_usage:
        log_usage_markdown(
            channel="ApplyPilot",
            task=f"{agent}: {action}",
            outcome=outcome,
            notes=notes
        )
