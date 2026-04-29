#!/bin/bash
# Rupeeboss CRM Auto-Update & Deploy Script
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

CLOUDFLARE_TOKEN="${CLOUDFLARE_API_TOKEN}"
CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID}"
BASE_DIR="$SCRIPT_DIR"
LOG="$BASE_DIR/update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

cd "$BASE_DIR"

log "=========================================="
log "Rupeeboss CRM Auto-Update Starting..."

# Step 1: Extract leads from D-insights
log "Extracting leads from D-insights..."
python3 extract-leads.py >> "$LOG" 2>&1

# Step 2: Generate static HTML
log "Generating static CRM..."
python3 << 'PYEOF' >> /dev/null
import csv
import json
from datetime import datetime

leads = []
with open('/root/.openclaw/workspace/rupeeboss/leads.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        leads.append(row)

hot = [l for l in leads if l['Phone']]
cold = [l for l in leads if not l['Phone']]
leads_json = json.dumps(leads)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rupeeboss CRM - Lead Management</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%); min-height: 100vh; color: #fff; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
    .logo {{ font-size: 24px; font-weight: bold; color: #f59e0b; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 25px 0; }}
    .stat-card {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); }}
    .stat-value {{ font-size: 28px; font-weight: bold; color: #f59e0b; }}
    .stat-label {{ color: rgba(255,255,255,0.6); font-size: 12px; margin-top: 5px; }}
    .stat-card.hot {{ border-top: 3px solid #ef4444; }}
    .stat-card.cold {{ border-top: 3px solid #6b7280; }}
    .search-box {{ width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); color: #fff; margin: 15px 0; }}
    .filter-tabs {{ display: flex; gap: 10px; margin: 15px 0; }}
    .filter-tab {{ padding: 8px 16px; border-radius: 20px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid transparent; transition: all 0.3s; }}
    .filter-tab.active {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border-color: #f59e0b; }}
    .leads-table {{ background: rgba(255,255,255,0.03); border-radius: 12px; overflow: hidden; }}
    .table-header {{ display: grid; grid-template-columns: 2fr 2fr 1.5fr 1fr 100px; padding: 14px 16px; background: rgba(255,255,255,0.05); font-weight: 600; font-size: 11px; text-transform: uppercase; color: rgba(255,255,255,0.6); gap: 10px; }}
    .lead-row {{ display: grid; grid-template-columns: 2fr 2fr 1.5fr 1fr 100px; padding: 14px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); gap: 10px; align-items: center; }}
    .lead-row:hover {{ background: rgba(255,255,255,0.03); }}
    .status-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }}
    .status-hot {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}
    .status-cold {{ background: #6b7280; }}
    .lead-status {{ display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 11px; }}
    .status-hot-bg {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
    .status-cold-bg {{ background: rgba(107, 114, 128, 0.2); color: #6b7280; }}
    .phone {{ font-family: monospace; color: #f59e0b; }}
    .empty {{ text-align: center; padding: 40px; color: rgba(255,255,255,0.5); }}
    .note {{ background: rgba(255,255,255,0.05); padding: 10px 15px; border-radius: 8px; font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 20px; }}
    .updated {{ color: rgba(255,255,255,0.4); font-size: 12px; }}
    .action-btn {{ padding: 6px 12px; border-radius: 6px; border: none; background: rgba(245, 158, 11, 0.2); color: #f59e0b; cursor: pointer; }}
    .action-btn:disabled {{ opacity: 0.3; cursor: not-allowed; }}
    @media (max-width: 768px) {{ .table-header, .lead-row {{ grid-template-columns: 1fr 1fr; }} .lead-row > *:nth-child(n+3) {{ display: none; }} }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">💰 Rupeeboss CRM</div>
      <div class="updated">Updated: {now}</div>
    </div>

    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">{len(leads)}</div><div class="stat-label">Total Leads</div></div>
      <div class="stat-card hot"><div class="stat-value">{len(hot)}</div><div class="stat-label">🔥 Hot Leads</div></div>
      <div class="stat-card"><div class="stat-value">{len(hot)}</div><div class="stat-label">📱 With Phone</div></div>
      <div class="stat-card cold"><div class="stat-value">{len(cold)}</div><div class="stat-label">❄️ Cold</div></div>
    </div>

    <input type="text" class="search-box" id="searchInput" placeholder="🔍 Search by name, email, phone..." oninput="filterLeads()">

    <div class="filter-tabs">
      <div class="filter-tab active" onclick="setFilter('all')">All ({len(leads)})</div>
      <div class="filter-tab" onclick="setFilter('Hot')">🔥 Hot ({len(hot)})</div>
      <div class="filter-tab" onclick="setFilter('Cold')">❄️ Cold ({len(cold)})</div>
    </div>

    <div class="leads-table">
      <div class="table-header">
        <div>Name</div><div>Email</div><div>Phone</div><div>Status</div><div>Action</div>
      </div>
      <div id="leadsList"></div>
    </div>

    <div class="note">💡 <b>Auto-Updated</b> from D-insights CRM API. Last sync: {now}</div>
  </div>

  <script>
    const LEADS_DATA = {leads_json};

    let currentFilter = 'all';
    let searchQuery = '';

    function renderLeads() {{
      const container = document.getElementById('leadsList');
      let filtered = LEADS_DATA;
      
      if (currentFilter !== 'all') filtered = filtered.filter(l => (l.Phone ? 'Hot' : 'Cold') === currentFilter);
      if (searchQuery) {{
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(l => 
          (l.Name && l.Name.toLowerCase().includes(q)) ||
          l.Email.toLowerCase().includes(q) ||
          (l.Phone && l.Phone.includes(q))
        );
      }}
      
      if (filtered.length === 0) {{
        container.innerHTML = '<div class="empty">No leads found</div>';
        return;
      }}
      
      container.innerHTML = filtered.map(l => `
        <div class="lead-row">
          <div><span class="status-dot status-${{l.Phone ? 'hot' : 'cold'}}"></span>${{l.Name || 'N/A'}}</div>
          <div style="color:rgba(255,255,255,0.8);">${{l.Email || '-'}}</div>
          <div class="phone">${{l.Phone || '-'}}</div>
          <div><span class="lead-status status-${{l.Phone ? 'hot' : 'cold'}}-bg">${{l.Phone ? '🔥 Hot' : '❄️ Cold'}}</span></div>
          <div><button class="action-btn" onclick="window.open('tel:${{l.Phone}}')" ${{!l.Phone ? 'disabled' : ''}}>📞</button></div>
        </div>
      `).join('');
    }}

    function setFilter(f) {{
      currentFilter = f;
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');
      renderLeads();
    }}

    function filterLeads() {{
      searchQuery = document.getElementById('searchInput').value;
      renderLeads();
    }}

    renderLeads();
  </script>
</body>
</html>'''

import os
os.makedirs('/tmp/rupeeboss-deploy', exist_ok=True)
with open('/tmp/rupeeboss-deploy/index.html', 'w') as f:
    f.write(html)
print(f"Generated: {len(leads)} leads ({len(hot)} hot)")
PYEOF

# Step 3: Deploy to Cloudflare Pages
log "Deploying to Cloudflare Pages..."
export CLOUDFLARE_API_TOKEN="$CLOUDFLARE_TOKEN"
export CLOUDFLARE_ACCOUNT_ID="$CLOUDFLARE_ACCOUNT_ID"

cd /tmp && wrangler pages deploy rupeeboss-deploy --project-name=rupeeboss-crm 2>&1 | tee -a "$LOG"

# Promote latest deployment to production
DEPLOY_ID=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/rupeeboss-crm/deployments" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['id'])")

curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/rupeeboss-crm" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"canonical_deployment\": \"$DEPLOY_ID\"}" > /dev/null

log "Promoted deployment to production"
log "🌐 Live CRM: https://rupeeboss-crm.pages.dev"
