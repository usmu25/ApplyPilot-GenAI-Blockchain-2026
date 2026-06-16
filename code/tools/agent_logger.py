import json
import os
import uuid
from datetime import datetime


LOG_DIR = "data/logs"
MAIN_LOG_FILE = os.path.join(LOG_DIR, "agent_activity.jsonl")
SESSION_DIR = os.path.join(LOG_DIR, "sessions")


def create_session_id(prefix: str = "session") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{short_id}"


def make_json_safe(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def log_agent_event(
    session_id: str,
    agent_name: str,
    action: str,
    status: str = "success",
    input_data=None,
    output_data=None,
    error=None,
    metadata=None
) -> dict:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SESSION_DIR, exist_ok=True)

    event = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "agent_name": agent_name,
        "action": action,
        "status": status,
        "input_data": make_json_safe(input_data),
        "output_data": make_json_safe(output_data),
        "error": str(error) if error else None,
        "metadata": make_json_safe(metadata),
    }

    with open(MAIN_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    session_file = os.path.join(SESSION_DIR, f"{session_id}.jsonl")

    with open(session_file, "a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event
