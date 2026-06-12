#!/usr/bin/env python3
"""
Rebuild CRM with REAL summaries from ElevenLabs
This fetches fresh data with transcript_summary field
"""

import json
import urllib.request
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
KEY = os.getenv('ELEVENLABS_API_KEY')
AGENT_ID = "gKNyAo0UhrdRiQ7FAWVZ"
BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'

def make_request(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())

def get_conversation_detail(conv_id):
    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
        data = make_request(url, headers={"xi-api-key": KEY}, timeout=20)
        return data
    except Exception as e:
        print(f"  ERROR fetching {conv_id}: {e}")
        return None

def update_db_with_real_summary(conv_id, summary_title, summary):
    """Update existing conversation with real summary"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE conversations 
        SET call_summary_title = ?, call_summary = ?
        WHERE conversation_id = ?
    ''', (summary_title, summary, conv_id))
    conn.commit()
    conn.close()

def process_all_conversations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT conversation_id FROM conversations")
    conv_ids = [row[0] for row in c.fetchall()]
    conn.close()
    
    print(f"Processing {len(conv_ids)} conversations...")
    updated = 0
    failed = 0
    
    for i, conv_id in enumerate(conv_ids):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(conv_ids)} (Updated: {updated}, Failed: {failed})")
        
        detail = get_conversation_detail(conv_id)
        if not detail:
            failed += 1
            continue
        
        analysis = detail.get('analysis', {}) or {}
        summary_title = analysis.get('call_summary_title', '')
        summary = analysis.get('transcript_summary', '')
        
        if summary:  # Only update if we got a real summary
            update_db_with_real_summary(conv_id, summary_title, summary)
            updated += 1
        else:
            # Still update title even if no summary
            update_db_with_real_summary(conv_id, summary_title, '')
    
    return updated, failed

def rebuild_dashboard():
    """Rebuild dashboard_data.json from database with real summaries"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT conversation_id, date, call_summary_title, call_summary, 
               client_name, client_phone, client_email, transcript, duration_secs
        FROM conversations
        ORDER BY date DESC, start_time DESC
    ''')
    
    leads = []
    for idx, row in enumerate(c.fetchall()):
        conv_id, date, title, summary, name, phone, email, transcript, duration = row
        
        # Generate lead ID
        lead_id = f"rb_{idx+1:04d}"
        
        # Extract category from conversation analysis
        category = "COLD"
        if transcript and len(transcript) > 500:
            category = "HOT"
        
        lead = {
            "id": lead_id,
            "name": name if name else "Unknown",
            "phone": phone if phone else "",
            "email": email if email else "",
            "title": title if title else "RupeeBoss Loan Inquiry",
            "summary": summary if summary else title,
            "transcript": transcript[:2000] if transcript else "",
            "date": date,
            "category": category,
            "conversation_id": conv_id,
            "duration": duration or 0,
            "message_count": transcript.count('\n') if transcript else 0
        }
        leads.append(lead)
    
    conn.close()
    
    # Build dashboard data
    dashboard = {
        "lastUpdated": datetime.now().isoformat(),
        "metadata": {
            "totalLeads": len(leads),
            "lastUpdated": datetime.now().isoformat(),
            "source": "ElevenLabs Real Summary Rebuild"
        },
        "leads": leads
    }
    
    # Save
    with open(f'{BASE_DIR}/public/dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    return len(leads)

def main():
    print("=" * 60)
    print("REBUILD: Real Summaries from ElevenLabs")
    print("=" * 60)
    
    # Step 1: Update database with real summaries
    print("\n[1/3] Fetching real summaries from ElevenLabs...")
    updated, failed = process_all_conversations()
    print(f"\n  ✓ Updated: {updated} conversations")
    print(f"  ✗ Failed: {failed} conversations")
    
    # Step 2: Rebuild dashboard
    print("\n[2/3] Rebuilding dashboard_data.json...")
    total = rebuild_dashboard()
    print(f"  ✓ Created {total} leads with real summaries")
    
    # Step 3: Show sample
    print("\n[3/3] Sample data with real summaries:")
    with open(f'{BASE_DIR}/public/dashboard_data.json') as f:
        d = json.load(f)
    
    for lead in d['leads'][:3]:
        print(f"\n  {lead['id']} | {lead['date']}")
        print(f"    Title: {lead['title']}")
        print(f"    Summary: {lead['summary'][:100]}..." if lead['summary'] else "    Summary: (empty)")
    
    print("\n" + "=" * 60)
    print("✅ REBUILD COMPLETE")
    print(f"   Total leads: {total}")
    print(f"   With real summaries: {updated}")
    print("=" * 60)

if __name__ == "__main__":
    main()
