#!/usr/bin/env python3
"""
INCREMENTAL sync: Only fetch NEW conversations from ElevenLabs for agent gKNyAo0UhrdRiQ7FAWVZ
and add them to the existing SQLite DB.
"""

import json
import urllib.request
import sqlite3
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def get_existing_ids():
    """Get set of conversation IDs already in DB"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT conversation_id FROM conversations")
        return {row[0] for row in c.fetchall()}
    except sqlite3.OperationalError:
        return set()
    finally:
        conn.close()

def get_conversation_detail(conv_id):
    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
        data = make_request(url, headers={"xi-api-key": KEY}, timeout=20)
        return data
    except Exception as e:
        print(f"  ERROR fetching {conv_id}: {e}")
        return None

def extract_client_data(transcript_list, analysis):
    import re
    user_text = ""
    for msg in transcript_list:
        if msg.get('role') == 'user':
            user_text += " " + (msg.get('message') or msg.get('original_message') or '')
    
    phones = list(set(re.findall(r'\b([6-9]\d{9})\b', user_text)))
    
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
    
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', user_text)
    
    client_name = ""
    if analysis and isinstance(analysis, dict):
        client_name = analysis.get('customer_name', '') or analysis.get('client_name', '')
    
    return {
        'name': client_name or (names[0] if names else ''),
        'phone': phones[0] if phones else '',
        'email': emails[0] if emails else ''
    }

def save_to_db(conv_id, agent_id, date, start_time, end_time, duration, status,
               summary_title, summary, client_name, client_phone, client_email,
               transcript_text, transcript_json, analysis_json, metadata_json):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO conversations
        (conversation_id, agent_id, date, start_time, end_time, duration_secs,
         status, call_summary_title, call_summary, client_name, client_phone,
         client_email, transcript, transcript_json, analysis_json, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (conv_id, agent_id, date, start_time, end_time, duration, status,
          summary_title, summary, client_name, client_phone, client_email,
          transcript_text, transcript_json, analysis_json, metadata_json))
    conn.commit()
    conn.close()

def process_conversation(conv):
    conv_id = conv['conversation_id']
    
    start_ts = conv.get('start_time_unix_secs', 0)
    end_ts = conv.get('end_time_unix_secs', 0)
    date = datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d') if start_ts else 'unknown'
    start_time = datetime.fromtimestamp(start_ts).isoformat() if start_ts else ''
    end_time = datetime.fromtimestamp(end_ts).isoformat() if end_ts else ''
    
    detail = get_conversation_detail(conv_id)
    if not detail:
        return False
    
    transcript_list = detail.get('transcript', [])
    analysis = detail.get('analysis', {})
    metadata = detail.get('metadata', {})
    
    transcript_lines = []
    for msg in transcript_list:
        role = msg.get('role', 'unknown')
        text = msg.get('message', '') or msg.get('original_message', '') or ''
        if text:
            transcript_lines.append(f"[{role.upper()}]: {text}")
    transcript_text = "\n".join(transcript_lines)
    
    client_data = extract_client_data(transcript_list, analysis)
    
    summary_title = conv.get('call_summary_title', '') or (analysis.get('call_summary_title', '') if analysis else '') or ''
    summary = analysis.get('call_summary', '') if isinstance(analysis, dict) else ''
    
    status = detail.get('status', '') or conv.get('status', '')
    duration = detail.get('call_duration_secs', 0) or conv.get('call_duration_secs', 0)
    
    save_to_db(
        conv_id=conv_id, agent_id=AGENT_ID, date=date, start_time=start_time,
        end_time=end_time, duration=duration, status=status,
        summary_title=summary_title, summary=summary,
        client_name=client_data['name'], client_phone=client_data['phone'],
        client_email=client_data['email'], transcript_text=transcript_text,
        transcript_json=json.dumps(transcript_list, ensure_ascii=False),
        analysis_json=json.dumps(analysis, ensure_ascii=False) if analysis else '{}',
        metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else '{}'
    )
    
    return True

def main():
    print("=" * 60)
    print("INCREMENTAL SYNC: ElevenLabs Conversations")
    print(f"Agent: {AGENT_ID}")
    print(f"DB: {DB_PATH}")
    print("=" * 60)
    
    existing_ids = get_existing_ids()
    print(f"Existing conversations in DB: {len(existing_ids)}")
    
    # Fetch conversation list
    print("\n[1/2] Fetching conversation list from ElevenLabs...")
    all_convs = []
    next_cursor = None
    page = 0
    
    while True:
        url = f"https://api.elevenlabs.io/v1/convai/conversations?agent_id={AGENT_ID}&page_size=100"
        if next_cursor:
            url += f"&cursor={next_cursor}"
        
        try:
            data = make_request(url, headers={"xi-api-key": KEY})
            convs = data.get('conversations', [])
            all_convs.extend(convs)
            page += 1
            if page % 5 == 0:
                print(f"  Page {page}: {len(all_convs)} fetched")
            
            if not data.get('has_more', False):
                break
            next_cursor = data.get('next_cursor')
        except Exception as e:
            print(f"  ERROR: {e}")
            break
    
    # Filter to only new conversations
    new_convs = [c for c in all_convs if c['conversation_id'] not in existing_ids]
    print(f"\nTotal from API: {len(all_convs)}")
    print(f"Already in DB: {len(existing_ids)}")
    print(f"NEW to sync: {len(new_convs)}")
    
    if not new_convs:
        print("\n✅ Nothing new to sync. DB is up to date.")
        return
    
    # Process new conversations
    print(f"\n[2/2] Fetching details for {len(new_convs)} new conversations...")
    success = 0
    failed = 0
    
    batch_size = 20
    for batch_start in range(0, len(new_convs), batch_size):
        batch = new_convs[batch_start:batch_start + batch_size]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_conversation, c): c for c in batch}
            for future in as_completed(futures):
                if future.result():
                    success += 1
                else:
                    failed += 1
        
        processed = min(batch_start + batch_size, len(new_convs))
        print(f"  Processed {processed}/{len(new_convs)}... Saved: {success}, Failed: {failed}")
        
        if processed < len(new_convs):
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("SYNC COMPLETE!")
    print(f"New conversations synced: {success}")
    print(f"Failed: {failed}")
    print(f"Total in DB now: {len(existing_ids) + success}")
    print("=" * 60)

if __name__ == '__main__':
    main()
