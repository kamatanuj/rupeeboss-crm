#!/usr/bin/env python3
"""FULL REBUILD: Fetch all conversations, extract leads with real dates"""
import json, urllib.request, os, csv, re, time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
KEY = os.getenv('ELEVENLABS_API_KEY')
AGENT_ID = os.getenv('ELEVENLABS_AGENT_ID')

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
print("="*60)
print("FULL REBUILD: RupeeBoss CRM")
print("Fetching ALL conversations with correct dates")
print("="*60)

# Step 1: Fetch all conversation IDs (paginated)
print("\n[1/4] Fetching conversation list...")
all_conversations = []
next_cursor = None
page = 0

while True:
    url = f"https://api.elevenlabs.io/v1/convai/conversations?page_size=100"
    if next_cursor:
        url += f"&cursor={next_cursor}"
    
    req = urllib.request.Request(url, headers={"xi-api-key": KEY})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    
    convs = data.get('conversations', [])
    all_conversations.extend(convs)
    page += 1
    
    if page % 5 == 0:
        print(f"  Page {page}: {len(all_conversations)} conversations fetched")
    
    if not data.get('has_more', False):
        break
    next_cursor = data.get('next_cursor')
    
    # Rate limiting - be gentle
    time.sleep(0.2)
    
    if page >= 50:  # Hard limit
        break

print(f"\nTotal conversations: {len(all_conversations)}")

# Step 2: Fetch each conversation and extract leads
print("\n[2/4] Processing conversations and extracting leads...")
all_leads = {}
errors = 0

for i, conv in enumerate(all_conversations):
    cid = conv.get('conversation_id', '')
    
    if (i + 1) % 100 == 0:
        print(f"  Processed {i+1}/{len(all_conversations)}... (leads: {len(all_leads)}, errors: {errors})")
    
    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{cid}"
        req = urllib.request.Request(url, headers={"xi-api-key": KEY})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        
        # Extract date from conversation
        ts = data.get('start_time_unix_secs', 0)
        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else 'unknown'
        
        # Extract user messages
        transcript = data.get('transcript', [])
        if not transcript:
            continue
        
        user_text = " ".join([
            m.get('message', '') or '' 
            for m in transcript 
            if m.get('role') == 'user'
        ])
        
        # Extract phone numbers
        phones = list(set(re.findall(r'\b([6-9]\d{9})\b', user_text)))
        
        # Extract names
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
        
        # Store leads
        for phone in phones:
            if phone not in all_leads:
                all_leads[phone] = {
                    'phone': phone,
                    'name': names[0] if names else '',
                    'date': date,
                    'email': '',
                    'conversation_id': cid
                }
            elif names and not all_leads[phone]['name']:
                all_leads[phone]['name'] = names[0]
        
        # Rate limiting
        if (i + 1) % 50 == 0:
            time.sleep(0.5)
            
    except Exception as e:
        errors += 1
        continue

print(f"\nExtraction complete: {len(all_leads)} unique leads")
print(f"Errors: {errors}")

# Step 3: Write fresh leads.csv
print("\n[3/4] Writing fresh leads.csv...")
with open(f'{BASE_DIR}/leads.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Email', 'Phone', 'Date'])
    for phone, lead in sorted(all_leads.items(), key=lambda x: x[1]['date']):
        writer.writerow([lead['name'], lead['email'], lead['phone'], lead['date']])

print(f"Written {len(all_leads)} rows to leads.csv")

# Step 4: Rebuild dashboard_data.json with CORRECT dates
print("\n[4/4] Rebuilding dashboard_data.json with correct dates...")

leads_list = []
for i, (phone, lead) in enumerate(sorted(all_leads.items(), key=lambda x: x[1]['date'])):
    leads_list.append({
        "id": f"rb_{i+1:04d}",
        "name": lead['name'] or "Unknown",
        "phone": lead['phone'],
        "email": lead['email'],
        "title": f"RupeeBoss Loan Inquiry - {lead['phone']}",
        "summary": f"Lead from conversation on {lead['date']}. Phone: {lead['phone']}",
        "transcript": "[Extracted from conversation metadata]",
        "date": lead['date'],
        "category": "HOT" if lead['name'] else "COLD",
        "conversation_id": lead['conversation_id']
    })

# Build dashboard
dashboard = {
    "lastUpdated": datetime.now().isoformat(),
    "metadata": {
        "totalLeads": len(leads_list),
        "lastUpdated": datetime.now().isoformat(),
        "source": "ElevenLabs ConvAI - Full Rebuild"
    },
    "leads": leads_list
}

with open(f'{BASE_DIR}/public/dashboard_data.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"Dashboard rebuilt: {len(leads_list)} leads")

# Summary by date
date_counts = {}
for lead in leads_list:
    d = lead['date']
    date_counts[d] = date_counts.get(d, 0) + 1

print("\n📊 Recent dates breakdown:")
for date in sorted(date_counts.keys())[-10:]:
    print(f"  {date}: {date_counts[date]} leads")

print("\n" + "="*60)
print("REBUILD COMPLETE!")
print("Run: cd /root/.openclaw/workspace/rupeeboss && bash auto-update.sh")
print("="*60)
