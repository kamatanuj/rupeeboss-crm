import json, urllib.request, os, csv, re
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
key = os.getenv('ELEVENLABS_API_KEY')

with open('/root/.openclaw/workspace/rupeeboss/recoverable_conversations.json') as f:
    gap_ids = json.load(f)['june_gap_ids']

print(f"Recovering {len(gap_ids)} gap conversations...")
recovered = []

for i, cid in enumerate(gap_ids):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{cid}"
    req = urllib.request.Request(url, headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        transcript = data.get('transcript', [])
        if not transcript:
            print(f"  [{i+1}] {cid[:20]}... | NO TRANSCRIPT")
            continue

        # Print first message structure for debugging
        if i == 0:
            print("DEBUG - First message keys:", list(transcript[0].keys()))
            print("DEBUG - First message:", transcript[0])

        # Extract user text - check different possible structures
        user_text = ""
        for m in transcript:
            role = m.get('role', '')
            if role == 'user':
                # Try different message keys
                msg = m.get('message', '') or m.get('text', '') or m.get('content', '') or str(m)
                user_text += " " + msg

        phones = list(set(re.findall(r'\b([6-9]\d{9})\b', user_text)))

        ts = data.get('start_time_unix_secs', 0)
        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else 'unknown'
        title = data.get('call_summary_title', 'N/A')[:40]

        print(f"  [{i+1}] {date} | {title} | msgs={len(transcript)} | user_chars={len(user_text)} | phones={phones}")

        for phone in phones:
            recovered.append({'date': date, 'phone': phone, 'cid': cid})

    except Exception as e:
        print(f"  [{i+1}] Error: {str(e)[:60]}")

print(f"\nRecovered {len(recovered)} leads:")
for r in recovered:
    print(f"  {r['date']} | {r['phone']}")

# Save
with open('/root/.openclaw/workspace/rupeeboss/recovered_june_leads.json', 'w') as f:
    json.dump(recovered, f, indent=2)

with open('/root/.openclaw/workspace/rupeeboss/leads.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    for r in recovered:
        writer.writerow(['', '', r['phone'], ''])
print(f"\nAppended {len(recovered)} to leads.csv")
