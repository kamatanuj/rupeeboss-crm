#!/usr/bin/env python3
"""
Complete RupeeBoss CRM rebuild.
- Fetches all ElevenLabs conversations with rate-limit backoff
- Stores full details in conversations.db
- Rebuilds leads.csv + public/dashboard_data.json
- Relaxed extraction: every conversation becomes a lead; phone/name captured when present
"""
import json
import urllib.request
import urllib.error
import sqlite3
import os
import re
import csv
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
KEY = os.getenv('ELEVENLABS_API_KEY')
AGENT_ID = "gKNyAo0UhrdRiQ7FAWVZ"
BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'

FALSE_NAMES = {
    'riya', 'rupeeboss', 'support', 'loan', 'business', 'home', 'personal',
    'looking', 'interested', 'salaried', 'from', 'calling', 'call', 'customer',
    'application', 'registration', 'issue', 'inquiry', 'callback', 'request',
    'transfer', 'connect', 'speaking', 'new', 'old', 'existing', 'first',
    'second', 'third', 'name', 'naam', 'mobile', 'phone', 'number', 'agent',
    'yes', 'no', 'hello', 'hi', 'sir', 'maam', 'madam', 'okay', 'ok'
}


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def make_request(url, headers=None, timeout=25, max_retries=5):
    """Make request with exponential backoff on 429/5xx."""
    headers = headers or {}
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                sleep = (2 ** attempt) + random.random()
                log(f"Rate limited (429). Sleeping {sleep:.1f}s before retry {attempt+1}/{max_retries}...")
                time.sleep(sleep)
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                sleep = (2 ** attempt) + random.random()
                log(f"Network error: {e}. Sleeping {sleep:.1f}s before retry {attempt+1}/{max_retries}...")
                time.sleep(sleep)
                continue
            raise
    raise Exception(f"Failed after {max_retries} retries: {url}")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT UNIQUE NOT NULL,
            agent_id TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_secs INTEGER,
            status TEXT,
            call_summary_title TEXT,
            call_summary TEXT,
            client_name TEXT,
            client_phone TEXT,
            client_email TEXT,
            transcript TEXT,
            transcript_json TEXT,
            analysis_json TEXT,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_existing_ids():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT conversation_id FROM conversations")
        return {row[0] for row in c.fetchall()}
    except sqlite3.OperationalError:
        return set()
    finally:
        conn.close()


