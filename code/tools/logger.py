import csv
import os
from datetime import datetime


LOG_FILE = "data/applications.csv"


def save_application_log(
    user_goal: str,
    intake_result: dict,
    selected_opportunity: dict,
    writer_result: dict
) -> dict:
    os.makedirs("data", exist_ok=True)

    headers = [
        "date",
        "user_goal",
        "opportunity_type",
        "field",
        "location",
        "opportunity_title",
        "organization",
        "match_score",
        "recommendation",
        "status",
        "email_drafted"
    ]

    row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_goal": user_goal,
        "opportunity_type": intake_result.get("opportunity_type"),
        "field": intake_result.get("field"),
        "location": intake_result.get("location"),
        "opportunity_title": selected_opportunity.get("title"),
        "organization": selected_opportunity.get("organization"),
        "match_score": selected_opportunity.get("match_score"),
        "recommendation": selected_opportunity.get("recommendation"),
        "status": "Drafted",
        "email_drafted": "Yes"
    }

    file_exists = os.path.isfile(LOG_FILE)
    file_empty = not file_exists or os.path.getsize(LOG_FILE) == 0

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)

        if file_empty:
            writer.writeheader()

        writer.writerow(row)

    return {
        "status": "saved",
        "file": LOG_FILE,
        "logged_opportunity": selected_opportunity.get("title")
    }
