#!/usr/bin/env python3
"""Extract leads from D-insights Rupeeboss conversations"""
import json
import re
import csv
import urllib.request
import os

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
CONV_URL = "https://api.elevenlabs.io/v1/convai/conversations?page_size=100"

def get_conversations():
    req = urllib.request.Request(CONV_URL, headers={"xi-api-key": ELEVENLABS_API_KEY})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get('conversations', [])

def get_conversation(cid):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{cid}"
    req = urllib.request.Request(url, headers={"xi-api-key": ELEVENLABS_API_KEY})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def extract_leads_from_conversation(conv_data):
    transcript = conv_data.get('transcript', [])
    if not transcript:
        return []
    
    # Get all user messages
    user_text = " ".join([msg.get('message', '') or '' for msg in transcript if msg.get('role') == 'user'])
    
    # Find Indian phone numbers (10 digits starting with 6-9)
    phones = re.findall(r'\b([6-9]\d{9})\b', user_text)
    
    # Find names - look for patterns
    names = []
    name_patterns = [
        r'नाम[:\s]+([A-Za-z]{2,20})',
        r'My name is[:\s]+([A-Za-z]{2,20})',
        r'This is ([A-Za-z]{2,20})',
        r'I am ([A-Za-z]{2,20})',
    ]
    for pattern in name_patterns:
        found = re.findall(pattern, user_text, re.IGNORECASE)
        names.extend(found)
    
    leads = []
    seen_phones = set()
    for phone in phones:
        if phone not in seen_phones:
            seen_phones.add(phone)
            leads.append({
                'email': '',
                'phone': phone,
                'name': names[0].strip().title() if names else ''
            })
    return leads

def main():
    print("Fetching conversations...")
    conversations = get_conversations()
    print(f"Found {len(conversations)} conversations")
    
    all_leads = {}
    
    for i, conv in enumerate(conversations):
        cid = conv.get('conversation_id', '')
        if (i + 1) % 20 == 0:
            print(f"Processing {i+1}/{len(conversations)}...")
        
        try:
            conv_data = get_conversation(cid)
            leads = extract_leads_from_conversation(conv_data)
            
            for lead in leads:
                phone = lead['phone']
                if phone not in all_leads:
                    all_leads[phone] = lead
                elif lead['name'] and not all_leads[phone]['name']:
                    all_leads[phone]['name'] = lead['name']
        except Exception as e:
            continue
    
    # Write CSV
    with open('/root/.openclaw/workspace/rupeeboss/leads.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Email', 'Phone', 'Source Conversation'])
        for phone, lead in sorted(all_leads.items()):
            writer.writerow([lead['name'], lead['email'], phone, ''])
    
    print(f"\n✅ Extracted {len(all_leads)} unique leads")
    hot = [l for l in all_leads.values() if l['phone']]
    if hot[:5]:
        print(f"\n🔥 Sample hot leads:")
        for l in hot[:5]:
            print(f"  {l['name'] or 'N/A'} | {l['phone']}")

if __name__ == "__main__":
    main()
