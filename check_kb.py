#!/usr/bin/env python3
import urllib.request
import json
import os

# Load key from env or .env
KEY = os.getenv('ELEVENLABS_API_KEY', '')
if not KEY:
    with open('/root/.openclaw/workspace/rupeeboss/.env') as f:
        for line in f:
            if line.startswith('ELEVENLABS_API_KEY='):
                KEY = line.strip().split('=', 1)[1]

AGENT = 'gKNyAo0UhrdRiQ7FAWVZ'

# Check existing KB documents
req = urllib.request.Request(
    'https://api.elevenlabs.io/v1/convai/knowledge-base',
    headers={'xi-api-key': KEY}
)
try:
    with urllib.request.urlopen(req) as resp:
        docs = json.loads(resp.read())
        print(f"KB docs in account: {len(docs)}")
        for d in docs:
            print(f"  {d.get('id')}: {d.get('name')} ({d.get('type', 'file')})")
except Exception as e:
    print(f"Error listing KB: {e}")

# Check agent
req = urllib.request.Request(
    f'https://api.elevenlabs.io/v1/convai/agents/{AGENT}',
    headers={'xi-api-key': KEY}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

kb = data.get('conversation_config', {}).get('agent', {}).get('knowledge_base', [])
print(f"\nAgent KB entries: {len(kb)}")
for item in kb:
    print(f"  {item.get('id')}: {item.get('name')} ({item.get('type')})")

# Check RAG
rag = data.get('conversation_config', {}).get('agent', {}).get('rag', {})
print(f"\nRAG enabled: {rag.get('enabled', False)}")
print(f"RAG model: {rag.get('embedding_model', 'N/A')}")
print(f"RAG similarity threshold: {rag.get('similarity_threshold', 'N/A')}")
print(f"RAG max documents: {rag.get('max_documents', 'N/A')}")
