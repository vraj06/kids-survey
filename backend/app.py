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
    """Generates a colorful, kid-learning-themed HTML email for survey submissions."""

    rows = [
        ("👤 Parent / Guardian name", data.get("parentName", "-")),
        ("📧 Parent / Guardian email", data.get("parentEmail", "-")),
        ("🧒 Child's name", data.get("childName", "-")),
        ("🎂 Child's age", data.get("childAge", "-")),
        ("📚 Grade / class", data.get("grade", "-")),
        ("⭐ Subjects the child enjoys", data.get("subjects", "-")),
        ("🎧 Favorite way to learn", data.get("learningStyle", "-")),
        ("⏱️ Average daily learning time", data.get("screenTime", "-")),
        ("😊 Enjoyment rating (1-5)", data.get("rating", "-")),
        ("👍 Would recommend to other parents", data.get("recommend", "-")),
        ("💬 Comments / suggestions", data.get("feedback", "-")),
    ]

    rows_html = "\n".join(
        f"""
        <tr>
          <td style="padding:14px 20px; font-weight:600; color:#4B3F72; font-size:14px; border-bottom:1px solid #F0E9FF; width:55%;">
            {label}
          </td>
          <td style="padding:14px 20px; color:#333333; font-size:14px; border-bottom:1px solid #F0E9FF;">
            {value}
          </td>
        </tr>
        """
        for label, value in rows
    )
data["submitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    <html>
    <body style="margin:0; padding:0; background-color:#FDF6EC; font-family:'Segoe UI', Arial, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#FDF6EC; padding:32px 0;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:20px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,0.06);">

              <!-- Header -->
              <tr>
                <td style="background:linear-gradient(135deg,#FF9A6C,#FFD36C); padding:32px 24px; text-align:center;">
                  <div style="font-size:36px; margin-bottom:8px;">🌈✏️📖</div>
                  <div style="font-size:22px; font-weight:800; color:#ffffff; letter-spacing:0.3px;">
                    New Survey Response!
                  </div>
                  <div style="font-size:13px; color:#FFF3E0; margin-top:4px;">
                    A parent just shared feedback about their little learner
                  </div>
                </td>
              </tr>

              <!-- Timestamp badge -->
              <tr>
                <td style="padding:20px 24px 0 24px;">
                  <span style="display:inline-block; background:#EAF7EE; color:#2E7D4F; font-size:12px; font-weight:600; padding:6px 14px; border-radius:999px;">
                    🕒 Submitted: {data.get("submitted_at", "-")}
                  </span>
                </td>
              </tr>

              <!-- Table -->
              <tr>
                <td style="padding:16px 24px 24px 24px;">
                  <table width="100%" cellpadding="0" cellspacing="0" style="background:#FFFDF9; border-radius:14px; overflow:hidden; border:1px solid #F0E9FF;">
                    {rows_html}
                  </table>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background:#FFF6E9; padding:20px 24px; text-align:center;">
                  <div style="font-size:13px; color:#A08B6F;">
                    Sent automatically from <strong style="color:#FF9A6C;">LittleLearners</strong> 🧸
                  </div>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
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
