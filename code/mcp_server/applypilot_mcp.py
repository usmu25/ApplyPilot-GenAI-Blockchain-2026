import csv
from pathlib import Path
from mcp.server.fastmcp import FastMCP


BASE_DIR = Path(__file__).resolve().parents[1]
mcp = FastMCP("applypilot-mcp")


@mcp.tool()
def applypilot_status() -> dict:
    """Return basic ApplyPilot project status."""
    return {
        "project": "ApplyPilot",
        "base_dir": str(BASE_DIR),
        "bot_exists": (BASE_DIR / "bot.py").exists(),
        "workflow_exists": (BASE_DIR / "workflow.py").exists(),
        "usage_log_exists": (BASE_DIR / "usage_log" / "USAGE_LOG.md").exists(),
        "application_tracker_exists": (BASE_DIR / "data" / "application_tracker.csv").exists(),
        "status": "ApplyPilot MCP server is reachable"
    }


@mcp.tool()
def latest_usage_log(lines: int = 20) -> str:
    """Return the latest lines from the ApplyPilot usage log."""
    log_file = BASE_DIR / "usage_log" / "USAGE_LOG.md"

    if not log_file.exists():
        return "usage_log/USAGE_LOG.md not found."

    content = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


@mcp.tool()
def application_tracker_summary(limit: int = 10) -> list[dict]:
    """Return latest application tracker rows without exposing attachments."""
    tracker_file = BASE_DIR / "data" / "application_tracker.csv"

    if not tracker_file.exists():
        return []

    rows = []

    with open(tracker_file, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append({
                "application_id": row.get("application_id", ""),
                "opportunity_title": row.get("opportunity_title", ""),
                "organization": row.get("organization", ""),
                "email_status": row.get("email_status", ""),
                "reply_status": row.get("reply_status", ""),
                "sent_at": row.get("sent_at", ""),
                "reply_received_at": row.get("reply_received_at", "")
            })

    return rows[-limit:]


if __name__ == "__main__":
    mcp.run(transport="stdio")
