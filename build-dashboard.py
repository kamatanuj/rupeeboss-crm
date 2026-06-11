#!/usr/bin/env python3
"""Build dashboard from real_rebuild.py output — minimal wrapper."""
import json, os

BASE_DIR = '/root/.openclaw/workspace/rupeeboss'
json_path = f'{BASE_DIR}/public/dashboard_data.json'

if not os.path.exists(json_path):
    print("ERROR: dashboard_data.json not found. Run real_rebuild.py first.")
    exit(1)

with open(json_path) as f:
    data = json.load(f)

print(f"Dashboard ready: {data['metadata']['totalLeads']} leads")
print(f"Last updated: {data['metadata']['lastUpdated']}")
