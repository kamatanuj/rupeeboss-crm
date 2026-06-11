#!/usr/bin/env python3
"""
Export RupeeBoss conversations as ElevenLabs Knowledge Base documents.
Creates multiple TXT files that can be uploaded to ElevenLabs ConvAI.
"""

import sqlite3
import os
import re
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/rupeeboss/conversations.db'
OUTPUT_DIR = '/root/.openclaw/workspace/rupeeboss/knowledge_base'

def clean_text(text):
    """Clean transcript for knowledge base"""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def create_knowledge_base():
    """Export conversations as knowledge base documents"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # ============================================
    # DOCUMENT 1: FAQ - Common Customer Questions
    # ============================================
    print("Building FAQ document...")
    c.execute("""
        SELECT call_summary_title, call_summary, transcript, date
        FROM conversations
        WHERE call_summary_title != '' AND transcript != ''
        ORDER BY date DESC
        LIMIT 500
    """)
    
    faq_content = """RupeeBoss Customer Support Knowledge Base
=============================================
Last Updated: {date}
Total Conversations Analyzed: 2073

This document contains real customer conversations and outcomes.
Use this to understand customer needs and provide accurate responses.

SECTION 1: COMMON CUSTOMER QUESTIONS AND RESPONSES
===================================================

""".format(date=datetime.now().strftime('%Y-%m-%d'))
    
    seen_titles = set()
    for row in c.fetchall():
        title, summary, transcript, date = row
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        # Extract customer question (first user message)
        user_lines = re.findall(r'\[USER\]: (.+)', transcript)
        if user_lines:
            customer_q = user_lines[0][:200]
            
            # Extract agent response (first agent response)
            agent_lines = re.findall(r'\[AGENT\]: (.+)', transcript)
            agent_response = agent_lines[0][:300] if agent_lines else ""
            
            faq_content += f"""
Question Type: {title}
Date: {date}
Customer Asked: {customer_q}
Agent Response: {agent_response}
Outcome: {summary or 'Inquiry recorded'}
---
"""
    
    with open(f'{OUTPUT_DIR}/01_customer_faq.txt', 'w') as f:
        f.write(faq_content)
    print(f"  Written: 01_customer_faq.txt ({len(faq_content)} chars)")
    
    # ============================================
    # DOCUMENT 2: Loan Types Guide
    # ============================================
    print("Building Loan Types guide...")
    
    loan_types = {
        'Home Loan': [],
        'Business Loan': [],
        'Personal Loan': [],
        'Loan Against Property': [],
        'Machinery Loan': [],
        'Startup Loan': [],
        'Balance Transfer': [],
        'Partner': []
    }
    
    c.execute("""
        SELECT call_summary_title, transcript, call_summary
        FROM conversations
        WHERE call_summary_title != '' AND transcript != ''
    """)
    
    for row in c.fetchall():
        title, transcript, summary = row
        title_lower = title.lower()
        
        for loan_type in loan_types.keys():
            if loan_type.lower().replace(' ', '') in title_lower.replace(' ', ''):
                user_lines = re.findall(r'\[USER\]: (.+)', transcript)
                if user_lines and len(loan_types[loan_type]) < 50:
                    loan_types[loan_type].append({
                        'question': user_lines[0][:150],
                        'summary': summary or title
                    })
    
    loan_guide = """RupeeBoss Loan Products Guide
================================

This document describes the loan products offered by RupeeBoss
based on actual customer conversations.

"""
    
    for loan_type, examples in loan_types.items():
        if examples:
            loan_guide += f"""
{loan_type.upper()}
{'='*len(loan_type)}
Common customer needs:
"""
            for i, ex in enumerate(examples[:10], 1):
                loan_guide += f"{i}. {ex['question']}\n"
            loan_guide += f"\nTypical outcome: {examples[0]['summary']}\n\n"
    
    with open(f'{OUTPUT_DIR}/02_loan_types_guide.txt', 'w') as f:
        f.write(loan_guide)
    print(f"  Written: 02_loan_types_guide.txt ({len(loan_guide)} chars)")
    
    # ============================================
    # DOCUMENT 3: Agent Best Practices
    # ============================================
    print("Building Agent Best Practices...")
    
    c.execute("""
        SELECT transcript, call_summary_title, date
        FROM conversations
        WHERE transcript != '' AND LENGTH(transcript) > 200
        ORDER BY date DESC
        LIMIT 300
    """)
    
    best_practices = """RupeeBoss Agent Best Practices
