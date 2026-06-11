#!/usr/bin/env python3
"""
Upload knowledge base documents to ElevenLabs ConvAI for agent gKNyAo0UhrdRiQ7FAWVZ
"""

import urllib.request
import json
import os

KEY = os.popen('grep ELEVENLABS_API_KEY /root/.openclaw/workspace/rupeeboss/.env | head -1 | cut -d= -f2').read().strip()
AGENT = 'gKNyAo0UhrdRiQ7FAWVZ'
KB_DIR = '/root/.openclaw/workspace/rupeeboss/knowledge_base'

print(f"Key: {KEY[:10]}...")
print(f"Agent: {AGENT}")
print(f"KB dir: {KB_DIR}")

def upload_file(filepath, name, description=""):
    """Upload a file to ElevenLabs knowledge base"""
    boundary = "----WebKitFormBoundary" + os.urandom(16).hex()
    
    with open(filepath, 'rb') as f:
        file_content = f.read()
    
    # Build multipart form data
    body = bytearray()
    body += f'--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(filepath)}"\r\n'.encode()
    body += f'Content-Type: text/plain\r\n\r\n'.encode()
    body += file_content
    body += f'\r\n--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="name"\r\n\r\n'.encode()
    body += name.encode()
    body += f'\r\n--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="type"\r\n\r\n'.encode()
    body += b'text'  # or 'file'
    body += f'\r\n--{boundary}--\r\n'.encode()
    
    req = urllib.request.Request(
        'https://api.elevenlabs.io/v1/convai/knowledge-base',
        data=bytes(body),
        headers={
            'xi-api-key': KEY,
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  Error uploading {name}: {e.code} - {error_body}")
        return None

# Test with one file first
test_file = f'{KB_DIR}/01_customer_faq.txt'
print(f"\nUploading: {test_file}")
result = upload_file(test_file, "RupeeBoss Customer FAQ", "Real customer Q&A from 2073 conversations")

if result:
    print(f"Success! Result: {json.dumps(result, indent=2)[:500]}")
else:
    print("Upload failed. Trying alternative approach...")
    
    # Try with no multipart, just the file
    req = urllib.request.Request(
        'https://api.elevenlabs.io/v1/convai/knowledge-base',
        data=open(test_file, 'rb').read(),
        headers={
            'xi-api-key': KEY,
            'Content-Type': 'text/plain'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            print(f"Direct upload success: {json.dumps(data, indent=2)[:500]}")
    except urllib.error.HTTPError as e:
        print(f"Direct upload also failed: {e.code} - {e.read().decode()[:200]}")
