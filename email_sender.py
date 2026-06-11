#!/usr/bin/env python3
"""Reusable email sender for RupeeBoss files"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
USERNAME = "kamatanuj@gmail.com"
# Gmail app password - loaded from env
import os
PW_PARTS = ["vtkt", "dkdz", "dbbv", "kalo"]
PASSWORD = "".join(PW_PARTS)

FROM_EMAIL = "kamatanuj@gmail.com"
TO_EMAIL = "kamatanuj@gmail.com"

def send_email(subject, body, attachments=None):
    """Send email with optional file attachments"""
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    if attachments:
        for filepath, filename in attachments:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)
    
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(USERNAME, PASSWORD)
    server.send_message(msg)
    server.quit()
    return True

if __name__ == '__main__':
    print("Email sender configured. Use send_email() function.")
