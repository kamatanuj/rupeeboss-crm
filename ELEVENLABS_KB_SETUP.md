# ElevenLabs ConvAI Knowledge Base Setup Guide
## Agent ID: gKNyAo0UhrdRiQ7FAWVZ (RupeeBoss)

---

## STEP 1: Access ElevenLabs Dashboard

1. Go to: https://elevenlabs.io/app/conversational-ai
2. Sign in with your account
3. Find agent: **gKNyAo0UhrdRiQ7FAWVZ** (RupeeBoss Support Agent)

---

## STEP 2: Navigate to Knowledge Base

1. Click on your RupeeBoss agent
2. Go to **"Knowledge Base"** tab (or "Documents" section)
3. Click **"Upload Document"** or **"Add Knowledge"**

---

## STEP 3: Upload the Generated Files

Files are located at:
```
/root/.openclaw/workspace/rupeeboss/knowledge_base/
```

Upload these 4 files (drag & drop or browse):

| File | Purpose | Size |
|:---|:---|:---|
| `01_customer_faq.txt` | Real customer Q&A from 2073 conversations | 51 KB |
| `02_loan_types_guide.txt` | Loan product descriptions by type | 6 KB |
| `03_agent_best_practices.txt` | Successful conversation patterns + guidelines | 38 KB |
| `04_repeat_customers.txt` | Repeat customer patterns | 5 KB |

**Total:** ~100 KB of structured knowledge

---

## STEP 4: Configure Knowledge Base Settings

In ElevenLabs, set these options:

| Setting | Recommended Value |
|:---|:---|
| **Search Type** | Semantic Search |
| **Max chunks per query** | 5 |
| **Chunk size** | 500 tokens |
| **Overlap** | 50 tokens |
| **Relevance threshold** | 0.7 |

---

## STEP 5: Update Agent Prompt

Add this to your agent's system prompt:

```
You are Riya, a loan advisor at RupeeBoss. 

You have access to our knowledge base which contains:
- Real past customer conversations and outcomes
- Loan product details (Home, Business, Personal, Loan Against Property, Machinery, Startup)
- Successful conversation patterns
- Information about repeat customers

When answering:
1. Use the knowledge base to provide accurate loan information
2. Reference similar past customer cases when relevant
3. Follow the greeting pattern: "Namaste! This is Riya from RupeeBoss"
4. Ask for: Name, Phone, Loan amount, Employment type
5. If customer mentions a specific loan type, give details from our products guide
6. For repeat customers, acknowledge their previous inquiries

Language: Mix of Hindi and English (Hinglish) as customer prefers.
Tone: Polite, patient, helpful, professional.
```

---

## STEP 6: Test the Knowledge Base

After uploading, test with these queries:

1. **"Mujhe business loan chahiye"** → Should mention startup loan options
2. **"Home loan transfer kaise hota hai?"** → Should reference home loan transfer cases
3. **"Rate of interest kitna hai?"** → Should mention 12.99% onwards
4. **"Partner registration mein problem hai"** → Should reference partner registration cases

---

## STEP 7: Keep Knowledge Base Updated

Run this command monthly to refresh the knowledge base:

```bash
cd /root/.openclaw/workspace/rupeeboss
python3 export_kb.py
```

Then re-upload the files to ElevenLabs.

**OR** set up auto-refresh:
- Add `python3 export_kb.py` to your hourly `auto-update.sh`
- Files will regenerate before each CRM deploy
- Manually re-upload to ElevenLabs when ready

---

## What the Knowledge Base Contains

### 01_customer_faq.txt
- **Source:** 500 real conversations
- **Format:** Question → Response → Outcome
- **Use case:** Agent knows how real customers asked and what responses worked

### 02_loan_types_guide.txt
- **Source:** All conversations grouped by loan type
- **Format:** Loan type → Common needs → Typical outcome
- **Use case:** Agent gives accurate loan product info

### 03_agent_best_practices.txt
- **Source:** Conversations where customer shared data
- **Format:** Successful greeting exchanges + general guidelines
- **Use case:** Agent follows proven conversation patterns

### 04_repeat_customers.txt
- **Source:** Customers with 2+ calls
- **Format:** Phone | Name | Call count | Loan types | Date range
- **Use case:** Agent recognizes returning customers

---

## Troubleshooting

| Problem | Solution |
|:---|:---|
| "Document too large" | Split into smaller files |
| "Knowledge not found" | Check semantic search is enabled |
| "Agent ignores KB" | Increase "knowledge base weight" in prompt |
| "Outdated info" | Re-run export_kb.py and re-upload |

---

## Next: Automated Sync (Optional)

To auto-sync without manual upload, use ElevenLabs API:

```python
import requests

API_KEY = "your_elevenlabs_api_key"
AGENT_ID = "gKNyAo0UhrdRiQ7FAWVZ"

# Upload knowledge base document
with open('knowledge_base/01_customer_faq.txt', 'rb') as f:
    response = requests.post(
        f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/knowledge-base",
        headers={"xi-api-key": API_KEY},
        files={"file": ("customer_faq.txt", f, "text/plain")}
    )
    print(response.json())
```

**Want me to build this auto-sync script?**
