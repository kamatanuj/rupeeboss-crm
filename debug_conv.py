import json, urllib.request, os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path='/root/.openclaw/workspace/rupeeboss/.env')
API_KEY=*** ith open('recoverable_conversations.json') as f:
    gap_ids = json.load(f)['june_gap_ids']

for cid in gap_ids:
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{cid}"
    req = urllib.request.Request(url, headers={"xi-api-key": API_KEY})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        
        ts = data.get('start_time_unix_secs', 0)
        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else 'no_ts'
        dur = data.get('call_duration_secs', 0)
        title = data.get('call_summary_title', 'N/A')
        
        # Check transcript structure
        transcript = data.get('transcript', [])
        if transcript:
            msg = transcript[0]
            print(f"{date} | dur={dur}s | msgs={len(transcript)} | title={title}")
            # Check keys in first message
            print(f"  Keys: {list(msg.keys())}")
            if 'role' in msg:
                print(f"  Sample message: {msg}")
        else:
            print(f"{date} | dur={dur}s | NO TRANSCRIPT | title={title}")
        break  # Just check first one
    except Exception as e:
        print(f"Error: {e}")
