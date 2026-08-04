"""
Backend for the Kids Learning Platform survey.

Receives the submitted survey as JSON, formats it, and emails it via the
Resend API (https://resend.com) over plain HTTPS. We use an HTTP-based email
API instead of raw SMTP because many free hosting tiers (Render, Railway,
etc.) block outbound SMTP ports entirely - HTTPS is never blocked.

Run locally:
    pip install -r requirements.txt
    cp .env.example .env      # then fill in your Resend API key
    uvicorn app:app --reload --port 5000
"""

import os
from datetime import datetime
from typing import List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Little Learners Survey API")

# allow the React dev server / deployed frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Resend configuration (set these in a .env file, see .env.example) ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# Resend's shared test sender works out of the box with no domain setup.
# Swap it for something like "surveys@yourdomain.com" once you verify a
# domain in the Resend dashboard.
RESEND_FROM = os.getenv("RESEND_FROM", "onboarding@resend.dev")
MAIL_TO = os.getenv("MAIL_TO")

# Fields we expect from the frontend, and the friendly labels used in the email
FIELD_LABELS = {
    "parentName": "Parent / Guardian name",
    "parentEmail": "Parent / Guardian email",
    "childName": "Child's name",
    "childAge": "Child's age",
    "grade": "Grade / class",
    "subjects": "Subjects the child enjoys",
    "learningStyle": "Favorite way to learn",
    "screenTime": "Average daily learning time",
    "rating": "How much the child enjoys the platform (1-5)",
    "recommend": "Would recommend to other parents",
    "feedback": "Comments / suggestions",
}


class SurveyPayload(BaseModel):
    parentName: str
    parentEmail: str
    childName: str
    childAge: Optional[str] = ""
    grade: Optional[str] = ""
    subjects: Optional[List[str]] = []
    learningStyle: Optional[str] = ""
    screenTime: Optional[str] = ""
    rating: Optional[int] = 0
    recommend: Optional[str] = ""
    feedback: Optional[str] = ""


def build_email_html(data: dict) -> str:
    rows = []
    for key, label in FIELD_LABELS.items():
        value = data.get(key, "")
        if isinstance(value, list):
            value = ", ".join(value) if value else "-"
        if value in ("", None, 0):
            value = "-"
        rows.append(
            f"<tr><td style='padding:6px 12px;font-weight:600;color:#1F2A44;"
            f"border-bottom:1px solid #eee;'>{label}</td>"
            f"<td style='padding:6px 12px;color:#333;border-bottom:1px solid #eee;'>"
            f"{value}</td></tr>"
        )
    submitted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">
      <h2 style="color:#1F2A44;">New survey response</h2>
      <p style="color:#666;font-size:13px;">Submitted: {submitted}</p>
      <table style="width:100%;border-collapse:collapse;">{''.join(rows)}</table>
    </div>
    """


def send_email(subject: str, html: str) -> None:
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set. Add it to backend/.env")
    if not MAIL_TO:
        raise RuntimeError("MAIL_TO is not set. Add it to backend/.env")

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM,
            "to": [MAIL_TO],
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Resend API error ({response.status_code}): {response.text}")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/submit-survey")
def submit_survey(payload: SurveyPayload):
    data = payload.model_dump()

    html = build_email_html(data)
    subject = f"New Survey Response - {data.get('childName', 'Unknown Child')}"

    try:
        send_email(subject, html)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Could not send email: {exc}"},
        )

    return {"success": True, "message": "Survey submitted and emailed successfully!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
