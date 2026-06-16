from fastapi import FastAPI
from pydantic import BaseModel

from workflow import run_applypilot_workflow

app = FastAPI(title="ApplyPilot API")


class ApplyRequest(BaseModel):
    user_goal: str
    cv_text: str


@app.get("/")
def home():
    return {
        "message": "ApplyPilot is running successfully"
    }


@app.post("/applypilot")
def applypilot(request: ApplyRequest):
    result = run_applypilot_workflow(
        user_goal=request.user_goal,
        cv_text=request.cv_text
    )

    result["next_step"] = "Telegram interface added successfully."
    return result