def fetch_conversation_list():
    log("Fetching conversation list from ElevenLabs...")
    all_convs = []
    next_cursor = None
    page = 0
    while True:
        url = f"https://api.elevenlabs.io/v1/convai/conversations?agent_id={AGENT_ID}&page_size=100"
        if next_cursor:
            url += f"&cursor={next_cursor}"
        data = make_request(url, headers={"xi-api-key": KEY})
        convs = data.get('conversations', [])
        for c in convs:
            ts = c.get('start_time_unix_secs', 0)
            c['date'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else 'unknown'
        all_convs.extend(convs)
        page += 1
        if page % 5 == 0:
            log(f"  Page {page}: {len(all_convs)} conversations")
        if not data.get('has_more', False) or page >= 100:
            break
        next_cursor = data.get('next_cursor')
    log(f"Total conversations from API: {len(all_convs)}")
    return all_convs


def fetch_detail(conv_id):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
    return make_request(url, headers={"xi-api-key": KEY}, timeout=25)


def extract_phone_from_text(text):
    """Extract Indian mobile numbers, tolerating spaces/pauses."""
    if not text:
        return ''
    # Direct 10-digit
    phones = re.findall(r'\b([6-9]\d{9})\b', text)
    if phones:
        return phones[0]
    # Spoken digits like "9 8 7 6 5 4 3 2 1 0" or "9,8,7,6,5,4,3,2,1,0"
    spaced = re.findall(r'(?:\b\d\b[\s,\.]){9}\b\d\b', text)
    for s in spaced:
        digits = re.sub(r'\D', '', s)
        if len(digits) == 10 and digits[0] in '6789':
            return digits
    # With +91 prefix
    phones = re.findall(r'(?:\+91[-\s]?)?([6-9]\d{9})\b', text)
    if phones:
        return phones[0]
    return ''


def extract_name_from_text(text, analysis=None):
    """Extract name from user transcript or analysis."""
    if not text:
        return ''

    # First try analysis structured fields
    if analysis and isinstance(analysis, dict):
        data_collection = analysis.get('data_collection_results', {})
        for field in ['Name', 'Customer Name', 'Client Name', 'customer_name', 'client_name']:
            val = data_collection.get(field, {}).get('value') if isinstance(data_collection.get(field), dict) else None
            if not val:
                val = analysis.get(field, '')
            if val and str(val).lower() not in ['null', 'none', '']:
                val = str(val).strip()
                if 'riya' not in val.lower() and len(val) >= 2:
                    return val.split()[0].title() if len(val.split()) > 1 else val.title()

    # Patterns for English and Hindi
    patterns = [
        (r'(?:[Mm]y\s+name\s+is\s+|[Nn]ame\s*:?\s*|[Nn]ame\s+is\s+|[Mm]yself\s+|[Tt]his\s+is\s+|[Ii]\s+am\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'en'),
        (r'मेरा\s+नाम\s+([\u0900-\u097F\s]+?)(?:\s+है|\s+hai|\s*[,;]|$)', 'hi'),
        (r'नाम\s+([\u0900-\u097F\s]+?)(?:\s+है|\s+hai|\s*[,;]|$)', 'hi'),
        (r'(?:[Mm]era\s+[Nn]aam\s+|[Mm]era\s+naam\s+)([A-Za-z\s]+?)(?:\s+hai|\s+hai|\s*[,;]|$)', 'en'),
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s*,?\s*[6-9]\d{9}', 'en'),
    ]
    for pat, lang in patterns:
        matches = re.findall(pat, text)
        for m in matches:
            name = m.strip().split()[0]
            if lang == 'en':
                name = name.title()
            if len(name) >= 2 and len(name) <= 20 and name.lower() not in FALSE_NAMES:
                if lang == 'hi' or re.match(r'^[A-Za-z\u0900-\u097F\s\.]+$', name):
                    return name
    return ''


def process_conversation(conv, save_to_db=True):
    """Fetch detail, extract data, save to DB. Returns dict of extracted fields."""
    conv_id = conv['conversation_id']
    date = conv.get('date', 'unknown')
    start_ts = conv.get('start_time_unix_secs', 0)
    end_ts = conv.get('end_time_unix_secs', 0)
    start_time = datetime.fromtimestamp(start_ts).isoformat() if start_ts else ''
    end_time = datetime.fromtimestamp(end_ts).isoformat() if end_ts else ''

    try:
        detail = fetch_detail(conv_id)
    except Exception as e:
        log(f"  ERROR fetching detail {conv_id}: {e}")
        return None

    transcript_list = detail.get('transcript', [])
    analysis = detail.get('analysis', {})
    metadata = detail.get('metadata', {})

    transcript_lines = []
    user_text = ""
    for msg in transcript_list:
        role = msg.get('role', 'unknown')
        text = msg.get('message', '') or msg.get('original_message', '') or ''
        if text:
            transcript_lines.append(f"[{role.upper()}]: {text}")
        if role == 'user':
            user_text += " " + text

    full_transcript = "\n".join(transcript_lines)

    phone = extract_phone_from_text(user_text)
    name = extract_name_from_text(user_text, analysis)
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', user_text)
    email = emails[0] if emails else ''

    summary_title = (conv.get('call_summary_title', '')
                     or (analysis.get('call_summary_title', '') if isinstance(analysis, dict) else '')
                     or '')
    summary = (analysis.get('transcript_summary', '') or analysis.get('call_summary', '')
               if isinstance(analysis, dict) else '')
    if not summary:
        summary = summary_title

    status = detail.get('status', '') or conv.get('status', '')
    duration = detail.get('call_duration_secs', 0) or conv.get('call_duration_secs', 0)

    if save_to_db:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO conversations
            (conversation_id, agent_id, date, start_time, end_time, duration_secs,
             status, call_summary_title, call_summary, client_name, client_phone,
             client_email, transcript, transcript_json, analysis_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (conv_id, AGENT_ID, date, start_time, end_time, duration, status,
              summary_title, summary, name, phone, email, full_transcript,
              json.dumps(transcript_list, ensure_ascii=False),
              json.dumps(analysis, ensure_ascii=False) if analysis else '{}',
              json.dumps(metadata, ensure_ascii=False) if metadata else '{}'))
        conn.commit()
        conn.close()

    return {
        'conversation_id': conv_id,
        'date': date,
        'name': name,
        'phone': phone,
        'email': email,
        'title': summary_title or 'RupeeBoss Loan Inquiry',
        'summary': summary or summary_title or 'Lead from conversation',
        'transcript': full_transcript,
        'duration': duration,
        'message_count': len(transcript_list),
    }


def sync_conversations():
    init_db()
    existing_ids = get_existing_ids()
    log(f"Existing conversations in DB: {len(existing_ids)}")

    all_convs = fetch_conversation_list()
    new_convs = [c for c in all_convs if c['conversation_id'] not in existing_ids]
    log(f"New to sync: {len(new_convs)}")

    if not new_convs:
        log("No new conversations to sync.")
        return all_convs

    success = 0
    failed = 0
    batch_size = 10
    for batch_start in range(0, len(new_convs), batch_size):
        batch = new_convs[batch_start:batch_start + batch_size]
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(process_conversation, c): c for c in batch}
            for future in as_completed(futures):
                if future.result():
                    success += 1
                else:
                    failed += 1
        processed = min(batch_start + batch_size, len(new_convs))
        log(f"  Processed {processed}/{len(new_convs)}... Saved: {success}, Failed: {failed}")
        if processed < len(new_convs):
            time.sleep(1)

    log(f"Sync complete. New saved: {success}, failed: {failed}")
    return all_convs


def rebuild_from_db():
    """Rebuild leads.csv and dashboard_data.json from DB."""
    log("Rebuilding dashboard from DB...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT conversation_id, date, call_summary_title, call_summary,
               client_name, client_phone, client_email, transcript, duration_secs
        FROM conversations
        ORDER BY date DESC, start_time DESC
    ''')

    leads = []
    seen_phones = set()
    idx = 0
    for row in c.fetchall():
        conv_id, date, title, summary, name, phone, email, transcript, duration = row
        idx += 1

        # Deduplicate by phone when phone exists
        if phone:
            if phone in seen_phones:
                continue
            seen_phones.add(phone)

        has_name = name and name.lower() not in ['', 'unknown']
        has_phone = bool(phone)
        has_transcript = bool(transcript and len(transcript) > 100)

        if has_name and has_phone and has_transcript:
            category = "HOT"
        elif has_phone or (has_name and has_transcript):
            category = "WARM"
        else:
            category = "COLD"

        leads.append({
            "id": f"rb_{idx:04d}",
            "name": name or "Unknown",
            "phone": phone or "",
            "email": email or "",
            "title": title or "RupeeBoss Loan Inquiry",
            "summary": summary or title or f"Lead from {date}",
            "transcript": transcript or "[No transcript available]",
            "date": date,
            "category": category,
            "conversation_id": conv_id,
            "duration": duration or 0,
            "message_count": transcript.count('\n') if transcript else 0
        })
    conn.close()

    # Write leads.csv
    with open(f'{BASE_DIR}/leads.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Email', 'Phone', 'Date', 'Summary'])
        for lead in leads:
            writer.writerow([lead['name'], lead['email'], lead['phone'], lead['date'], lead['summary']])

    # Write dashboard_data.json
    dashboard = {
        "lastUpdated": datetime.now().isoformat(),
        "metadata": {
            "totalLeads": len(leads),
            "lastUpdated": datetime.now().isoformat(),
            "source": "Complete Rebuild (DB-backed)",
            "agentId": AGENT_ID
        },
        "leads": leads
    }
    with open(f'{BASE_DIR}/public/dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)

    hot = sum(1 for l in leads if l['category'] == 'HOT')
    warm = sum(1 for l in leads if l['category'] == 'WARM')
    cold = sum(1 for l in leads if l['category'] == 'COLD')
    log(f"Dashboard rebuilt: {len(leads)} leads ({hot} HOT, {warm} WARM, {cold} COLD)")
    return leads


def main():
    log("=" * 60)
    log("COMPLETE RUPEEBOSS CRM REBUILD")
    log("=" * 60)
    sync_conversations()
    leads = rebuild_from_db()

    log("\nSample leads:")
    for lead in leads[:5]:
        log(f"  {lead['date']} | {lead['phone'] or 'N/A':<12} | {lead['name']:<12} | {lead['title'][:50]}")

    log("\n✅ Complete rebuild finished!")


if __name__ == '__main__':
    main()
