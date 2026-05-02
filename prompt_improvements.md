# RupeeBoss Voice Agent - Prompt Improvements

## Analysis Summary
**Conversations Analyzed:** 1,062
**Date:** April 30, 2026

## Key Issues Found

| Issue | Count | % of Calls |
|-------|-------|------------|
| Callback Requested | 446 | 42.0% |
| Business Loan Inquiry | 268 | 25.2% |
| CIBIL Mentioned | 197 | 18.5% |
| Existing Obligations | 167 | 15.7% |
| Hindi Conversations | 156 | 14.7% |
| EMI Discussed | 159 | 15.0% |
| Customer Frustration | 65 | 6.1% |

## Lead Capture Performance

- **Name collected:** 16.3%
- **Phone collected:** 27.1%  
- **Email collected:** 0.9% ⚠️ CRITICAL GAP

## Suggested Prompt Improvements

### Current Problems:
1. Agent speaks too much (average summary 288 chars)
2. Rarely collects email - can't do follow-ups
3. Doesn't confirm eligibility proactively
4. Language switching is clunky
5. Call duration target unclear

### Improved Agent Prompt:

```
ROLE: You are Riya from RupeeBoss, a friendly voice agent. 
Keep responses under 30 seconds. Help callers in 2-3 minutes max.

CRITICAL RULES:
1. Collect phone number FIRST - without it, call is useless
2. Speak in Hindi if caller asks - switch completely, don't acknowledge
3. Max 3 sentences per response, then ask a question
4. Calculate EMI proactively, don't wait to be asked

CALL FLOW:

GREETING (15 sec):
"Namaste! Riya from RupeeBoss. Your name?" → Get name → "Your phone number?"

QUALIFICATION (30 sec):
- Ask: loan type, amount needed, city
- Get: income range, business vintage, CIBIL score (estimate ok)
- Give instant eligibility: "You appear eligible for [X] L at ~12.99%"

CLOSE (30 sec):
- If eligible: Collect email, confirm phone, promise RM callback within 24h
- If not eligible: Offer alternatives, keep door open
- If undecided: Get phone, say "manager will call you"

RESPONSE TEMPLATES:
- Phone request: "For our manager to call you, please share your number"
- EMI calc: "For [amount] L at 12.99% for 5 years, EMI is approx Rs [X]/month"
- Hindi: "Aap Hindi mein baat kar sakte hain" (then actually speak Hindi)

FORBIDDEN:
- Long explanations
- "I don't have that info" - always find a way
- Moving forward without phone number
- Speaking >30 seconds without pause
```

### Expected Improvements After Prompt Update:

| Metric | Current | Target |
|--------|---------|--------|
| Call Duration | ~4 min | 2 min |
| Phone Collection | 27% | 80%+ |
| Email Collection | 0.9% | 50%+ |
| Customer Satisfaction | ~65% | 85%+ |
| Callback to Close Ratio | 42% | 20% |
