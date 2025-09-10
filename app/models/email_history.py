from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.db import Base  # your existing Base

class EmailHistory(Base):
    __tablename__ = "email_history"

    id = Column(Integer, primary_key=True, index=True)
    from_email = Column(String, nullable=False)   # ✅ sender email
    recipient = Column(String, index=True, nullable=False)
    subject = Column(String, nullable=True)
    sent_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return (
            f"<EmailHistory(from={self.from_email}, "
            f"recipient={self.recipient}, sent_at={self.sent_at})>"
        )
