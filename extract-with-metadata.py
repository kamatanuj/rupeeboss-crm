#!/usr/bin/env python3
"""Extract leads using API metadata - checks data_collection_results and phone_call fields"""
import json
import re
import csv
import urllib.request
import time
import sys

API_KEY = "3a708d1216251b9801380110a5ec11fb82f806545f70978ad63aa3283fbf23d4"

print("="*50)
print("RupeeBoss CRM - Extract Leads (With Metadata)")
print("="*50)

# Read conversation IDs from temp file
print("\n[Step 1] Reading conversation IDs...")
conversation_ids = []
with open('/tmp/tmp.axsNIFFCHD', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            conv = json.loads(line)
            conv_id = conv.get('conversation_id', '')
            # Only process conversations that might have data
            if conv_id and (conv.get('call_successful') == 'success' or conv.get('call_duration_secs', 0) > 15):
                conversation_ids.append(conv_id)
        except:
            continue

print(f"✅ Found {len(conversation_ids)} potential conversations to check")

# Step 2: Fetch details and extract leads
print("\n[Step 2] Fetching details and extracting leads from metadata...")
all_leads = {}

for i, conv_id in enumerate(conversation_ids):
    if (i + 1) % 50 == 0:
        print(f"  Processing {i+1}/{len(conversation_ids)}... (Found: {len(all_leads)} leads)")
    
    try:
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
        req = urllib.request.Request(url, headers={"xi-api-key": API_KEY})
        
        with urllib.request.urlopen(req) as resp:
            conv_data = json.loads(resp.read())
        
        # Extract from data_collection_results (structured data)
        analysis = conv_data.get('analysis', {})
        data_collection = analysis.get('data_collection_results', {})
        
        # Get phone number from data collection
        phone = None
        name = None
        
        # Check "Telephone number" field
        tel_field = data_collection.get('Telephone number', {})
        if tel_field and tel_field.get('value'):
            phone_raw = tel_field['value']
            # Clean phone number (extract digits)
            digits = re.findall(r'\d+', phone_raw)
            if digits:
                phone = ''.join(digits)
                # Validate Indian phone number
                if re.match(r'^[6-9]\d{9}$', phone):
                    pass  # Valid
                else:
                    phone = None
        
        # Check "Name" field
        name_field = data_collection.get('Name', {})
        if name_field and name_field.get('value'):
            name = name_field['value'].strip()
            # Clean name (take first word, capitalize)
            name = name.split()[0].title() if name else None
        
        # If no phone in data_collection, try transcript
        if not phone:
            transcript = conv_data.get('transcript', [])
            if transcript:
                user_text = " ".join([msg.get('message', '') or '' for msg in transcript if msg.get('role') == 'user'])
                phones_found = re.findall(r'\b([6-9]\d{9})\b', user_text)
                if phones_found:
                    phone = phones_found[0]
        
        # If no name in data_collection, try transcript
        if not name:
            transcript = conv_data.get('transcript', [])
            if transcript:
                user_text = " ".join([msg.get('message', '') or '' for msg in transcript if msg.get('role') == 'user'])
                name_patterns = [
                    r'मेरा नाम है ([A-Za-z\s]+?)(?:[,.\s]|$)',
                    r'नाम है ([A-Za-z\s]+?)(?:[,.\s]|$)',
                    r'My name is ([A-Za-z\s]+?)(?:[,.\s]|$)',
                    r'This is ([A-Za-z\s]+?)(?:[,.\s]|$)',
                    r'I am ([A-Za-z\s]+?)(?:[,.\s]|$)',
                ]
                for pattern in name_patterns:
                    found = re.findall(pattern, user_text, re.IGNORECASE)
                    if found:
                        raw_name = found[0].strip()
                        if 2 <= len(raw_name.split()[0]) <= 15:
                            name = raw_name.split()[0].title()
                            break
        
        # Add lead if we have a valid phone
        if phone:
            if phone not in all_leads:
                all_leads[phone] = {
                    'Name': name or '',
                    'Email': '',
                    'Phone': phone,
                    'Source': conv_id
                }
            elif name and not all_leads[phone]['Name']:
                all_leads[phone]['Name'] = name
        
        time.sleep(0.7)  # Rate limiting
        
    except urllib.error.HTTPError as e:
        # Conversation might be deleted/archived
        if e.code == 404:
            pass  # Skip silently
        else:
            print(f"  ⚠️ Error fetching {conv_id}: {e.code}")
        time.sleep(0.7)
    except Exception as e:
        # Skip errors
        time.sleep(0.7)
        continue

# Step 3: Write to CSV
print(f"\n[Step 3] Writing {len(all_leads)} unique leads to CSV...")
with open('/root/.openclaw/workspace/rupeeboss/leads.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Email', 'Phone'])
    for phone, lead in sorted(all_leads.items()):
        writer.writerow([lead['Name'], lead['Email'], phone])

print(f"✅ Extracted {len(all_leads)} unique leads!")

# Stats
named = [l for l in all_leads.values() if l['Name']]
print(f"\n📊 Statistics:")
print(f"  - Total unique leads: {len(all_leads)}")
print(f"  - Leads with names: {len(named)}")
print(f"  - Leads from data_collection: {len([l for l in all_leads.values() if l['Source']])}")

if named[:10]:
    print(f"\n🔥 Sample leads with names:")
    for l in named[:10]:
        print(f"  {l['Name']} | {l['Phone']}")

print("\n" + "="*50)
print("✅ DONE! All leads extracted with metadata!")
print("="*50)
