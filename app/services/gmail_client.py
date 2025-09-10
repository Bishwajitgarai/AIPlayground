import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.core.config import settings



class GmailSender:
    def __init__(self, user_id: str, app_password: str):
        self.user_id = user_id
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_mail(self, to_email: str, subject: str, body: str, attachments: list[str] = None):
        """
        Send an email using Gmail with optional file attachments.

        :param to_email: Receiver's email address
        :param subject: Email subject
        :param body: Email body text
        :param attachments: List of file paths to attach
        """
        # Create the email message
        message = MIMEMultipart()
        message["From"] = self.user_id
        message["To"] = to_email
        message["Subject"] = subject

        # Attach body text
        message.attach(MIMEText(body, "plain"))

        # Attach multiple files if provided
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_attachment = MIMEApplication(f.read(), _subtype="octet-stream")
                        file_attachment.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=os.path.basename(file_path)
                        )
                        message.attach(file_attachment)

        # Connect and send
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()  # Secure connection
            server.login(self.user_id, self.app_password)
            server.sendmail(self.user_id, to_email, message.as_string())
            print("✅ Email sent successfully!")


gmail_sender = GmailSender(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
