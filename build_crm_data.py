#!/usr/bin/env python3
"""
Build clean Rupeeboss CRM data from parsed leads.
- Map source conversation IDs to simple lead IDs
- Categorize: HOT (has name + phone), COLD (phone only, no real name)
- Use summaries and transcripts from original data
"""

import pandas as pd
import json
import re
from datetime import datetime

print("=" * 80)
print("BUILDING CLEAN RUPEEBOSS CRM DATA")
print("=" * 80)

# Read the parsed leads
df = pd.read_csv('/root/.openclaw/workspace/rupeeboss/fresh_parsed_leads.csv')
print(f"Loaded {len(df)} parsed leads")

# Read original CSV to get full transcripts
print("Loading original data for transcripts...")
original = pd.read_csv('/root/.openclaw/workspace/rupeeboss/rupeeboss_leads.csv', 
                         low_memory=False, on_bad_lines='skip')
print(f"Loaded {len(original)} original rows")

# Noise names to treat as Unknown
noise_names = [
    'riya from rupeeboss support', 'riya from rupeeboss', 'riya',
    'from lucknow', 'sorry', 'ready', 'sir', 'the new', 'not aware',
    'one more question yes madam', 'fresher', 'interested', 'slowly',
    'going to call number', 'working as cleaning housekeeping',
    'and number', 'and cell phone number', 'an agent', 'out',
    'still here', 'more effective in english', 'seeking for cgtmse loan of',
    'the first year of my business and my annual turnover is',
    'skybridge inzicon private limited',  # company name, not person
    'avc',  # company abbreviation
]

# Clean up names
def clean_name(name):
    if pd.isna(name) or str(name).strip() == '' or str(name).strip().lower() == 'unknown':
        return None
    
    name_lower = str(name).strip().lower()
    
    # Check if it's noise
    for noise in noise_names:
        if noise in name_lower or name_lower in noise:
            return None
    
    # Clean up the name
    clean = str(name).strip().title()
    
    # Remove trailing junk
    clean = re.sub(r'\s+(and|my|from|the|is|\d+)$', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+(and\s+my\s+.*|my\s+.*|cell\s+.*|phone\s+.*)$', '', clean, flags=re.IGNORECASE)
    
    if len(clean) < 2:
        return None
    
    return clean

# Process each lead
clean_leads = []
lead_counter = 1

for idx, row in df.iterrows():
    conv_id = row['conversation_id']
    
    # Get full transcript from original data
    conv_messages = original[original['conversation_id'] == conv_id]
    
    # Build transcript
    transcript_parts = []
    for _, msg_row in conv_messages.iterrows():
        role = msg_row['role']
        msg = str(msg_row['message'])
        transcript_parts.append(f"[{role.upper()}] {msg}")
    
    full_transcript = '\n'.join(transcript_parts)
    
    # Clean name
    raw_name = row['name']
    clean_name_val = clean_name(raw_name)
    
    # Determine category
    has_real_name = clean_name_val is not None
    has_phone = pd.notna(row['phone']) and str(row['phone']).strip() != ''
    
    if has_real_name and has_phone:
        category = 'HOT'
    else:
        category = 'COLD'
    
    # Generate simple lead ID
    simple_id = f"rb_{lead_counter:04d}"
    lead_counter += 1
    
    # Use current date if none available
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Build title from summary
    summary = str(row['summary']) if pd.notna(row['summary']) else ''
    if summary:
        # Extract key topic from summary
        title = summary.split('.')[0][:80] if '.' in summary else summary[:80]
    else:
        title = 'Business Loan Inquiry'
    
    lead = {
        'id': simple_id,
        'source_conversation': conv_id,
        'date': date_str,
        'name': clean_name_val if clean_name_val else 'Unknown',
        'phone': str(row['phone']) if pd.notna(row['phone']) else '',
        'email': '',  # No emails in this dataset
        'title': title,
        'category': category,
        'status': 'New',
        'summary': summary,
        'transcript': full_transcript,
        'notes': '',
        'documents': []
    }
    
    clean_leads.append(lead)

# Create DataFrame
leads_df = pd.DataFrame(clean_leads)

# Summary
hot_count = len(leads_df[leads_df['category'] == 'HOT'])
cold_count = len(leads_df[leads_df['category'] == 'COLD'])

print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}")
print(f"Total leads: {len(leads_df)}")
print(f"  🔥 HOT (Name + Phone): {hot_count}")
print(f"  ❄️ COLD (Phone only): {cold_count}")

print(f"\n{'='*80}")
print("SAMPLE HOT LEADS")
print(f"{'='*80}")
for _, lead in leads_df[leads_df['category'] == 'HOT'].head(15).iterrows():
    print(f"  {lead['id']}: {lead['name']} | {lead['phone']} | {lead['title'][:50]}")

print(f"\n{'='*80}")
print("SAMPLE COLD LEADS")
print(f"{'='*80}")
for _, lead in leads_df[leads_df['category'] == 'COLD'].head(10).iterrows():
    print(f"  {lead['id']}: {lead['phone']} | {lead['title'][:50]}")

# Save as JSON for CRM
output = {
    'leads': clean_leads,
    'metadata': {
        'total': len(clean_leads),
        'hot': hot_count,
        'cold': cold_count,
        'generated_at': datetime.now().isoformat()
    }
}

with open('/root/.openclaw/workspace/rupeeboss/crm_data.json', 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Also save as CSV for review
leads_df.to_csv('/root/.openclaw/workspace/rupeeboss/crm_leads.csv', index=False)

print(f"\n{'='*80}")
print("FILES SAVED")
print(f"{'='*80}")
print("✓ crm_data.json - Full data for CRM")
print("✓ crm_leads.csv - CSV for review")

print(f"\n{'='*80}")
print("READY TO DEPLOY")
print(f"{'='*80}")
print(f"Replace dashboard_data.json in the CRM with crm_data.json contents")
