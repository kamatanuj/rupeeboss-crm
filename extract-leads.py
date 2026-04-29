#!/usr/bin/env python3
"""Extract leads from D-insights conversations"""
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
    user_text = " ".join([msg.get('message', '') for msg in transcript if msg.get('role') == 'user'])
    emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', user_text, re.IGNORECASE)
    phones = re.findall(r'\b\d{10,12}\b', user_text)
    names = re.findall(r'(?:my name is|i am|this is|name:?)\s+([A-Za-z\s]+?)(?:,|\.|from| |$)', user_text, re.IGNORECASE)
    leads = []
    for email in emails:
        leads.append({'email': email, 'phone': phones[0] if phones else '', 'name': names[0].strip().title() if names else ''})
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
                email = lead['email'].lower()
                if email not in all_leads:
                    all_leads[email] = lead
                elif lead['phone'] and not all_leads[email]['phone']:
                    all_leads[email]['phone'] = lead['phone']
        except Exception as e:
            print(f"  Error: {e}")
            continue
    with open('/root/.openclaw/workspace/rupeeboss/leads.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Email', 'Phone', 'Source Conversation'])
        for email, lead in sorted(all_leads.items()):
            writer.writerow([lead['name'], email, lead['phone'], ''])
    print(f"\n✅ Extracted {len(all_leads)} unique leads")
    hot = [l for l in all_leads.values() if l['phone']]
    if hot:
        print(f"\n🔥 Hot leads ({len(hot)}):")
        for l in hot[:5]:
            print(f"  {l['name'] or 'N/A'} | {l['email']} | {l['phone']}")

if __name__ == "__main__":
    main()
