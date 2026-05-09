#!/usr/bin/env python3
"""
Generate clean dashboard_data.json for Rupeeboss CRM
"""

import json
import pandas as pd

# Read the clean leads data
df = pd.read_csv('/root/.openclaw/workspace/rupeeboss/crm_leads.csv')

# Convert to the format expected by the CRM
leads = []
for _, row in df.iterrows():
    lead = {
        "id": row['id'],
        "source_conversation": row['source_conversation'],
        "date": row['date'],
        "name": row['name'],
        "phone": row['phone'],
        "email": row['email'],
        "title": row['title'],
        "category": row['category'],
        "status": row['status'],
        "summary": row['summary'],
        "transcript": row['transcript'],
        "notes": row['notes'],
        "documents": json.loads(row['documents']) if isinstance(row['documents'], str) and row['documents'] else []
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

# Save
with open('/root/.openclaw/workspace/rupeeboss/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ Generated dashboard_data.json with {len(leads)} leads")
print(f"  HOT: {output['metadata']['hot']}")
print(f"  COLD: {output['metadata']['cold']}")
