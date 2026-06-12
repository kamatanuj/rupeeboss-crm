#!/usr/bin/env python3
"""
Extract REAL summaries from existing analysis_json and rebuild CRM
"""

import json
import sqlite3
from datetime import datetime

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'

def update_database_with_real_summaries():
    """Extract real summaries from analysis_json and update DB"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all conversations with analysis_json
    c.execute('''
        SELECT conversation_id, analysis_json, call_summary_title
        FROM conversations
        WHERE analysis_json IS NOT NULL AND analysis_json != ''
    ''')
    
    updated = 0
    no_summary = 0
    
    for row in c.fetchall():
        conv_id, analysis_json, current_title = row
        
        try:
            analysis = json.loads(analysis_json)
            real_summary = analysis.get('transcript_summary', '')
            real_title = analysis.get('call_summary_title', '') or current_title
            
            # Update database with real summary
            c.execute('''
                UPDATE conversations
                SET call_summary = ?, call_summary_title = ?
                WHERE conversation_id = ?
            ''', (real_summary, real_title, conv_id))
            
            if real_summary:
                updated += 1
            else:
                no_summary += 1
                
        except json.JSONDecodeError:
            no_summary += 1
            continue
    
    conn.commit()
    conn.close()
    
    return updated, no_summary

def rebuild_dashboard():
    """Rebuild dashboard_data.json from updated database"""
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
        
        lead_id = f"rb_{idx+1:04d}"
        
        # Determine category based on transcript length
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
    
    # Build dashboard
    dashboard = {
        "lastUpdated": datetime.now().isoformat(),
        "metadata": {
            "totalLeads": len(leads),
            "lastUpdated": datetime.now().isoformat(),
            "source": "ElevenLabs Real Summary Rebuild"
        },
        "leads": leads
    }
    
    with open(f'{BASE_DIR}/public/dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    return len(leads)

def main():
    print("=" * 60)
    print("EXTRACTING REAL SUMMARIES from ElevenLabs analysis_json")
    print("=" * 60)
    
    # Step 1: Extract and update DB
    print("\n[1/2] Extracting real summaries from existing data...")
    updated, no_summary = update_database_with_real_summaries()
    print(f"  ✓ Updated with real summaries: {updated}")
    print(f"  ℹ No summary available: {no_summary}")
    
    # Step 2: Rebuild dashboard
    print("\n[2/2] Rebuilding dashboard_data.json...")
    total = rebuild_dashboard()
    print(f"  ✓ Created dashboard with {total} leads")
    
    # Show samples
    print("\n" + "=" * 60)
    print("SAMPLE DATA (First 3 leads):")
    print("=" * 60)
    
    with open(f'{BASE_DIR}/public/dashboard_data.json') as f:
        d = json.load(f)
    
    for lead in d['leads'][:3]:
        print(f"\n📞 {lead['id']} | {lead['date']} | {lead.get('phone', 'N/A')}")
        print(f"   Title: {lead['title']}")
        summary = lead.get('summary', '')
        if summary and len(summary) > 100:
            print(f"   Summary: {summary[:150]}...")
        elif summary:
            print(f"   Summary: {summary}")
        else:
            print(f"   Summary: (no summary available)")
    
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE: {total} leads with real summaries")
    print("=" * 60)

if __name__ == "__main__":
    main()
