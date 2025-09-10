from fastapi import APIRouter, UploadFile, Header, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.services.gmail_client import GmailSender
from app.core.config import settings
import tempfile
import os

gmail_router = APIRouter(tags=["gmail"], prefix="/gmail")

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DEFAULT_CV_PATH = os.path.join(PROJECT_DIR, "files", "BishwajitGarai_9547066044.pdf")

# Default subject/body
DEFAULT_SUBJECT = "Application for Software Developer Position – Bishwajit Garai"
DEFAULT_BODY = """Dear Hiring Manager,

I hope this email finds you well. I am writing to express my interest in the Software Developer position at your organization. With over 3 years of experience in backend development using Python, Django, Flask, and FastAPI, I have built scalable applications, optimized systems, and delivered AI-powered solutions that enhance efficiency and reliability.

Most recently, I led the development of MeetMemo, an AI-powered meeting assistant leveraging FastAPI, Redis, and MySQL for real-time processing, transcription, and analysis. I have also worked extensively with microservices, API integrations, automation, and cloud deployment, ensuring robust and maintainable systems.

I have attached my CV for your review. I would be delighted to discuss how my skills and experience can contribute to your team’s success.

Thank you for your time and consideration.

Best regards,  
Bishwajit Garai  
📞 +91 9547066044  
✉️ bishwajitgarai2520@gmail.com
"""


@gmail_router.post("/send")
async def send_gmail(
    to_emails: List[str] = Form(..., description="List of email addresses"),
    subject: Optional[str] = Form(None, description="Email subject"),
    body: Optional[str] = Form(None, description="Email body"),
    attachments: Optional[List[UploadFile]] = None,
    x_gmail_token: Optional[str] = Header(None, alias="X-Gmail-Token"),
    gmail_user: Optional[str] = Header(None, alias="GMAIL-USER"),
    gmail_app_password: Optional[str] = Header(None, alias="GMAIL-APP-PASSWORD"),
):
    """
    Send an email using Gmail with optional subject, body, and attachments.
    - If X-Gmail-Token header is provided → validate and use default credentials.
    - Otherwise → use GMAIL-USER and GMAIL-APP-PASSWORD headers directly.
    """

    # ✅ Authentication logic
    if x_gmail_token:
        if x_gmail_token != settings.GMAIL_APP_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid Gmail Header token")
        user = settings.GMAIL_USER
        password = settings.GMAIL_APP_PASSWORD
    else:
        if not gmail_user or not gmail_app_password:
            raise HTTPException(
                status_code=401,
                detail="Missing Gmail authentication (provide either X-Gmail-Token or GMAIL-USER + GMAIL-APP-PASSWORD headers)",
            )
        user = gmail_user
        password = gmail_app_password

    try:
        file_paths = []

        # Save uploaded files temporarily
        if attachments:
            for file in attachments:
                temp_path = os.path.join(tempfile.gettempdir(), file.filename)
                with open(temp_path, "wb") as f:
                    f.write(await file.read())
                file_paths.append(temp_path)

        # If no attachments → use default CV
        if not file_paths:
            if not os.path.exists(DEFAULT_CV_PATH):
                raise FileNotFoundError(f"Default CV not found at {DEFAULT_CV_PATH}")
            file_paths.append(DEFAULT_CV_PATH)

        # Use defaults if not provided
        subject = subject or DEFAULT_SUBJECT
        body = body or DEFAULT_BODY

        # Send email to each recipient
        sender = GmailSender(user, password)
        for recipient in to_emails:
            sender.send_mail(
                to_email=recipient,
                subject=subject,
                body=body,
                attachments=file_paths,
            )

        # Cleanup only temp files
        for path in file_paths:
            if path != DEFAULT_CV_PATH and os.path.exists(path):
                os.remove(path)

        return JSONResponse(
            status_code=200,
            content={"status_code": 200, "message": "Email sent successfully"},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "message": "Error while sending email",
                "error": str(e),
            },
        )