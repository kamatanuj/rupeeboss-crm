#!/usr/bin/env python3
"""
Upload ALL knowledge base documents to ElevenLabs and attach to agent gKNyAo0UhrdRiQ7FAWVZ
"""

import urllib.request
import json
import os

KEY = os.popen('grep ELEVENLABS_API_KEY /root/.openclaw/workspace/rupeeboss/.env | head -1 | cut -d= -f2').read().strip()
AGENT = 'gKNyAo0UhrdRiQ7FAWVZ'
KB_DIR = '/root/.openclaw/workspace/rupeeboss/knowledge_base'

print(f"Key: {KEY[:10]}...")
print(f"Agent: {AGENT}")

FILES = [
    ('01_customer_faq.txt', 'RupeeBoss Customer FAQ', 'Real customer Q&A from 2073 conversations'),
    ('02_loan_types_guide.txt', 'RupeeBoss Loan Products Guide', 'Home, Business, Personal, Startup, Machinery loan details'),
    ('03_agent_best_practices.txt', 'RupeeBoss Agent Best Practices', 'Successful conversation patterns and guidelines'),
    ('04_repeat_customers.txt', 'RupeeBoss Repeat Customers', 'Customer call history patterns')
]

uploaded_ids = []

for filename, name, desc in FILES:
    filepath = f'{KB_DIR}/{filename}'
    size = os.path.getsize(filepath)
    print(f"\n[{len(uploaded_ids)+1}/4] Uploading: {name} ({size:,} bytes)")
    
    req = urllib.request.Request(
        'https://api.elevenlabs.io/v1/convai/knowledge-base',
        data=open(filepath, 'rb').read(),
        headers={
            'xi-api-key': KEY,
            'Content-Type': 'text/plain'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            kb_id = data.get('id')
            uploaded_ids.append(kb_id)
            print(f"  ✅ Success! ID: {kb_id}")
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"  ❌ Failed: {e.code} - {error[:200]}")

# Attach to agent
print(f"\n[5/5] Attaching {len(uploaded_ids)} documents to agent...")

# Get current agent config
req = urllib.request.Request(
    f'https://api.elevenlabs.io/v1/convai/agents/{AGENT}',
    headers={'xi-api-key': KEY}
)
with urllib.request.urlopen(req) as resp:
    agent_data = json.loads(resp.read())

# Build patch payload - add knowledge base references
kb_refs = [{"id": kb_id, "type": "file"} for kb_id in uploaded_ids]

patch_payload = {
    "conversation_config": {
        "agent": {
            "knowledge_base": kb_refs
        }
    }
}

req = urllib.request.Request(
    f'https://api.elevenlabs.io/v1/convai/agents/{AGENT}',
    data=json.dumps(patch_payload).encode(),
    headers={
        'xi-api-key': KEY,
        'Content-Type': 'application/json'
    },
    method='PATCH'
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        print(f"\n✅ Agent updated successfully!")
        print(f"Knowledge base attached: {len(kb_refs)} documents")
        
        # Verify
        kb_list = result.get('conversation_config', {}).get('agent', {}).get('knowledge_base', [])
        print(f"\n📚 Documents now in knowledge base:")
        for item in kb_list:
            print(f"  - {item.get('name', 'N/A')} ({item.get('id', 'N/A')})")
        
        # Save IDs for reference
        with open(f'{KB_DIR}/kb_ids.json', 'w') as f:
            json.dump({"agent_id": AGENT, "kb_ids": uploaded_ids, "files": FILES}, f, indent=2)
        print(f"\n💾 IDs saved to {KB_DIR}/kb_ids.json")
        
except urllib.error.HTTPError as e:
    print(f"❌ Failed to attach KB: {e.code} - {e.read().decode()[:300]}")

print("\n" + "="*60)
print("UPLOAD COMPLETE")
print("="*60)
