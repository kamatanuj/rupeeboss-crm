#!/usr/bin/env python3
"""
Parse rupeeboss leads.csv and extract clean list of leads with names and phone numbers.
Starting fresh - no previous data assumptions.
"""

import pandas as pd
import re

# Read the CSV file
df = pd.read_csv('/root/.openclaw/workspace/rupeeboss/leads.csv')

print("=" * 80)
print("RUPEEBOSS LEADS - FRESH PARSE")
print("=" * 80)
print(f"\nTotal rows in CSV: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst few rows:")
print(df.head(10).to_string())

# Clean up the data
print("\n" + "=" * 80)
print("CLEANING DATA")
print("=" * 80)

# Remove rows where Name is just noise words or clearly not a name
noise_words = ['sorry', 'ready', 'starting', 'the', 'and', 'from', 'an', 'agent', 'out', 'still here', 
               'more effective in english', 'working as cleaning housekeeping and vehicle hiring services and already worked at least back',
               'the business of the badanabad', 'not able to send text messages', 'seeking for cgtmse loan of',
               'the first year of my business and my annual turnover is', 'interested great', 'slowly']

# Function to check if a name is valid (not just noise)
def is_valid_name(name):
    if pd.isna(name) or str(name).strip() == '' or str(name).strip().lower() == 'unknown':
        return False
    name_lower = str(name).strip().lower()
    if name_lower in noise_words:
        return False
    # Check if it's just a phrase like "and cell phone number"
    if 'cell phone number' in name_lower or 'phone number' in name_lower:
        return False
    if 'my number' in name_lower:
        return False
    if len(name_lower) < 2:
        return False
    return True

# Function to clean up phone numbers
def clean_phone(phone):
    if pd.isna(phone):
        return None
    phone_str = str(phone).strip()
    # Remove any non-digit characters
    digits_only = re.sub(r'\D', '', phone_str)
    if len(digits_only) >= 10:
        return digits_only[-10:]  # Take last 10 digits (in case of country code)
    return None

# Apply cleaning
df['has_name'] = df['Name'].apply(is_valid_name)
df['clean_phone'] = df['Phone'].apply(clean_phone)

# Filter leads with valid phone numbers
df_valid = df[df['clean_phone'].notna()].copy()

print(f"\nLeads with valid phone numbers: {len(df_valid)}")

# Separate named vs unnamed leads
named_leads = df_valid[df_valid['has_name'] == True].copy()
unnamed_leads = df_valid[df_valid['has_name'] == False].copy()

print(f"Leads with names: {len(named_leads)}")
print(f"Leads without names (Unknown): {len(unnamed_leads)}")

print("\n" + "=" * 80)
print("LEADS WITH NAMES")
print("=" * 80)
for idx, row in named_leads.iterrows():
    print(f"Name: {row['Name']}")
    print(f"Phone: {row['clean_phone']}")
    print(f"Conversation: {row['Source Conversation']}")
    print("-" * 40)

print("\n" + "=" * 80)
print("LEADS WITHOUT NAMES (PHONE ONLY)")
print("=" * 80)
print(f"Total unnamed leads: {len(unnamed_leads)}")
for idx, row in unnamed_leads.head(20).iterrows():  # Show first 20
    print(f"Phone: {row['clean_phone']} | Conv: {row['Source Conversation']}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total leads with phone numbers: {len(df_valid)}")
print(f"  - Named leads: {len(named_leads)}")
print(f"  - Unnamed leads: {len(unnamed_leads)}")
print(f"\nNamed leads list:")
for idx, row in named_leads.iterrows():
    print(f"  ✓ {row['Name']} | {row['clean_phone']}")

print(f"\nSample unnamed leads:")
for idx, row in unnamed_leads.head(10).iterrows():
    print(f"  ? Unknown | {row['clean_phone']}")

# Save clean list
named_leads[['Name', 'clean_phone', 'Source Conversation']].to_csv('/root/.openclaw/workspace/rupeeboss/named_leads_clean.csv', index=False)
unnamed_leads[['clean_phone', 'Source Conversation']].to_csv('/root/.openclaw/workspace/rupeeboss/unnamed_leads_clean.csv', index=False)

print("\n" + "=" * 80)
print("FILES SAVED")
print("=" * 80)
print("✓ named_leads_clean.csv - Leads with names")
print("✓ unnamed_leads_clean.csv - Leads without names")
