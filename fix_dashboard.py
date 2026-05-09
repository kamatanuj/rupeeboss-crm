#!/usr/bin/env python3
"""
Generate clean dashboard_data.json for Rupeeboss CRM
- Fix NaN values
- Proper JSON format
"""

import json
import pandas as pd
import numpy as np

# Read the clean leads data
df = pd.read_csv('/root/.openclaw/workspace/rupeeboss/crm_leads.csv')

# Convert to the format expected by the CRM
leads = []
for _, row in df.iterrows():
    # Handle NaN values properly
    phone = str(int(row['phone'])) if pd.notna(row['phone']) else ''
    email = str(row['email']) if pd.notna(row['email']) else ''
    notes = str(row['notes']) if pd.notna(row['notes']) else ''
    
    lead = {
        "id": str(row['id']),
        "source_conversation": str(row['source_conversation']),
        "date": str(row['date']),
        "name": str(row['name']),
        "phone": phone,
        "email": email,
        "title": str(row['title']),
        "category": str(row['category']),
        "status": str(row['status']),
        "summary": str(row['summary']),
        "transcript": str(row['transcript']),
        "notes": notes,
        "documents": []
    }
    leads.append(lead)

# Build the dashboard data
output = {
    "leads": leads,
    "metadata": {
        "total": len(leads),
        "hot": len(df[df['category'] == 'HOT']),
        "cold": len(df[df['category'] == 'COLD']),
        "generated_at": "2026-05-09"
    }
}

# Save with proper JSON formatting
with open('/root/.openclaw/workspace/rupeeboss/public/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ Generated dashboard_data.json with {len(leads)} leads")
print(f"  HOT: {output['metadata']['hot']}")
print(f"  COLD: {output['metadata']['cold']}")

# Verify it's valid JSON
with open('/root/.openclaw/workspace/rupeeboss/public/dashboard_data.json', 'r') as f:
    verify = json.load(f)
    print(f"\n✓ Valid JSON confirmed")
    print(f"  First lead ID: {verify['leads'][0]['id']}")
    print(f"  First lead name: {verify['leads'][0]['name']}")
    print(f"  First lead category: {verify['leads'][0]['category']}")
