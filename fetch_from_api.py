#!/usr/bin/env python3
"""
Fetch ALL Rupeeboss data from ElevenLabs API from scratch.
Saves progress every 50 conversations to avoid losing data.
"""
import json
import urllib.request
import time
import os
from datetime import datetime
import re

API_KEY = "3a708d1216251b9801380110a5ec11fb82f806545f70978ad63aa3283fbf23d4"
AGENT_ID = "gKNyAo0UhrdRiQ7FAWVZ"
PROGRESS_FILE = '/tmp/rupeeboss_api_progress.json'

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'conversations': [], 'leads': [], 'cursor': None, 'page': 1, 'done_list': False, 'processed_count': 0}

def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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
        print(f"    Error: {e}")
        return None

def extract_lead(detail):
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
    
    # Name
    name = ''
    name_field = data_collection.get('Name', {})
    if name_field and name_field.get('value'):
        name = str(name_field['value']).strip().title()
    
    # Transcript
    transcript_lines = []
    for msg in detail.get('transcript', []):
        role = msg.get('role', 'unknown').upper()
        text = msg.get('message', '')
        if text:
            transcript_lines.append(f"[{role}] {text}")
    transcript = '\n'.join(transcript_lines)
    
    # Summary
    summary = analysis.get('transcript_summary', '')
    
    # Only include if we have meaningful data
    if not transcript and not phone:
        return None
    
    has_name = name and len(name) > 1 and name.lower() not in ['unknown', 'interested', 'my', 'sir', 'maam', 'yes']
    has_phone = len(phone) == 10
    category = 'HOT' if (has_name and has_phone) else 'COLD'
    
    # Title from first user message
    title = 'Business Loan Inquiry'
    for line in transcript_lines:
        if '[USER]' in line:
            user_msg = line.replace('[USER]', '').strip()
            if len(user_msg) > 5:
                title = user_msg[:80]
                break
    
    return {
        'id': '',
        'date': date_str,
        'name': name if has_name else 'Unknown',
        'phone': phone,
        'email': '',
        'title': title,
        'category': category,
        'status': 'New',
        'summary': summary if summary else (f"Loan inquiry from {phone}" if phone else "Business loan inquiry"),
        'transcript': transcript,
        'source_conversation': detail.get('conversation_id', ''),
        'duration': metadata.get('call_duration_secs', 0),
        'notes': '',
        'documents': []
    }

def main():
    print("="*60)
    print("FETCHING ALL RUPEEBOSS DATA FROM ELEVENLABS API")
    print("="*60)
    
    progress = load_progress()
    
    # Step 1: Fetch all conversation IDs
    if not progress['done_list']:
        print("\n[1/2] Fetching conversation list...")
        while True:
            data = fetch_page(progress['cursor'])
            convs = data.get('conversations', [])
            progress['conversations'].extend([c['conversation_id'] for c in convs])
            progress['cursor'] = data.get('next_cursor')
            progress['page'] += 1
            
            print(f"  Page {progress['page']-1}: {len(convs)} convs (total: {len(progress['conversations'])})")
            
            if not progress['cursor'] or len(convs) == 0:
                progress['done_list'] = True
                save_progress(progress)
                break
            
            save_progress(progress)
            time.sleep(0.2)
        
        print(f"\n✅ Total conversations: {len(progress['conversations'])}")
    else:
        print(f"\n✅ Using existing list: {len(progress['conversations'])} conversations")
    
    # Step 2: Process each conversation
    print("\n[2/2] Processing conversations...")
    total = len(progress['conversations'])
    
    for i in range(progress['processed_count'], total):
        conv_id = progress['conversations'][i]
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{total}... (leads: {len(progress['leads'])})")
            save_progress(progress)
        
        detail = fetch_detail(conv_id)
        lead = extract_lead(detail)
        
        if lead:
            progress['leads'].append(lead)
        
        progress['processed_count'] = i + 1
        time.sleep(0.25)
    
    print(f"\n✅ Total leads: {len(progress['leads'])}")
    
    # Sort by date descending
    print("\nSorting by date...")
    progress['leads'].sort(key=lambda x: x['date'], reverse=True)
    
    # Assign IDs
    for i, lead in enumerate(progress['leads']):
        lead['id'] = f"rb_{i+1:04d}"
    
    # Build output
    output = {
        'leads': progress['leads'],
        'metadata': {
            'total': len(progress['leads']),
            'generated_at': datetime.now().isoformat(),
            'source': 'ElevenLabs API'
        }
    }
    
    # Save
    with open('public/dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Clean up progress
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    
    # Stats
    hot = sum(1 for l in progress['leads'] if l['category'] == 'HOT')
    cold = len(progress['leads']) - hot
    dates = [l['date'] for l in progress['leads']]
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total: {len(progress['leads'])} leads")
    print(f"  HOT: {hot}")
    print(f"  COLD: {cold}")
    print(f"\nDate range: {min(dates)} to {max(dates)}")
    print(f"\nLatest 5:")
    for lead in progress['leads'][:5]:
        print(f"  {lead['date']} | {lead['id']} | {lead['name'][:25]}")
    
    real_transcripts = sum(1 for l in progress['leads'] if len(l['transcript']) > 100)
    print(f"\nLeads with transcripts: {real_transcripts}/{len(progress['leads'])}")
    
    print("\n✅ Saved to public/dashboard_data.json")

if __name__ == "__main__":
    main()
