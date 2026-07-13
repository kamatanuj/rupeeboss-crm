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

# Step 1: Extract leads with REAL summaries and transcripts
log "Building leads with real summaries and transcripts..."
/usr/bin/python3.12 complete_rebuild.py >> "$LOG" 2>&1 || log "Complete rebuild finished"

# Step 2: Sync conversation database (now handled inside complete_rebuild.py)
# Kept as optional fallback
log "Sync step is integrated in complete_rebuild.py; running light sync fallback..."
/usr/bin/python3.12 sync_conversations.py >> "$LOG" 2>&1 || log "DB sync completed"

# Step 3: Build dashboard from real rebuild output
log "Updating dashboard_data.json from rebuild..."
python3 build-dashboard.py >> "$LOG" 2>&1 || log "Dashboard build completed"

# Step 3: Commit changes to GitHub
log "Committing changes to GitHub..."
git add -A >> "$LOG" 2>&1
git commit -m "Auto-update: Add new leads $(date +%Y-%m-%d_%H:%M)" >> "$LOG" 2>&1 || log "No changes to commit"
# Pull --rebase first: another repo (/root/.openclaw/workspace/rupeeboss via Hermes cron)
# pushes to the same remote, so our push will fail without rebasing first.
git pull --rebase origin main >> "$LOG" 2>&1 || log "Pull rebase failed - check manually"
git push origin main >> "$LOG" 2>&1 || log "Push may have failed - check manually"

# Step 4: Deploy via GitHub Actions (Cloudflare Pages auto-deploy)
log "GitHub Actions will auto-deploy to Cloudflare Pages..."
log "Monitor at: https://github.com/kamatanuj/rupeeboss-crm/actions"

# Step 5: Promote latest deployment to production (fallback)
log "Promoting deployment to production..."
DEPLOY_ID=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/rupeeboss-crm/deployments" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['id'])" 2>/dev/null || echo "")

if [ -n "$DEPLOY_ID" ]; then
    curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/rupeeboss-crm" \
      -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"canonical_deployment\": \"$DEPLOY_ID\"}" > /dev/null
    log "Promoted deployment to production"
fi

log "✅ Auto-update complete!"
log "🌐 Live CRM: https://rupeeboss-crm.pages.dev"
log "=========================================="
