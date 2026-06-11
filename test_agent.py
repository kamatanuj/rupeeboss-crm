#!/usr/bin/env python3
import urllib.request
import json
import os

KEY = os.popen('grep ELEVENLABS_API_KEY /root/.openclaw/workspace/rupeeboss/.env | head -1 | cut -d= -f2').read().strip()
AGENT = 'gKNyAo0UhrdRiQ7FAWVZ'
print(f"Key: {KEY[:10]}...")

# Check agent
req = urllib.request.Request(
    f'https://api.elevenlabs.io/v1/convai/agents/{AGENT}',
    headers={'xi-api-key': KEY}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

agent_cfg = data.get('conversation_config', {}).get('agent', {})
kb = agent_cfg.get('knowledge_base', [])
print(f"Agent: {data.get('name')}")
print(f"KB entries: {len(kb)}")

for item in kb:
    print(f"  {item.get('id')}: {item.get('name')}")

prompt = agent_cfg.get('prompt', '')
print(f"Prompt type: {type(prompt)}")
if isinstance(prompt, str):
    print(f"Prompt: {len(prompt)} chars, first 100: {prompt[:100]}")
elif isinstance(prompt, dict):
    print(f"Prompt keys: {list(prompt.keys())}")
    for k, v in prompt.items():
        print(f"  {k}: {str(v)[:80]}")
else:
    print(f"Prompt: {str(prompt)[:150]}")
