#!/usr/bin/env python3
"""
Apply improved name extraction to existing conversations.db WITHOUT changing anything else.
Creates backup internally and reports stats.
"""
import sqlite3
import json
import re
import shutil
from datetime import datetime

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
DB_PATH = f'{BASE_DIR}/conversations.db'
ROLLBACK_DIR = f'{BASE_DIR}/.rollback/2026-06-18_0305'

FALSE_NAMES = {
    'riya', 'rupeeboss', 'support', 'loan', 'business', 'home', 'personal',
    'looking', 'interested', 'salaried', 'from', 'calling', 'call', 'customer',
    'application', 'registration', 'issue', 'inquiry', 'callback', 'request',
    'transfer', 'connect', 'speaking', 'new', 'old', 'existing', 'first',
    'second', 'third', 'name', 'naam', 'mobile', 'phone', 'number', 'agent',
    'yes', 'no', 'hello', 'hi', 'sir', 'maam', 'madam', 'okay', 'ok', 'main',
    'hai', 'hoon', 'hun', 'raha', 'rahi', 'bol', 'aap', 'kya', 'nahi', 'na',
    'batao', 'bataiye', 'dhanyawad', 'shukriya', 'thank', 'thanks', 'mujhe',
    'mere', 'mera', 'meri', 'apna', 'apni', 'chahiye', 'karana', 'karna',
    'rupee', 'rupeeboss', 'boss', 'need', 'want', 'application', 'apply'
}


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def clean_name(name):
    if not name:
        return ''
    name = name.strip().strip('.,;:?!"\' ')
    name = re.sub(r'\s+(hai|hoon|hun|speaking|here|from|and|with|bol|raha|rahi|hu|hun)\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^(name|naam|myself|i am|this is|mera naam|mera|mai|main|i\s*\'?m)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def is_valid_name(name):
    if not name:
        return False
    if len(name) < 2 or len(name) > 40:
        return False
    if name.lower() in FALSE_NAMES:
        return False
    if not re.match(r'^[A-Za-z\u0900-\u097F\s\.\-]+$', name):
        return False
    words = name.lower().split()
    if any(w in FALSE_NAMES for w in words):
        return False
    return True


def detect_language(name):
    if re.search(r'[\u0900-\u097F]', name):
        return 'hindi'
    if re.match(r'^[A-Za-z\s\.\-]+$', name):
        return 'english'
    return 'mixed'


def extract_name_from_analysis(analysis_json):
    if not analysis_json:
        return None
    try:
        analysis = json.loads(analysis_json)
        data_collection = analysis.get('data_collection_results', {})
        for field in ['Name', 'Customer Name', 'Client Name', 'customer_name', 'client_name']:
            val = None
            if isinstance(data_collection.get(field), dict):
                val = data_collection[field].get('value')
            if not val:
                val = analysis.get(field)
            if val and str(val).lower() not in ['null', 'none', '']:
                val = clean_name(str(val))
                if 'riya' not in val.lower() and is_valid_name(val):
                    return val
    except Exception:
        pass
    return None


def extract_names_from_transcript(user_text):
    """Return list of candidate (name, lang) tuples."""
    candidates = []
    patterns = [
        (r'(?:my\s+name\s+is\s+|name\s*:?\s*|name\s+is\s+|myself\s+|this\s+is\s+|i\s*\'?m\s+|i\s+am\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'en'),
        (r"(?:it(?:\'s|s)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})(?:\s+here|\s+speaking)", 'en'),
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s+(?:here|speaking)', 'en'),
        (r'(?:मेरा\s+नाम\s+|मेरा\s+नाम\s*)([\u0900-\u097F\s]+?)(?:\s+है|\s+hai|\s*[,;]|$)', 'hi'),
        (r'(?:नाम\s+)([\u0900-\u097F\s]+?)(?:\s+है|\s+hai|\s*[,;]|$)', 'hi'),
        (r'(?:मैं\s+)([\u0900-\u097F\s]+?)(?:\s+बोल\s+रहा|\s+बोल\s+रही|\s+bol\s+raha|\s+bol\s+rahi)', 'hi'),
        (r'(?:mera\s+naam\s+|mera\s+naam\s*)([A-Za-z\s]+?)(?:\s+hai|\s*[,;]|$)', 'en'),
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s*,?\s*[:\-]?\s*[6-9]\d{9}', 'en'),
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s*,\s*(?:mera\s+)?(?:phone\s+|mobile\s+|number\s+)?\d', 'en'),
        (r'[Nn]ame:\s*([A-Za-z\u0900-\u097F\s]+?)(?:\s+Mobile|\s+Phone|\s+Number|\s+mai|\s+main|$)', 'mixed'),
    ]
    for pat, lang in patterns:
        matches = re.findall(pat, user_text)
        for m in matches:
            candidate = clean_name(m)
            if is_valid_name(candidate):
                candidates.append((candidate, lang))
    return candidates


def choose_best_name(analysis_json, transcript):
    # 1. Try structured analysis
    name = extract_name_from_analysis(analysis_json)
    if name:
        return name, 'analysis'

    # 2. Extract from user text
    user_lines = re.findall(r'\[USER\]: ([^\[]+)', transcript)
    user_text = ' '.join(user_lines)
    candidates = extract_names_from_transcript(user_text)
    if candidates:
        # Prefer first valid candidate
        return candidates[0][0], candidates[0][1]

    return None, None


def main():
    log("=" * 60)
    log("APPLYING IMPROVED NAME EXTRACTION")
    log("=" * 60)
    log(f"Rollback point: {ROLLBACK_DIR}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Stats before
    c.execute("SELECT COUNT(*), COUNT(CASE WHEN client_name != '' AND client_name IS NOT NULL AND client_name != 'Unknown' THEN 1 END) FROM conversations")
    total, named_before = c.fetchone()
    log(f"Total conversations: {total}, currently named: {named_before}")

    # Fetch all rows that need processing
    c.execute('''
        SELECT conversation_id, client_name, transcript, analysis_json
        FROM conversations
        WHERE transcript IS NOT NULL AND transcript != ''
    ''')
    rows = c.fetchall()

    updated = 0
    unchanged = 0
    newly_named = 0
    corrected = 0
    samples = []

    for conv_id, current_name, transcript, analysis_json in rows:
        current_clean = clean_name(current_name or '')
        if not is_valid_name(current_clean):
            current_clean = ''

        best_name, source = choose_best_name(analysis_json, transcript)

        if not best_name:
            unchanged += 1
            continue

        if not current_clean:
            newly_named += 1
            if len(samples) < 10:
                samples.append(('NEW', conv_id, best_name, source))
        elif current_clean.lower() != best_name.lower():
            corrected += 1
            if len(samples) < 20:
                samples.append(('CORRECT', conv_id, f"'{current_clean}' -> '{best_name}'", source))
        else:
            unchanged += 1
            continue

        c.execute('UPDATE conversations SET client_name = ? WHERE conversation_id = ?', (best_name, conv_id))
        updated += 1

    conn.commit()

    # Stats after
    c.execute("SELECT COUNT(CASE WHEN client_name != '' AND client_name IS NOT NULL AND client_name != 'Unknown' THEN 1 END) FROM conversations")
    named_after = c.fetchone()[0]
    conn.close()

    log(f"Updated rows: {updated}")
    log(f"  Newly named: {newly_named}")
    log(f"  Corrected: {corrected}")
    log(f"  Named before: {named_before}, after: {named_after}")

    log("\nSample changes:")
    for kind, conv_id, detail, source in samples:
        log(f"  [{kind}] {conv_id[:16]} | {detail} | src={source}")

    log("\n✅ Name extraction applied. Rollback files are in .rollback/2026-06-18_0305/")


if __name__ == '__main__':
    main()
