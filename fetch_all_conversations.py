#!/usr/bin/env python3
"""
Fetch ALL Rupeeboss conversations from ElevenLabs API and update dashboard.
Processes conversations in batches for efficiency.
"""
import json
import urllib.request
import time
import os
import re
from datetime import datetime

API_KEY = "3a708d1216251b9801380110a5ec11fb82f806545f70978ad63aa3283fbf23d4"
AGENT_ID = "gKNyAo0UhrdRiQ7FAWVZ"
BASE_DIR = "/root/.openclaw/workspace/rupeeboss"

def fetch_page(cursor=None):
    url = f"https://api.elevenlabs.io/v1/convai/conversations?agent_id={AGENT_ID}&page_size=100"
    if cursor:
        url += f"&cursor={cursor}"
    req = urllib.request.Request(url, headers={"xi-api-key": API_KEY})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fetch_detail(conv_id):
    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
        req = urllib.request.Request(url, headers={"xi-api-key": API_KEY})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    Error fetching detail: {e}")
        return None

def extract_lead(detail, conv_id):
    if not detail:
        return None
    
    metadata = detail.get('metadata') or {}
    start_time = metadata.get('start_time_unix_secs', 0)
    if not start_time:
        return None
    
    date_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
    
    analysis = detail.get('analysis') or {}
    data_collection = analysis.get('data_collection_results') or {}
    
    # Phone
    phone = ''
    tel_field = data_collection.get('Telephone number', {})
    if tel_field and tel_field.get('value'):
        digits = re.sub(r'\D', '', str(tel_field['value']))
        if len(digits) >= 10:
            phone = digits[-10:]
    
    # Also try to extract phone from transcript
    if not phone:
        transcript = detail.get('transcript', [])
        user_text = " ".join([msg.get('message', '') for msg in transcript if msg.get('role') == 'user'])
        phones = re.findall(r'\b([6-9]\d{9})\b', user_text)
        if phones:
            phone = phones[0]
    
    # Name
    name = ''
    name_field = data_collection.get('Name', {})
    if name_field and name_field.get('value'):
        name = str(name_field['value']).strip().title()
    
    # Also try to extract name from transcript patterns
    if not name or len(name) < 2:
        transcript = detail.get('transcript', [])
        user_text = " ".join([msg.get('message', '') for msg in transcript if msg.get('role') == 'user'])
        
        patterns = [
            r'मेरा नाम ([^\s,.]+)',
            r'नाम ([^\s,.]+)',
            r'My name is ([A-Za-z\s]+?)(?:[,\.\s]|$)',
            r'I am ([A-Za-z\s]+?)(?:[,\.\s]|$)',
            r'This is ([A-Za-z\s]+?)(?:[,\.\s]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 1 and name.lower() not in ['unknown', 'interested', 'my', 'sir', 'maam', 'yes', 'salaried', 'here']:
                    break
    
    # Transcript
    transcript_lines = []
    for msg in detail.get('transcript', []):
        role = msg.get('role', 'unknown').upper()
        text = msg.get('message', '')
        if text:
            transcript_lines.append(f"[{role}] {text}")
    transcript = '\n'.join(transcript_lines)
    
    # Summary from analysis
    summary = analysis.get('transcript_summary', '') or analysis.get('call_summary', '')
    
    # Title from first user message or call_summary_title
    title = detail.get('call_summary_title', 'Business Loan Inquiry')
    if not title or title in ['No User Response', 'Unclear User Input']:
        for line in transcript_lines:
            if '[USER]' in line:
                user_msg = line.replace('[USER]', '').strip()
                if len(user_msg) > 5:
                    title = user_msg[:80]
                    break
    
    # Category
    has_name = name and len(name) > 1 and name.lower() not in ['unknown', 'interested', 'my', 'sir', 'maam', 'yes', 'salaried', 'here']
    has_phone = len(phone) == 10
    category = 'HOT' if (has_name and has_phone) else 'COLD'
    
    # Only include if we have a phone or meaningful transcript
    if not phone and len(transcript) < 50:
        return None
    
    return {
        'id': f"rb_{conv_id[-8:]}",
        'name': name or 'Unknown',
        'phone': phone,
        'email': '',
        'date': date_str,
        'title': title,
        'summary': summary or f"Rupeeboss loan inquiry. Phone: {phone}",
        'transcript': transcript,
        'category': category,
        'language': detail.get('main_language', 'hi'),
        'duration': metadata.get('call_duration_secs', 0)
    }

def main():
    print("🚀 Fetching ALL Rupeeboss conversations...")
    print("=" * 60)
    
    # Step 1: Fetch all conversation IDs
    cursor = None
    all_conversations = []
    page = 0
    
    while True:
        data = fetch_page(cursor)
        all_conversations.extend(data['conversations'])
        page += 1
        print(f"📄 Page {page}: {len(data['conversations'])} conversations. Total: {len(all_conversations)}")
        
        if not data.get('has_more'):
            break
        cursor = data.get('next_cursor')
        time.sleep(0.5)
    
    print(f"\n✅ Total conversations fetched: {len(all_conversations)}")
    
    # Step 2: Process each conversation to extract leads
    all_leads = []
    seen_phones = set()
    
    for i, conv in enumerate(all_conversations):
        conv_id = conv['conversation_id']
        print(f"\n🔍 [{i+1}/{len(all_conversations)}] Processing {conv_id[:20]}...")
        
        detail = fetch_detail(conv_id)
        if not detail:
            continue
        
        lead = extract_lead(detail, conv_id)
        if lead:
            # Avoid duplicates by phone
            if lead['phone'] and lead['phone'] in seen_phones:
                print(f"   ⏭ Skipping duplicate phone: {lead['phone']}")
                continue
            
            if lead['phone']:
                seen_phones.add(lead['phone'])
            
            all_leads.append(lead)
            print(f"   ✅ Lead: {lead['name'][:20]:20} | {lead['phone'][:12]:12} | {lead['date']}")
        else:
            print(f"   ⚠️ No lead extracted")
        
        time.sleep(0.3)  # Rate limiting
    
    print(f"\n{'='*60}")
    print(f"📊 Total leads extracted: {len(all_leads)}")
    
    # Step 3: Sort by date (newest first)
    all_leads.sort(key=lambda x: x['date'], reverse=True)
    
    # Step 4: Save to dashboard_data.json
    dashboard = {
        "lastUpdated": datetime.now().isoformat(),
        "metadata": {
            "totalLeads": len(all_leads),
            "lastUpdated": datetime.now().isoformat(),
            "agentId": AGENT_ID,
            "source": "ElevenLabs API"
        },
        "leads": all_leads
    }
    
    dashboard_path = os.path.join(BASE_DIR, "public", "dashboard_data.json")
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to {dashboard_path}")
    print(f"📈 Total leads: {len(all_leads)}")
    print(f"🔥 HOT leads: {sum(1 for l in all_leads if l['category'] == 'HOT')}")
    print(f"❄️ COLD leads: {sum(1 for l in all_leads if l['category'] == 'COLD')}")
    
    # Also save as CSV
    csv_path = os.path.join(BASE_DIR, "crm_leads.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Phone', 'Email', 'Date', 'Category', 'Title'])
        for lead in all_leads:
            writer.writerow([lead['name'], lead['phone'], lead['email'], lead['date'], lead['category'], lead['title']])
    
    print(f"💾 Also saved to {csv_path}")

if __name__ == "__main__":
    import csv
    main()
