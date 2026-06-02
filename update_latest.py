#!/usr/bin/env python3
"""
Quick update for Rupeeboss CRM - Fetches latest 200 conversations only
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

def fetch_page(cursor=None, page_size=100):
    url = f"https://api.elevenlabs.io/v1/convai/conversations?agent_id={AGENT_ID}&page_size={page_size}"
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
    print("🚀 Fetching latest Rupeeboss conversations (last 200)...")
    print("=" * 60)
    
    # Load existing dashboard data
    dashboard_path = os.path.join(BASE_DIR, "public", "dashboard_data.json")
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)
        existing_leads = dashboard.get('leads', [])
        existing_phones = {lead.get('phone', '') for lead in existing_leads}
        print(f"📊 Current dashboard has {len(existing_leads)} leads")
    except:
        existing_leads = []
        existing_phones = set()
    
    # Fetch latest 200 conversations (2 pages)
    all_conversations = []
    cursor = None
    for page in range(2):
        data = fetch_page(cursor, 100)
        all_conversations.extend(data['conversations'])
        if not data.get('has_more'):
            break
        cursor = data.get('next_cursor')
        time.sleep(0.5)
    
    print(f"📄 Fetched {len(all_conversations)} latest conversations")
    
    # Process conversations
    new_leads = []
    
    for i, conv in enumerate(all_conversations):
        conv_id = conv['conversation_id']
        print(f"\n🔍 [{i+1}/{len(all_conversations)}] {conv_id[:20]}...")
        
        detail = fetch_detail(conv_id)
        if not detail:
            print("   ⚠️ No detail available")
            continue
        
        lead = extract_lead(detail, conv_id)
        if lead:
            # Check if already exists
            if lead['phone'] and lead['phone'] in existing_phones:
                print(f"   ⏭ Duplicate: {lead['phone']}")
                continue
            
            new_leads.append(lead)
            print(f"   ✅ {lead['name'][:20]:20} | {lead['phone'][:12]:12} | {lead['date']}")
        else:
            print(f"   ⚠️ No lead extracted")
        
        time.sleep(0.2)
    
    print(f"\n{'='*60}")
    print(f"📊 New leads found: {len(new_leads)}")
    
    if new_leads:
        # Add new leads to existing
        all_leads = new_leads + existing_leads
        
        # Sort by date (newest first)
        all_leads.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Update dashboard
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
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Updated dashboard_data.json")
        print(f"📈 Total leads now: {len(all_leads)}")
        print(f"🔥 HOT leads: {sum(1 for l in all_leads if l.get('category') == 'HOT')}")
        print(f"❄️ COLD leads: {sum(1 for l in all_leads if l.get('category') == 'COLD')}")
        
        # Save to CSV
        import csv
        csv_path = os.path.join(BASE_DIR, "crm_leads.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Phone', 'Email', 'Date', 'Category', 'Title'])
            for lead in all_leads:
                writer.writerow([lead['name'], lead['phone'], lead['email'], lead['date'], lead['category'], lead['title']])
        
        print(f"💾 Also saved to {csv_path}")
        
        # Git commit
        os.system('cd /root/.openclaw/workspace/rupeeboss && git add -A && git commit -m "Update: Latest leads ' + datetime.now().strftime('%Y-%m-%d_%H:%M') + '" && git push origin main')
        print("\n🚀 Changes pushed to GitHub!")
    else:
        print("\n✅ No new leads found. Dashboard is up to date!")

if __name__ == "__main__":
    main()
