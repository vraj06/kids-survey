"""
Backend for the Kids Learning Platform survey.

Receives the submitted survey as JSON, formats it, and emails it via SMTP.

Run locally:
    pip install -r requirements.txt
    cp .env.example .env      # then fill in your SMTP details
    uvicorn app:app --reload --port 5000
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Little Learners Survey API")

# allow the React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SMTP configuration (set these in a .env file, see .env.example) ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")          # the mailbox that sends the email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # app password, not your login password
MAIL_TO = os.getenv("MAIL_TO", SMTP_USER)   # who receives the survey results

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


def build_email_body(data: dict) -> str:
    lines = [
        "New survey response from the Kids Learning Platform",
        "=" * 52,
        f"Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for key, label in FIELD_LABELS.items():
        value = data.get(key, "")
        if isinstance(value, list):
            value = ", ".join(value) if value else "-"
        if value in ("", None, 0):
            value = "-"
        lines.append(f"{label}: {value}")
    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USER / SMTP_PASSWORD are not set. Add them to backend/.env"
        )

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, MAIL_TO, msg.as_string())


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/submit-survey")
def submit_survey(payload: SurveyPayload):
    data = payload.model_dump()

    body = build_email_body(data)
    subject = f"New Survey Response - {data.get('childName', 'Unknown Child')}"

    try:
        send_email(subject, body)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Could not send email: {exc}"},
        )

    return {"success": True, "message": "Survey submitted and emailed successfully!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