=================================

This document contains successful conversation patterns
that agents should follow when speaking with customers.

"""
    
    successful_patterns = []
    for row in c.fetchall():
        transcript, title, date = row
        
        # Look for conversations where customer shared info
        if re.search(r'\b([6-9]\d{9})\b', transcript):
            # Extract the opening exchange
            lines = transcript.split('\n')
            opening = []
            for line in lines[:8]:  # First 8 lines
                if line.strip():
                    opening.append(line)
            
            if len(opening) >= 4:
                successful_patterns.append({
                    'title': title,
                    'date': date,
                    'exchange': '\n'.join(opening)
                })
    
    best_practices += f"""
PATTERN 1: SUCCESSFUL GREETING AND NEED IDENTIFICATION
---------------------------------------------------------
"""
    
    for i, pattern in enumerate(successful_patterns[:20], 1):
        best_practices += f"""
Example {i}: {pattern['title']} ({pattern['date']})
{pattern['exchange']}
---
"""
    
    # Add general guidelines
    best_practices += """
GENERAL GUIDELINES FOR RUPEEBOSS AGENTS
========================================

1. GREETING
   - Always greet with "Namaste! This is Riya from RupeeBoss"
   - Ask which loan type they need

2. NEED IDENTIFICATION
   - Ask specific questions about loan purpose
   - Check if they have property/collateral
   - Ask about employment status (salaried/self-employed)

3. DATA COLLECTION
   - Must collect: Name, Phone number, Loan amount needed
   - Should collect: Income, City, Property details
   - If customer hesitates, explain why data is needed

4. LOAN TYPES TO MENTION
   - Home Loan: For buying house/flat
   - Business Loan: For business expansion
   - Personal Loan: For salaried employees, no collateral
   - Loan Against Property: Using existing property
   - Machinery Loan: For buying equipment
   - Startup Loan: For new businesses, collateral-free

5. COMMON OBJECTIONS
   - "I don't want to share details" → Explain data privacy
   - "Interest rate is too high" → Mention balance transfer option
   - "I need it urgently" → Mention fast processing
   - "I was rejected before" → Mention alternative lenders

6. CLOSING
   - Always summarize what was discussed
   - Explain next steps (document collection, verification)
   - Give realistic timeline
   - Thank the customer

7. LANGUAGE
   - Speak in Hindi + English mix as customer prefers
   - Use simple terms, avoid banking jargon
   - Be polite and patient
"""
    
    with open(f'{OUTPUT_DIR}/03_agent_best_practices.txt', 'w') as f:
        f.write(best_practices)
    print(f"  Written: 03_agent_best_practices.txt ({len(best_practices)} chars)")
    
    # ============================================
    # DOCUMENT 4: Customer History Lookup
    # ============================================
    print("Building Customer History reference...")
    
    c.execute("""
        SELECT client_phone, client_name, COUNT(*) as call_count,
               GROUP_CONCAT(call_summary_title, '; ') as titles,
               MAX(date) as last_call,
               MIN(date) as first_call
        FROM conversations
        WHERE client_phone != ''
        GROUP BY client_phone
        HAVING call_count > 1
        ORDER BY call_count DESC
        LIMIT 100
    """)
    
    customer_history = """RupeeBoss Repeat Customer Reference
====================================

This document lists customers who called multiple times.
Use this to understand follow-up patterns.

"""
    
    for row in c.fetchall():
        phone, name, count, titles, last, first = row
        customer_history += f"""
Customer: {name or 'Unknown'} | Phone: {phone}
Total Calls: {count} | First: {first} | Last: {last}
Loan Types Discussed: {titles}
---
"""
    
    with open(f'{OUTPUT_DIR}/04_repeat_customers.txt', 'w') as f:
        f.write(customer_history)
    print(f"  Written: 04_repeat_customers.txt ({len(customer_history)} chars)")
    
    conn.close()
    
    print(f"\n✅ Knowledge base documents created in: {OUTPUT_DIR}")
    print("\nFiles:")
    for f in os.listdir(OUTPUT_DIR):
        size = os.path.getsize(f'{OUTPUT_DIR}/{f}')
        print(f"  - {f} ({size:,} bytes)")

if __name__ == '__main__':
    create_knowledge_base()
