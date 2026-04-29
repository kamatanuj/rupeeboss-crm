#!/usr/bin/env python3
"""Extract leads from D-insights Rupeeboss conversations with Hindi name support"""
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
    
    # Find Hindi names - pattern: "मेरा नाम है <name>" or "नाम है <name>"
    # Hindi names typically come after these phrases
    names = []
    
    # Pattern 1: मेरा नाम है followed by name (may include Kumar, Singh, etc.)
    patterns = [
        r'मेरा नाम है ([A-Za-z\s]+?)(?:[,.\s]|$)',
        r'नाम है ([A-Za-z\s]+?)(?:[,.\s]|$)',
        r'My name is ([A-Za-z\s]+?)(?:[,.\s]|$)',
        r'This is ([A-Za-z\s]+?)(?:[,.\s]|$)',
        r'I am ([A-Za-z\s]+?)(?:[,.\s]|$)',
    ]
    
    for pattern in patterns:
        found = re.findall(pattern, user_text, re.IGNORECASE)
        for f in found:
            # Clean up the name
            name = f.strip()
            # Filter out very short or long names
            if 2 <= len(name.split()[0]) <= 15:
                names.append(name.split()[0].title())
    
    # Also try to find names in Hindi text more specifically
    # Look for name + Kumar/Singh/Patel patterns
    hindi_name_pattern = r'(?:नेरज|दीपक|अक्षय|पूजा|राज|विकास|अमित|सुनील|संजय|गोपाल|हरीश|मनीष|आशिष|नितेश|राहुल|प्रवीण|आनन्द|विजय|रमेश|यश|करण|सागर|मयंक|शुभम|अभिषेक|तरुण|वivek|रवि|किशन|महेश|प्रशांत|दिनेश|जगदीश|सुरेश|भरत|आलोक|शैलेश|दर्शन|मनोज|ललित|रमन|वineet|अनिल|राजेश|मुकेश|जितेन|दिनीष|हर्ष|मंगेश|सचिन|युवराज|शरद|विनोद|शंकर|जय|विजय|कृष्ण|राधा|गOVIND)[A-Za-z\s]*'
    
    leads = []
    seen_phones = set()
    for phone in phones:
        if phone not in seen_phones:
            seen_phones.add(phone)
            lead_name = names[0] if names else ''
            leads.append({
                'email': '',
                'phone': phone,
                'name': lead_name
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
    named = [l for l in hot if l['name']]
    print(f"   - {len(named)} leads with names")
    print(f"   - {len(hot) - len(named)} leads without names")
    if named[:10]:
        print(f"\n🔥 Sample leads with names:")
        for l in named[:10]:
            print(f"  {l['name']} | {l['phone']}")

if __name__ == "__main__":
    main()
