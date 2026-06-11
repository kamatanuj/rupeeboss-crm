#!/usr/bin/env python3
"""FAST REBUILD with correct dates from list view"""
import json, urllib.request, os, csv, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
KEY = os.getenv('ELEVENLABS_API_KEY')
BASE_DIR = '/root/.openclaw/workspace/rupeeboss'

print("="*60)
print("FAST REBUILD: Correct Dates")
print("="*60)

# Step 1: Fetch all conversations WITH timestamps
print("\n[1/3] Fetching conversation list with timestamps...")
all_convs = []
next_cursor = None
page = 0

while True:
    url = f"https://api.elevenlabs.io/v1/convai/conversations?page_size=100"
    if next_cursor:
        url += f"&cursor={next_cursor}"
    req = urllib.request.Request(url, headers={"xi-api-key": KEY})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    convs = data.get('conversations', [])
    for c in convs:
        ts = c.get('start_time_unix_secs', 0)
        c['date'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else 'unknown'
    all_convs.extend(convs)
    page += 1
    if page % 5 == 0:
        print(f"  Page {page}: {len(all_convs)} conversations")
    if not data.get('has_more', False) or page >= 50:
        break
    next_cursor = data.get('next_cursor')

print(f"Total: {len(all_convs)} conversations")

# Step 2: Fetch details and extract leads
print("\n[2/3] Extracting leads...")

def fetch_and_extract(conv):
    cid = conv['conversation_id']
    date = conv['date']
    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{cid}"
        req = urllib.request.Request(url, headers={"xi-api-key": KEY})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        
        transcript = data.get('transcript', [])
        if not transcript:
            return []
        
        user_text = " ".join([
            m.get('message', '') or '' 
            for m in transcript 
            if m.get('role') == 'user'
        ])
        
        phones = list(set(re.findall(r'\b([6-9]\d{9})\b', user_text)))
        if not phones:
            return []
        
        # Extract name
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
        
        return [{
            'phone': p,
            'name': names[0] if names else '',
            'date': date,
            'email': '',
            'conversation_id': cid
        } for p in phones]
        
    except Exception:
        return []

all_leads_dict = {}
processed = 0

for batch_start in range(0, len(all_convs), 50):
    batch = all_convs[batch_start:batch_start + 50]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_and_extract, c): c for c in batch}
        for future in as_completed(futures):
            for lead in future.result():
                phone = lead['phone']
                if phone not in all_leads_dict:
                    all_leads_dict[phone] = lead
                elif lead['name'] and not all_leads_dict[phone]['name']:
                    all_leads_dict[phone]['name'] = lead['name']
    
    processed += len(batch)
    if processed % 100 == 0 or processed == len(batch):
        print(f"  Processed {processed}/{len(all_convs)}... leads: {len(all_leads_dict)}")

print(f"\nTotal unique leads: {len(all_leads_dict)}")

# Step 3: Write fresh CSV (LATEST FIRST)
print("\n[3/3] Writing files...")

with open(f'{BASE_DIR}/leads.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Email', 'Phone', 'Date'])
    for phone, lead in sorted(all_leads_dict.items(), key=lambda x: x[1]['date'], reverse=True):
        writer.writerow([lead['name'], lead['email'], lead['phone'], lead['date']])

print(f"Written leads.csv: {len(all_leads_dict)} rows")

leads_list = []
for i, (phone, lead) in enumerate(sorted(all_leads_dict.items(), key=lambda x: x[1]['date'], reverse=True)):
    leads_list.append({
        "id": f"rb_{i+1:04d}",
        "name": lead['name'] or "Unknown",
        "phone": lead['phone'],
        "email": lead['email'],
        "title": f"RupeeBoss Loan Inquiry - {lead['phone']}",
        "summary": f"Lead from {lead['date']}. Phone: {lead['phone']}",
        "transcript": "[Extracted]",
        "date": lead['date'],
        "category": "HOT" if lead['name'] else "COLD",
        "conversation_id": lead['conversation_id']
    })

dashboard = {
    "lastUpdated": datetime.now().isoformat(),
    "metadata": {
        "totalLeads": len(leads_list),
        "lastUpdated": datetime.now().isoformat(),
        "source": "Correct Date Rebuild"
    },
    "leads": leads_list
}

with open(f'{BASE_DIR}/public/dashboard_data.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"Written dashboard_data.json")

# Summary
date_counts = {}
for lead in leads_list:
    d = lead['date']
    date_counts[d] = date_counts.get(d, 0) + 1

print("\nDate breakdown:")
for date in sorted(date_counts.keys())[-15:]:
    print(f"  {date}: {date_counts[date]} leads")

print("\nREBUILD COMPLETE!")
