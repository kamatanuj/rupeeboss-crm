#!/usr/bin/env python3
"""
RupeeBoss CRM — Agent Reach Integration
Feature 3: Social Media Monitoring (Twitter/Reddit/Web mentions)
Feature 4: Competitor Intelligence (loan products, pricing, offers)
Feature 5: Regulatory News Alerts (RBI, NBFC, policy changes every 4 hours)

Uses Agent Reach backends: Exa search, Jina Reader, RSS feeds.
Stores results in a new `market_intelligence` table in conversations.db.
Sends alerts via email when configured.

Usage:
  python3 agent_reach_monitor.py --feature social       # Run social monitoring
  python3 agent_reach_monitor.py --feature competitor   # Run competitor research
  python3 agent_reach_monitor.py --feature regulatory   # Run regulatory alerts
  python3 agent_reach_monitor.py --feature all          # Run all three
  python3 agent_reach_monitor.py --feature all --alert  # Run + email alerts
"""

import sqlite3
import json
import subprocess
import os
import sys
import argparse
import time
from datetime import datetime, timezone

DB_PATH = '/root/rupeeboss-crm-repo/conversations.db'
ALERT_EMAIL = 'kamatanuj@gmail.com'

# --- Keywords to monitor ---
SOCIAL_KEYWORDS = [
    "RupeeBoss",
    "rupeeboss personal loan",
    "rupeeboss business loan",
    "rupeeboss MSME loan",
    "rupeeboss review",
    "rupeeboss fraud",
    "rupeeboss complaint",
]

COMPETITOR_KEYWORDS = [
    "personal loan India interest rate 2026",
    "MSME loan best rates India",
    "business loan NBFC comparison India",
    "personal loan instant approval India",
    "loan aggregator India competitors",
]

COMPETITOR_SITES = [
    "https://www.bankbazaar.com/personal-loan-interest-rate.html",
    "https://www.paisabazaar.com/personal-loan/",
    "https://www.policybazaar.com/personal-loan/",
    "https://www.wishfin.com/personal-loan/",
    "https://www.rupeeboss.com/",
]

RSS_FEEDS = [
    # Indian finance / loan news
    "https://www.livemint.com/rss/industry/banking/finance",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://economictimes.indiatimes.com/wealth/personal-finance-news/rssfeeds/2546214.cms",
    "https://www.financialexpress.com/feed/",
]

# Regulatory / policy RSS feeds
REGULATORY_RSS_FEEDS = [
    "https://www.rbi.org.in/Scripts/Rss.aspx?cat=Press+Releases",
    "https://www.rbi.org.in/Scripts/Rss.aspx?cat=Notifications",
    "https://www.rbi.org.in/Scripts/Rss.aspx?cat=Circulars",
    "https://www.pib.gov.in/AllRel.aspx?reg=3&lang=1",
    "https://www.sebi.gov.in/rss/press.xml",
    "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358259.cms",
    "https://www.livemint.com/rss/economy/policy",
    "https://www.moneycontrol.com/rss/economy.xml",
]

