#!/usr/bin/env python3
"""
Extract names from transcripts and update CRM
"""

import json
import sqlite3
import re
from datetime import datetime

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'

def extract_names_from_transcript(transcript):
    """Extract customer name from transcript using Hindi and English patterns"""
    if not transcript:
        return None
    
    # Exclude agent phrases and false positives
    false_positives = ['riya', 'rupeeboss', 'support', 'loan', 'business', 'home', 'personal', 'aapka whatsapp', 'se', 'calling', 'call']
    
    patterns = [
        # Hindi: मेरा नाम ___ है
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*मेरा\s+नाम\s+([\u0900-\u097F\s]+?)\s+(?:है|है।)', 'hindi'),
        # Hindi: नाम है ___
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*नाम\s+(?:है|है)\s+([\u0900-\u097F\s]+?)(?:\s|$|,|\.)', 'hindi'),
        # Hindi: मैं ___ बोल रहा/रही हूँ
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*मैं\s+([\u0900-\u097F\s]+?)\s+(?:बोल\s+रहा|बोल\s+रही)', 'hindi'),
        # Hindi: ___ बोल रहा/रही हूँ
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*([\u0900-\u097F\s]+?)\s+(?:बोल\s+रहा|बोल\s+रही)\s+हूँ', 'hindi'),
        # English: my name is ___
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*[Mm]y\s+name\s+is\s+([A-Za-z\s\.]+?)(?:[,\.\s]|$|\band\b)', 'english'),
        # English: myself ___
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*[Mm]yself\s+([A-Za-z\s\.]+?)(?:[,\.\s]|$|\band\b)', 'english'),
        # English: I am ___ (name context)
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*[Ii]\s+am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:[,\.\s]|$|\band\b)', 'english'),
        # English: this is ___
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*.*[Tt]his\s+is\s+([A-Za-z\s\.]+?)(?:[,\.\s]|$|\band\b)', 'english'),
        # Name directly stated with phone
        (r'[Uu][Ss][Ee][Rr][^\[\]]*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s*,?\s*\d{5,}', 'english'),
    ]
    
    for pattern, lang in patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE | re.DOTALL)
        for match in matches:
            name = match.strip()
            # Clean up
            name = re.sub(r'\s+', ' ', name)
            name = name.strip('.,;:')
            
            # Validation
            if len(name) < 2 or len(name) > 50:
                continue
            if any(fp in name.lower() for fp in false_positives):
                continue
            if lang == 'english' and not re.match(r'^[A-Za-z\s\.]+$', name):
                continue
            if lang == 'hindi' and not re.match(r'^[\u0900-\u097F\s]+$', name):
                continue
                
            return name
    
    return None

def update_database_names():
    """Update names in database from transcripts"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all conversations with Unknown or empty names
    c.execute('''
        SELECT conversation_id, transcript, client_name
        FROM conversations
        WHERE (client_name IS NULL OR client_name = '' OR client_name = 'Unknown')
        AND transcript IS NOT NULL
    ''')
    
    updated = 0
    found = 0
    
    for row in c.fetchall():
        conv_id, transcript, current_name = row
        
        name = extract_names_from_transcript(transcript)
        
        if name:
            found += 1
            # Update database
            c.execute('''
                UPDATE conversations
                SET client_name = ?
                WHERE conversation_id = ?
            ''', (name, conv_id))
            updated += 1
    
    conn.commit()
    conn.close()
    
    return found, updated

def rebuild_dashboard():
    """Rebuild dashboard with updated names"""
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
        
        # Determine category
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
            "source": "ElevenLabs with Name Extraction"
        },
        "leads": leads
    }
    
    with open(f'{BASE_DIR}/public/dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    return len(leads)

def main():
    print("=" * 60)
    print("NAME EXTRACTION from Transcripts")
    print("=" * 60)
    
    # Step 1: Extract and update DB
    print("\n[1/3] Extracting names from transcripts...")
    found, updated = update_database_names()
    print(f"  ✓ Names found: {found}")
    print(f"  ✓ Database updated: {updated}")
    
    # Step 2: Rebuild dashboard
    print("\n[2/3] Rebuilding dashboard...")
    total = rebuild_dashboard()
    print(f"  ✓ Dashboard created with {total} leads")
    
    # Step 3: Show stats
    print("\n[3/3] Statistics:")
    with open(f'{BASE_DIR}/public/dashboard_data.json') as f:
        d = json.load(f)
    
    unknown_count = sum(1 for lead in d['leads'] if lead.get('name') == 'Unknown')
    named_count = len(d['leads']) - unknown_count
    
    print(f"  • Total leads: {len(d['leads'])}")
    print(f"  • With names: {named_count}")
    print(f"  • Unknown names: {unknown_count}")
    
    # Show sample named leads
    print("\nSample updated names:")
    count = 0
    for lead in d['leads']:
        if lead.get('name') != 'Unknown':
            print(f"  {lead['id']} | {lead['phone']} | {lead['name']}")
            count += 1
            if count >= 10:
                break
    
    print("\n" + "=" * 60)
    print("✅ Name extraction complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
