#!/usr/bin/env python3
"""Auto-update dashboard_data.json with latest leads from leads.csv"""
import json
import csv
import os
from datetime import datetime

def update_dashboard():
    base_dir = "/root/.openclaw/workspace/rupeeboss"
    
    # Read existing dashboard data
    dashboard_path = os.path.join(base_dir, "public", "dashboard_data.json")
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    
    # Read latest leads
    leads_path = os.path.join(base_dir, "leads.csv")
    if not os.path.exists(leads_path):
        print("No leads.csv found, skipping update")
        return
    
    with open(leads_path, 'r') as f:
        reader = csv.DictReader(f)
        new_leads = list(reader)
    
    # Get existing phone numbers to avoid duplicates
    existing_phones = {lead.get('phone', '') for lead in dashboard['leads']}
    
    # Add new leads
    today = datetime.now().strftime("%Y-%m-%d")
    added = 0
    for i, lead in enumerate(new_leads):
        phone = lead.get('Phone', '')
        if phone and phone not in existing_phones:
            lead_id = f"rb_{len(dashboard['leads']) + 1:04d}"
            new_lead = {
                "id": lead_id,
                "name": lead.get('Name', 'Unknown'),
                "phone": phone,
                "email": lead.get('Email', ''),
                "title": f"RupeeBoss Loan Inquiry - {phone}",
                "summary": f"Lead extracted from conversation. Phone: {phone}",
                "transcript": "[Transcript not available - extracted from metadata]",
                "date": today,
                "category": "HOT" if lead.get('Name') else "COLD"
            }
            dashboard['leads'].append(new_lead)
            existing_phones.add(phone)
            added += 1
    
    # Update metadata
    dashboard['metadata']['lastUpdated'] = datetime.now().isoformat()
    dashboard['metadata']['totalLeads'] = len(dashboard['leads'])
    
    # Write updated dashboard
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"✅ Added {added} new leads")
    print(f"📊 Total leads: {len(dashboard['leads'])}")

if __name__ == "__main__":
    update_dashboard()
