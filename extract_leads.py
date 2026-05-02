import pandas as pd
import re

df = pd.read_csv('rupeeboss_leads.csv', low_memory=False)

# Focus on user messages - they're more likely to have caller info
user_msgs = df[df['role'] == 'user']['message'].dropna().unique()
print(f"Total unique user messages: {len(user_msgs)}")

leads = {}

# Patterns to extract name and phone from messages
for msg in user_msgs:
    msg = str(msg)
    
    # Extract phone numbers (10 digits starting with 6-9)
    phones = re.findall(r'\b[6-9]\d{9}\b', msg)
    
    # Try to extract names - look for patterns before or around phone numbers
    # Common pattern: "my name is X" or "I am X" or "this is X"
    name_patterns = [
        r'(?:name is|named?|this is|my name\'s|i\'m|here\'s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:here|calling|from)',  # "Name here" or "Name calling"
    ]
    
    name = None
    for pattern in name_patterns:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            name = match.group(1).title()
            break
    
    for phone in phones:
        if phone not in leads:
            leads[phone] = {'name': name or 'Unknown', 'phone': phone}
        elif name and leads[phone]['name'] == 'Unknown':
            leads[phone]['name'] = name

# Also check transcript summaries for names when missing
summaries = df['transcript_summary'].dropna().unique()
for s in summaries:
    # Find phone and corresponding name in the summary
    phones = re.findall(r'\b[6-9]\d{9}\b', str(s))
    
    # Look for name pattern: "The user, Name" or "user Name" or "called/calling Name"
    name_match = re.search(r'(?:user|called|calling)[\s,]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', str(s))
    if name_match:
        name = name_match.group(1).title()
        for phone in phones:
            if phone in leads and leads[phone]['name'] == 'Unknown':
                leads[phone]['name'] = name

print(f"\nExtracted {len(leads)} unique leads")

# Convert to DataFrame and sort
leads_df = pd.DataFrame(list(leads.values()))
leads_df = leads_df.sort_values('name').reset_index(drop=True)

# Remove duplicates
leads_df = leads_df.drop_duplicates(subset='phone')

print("\nAll leads:")
print(leads_df.to_string())

# Save
leads_df.to_csv('leads.csv', index=False)
print(f"\nSaved {len(leads_df)} leads to leads.csv")