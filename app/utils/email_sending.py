from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models.email_history import EmailHistory

def can_send_email(db: Session, recipient: str) -> bool:
    """Check if email was sent to recipient within last 7 days."""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    record = (
        db.query(EmailHistory)
        .filter(EmailHistory.recipient == recipient)
        .filter(EmailHistory.sent_at >= seven_days_ago)
        .first()
    )
    return record is None
