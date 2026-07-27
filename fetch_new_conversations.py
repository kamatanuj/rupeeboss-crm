#!/usr/bin/env python3
"""
Fetch ONLY NEW RupeeBoss conversations from ElevenLabs API.
Preserves existing data in conversations.db, dashboard_data.json, and crm_leads.csv.
Only appends conversations with IDs not already in the DB.
"""
import json
import urllib.request
import os
import csv
import sqlite3
import re
from datetime import datetime

API_KEY = "3a708d1216251b9801380110a5ec11fb82f806545f70978ad63aa3283fbf23d4"
AGENT_ID = "gKNyAo0UhrdRiQ7FAWVZ"
BASE_DIR = "/root/.openclaw/workspace/rupeeboss"
DB_PATH = os.path.join(BASE_DIR, "conversations.db")

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
    for key in ['phone', 'phone_number', 'contact_number', 'mobile', 'telephone']:
        if key in data_collection and data_collection[key]:
            phone = str(data_collection[key]).strip()
            break
    
    # Name
    name = ''
    for key in ['name', 'caller_name', 'full_name', 'customer_name']:
        if key in data_collection and data_collection[key]:
            name = str(data_collection[key]).strip()
            break
    
    # Email
    email = ''
    for key in ['email', 'email_address']:
        if key in data_collection and data_collection[key]:
            email = str(data_collection[key]).strip()
            break
    
    # Transcript analysis for name/phone if not in data_collection
    transcript = detail.get('transcript', [])
    if not name or not phone:
        for line in transcript:
            if isinstance(line, dict):
                role = line.get('role', '')
                text = line.get('text', '')
                if role == 'user':
                    # Try to find phone
                    if not phone:
                        import re
                        phone_match = re.search(r'(\+?91)?[\s-]?(\d{10})', text)
                        if phone_match:
                            phone = phone_match.group(0).strip()
                    # Try to find name
                    if not name:
                        # Look for "my name is" pattern
                        name_match = re.search(r'(?:my name is|mera naam|naam|name is)\s+([a-zA-Z\u0900-\u097F\s]+?)(?:\.|,|!|$)', text, re.IGNORECASE)
                        if name_match:
                            name = name_match.group(1).strip()
    
    if not name:
        name = 'Unknown'
    
    # Summary
    summary = analysis.get('summary', '')
    title = analysis.get('summary_title', '') or (summary[:60] if summary else '')
    
    # Category
    category = 'COLD'
    summary_lower = (summary or '').lower()
    if any(w in summary_lower for w in ['hot', 'urgent', 'immediate', 'callback', 'follow up']):
        category = 'HOT'
    
    # Duration
    duration_secs = 0
    end_time = metadata.get('end_time_unix_secs', 0)
    if start_time and end_time:
        duration_secs = end_time - start_time
    
    return {
        'conv_id': conv_id,
        'date': date_str,
        'start_time': datetime.fromtimestamp(start_time).strftime('%Y-%m-%dT%H:%M:%S'),
        'end_time': datetime.fromtimestamp(end_time).strftime('%Y-%m-%dT%H:%M:%S') if end_time else '',
        'duration_secs': duration_secs,
        'status': metadata.get('status', ''),
        'call_summary_title': title,
        'call_summary': summary,
        'client_name': name,
        'client_phone': phone,
        'client_email': email,
        'transcript': json.dumps(detail.get('transcript', []), ensure_ascii=False),
        'transcript_json': json.dumps(detail.get('transcript', []), ensure_ascii=False),
        'analysis_json': json.dumps(analysis, ensure_ascii=False),
        'metadata_json': json.dumps(metadata, ensure_ascii=False),
    }

