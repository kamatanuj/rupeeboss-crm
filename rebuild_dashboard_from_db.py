#!/usr/bin/env python3
"""
Rebuild leads.csv and public/dashboard_data.json from conversations.db
after name extraction update.
"""
import sqlite3
import json
import csv
from datetime import datetime

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''
    SELECT conversation_id, date, call_summary_title, call_summary,
           client_name, client_phone, client_email, transcript, duration_secs
    FROM conversations
    ORDER BY date DESC, start_time DESC
''')

leads = []
seen_phones = set()
idx = 0

for row in c.fetchall():
    conv_id, date, title, summary, name, phone, email, transcript, duration = row
    idx += 1

    if phone:
        if phone in seen_phones:
            continue
        seen_phones.add(phone)

    has_name = name and name.lower() not in ['', 'unknown']
    has_phone = bool(phone)
    has_transcript = bool(transcript and len(transcript) > 100)

    if has_name and has_phone and has_transcript:
        category = "HOT"
    elif has_phone or (has_name and has_transcript):
        category = "WARM"
    else:
        category = "COLD"

    leads.append({
        "id": f"rb_{idx:04d}",
        "name": name or "Unknown",
        "phone": phone or "",
        "email": email or "",
        "title": title or "RupeeBoss Loan Inquiry",
        "summary": summary or title or f"Lead from {date}",
        "transcript": transcript[:2000] if transcript else "[No transcript available]",
        "date": date,
        "category": category,
        "conversation_id": conv_id,
        "duration": duration or 0,
        "message_count": transcript.count('\n') if transcript else 0
    })

conn.close()

# Write leads.csv
with open(f'{BASE_DIR}/leads.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Email', 'Phone', 'Date', 'Summary'])
    for lead in leads:
        writer.writerow([lead['name'], lead['email'], lead['phone'], lead['date'], lead['summary']])

# Write dashboard_data.json
dashboard = {
    "lastUpdated": datetime.now().isoformat(),
    "metadata": {
        "totalLeads": len(leads),
        "lastUpdated": datetime.now().isoformat(),
        "source": "Improved Name Extraction",
        "agentId": "gKNyAo0UhrdRiQ7FAWVZ"
    },
    "leads": leads
}

with open(f'{BASE_DIR}/public/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

hot = sum(1 for l in leads if l['category'] == 'HOT')
warm = sum(1 for l in leads if l['category'] == 'WARM')
cold = sum(1 for l in leads if l['category'] == 'COLD')
print(f"Rebuilt: {len(leads)} leads ({hot} HOT, {warm} WARM, {cold} COLD)")

print("\nSample leads:")
for lead in leads[:5]:
    print(f"  {lead['date']} | {lead['phone'] or 'N/A':<12} | {lead['name']:<25} | {lead['title'][:45]}")
