#!/usr/bin/env python3
"""Send RupeeBoss KB files via email to kamatanuj@gmail.com"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
USERNAME = "kamatanuj@gmail.com"
PASSWORD = "vtkt dkdz dbbv kalo".replace(" ", "")  # Remove spaces

TO_EMAIL = "kamatanuj@gmail.com"
FROM_EMAIL = "kamatanuj@gmail.com"

KB_DIR = "/root/.openclaw/workspace/rupeeboss/knowledge_base"
FILES = [
    ("01_customer_faq.txt", "RupeeBoss Customer FAQ - Real Q&A from 2073 conversations"),
    ("02_loan_types_guide.txt", "RupeeBoss Loan Products Guide"),
    ("03_agent_best_practices.txt", "RupeeBoss Agent Best Practices"),
    ("04_repeat_customers.txt", "RupeeBoss Repeat Customer History")
]

print("Sending email with KB files...")
print(f"From: {FROM_EMAIL}")
print(f"To: {TO_EMAIL}")

# Create message
msg = MIMEMultipart()
msg['From'] = FROM_EMAIL
msg['To'] = TO_EMAIL
msg['Subject'] = "RupeeBoss Knowledge Base Files for ElevenLabs Upload"

body = """Hi A.K.,

Here are the 4 knowledge base documents for your ElevenLabs ConvAI agent (gKNyAo0UhrdRiQ7FAWVZ):

1. 01_customer_faq.txt (51 KB)
   - Real customer Q&A from 2,073 conversations

2. 02_loan_types_guide.txt (6 KB)
   - Home, Business, Personal, Startup, Machinery loan details

3. 03_agent_best_practices.txt (38 KB)
   - Successful conversation patterns + agent guidelines

4. 04_repeat_customers.txt (5 KB)
   - Repeat customer call history

Upload these to ElevenLabs Dashboard:
https://elevenlabs.io/app/conversational-ai

Select agent "Support agent" (ID: gKNyAo0UhrdRiQ7FAWVZ)
→ Knowledge Base tab → Upload Documents

Best,
Hermes
"""

msg.attach(MIMEText(body, 'plain'))

# Attach files
for filename, description in FILES:
    filepath = os.path.join(KB_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)
        print(f"  Attached: {filename} ({os.path.getsize(filepath):,} bytes)")
    else:
        print(f"  MISSING: {filepath}")

# Send
print("\nConnecting to SMTP...")
try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    print("Logging in...")
    server.login(USERNAME, PASSWORD)
    print("Sending...")
    server.send_message(msg)
    server.quit()
    print("\n✅ Email sent successfully to kamatanuj@gmail.com")
except Exception as e:
    print(f"\n❌ Error: {e}")
