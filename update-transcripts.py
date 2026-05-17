#!/usr/bin/env python3
"""Update lead summaries and transcripts from rupeeboss_leads.csv"""
import json
import csv
from collections import defaultdict

def update_leads():
    # Load dashboard data
    with open('public/dashboard_data.json', 'r') as f:
        dashboard = json.load(f)
    
    # Read rupeeboss_leads.csv
    print("Loading rupeeboss_leads.csv...")
    with open('rupeeboss_leads.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Group by conversation
    conversations = defaultdict(list)
    summaries = {}
    for row in rows:
        conv_id = row['conversation_id']
        conversations[conv_id].append(row)
        if row['transcript_summary'] and row['transcript_summary'] != 'null':
            summaries[conv_id] = row['transcript_summary']
    
    print(f"Loaded {len(conversations)} conversations from CSV")
    
    # Update leads
    updated = 0
    missing = 0
    
    for lead in dashboard['leads']:
        conv_id = lead.get('source_conversation', '')
        
        if not conv_id:
            missing += 1
            continue
        
        # Find matching conversation in CSV
        if conv_id in conversations:
            messages = conversations[conv_id]
            
            # Build transcript
            transcript_lines = []
            for msg in messages:
                role = msg['role'].upper()
                message = msg['message']
                if message:
                    transcript_lines.append(f"[{role}] {message}")
            
            # Get summary
            summary = summaries.get(conv_id, '')
            
            # Update lead
            if transcript_lines:
                lead['transcript'] = '\n'.join(transcript_lines)
                updated += 1
            
            if summary:
                lead['summary'] = summary
            
            # Update title if it's generic
            if lead.get('title', '').startswith('RupeeBoss Loan Inquiry'):
                # Use first line of summary as title
                if summary:
                    lead['title'] = summary[:100]
        else:
            print(f"  ⚠️ No data for {lead['id']} (conv: {conv_id})")
            missing += 1
    
    # Write updated dashboard
    with open('public/dashboard_data.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Updated {updated} leads with transcripts")
    print(f"⚠️ Missing data: {missing} leads")
    
    # Verify a few leads
    print("\nSample updated leads:")
    for lead in dashboard['leads'][:3]:
        print(f"  {lead['id']}: {lead['summary'][:80]}...")
        print(f"    Transcript length: {len(lead.get('transcript', ''))} chars")

if __name__ == "__main__":
    update_leads()
