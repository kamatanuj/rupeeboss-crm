import json
import urllib.request
import os

KEY = os.getenv('ELEVENLABS_API_KEY', '')
AGENT_ID = 'gKNyAo0UhrdRiQ7FAWVZ'

if not KEY:
    # Fallback: try reading from .env
    try:
        with open('/root/.openclaw/workspace/rupeeboss/.env') as f:
            for line in f:
                if line.startswith('ELEVENLABS_API_KEY='):
                    KEY = line.strip().split('=', 1)[1]
    except:
        pass

print(f"Key loaded: {KEY[:10]}...")

# Check agent details
req = urllib.request.Request(
    f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}",
    headers={"xi-api-key": KEY}
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

# Check knowledge base
agent_cfg = data.get('conversation_config', {}).get('agent', {})
kb = agent_cfg.get('knowledge_base', [])

print(f"\nAgent: {data.get('name', 'Unknown')}")
print(f"Knowledge base entries: {len(kb)}")

if kb:
    for item in kb:
        print(f"  - ID: {item.get('id', 'N/A')} | Name: {item.get('name', 'N/A')} | Type: {item.get('type', 'N/A')}")
else:
    print("  No knowledge base documents attached.")

# Check if there are prompt/instructions
prompt = agent_cfg.get('prompt', '')
print(f"\nSystem prompt length: {len(prompt)} chars")
print(f"First 200 chars: {prompt[:200]}")