def main():
    # Step 1: Get existing conversation IDs from DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT conversation_id FROM conversations")
    existing_ids = set(r[0] for r in c.fetchall())
    print(f"📦 Existing conversations in DB: {len(existing_ids)}")
    
    # Step 2: Fetch conversation list from API
    print("\n🚀 Fetching conversation list from API...")
    all_convs = []
    cursor = None
    page = 1
    while True:
        data = fetch_page(cursor)
        convs = data.get('conversations', [])
        all_convs.extend(convs)
        print(f"  Page {page}: {len(convs)} conversations (total: {len(all_convs)})")
        cursor = data.get('next_cursor')
        if not cursor or not convs:
            break
        page += 1
    
    print(f"\n📋 Total conversations from API: {len(all_convs)}")
    
    # Step 3: Filter to only NEW conversations
    new_convs = [c for c in all_convs if c.get('conversation_id') not in existing_ids]
    print(f"🆕 New conversations not in DB: {len(new_convs)}")
    
    if not new_convs:
        print("✅ No new conversations to add. Existing data preserved.")
        conn.close()
        return
    
    # Step 4: Fetch details and insert into DB
    print(f"\n⏳ Processing {len(new_convs)} new conversations...")
    inserted = 0
    new_leads = []
    
    for i, conv in enumerate(new_convs, 1):
        conv_id = conv['conversation_id']
        print(f"  [{i}/{len(new_convs)}] {conv_id}...")
        
        detail = fetch_detail(conv_id)
        if not detail:
            continue
        
        lead = extract_lead(detail, conv_id)
        if not lead:
            print(f"    ⚠️ No data extracted")
            continue
        
        # Insert into DB
        c.execute("""
            INSERT OR IGNORE INTO conversations 
            (conversation_id, agent_id, date, start_time, end_time, duration_secs, 
             status, call_summary_title, call_summary, client_name, client_phone, 
             client_email, transcript, transcript_json, analysis_json, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead['conv_id'], AGENT_ID, lead['date'], lead['start_time'], lead['end_time'],
            lead['duration_secs'], lead['status'], lead['call_summary_title'], lead['call_summary'],
            lead['client_name'], lead['client_phone'], lead['client_email'],
            lead['transcript'], lead['transcript_json'], lead['analysis_json'], lead['metadata_json'],
            datetime.now().isoformat()
        ))
        inserted += 1
        new_leads.append(lead)
        print(f"    ✅ {lead['client_name']} | {lead['client_phone']} | {lead['date']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Inserted {inserted} new conversations into DB")
    print(f"📦 Total in DB now: {len(existing_ids) + inserted}")
    
    # Step 5: Rebuild dashboard_data.json and crm_leads.csv with ALL data (old + new)
    print("\n📊 Rebuilding dashboard data (preserving all existing leads)...")
    
    # Reload all data from DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT conversation_id, date, client_name, client_phone, client_email, 
               call_summary, call_summary_title, status
        FROM conversations ORDER BY date DESC
    """)
    
    all_leads = []
    for row in c.fetchall():
        # Category
        summary = row[5] or ''
        category = 'COLD'
        if any(w in summary.lower() for w in ['hot', 'urgent', 'immediate', 'callback', 'follow up']):
            category = 'HOT'
        
        all_leads.append({
            'id': row[0],
            'name': row[2] or 'Unknown',
            'phone': row[3] or '',
            'email': row[4] or '',
            'date': row[1] or '',
            'category': category,
            'title': row[6] or (summary[:60] if summary else ''),
            'summary': summary,
            'status': row[7] or ''
        })
    
    conn.close()
    
    # Write dashboard JSON (full rebuild with ALL data preserved)
    dashboard = {
        "totalLeads": len(all_leads),
        "lastUpdated": datetime.now().isoformat(),
        "leads": all_leads
    }
    
    dashboard_path = os.path.join(BASE_DIR, "dashboard_data.json")
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    print(f"  ✅ dashboard_data.json: {len(all_leads)} leads")
    
    # Write CSV (full rebuild with ALL data preserved)
    csv_path = os.path.join(BASE_DIR, "crm_leads.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Phone', 'Email', 'Date', 'Category', 'Title'])
        for lead in all_leads:
            writer.writerow([lead['name'], lead['phone'], lead['email'], lead['date'], lead['category'], lead['title']])
    print(f"  ✅ crm_leads.csv: {len(all_leads)} leads")
    
    print(f"\n🎉 Done! {inserted} new conversations added. All existing data preserved.")

if __name__ == '__main__':
    main()