from typing import List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

class EmailAttachment:
    def __init__(self, file_path: str, mime_type: str = None, filename: Optional[str] = None):
        self.file_path = file_path
        self.mime_type = mime_type or "application/octet-stream"
        self.filename = filename or os.path.basename(file_path)

class EmailMessageData:
    def __init__(self, subject: str, sender: str, recipient: str, text: str = None, html: str = None, attachments: Optional[List[EmailAttachment]] = None):
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.text = text
        self.html = html
        self.attachments = attachments or []

def build_multipart_message(msg_data: EmailMessageData) -> MIMEMultipart:
    # Outer message (mixed: allows attachments)
    outer = MIMEMultipart("mixed")
    outer["Subject"] = msg_data.subject
    outer["From"] = msg_data.sender
    outer["To"] = msg_data.recipient

    # Alternative section for plain-text + HTML
    alt = MIMEMultipart("alternative")
    if msg_data.text:
        alt.attach(MIMEText(msg_data.text, "plain"))
    if msg_data.html:
        alt.attach(MIMEText(msg_data.html, "html"))
    outer.attach(alt)

    # Attachments
    for att in msg_data.attachments:
        with open(att.file_path, "rb") as f:
            type_and_subtype = att.mime_type.split("/")
            if type_and_subtype[0] == "text":
                content = f.read().decode("utf-8")
                part = MIMEText(content, _subtype=type_and_subtype[-1])
            else:
                part = MIMEApplication(f.read(), _subtype=type_and_subtype[-1])
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=att.filename
            )
            outer.attach(part)
    return outer
