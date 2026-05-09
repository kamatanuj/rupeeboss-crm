#!/usr/bin/env python3
"""
Parse the ORIGINAL rupeeboss_leads.csv (94MB) to extract:
1. Customer names from actual transcripts
2. Phone numbers
3. Create a clean leads list

This reads ALL messages per conversation to find where customers share their info.
"""

import pandas as pd
import re
import json

print("=" * 80)
print("PARSING ORIGINAL RUPEEBOSS_LEADS.CSV (94MB)")
print("=" * 80)

# Read CSV - it's large so be patient
print("\nLoading CSV... (this may take a moment)")
df = pd.read_csv('/root/.openclaw/workspace/rupeeboss/rupeeboss_leads.csv', 
                 low_memory=False, 
                 on_bad_lines='skip')

print(f"✓ Loaded {len(df):,} rows")
print(f"Columns: {list(df.columns)}")

# Show sample
print("\n" + "=" * 80)
print("SAMPLE DATA")
print("=" * 80)
print(df.head(3).to_string())

# Group by conversation to see full transcripts
print("\n" + "=" * 80)
print("GROUPING BY CONVERSATION")
print("=" * 80)

# Get unique conversations
conversations = df['conversation_id'].unique()
print(f"Total unique conversations: {len(conversations)}")

# Let's look at a few complete conversations to understand the pattern
print("\n" + "=" * 80)
print("SAMPLE CONVERSATIONS (first 3)")
print("=" * 80)

for i, conv_id in enumerate(conversations[:3]):
    conv_data = df[df['conversation_id'] == conv_id]
    print(f"\n--- Conversation {i+1}: {conv_id} ({len(conv_data)} messages) ---")
    
    for _, row in conv_data.iterrows():
        role = row['role']
        msg = str(row['message'])[:150]  # Truncate long messages
        print(f"  [{role}] {msg}")
    print()

# Now let's extract names and phones from ALL conversations
print("\n" + "=" * 80)
print("EXTRACTING LEADS FROM ALL CONVERSATIONS")
print("=" * 80)

leads = []

for conv_id in conversations:
    conv_data = df[df['conversation_id'] == conv_id]
    
    # Get all user messages
    user_messages = conv_data[conv_data['role'] == 'user']['message'].tolist()
    all_user_text = ' '.join([str(m) for m in user_messages]).lower()
    
    # Look for phone numbers (10 digits)
    phone_pattern = r'\b\d{10}\b'
    phones_found = re.findall(phone_pattern, all_user_text)
    
    # Look for name patterns
    # Common patterns: "my name is X", "this is X", "i'm X", "X here"
    name_patterns = [
        r'my name is ([a-zA-Z\s]+?)(?:\.|,|and|my|phone|number|$)',
        r'this is ([a-zA-Z\s]+?)(?:\.|,|and|my|phone|number|$)',
        r'i am ([a-zA-Z\s]+?)(?:\.|,|and|my|phone|number|$)',
        r'i\'m ([a-zA-Z\s]+?)(?:\.|,|and|my|phone|number|$)',
        r'(?:hello|hi) ([a-zA-Z\s]+?)(?:\.|,|and|my|phone|number|$)',
        r'(?:speaking|here) ([a-zA-Z\s]+?)(?:\.|,|and|my|phone|number|$)',
    ]
    
    name_found = None
    for pattern in name_patterns:
        match = re.search(pattern, all_user_text, re.IGNORECASE)
        if match:
            potential_name = match.group(1).strip()
            # Filter out noise
            if len(potential_name) > 2 and potential_name not in ['riya', 'rupeeboss', 'support']:
                name_found = potential_name.title()
                break
    
    # Get summary if available
    summary = conv_data['transcript_summary'].iloc[0] if len(conv_data) > 0 and pd.notna(conv_data['transcript_summary'].iloc[0]) else ''
    
    # Only add if phone found
    if phones_found:
        # Take the first phone number found
        phone = phones_found[0]
        
        leads.append({
            'conversation_id': conv_id,
            'name': name_found if name_found else 'Unknown',
            'phone': phone,
            'summary': summary[:200] if summary else '',
            'message_count': len(conv_data),
            'all_messages': ' | '.join([str(m)[:100] for m in user_messages[:5]])  # First 5 messages
        })

print(f"\n✓ Extracted {len(leads)} leads with phone numbers")

# Create DataFrame
leads_df = pd.DataFrame(leads)

# Separate named and unnamed
named = leads_df[leads_df['name'] != 'Unknown'].copy()
unnamed = leads_df[leads_df['name'] == 'Unknown'].copy()

print(f"\nNamed leads: {len(named)}")
print(f"Unnamed leads: {len(unnamed)}")

print("\n" + "=" * 80)
print("NAMED LEADS")
print("=" * 80)
for _, lead in named.head(30).iterrows():
    print(f"\nName: {lead['name']}")
    print(f"Phone: {lead['phone']}")
    print(f"Conv: {lead['conversation_id']}")
    if lead['summary']:
        print(f"Summary: {lead['summary'][:100]}...")
    print("-" * 60)

print("\n" + "=" * 80)
print("UNNAMED LEADS (with phones) - First 20")
print("=" * 80)
for _, lead in unnamed.head(20).iterrows():
    print(f"Phone: {lead['phone']} | Conv: {lead['conversation_id']}")
    print(f"Messages: {lead['all_messages'][:120]}...")
    print("-" * 60)

# Save results
leads_df.to_csv('/root/.openclaw/workspace/rupeeboss/fresh_parsed_leads.csv', index=False)
named.to_csv('/root/.openclaw/workspace/rupeeboss/fresh_named_leads.csv', index=False)
unnamed.to_csv('/root/.openclaw/workspace/rupeeboss/fresh_unnamed_leads.csv', index=False)

print("\n" + "=" * 80)
print("FILES SAVED")
print("=" * 80)
print("✓ fresh_parsed_leads.csv - All leads")
print("✓ fresh_named_leads.csv - Named leads only")
print("✓ fresh_unnamed_leads.csv - Unnamed leads only")

print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total conversations analyzed: {len(conversations)}")
print(f"Leads with phone numbers: {len(leads_df)}")
print(f"Named leads: {len(named)}")
print(f"Unnamed leads: {len(unnamed)}")
print(f"\nNamed lead quality: {len(named)/len(leads_df)*100:.1f}% have names")
