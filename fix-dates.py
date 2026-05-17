#!/usr/bin/env python3
"""Fix all lead dates in dashboard_data.json to today's date"""
import json
from datetime import datetime

def fix_dates():
    dashboard_path = "/root/.openclaw/workspace/rupeeboss/public/dashboard_data.json"
    
    # Read existing dashboard data
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Update all lead dates
    updated_count = 0
    for lead in dashboard['leads']:
        if lead.get('date') == '2026-05-15':
            lead['date'] = today
            updated_count += 1
    
    # Update metadata
    dashboard['metadata']['lastUpdated'] = datetime.now().isoformat()
    
    # Write updated dashboard
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"✅ Updated {updated_count} leads with date: {today}")
    print(f"📊 Total leads: {len(dashboard['leads'])}")

if __name__ == "__main__":
    fix_dates()
