#!/usr/bin/env python3
"""
Extract names from transcripts and update CRM - IMPROVED VERSION
"""

import json
import sqlite3
import re
from datetime import datetime

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'

def extract_user_lines(transcript):
    """Extract only user lines from transcript"""
    if not transcript:
        return []
    # Find all [USER]: lines
    user_lines = re.findall(r'\[USER\]: ([^\[]+)', transcript)
    return [line.strip() for line in user_lines if line.strip()]

def clean_name(name):
    """Clean and validate extracted name"""
    if not name:
        return None
    
    name = name.strip()
    # Remove common suffixes/prefixes
    name = re.sub(r'^(?:name|naam|myself|i am|this is|mera|hai)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+(?:hai|hoon|hun|speaking|here|from|and|with).*$', '', name, flags=re.IGNORECASE)
    name = name.strip('.,;:?! ')
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    
    return name if name else None

def extract_names_from_transcript(transcript):
    """Extract customer name from transcript using Hindi and English patterns"""
    if not transcript:
        return None
    
    user_lines = extract_user_lines(transcript)
    user_text = ' '.join(user_lines)
    
    # False positives to exclude
    false_positives = [
        'riya', 'rupeeboss', 'support', 'loan', 'business', 'home', 'personal',
        'looking', 'interested', 'salaried', 'from', 'calling', 'call', 'customer',
        'application', 'registration', 'issue', 'inquiry', 'callback', 'request',
        'transfer', 'connect', 'speaking', 'new', 'old', 'existing', 'first',
        'second', 'third', 'name', 'naam', 'mobile', 'phone', 'number', 'agent'
    ]
    
    # Patterns to match names - in order of preference
    patterns = [
        # English: Name: ___ or name is ___
        (r'(?:[Nn]ame\s*:?\s*|[Nn]ame\s+is\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'english'),
        # English: Myself ___
        (r'[Mm]yself\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'english'),
        # English: This is ___
        (r'[Tt]his\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'english'),
        # Hindi: मेरा नाम ___ है
        (r'मेरा\s+नाम\s+([\u0900-\u097F\s]+?)(?:\s+है|\s+hai|\s*[,;]|$)', 'hindi'),
        # Hindi: नाम ___ है
        (r'नाम\s+([\u0900-\u097F\s]+?)(?:\s+है|\s+hai|\s*[,;]|$)', 'hindi'),
        # Hindi: मैं ___ बोल रहा हूँ / बोल रही हूँ
        (r'मैं\s+([\u0900-\u097F\s]+?)\s+(?:बोल\s+रहा|बोल\s+रही)', 'hindi'),
        # Hindi: ___ बोल रहा हूँ / बोल रही हूँ
        (r'([\u0900-\u097F\s]+?)\s+(?:बोल\s+रहा|बोल\s+रही)\s+हूँ', 'hindi'),
        # English: I am ___ (must be capitalized proper name)
        (r'[Ii]\s+am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'english'),
        # Direct name with number (e.g., "Rahul, 9876543210")
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s*,?\s*\d{10}', 'english'),
    ]
    
    for pattern, lang in patterns:
        matches = re.findall(pattern, user_text)
        for match in matches:
            name = clean_name(match)
            if not name:
                continue
            
            # Validation
            if len(name) < 2 or len(name) > 40:
                continue
            
            # Check for false positives
            if any(fp in name.lower() for fp in false_positives):
                continue
            
            # Language-specific validation
            if lang == 'english':
                # Should be mostly letters and spaces
                if not re.match(r'^[A-Za-z\s\.]+$', name):
                    continue
                # Should have proper capitalization
                words = name.split()
                if not all(w[0].isupper() for w in words if w):
                    continue
            
            if lang == 'hindi':
                # Should be Devanagari script
                if not re.match(r'^[\u0900-\u097F\s]+$', name):
                    continue
            
            return name
    
    # Try extracting from analysis_json if available
    return None

def extract_name_from_analysis(analysis_json):
    """Extract name from ElevenLabs analysis JSON"""
    if not analysis_json:
        return None
    
    try:
        analysis = json.loads(analysis_json)
        data_collection = analysis.get('data_collection_results', {})
        
        # Look for Name field
        name_data = data_collection.get('Name', {})
        if name_data:
            value = name_data.get('value', '')
            if value and value.lower() not in ['null', 'none', '']:
                # Filter out agent name
                if 'riya' not in value.lower():
                    return clean_name(value)
        
        # Try customer_name field
        customer_name = analysis.get('customer_name', '')
        if customer_name and 'riya' not in customer_name.lower():
            return clean_name(customer_name)
            
    except json.JSONDecodeError:
        pass
    
    return None

def update_database_names():
    """Update names in database from transcripts and analysis"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all conversations with empty/Unknown names
    c.execute('''
        SELECT conversation_id, transcript, analysis_json, client_name
        FROM conversations
        WHERE (client_name IS NULL OR client_name = '' OR client_name = 'Unknown')
        AND transcript IS NOT NULL
        ORDER BY date DESC
    ''')
    
    updated = 0
    found = 0
    samples = []
    
    for row in c.fetchall():
        conv_id, transcript, analysis_json, current_name = row
        
        # Try analysis_json first (structured data)
        name = extract_name_from_analysis(analysis_json)
        
        # Fall back to transcript parsing
        if not name:
            name = extract_names_from_transcript(transcript)
        
        if name:
            found += 1
            # Keep samples for display
            if len(samples) < 10:
                user_lines = extract_user_lines(transcript)
                samples.append({
                    'id': conv_id,
                    'name': name,
                    'user_lines': user_lines[:2]
                })
            
            # Update database
            c.execute('''
                UPDATE conversations
                SET client_name = ?
                WHERE conversation_id = ?
            ''', (name, conv_id))
            updated += 1
    
    conn.commit()
    conn.close()
    
    return found, updated, samples

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
    print("=" * 70)
    print("NAME EXTRACTION from Transcripts (Improved)")
    print("=" * 70)
    
    # Step 1: Extract and update DB
    print("\n[1/3] Extracting names...")
    found, updated, samples = update_database_names()
    print(f"  ✓ Names found: {found}")
    print(f"  ✓ Database updated: {updated}")
    
    if samples:
        print("\n  Sample extractions:")
        for s in samples[:5]:
            print(f"    → {s['name']}")
            for line in s['user_lines']:
                print(f"      [USER]: {line[:60]}...")
    
    # Step 2: Rebuild dashboard
    print("\n[2/3] Rebuilding dashboard...")
    total = rebuild_dashboard()
    print(f"  ✓ Dashboard created with {total} leads")
    
    # Step 3: Stats
    print("\n[3/3] Final Statistics:")
    with open(f'{BASE_DIR}/public/dashboard_data.json') as f:
        d = json.load(f)
    
    unknown_count = sum(1 for lead in d['leads'] if lead.get('name') == 'Unknown')
    named_count = len(d['leads']) - unknown_count
    
    print(f"  • Total leads: {len(d['leads'])}")
    print(f"  • With names: {named_count}")
    print(f"  • Unknown names: {unknown_count}")
    print(f"  • Named percentage: {(named_count/len(d['leads'])*100):.1f}%")
    
    # Show sample named leads
    print("\n  Sample named leads:")
    count = 0
    for lead in d['leads']:
        if lead.get('name') != 'Unknown':
            print(f"    {lead['id']} | {lead['phone'][:12] if lead['phone'] else 'N/A':<12} | {lead['name']}")
            count += 1
            if count >= 10:
                break
    
    print("\n" + "=" * 70)
    print("✅ Name extraction complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