# Keywords that trigger regulatory alerts
REGULATORY_KEYWORDS = [
    'rbi', 'repo rate', 'reverse repo', 'moratorium', 'nbfc', 'microfinance',
    'loan restructuring', 'emi', 'moratorium', 'interest rate', 'base rate',
    'mclr', 'lending rate', 'credit policy', 'monetary policy', 'regulation',
    'circular', 'notification', 'guideline', 'compliance', 'kyc', 'aadhaar',
    'pan card', 'credit score', 'cibil', 'dlf', 'foreclosure', 'prepayment',
    'dsao', 'digital lending', 'fintech', 'payment aggregator', 'upi',
    'insolvency', 'nclt', 'sma', 'npa', 'provisioning', 'priority sector',
    'msme', 'udyam', 'gst', ' Mudra', 'cgtmse', 'ecgc',
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_table():
    """Create market_intelligence table if not exists."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_intelligence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,          -- 'social_mention' or 'competitor_intel'
            source TEXT NOT NULL,         -- 'exa', 'jina', 'rss', 'scrapling'
            keyword TEXT,
            title TEXT,
            url TEXT,
            content TEXT,
            sentiment TEXT,               -- 'positive', 'negative', 'neutral'
            severity TEXT,                -- 'info', 'warning', 'critical'
            metadata_json TEXT,
            captured_at TEXT NOT NULL,
            alerted INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mi_type ON market_intelligence(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mi_captured ON market_intelligence(captured_at)")
    conn.commit()
    conn.close()
    print("✓ market_intelligence table ready")


def exa_search(query, num_results=5):
    """Use Agent Reach's Exa backend for web search."""
    try:
        result = subprocess.run(
            ['mcporter', 'call', f'exa.web_search_exa(query: "{query}", numResults: {num_results})'],
            capture_output=True, text=True, timeout=30
        )
        # Parse the output - it returns text blocks
        items = []
        current = {}
        for line in result.stdout.split('\n'):
            if line.startswith('Title: '):
                if current.get('title'):
                    items.append(current)
                current = {'title': line[7:].strip()}
            elif line.startswith('URL: '):
                current['url'] = line[5:].strip()
            elif line.startswith('Published: '):
                current['published'] = line[11:].strip()
            elif line.startswith('Highlights:'):
                current['highlights'] = ''
            elif current.get('highlights') is not None and line.strip():
                current['highlights'] += line.strip() + ' '
        if current.get('title'):
            items.append(current)
        return items
    except Exception as e:
        print(f"  ✗ Exa search failed for '{query}': {e}")
        return []


def jina_read(url):
    """Use Agent Reach's Jina Reader backend to read any web page."""
    try:
        result = subprocess.run(
            ['curl', '-s', f'https://r.jina.ai/{url}'],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout[:5000]  # Cap to 5k chars
    except Exception as e:
        print(f"  ✗ Jina Reader failed for {url}: {e}")
        return ""


def read_rss(feed_url):
    """Read an RSS/Atom feed using Agent Reach's feedparser backend."""
    try:
        result = subprocess.run(
            ['python3', '-c', f'''
import feedparser
feed = feedparser.parse("{feed_url}")
for entry in feed.entries[:5]:
    print(f"TITLE: {{entry.title}}")
    print(f"URL: {{entry.link}}")
    print(f"SUMMARY: {{entry.summary[:500]}}")
    print("---")
'''],
            capture_output=True, text=True, timeout=30
        )
        items = []
        current = {}
        for line in result.stdout.split('---\n'):
            for sub in line.strip().split('\n'):
                if sub.startswith('TITLE: '):
                    current['title'] = sub[7:]
                elif sub.startswith('URL: '):
                    current['url'] = sub[5:]
                elif sub.startswith('SUMMARY: '):
                    current['summary'] = sub[9:]
            if current.get('title'):
                items.append(current)
                current = {}
        return items
    except Exception as e:
        print(f"  ✗ RSS failed for {feed_url}: {e}")
        return []


def detect_sentiment(text):
    """Simple keyword-based sentiment detection."""
    text_lower = text.lower()
    negative_words = ['fraud', 'scam', 'complaint', 'worst', 'terrible', 'cheat', 'fake', 'problem', 'issue', 'angry', 'disappointed']
    positive_words = ['great', 'excellent', 'best', 'amazing', 'recommend', 'happy', 'satisfied', 'easy', 'fast', 'good']
    
    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)
    
    if neg_count > pos_count:
        return 'negative', 'warning' if neg_count > 2 else 'info'
    elif pos_count > neg_count:
        return 'positive', 'info'
    return 'neutral', 'info'


def store_intel(item_type, source, keyword, title, url, content, sentiment='neutral', severity='info', metadata=None):
    """Store intelligence in the database."""
    conn = get_db()
    # Check for duplicates
    if url:
        existing = conn.execute("SELECT id FROM market_intelligence WHERE url = ?", (url,)).fetchone()
        if existing:
            conn.close()
            return False
    
    conn.execute("""
        INSERT INTO market_intelligence 
        (type, source, keyword, title, url, content, sentiment, severity, metadata_json, captured_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_type, source, keyword, title, url, content[:2000],
        sentiment, severity,
        json.dumps(metadata or {}),
        datetime.now(timezone.utc).isoformat()
    ))
    conn.commit()
    conn.close()
    return True


def run_social_monitoring():
    """Feature 3: Monitor social media and web for RupeeBoss mentions."""
    print("\n📡 Feature 3: Social Media Monitoring")
    print("=" * 50)
    
    total_found = 0
    critical_found = 0
    
    # 1. Exa search for brand mentions
    print("\n🔍 Searching web for RupeeBoss mentions via Exa...")
    for kw in SOCIAL_KEYWORDS:
        print(f"  Searching: {kw}")
        results = exa_search(kw, num_results=5)
        for r in results:
            text = r.get('highlights', '') + ' ' + r.get('title', '')
            sentiment, severity = detect_sentiment(text)
            stored = store_intel(
                'social_mention', 'exa', kw,
                r.get('title', ''), r.get('url', ''),
                r.get('highlights', text),
                sentiment, severity,
                {'published': r.get('published', '')}
            )
            if stored:
                total_found += 1
                if severity == 'warning' or severity == 'critical':
                    critical_found += 1
                    print(f"    ⚠️  [{sentiment}] {r.get('title', '')[:60]}")
                else:
                    print(f"    ✓ [{sentiment}] {r.get('title', '')[:60]}")
        time.sleep(1)  # Rate limit
    
    # 2. RSS feeds for finance news mentioning loans
    print("\n📰 Checking RSS feeds for loan/finance news...")
    for feed_url in RSS_FEEDS:
        print(f"  Reading: {feed_url.split('/')[2]}")
        items = read_rss(feed_url)
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('summary', '')).lower()
            # Only store if relevant to loans/finance
            if any(kw in text for kw in ['loan', 'nbfc', 'rbi', 'credit', 'finance', 'emi']):
                stored = store_intel(
                    'social_mention', 'rss', 'finance_news',
                    item.get('title', ''), item.get('url', ''),
                    item.get('summary', ''),
                    'neutral', 'info',
                    {'feed': feed_url}
                )
                if stored:
                    total_found += 1
                    print(f"    ✓ {item.get('title', '')[:60]}")
    
    print(f"\n📊 Social Monitoring Summary: {total_found} new items, {critical_found} need attention")
    return total_found, critical_found


def run_competitor_intelligence():
    """Feature 4: Research competitor loan products and pricing."""
    print("\n🏢 Feature 4: Competitor Intelligence")
    print("=" * 50)
    
    total_found = 0
    
    # 1. Exa search for competitor keywords
    print("\n🔍 Searching for competitor loan products via Exa...")
    for kw in COMPETITOR_KEYWORDS:
        print(f"  Searching: {kw}")
        results = exa_search(kw, num_results=5)
        for r in results:
            stored = store_intel(
                'competitor_intel', 'exa', kw,
                r.get('title', ''), r.get('url', ''),
                r.get('highlights', ''),
                'neutral', 'info',
                {'published': r.get('published', '')}
            )
            if stored:
                total_found += 1
                print(f"    ✓ {r.get('title', '')[:60]}")
        time.sleep(1)
    
    # 2. Scrape competitor sites for rate data via Jina Reader
    print("\n🌐 Reading competitor websites for pricing data...")
    for site in COMPETITOR_SITES:
        print(f"  Reading: {site.split('/')[2]}")
        content = jina_read(site)
        if content:
            # Extract rate-related content
            rate_lines = [l for l in content.split('\n') if any(w in l.lower() for w in ['rate', 'interest', 'emi', '%', 'apr', 'processing fee'])]
            relevant = '\n'.join(rate_lines[:20]) if rate_lines else content[:2000]
            stored = store_intel(
                'competitor_intel', 'jina', 'competitor_site',
                f"Pricing data from {site.split('/')[2]}",
                site, relevant,
                'neutral', 'info',
                {'site': site, 'rate_lines_count': len(rate_lines)}
            )
            if stored:
                total_found += 1
                print(f"    ✓ Extracted {len(rate_lines)} rate-related lines")
        time.sleep(2)
    
    print(f"\n📊 Competitor Intel Summary: {total_found} new items captured")
    return total_found


def run_regulatory_monitoring():
    """Feature 5: Monitor regulatory/policy news for alerts (RBI, NBFC, loan rules)."""
    print("\n⚖️ Feature 5: Regulatory News Alerts")
    print("=" * 50)
    
    total_found = 0
    critical_found = 0
    
    print("\n📰 Checking regulatory RSS feeds (RBI, SEBI, PIB, ET, Mint, Moneycontrol)...")
    for feed_url in REGULATORY_RSS_FEEDS:
        source_name = feed_url.split('/')[2]
        print(f"  Reading: {source_name}")
        items = read_rss(feed_url)
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('summary', '')).lower()
            # Check if any regulatory keyword matches
            matched_keywords = [kw for kw in REGULATORY_KEYWORDS if kw in text]
            if matched_keywords:
                # Determine severity
                title = item.get('title', '')
                severity = 'info'
                if any(kw in text for kw in ['moratorium', 'ban', 'restrict', 'penalty', 'fine', 'suspended', 'insolvency', 'npa']):
                    severity = 'critical'
                elif any(kw in text for kw in ['circular', 'notification', 'guideline', 'regulation', 'compliance', 'rbi', 'monetary policy']):
                    severity = 'warning'
                
                # Determine sentiment
                sentiment, _ = detect_sentiment(title + ' ' + item.get('summary', ''))
                
                stored = store_intel(
                    'regulatory_alert', 'rss', matched_keywords[0],
                    title, item.get('url', ''),
                    item.get('summary', ''),
                    sentiment, severity,
                    {'feed': feed_url, 'matched_keywords': matched_keywords[:5]}
                )
                if stored:
                    total_found += 1
                    if severity == 'critical':
                        critical_found += 1
                        print(f"    🚨 [{severity}] {title[:60]}")
                    elif severity == 'warning':
                        print(f"    ⚠️  [{severity}] {title[:60]}")
                    else:
                        print(f"    ✓ [{severity}] {title[:60]}")
        time.sleep(0.5)
    
    # Also do Exa searches for latest regulatory news
    print("\n🔍 Searching for latest regulatory news via Exa...")
    reg_search_keywords = [
        "RBI circular loan NBFC 2026",
        "RBI monetary policy repo rate 2026",
        "NBFC regulation India latest 2026",
        "digital lending guidelines RBI 2026",
        "MSME loan policy change 2026",
    ]
    for kw in reg_search_keywords:
        print(f"  Searching: {kw}")
        results = exa_search(kw, num_results=3)
        for r in results:
            text = r.get('highlights', '') + ' ' + r.get('title', '')
            text_lower = text.lower()
            if any(kw in text_lower for kw in REGULATORY_KEYWORDS):
                sentiment, _ = detect_sentiment(text)
                severity = 'warning' if 'rbi' in text_lower or 'regulation' in text_lower else 'info'
                stored = store_intel(
                    'regulatory_alert', 'exa', kw,
                    r.get('title', ''), r.get('url', ''),
                    r.get('highlights', text),
                    sentiment, severity,
                    {'published': r.get('published', '')}
                )
                if stored:
                    total_found += 1
                    print(f"    ✓ [{sentiment}] {r.get('title', '')[:60]}")
        time.sleep(1)
    
    print(f"\n📊 Regulatory Alerts Summary: {total_found} new alerts, {critical_found} critical")
    return total_found, critical_found


def send_alert_email(subject, body):
    """Send alert email via Gmail SMTP."""
    import smtplib
    from email.mime.text import MIMEText
    
    PW_PARTS = ["vtkt", "dkdz", "dbbv", "kalo"]
    password = "".join(PW_PARTS)
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'kamatanuj@gmail.com'
    msg['To'] = ALERT_EMAIL
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('kamatanuj@gmail.com', password)
        server.send_message(msg)
        server.quit()
        print(f"📧 Alert email sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"✗ Email failed: {e}")


def generate_report():
    """Generate a summary report from the market_intelligence table."""
    conn = get_db()
    
    # Recent items
    recent = conn.execute("""
        SELECT * FROM market_intelligence 
        ORDER BY captured_at DESC LIMIT 20
    """).fetchall()
    
    # Stats
    stats = conn.execute("""
        SELECT type, sentiment, COUNT(*) as count 
        FROM market_intelligence 
        GROUP BY type, sentiment
    """).fetchall()
    
    conn.close()
    
    report_lines = []
    report_lines.append("📊 RUPPEBOSS CRM — MARKET INTELLIGENCE REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append("")
    
    # Stats
    report_lines.append("=== Summary ===")
    for s in stats:
        report_lines.append(f"  {s['type']} / {s['sentiment']}: {s['count']} items")
    report_lines.append("")
    
    # Recent items
    report_lines.append("=== Recent Intelligence (last 20) ===")
    for r in recent:
        report_lines.append(f"\n[{r['type']}] {r['title']}")
        report_lines.append(f"  Source: {r['source']} | Sentiment: {r['sentiment']} | Severity: {r['severity']}")
        report_lines.append(f"  URL: {r['url']}")
        report_lines.append(f"  Content: {r['content'][:200]}...")
    
    return '\n'.join(report_lines)


def main():
    parser = argparse.ArgumentParser(description='RupeeBoss CRM — Agent Reach Market Intelligence')
    parser.add_argument('--feature', choices=['social', 'competitor', 'regulatory', 'all', 'report'], default='all',
                        help='Which feature to run')
    parser.add_argument('--alert', action='store_true',
                        help='Send email alert with results')
    args = parser.parse_args()
    
    init_table()
    
    if args.feature == 'report':
        print(generate_report())
        return
    
    social_count = 0
    competitor_count = 0
    regulatory_count = 0
    critical_count = 0
    
    if args.feature in ('social', 'all'):
        social_count, critical_count = run_social_monitoring()
    
    if args.feature in ('competitor', 'all'):
        competitor_count = run_competitor_intelligence()
    
    if args.feature in ('regulatory', 'all'):
        regulatory_count, reg_critical = run_regulatory_monitoring()
        critical_count += reg_critical
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Complete: {social_count} social, {competitor_count} competitor, {regulatory_count} regulatory, {critical_count} critical")

    # Generate static JSON for Cloudflare Pages
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM market_intelligence ORDER BY captured_at DESC LIMIT 100").fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    json_data = {
        "items": items,
        "count": len(items),
        "lastUpdated": items[0]["captured_at"] if items else "N/A"
    }
    json_path = '/root/rupeeboss-crm-repo/public/market_intel.json'
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"📄 Updated market_intel.json: {len(items)} items")
    
    if args.alert and (critical_count > 0 or competitor_count > 0):
        report = generate_report()
        send_alert_email(
            f"🚨 RupeeBoss CRM Market Intelligence Alert — {datetime.now().strftime('%Y-%m-%d')}",
            report
        )


if __name__ == '__main__':
    main()