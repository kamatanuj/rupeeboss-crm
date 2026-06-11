#!/usr/bin/env python3
"""Recover leads from June 3-10 gap conversations"""
import json, urllib.request, os, csv, re
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
API_KEY=os.getenv('ELEVENLABS_API_KEY')

gap_ids = json.load(open('recoverable_conversations.json'))['june_gap_ids']

recovered = []
for i, cid in enumerate(gap_ids):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{cid}"
    req = urllib.request.Request(url, headers={"xi-api-key": API_KEY})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        transcript = data.get('transcript', [])
        if not transcript:
            continue

        user_text = " ".join([msg.get('message', '') or '' for msg in transcript if msg.get('role') == 'user'])
        phones = list(set(re.findall(r'\b([6-9]\d{9})\b', user_text)))

        names = []
        patterns = [
            r'mera naam hai ([a-z\s]+?)(?:[,\.\s]|$)',
            r'naam hai ([a-z\s]+?)(?:[,\.\s]|$)',
            r'my name is ([a-z\s]+?)(?:[,\.\s]|$)',
            r'this is ([a-z\s]+?)(?:[,\.\s]|$)',
            r'i am ([a-z\s]+?)(?:[,\.\s]|$)',
        ]
        for pat in patterns:
            found = re.findall(pat, user_text, re.IGNORECASE)
            for f in found:
                name = f.strip().split()[0].title()
                if 2 <= len(name) <= 15:
                    names.append(name)

        ts = data.get('start_time_unix_secs', 0)
        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else 'unknown'

        for phone in phones:
            recovered.append({
                'date': date,
                'phone': phone,
                'name': names[0] if names else '',
                'conversation_id': cid,
                'duration': data.get('call_duration_secs', 0),
                'title': data.get('call_summary_title', 'N/A')
            })

        print(f"  [{i+1}/{len(gap_ids)}] {date} | {data.get('call_summary_title','')} | Phones: {len(phones)}")
    except Exception as e:
        print(f"  [{i+1}/{len(gap_ids)}] ERROR: {e}")

print(f"\nRecovered {len(recovered)} leads from June 3-10:")
for r in recovered:
    print(f"  {r['date']} | {r['name'] or 'Unknown'} | {r['phone']} | {r['title']} ({r['duration']}s)")

# Save recovered leads
with open('recovered_june_leads.json', 'w') as f:
    json.dump(recovered, f, indent=2)

# Append to leads.csv
with open('leads.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for r in recovered:
        writer.writerow([r['name'], '', r['phone'], ''])

print(f"\nAppended {len(recovered)} leads to leads.csv")
