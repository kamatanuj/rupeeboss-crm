#!/bin/bash
# RupeeBoss CRM Rollback Script
# Usage: ./rollback.sh [commit_hash]
# If no commit_hash provided, shows available rollback points

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$SCRIPT_DIR"
LOG="$BASE_DIR/rollback.log"
BACKUP_DIR="$BASE_DIR/.rollback"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

# Function to create a rollback point
create_rollback_point() {
    local name="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local rollback_file="$BACKUP_DIR/rollback_${name}_${timestamp}.json"
    
    log "Creating rollback point: $name"
    
    # Backup current dashboard_data.json
    if [ -f "$BASE_DIR/public/dashboard_data.json" ]; then
        cp "$BASE_DIR/public/dashboard_data.json" "$rollback_file"
        log "✅ Rollback point created: $rollback_file"
        echo "$rollback_file"
    else
        log "❌ Error: dashboard_data.json not found"
        exit 1
    fi
}

# Function to list rollback points
list_rollback_points() {
    log "Available rollback points:"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR")" ]; then
        ls -lt "$BACKUP_DIR"/*.json 2>/dev/null | while read -r line; do
            echo "  $line"
        done
    else
        echo "  No rollback points found"
    fi
}

# Function to rollback to a specific point
rollback_to() {
    local rollback_file="$1"
    
    if [ ! -f "$rollback_file" ]; then
        log "❌ Error: Rollback file not found: $rollback_file"
        exit 1
    fi
    
    log "Rolling back to: $rollback_file"
    
    # Create backup of current state before rollback
    local current_backup="$BACKUP_DIR/pre_rollback_$(date +%Y%m%d_%H%M%S).json"
    cp "$BASE_DIR/public/dashboard_data.json" "$current_backup"
    log "Current state backed up to: $current_backup"
    
    # Restore the rollback file
    cp "$rollback_file" "$BASE_DIR/public/dashboard_data.json"
    log "✅ Dashboard data restored from: $rollback_file"
    
    # Commit and push the rollback
    cd "$BASE_DIR"
    git add public/dashboard_data.json
    git commit -m "Rollback: Restored dashboard_data from $(basename $rollback_file)"
    git push origin main
    
    log "✅ Rollback committed and pushed to GitHub"
    log "🌐 Live CRM will update shortly via GitHub Actions"
}

# Main logic
case "${1:-}" in
    "create")
        if [ -z "$2" ]; then
            echo "Usage: $0 create <rollback_name>"
            echo "Example: $0 create before_bulk_update"
            exit 1
        fi
        create_rollback_point "$2"
        ;;
    "list")
        list_rollback_points
        ;;
    "restore")
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <rollback_file>"
            echo "Example: $0 restore .rollback/rollback_stable_20260509_120000.json"
            exit 1
        fi
        rollback_to "$2"
        ;;
    *)
        echo "RupeeBoss CRM Rollback System"
        echo "=============================="
        echo ""
        echo "Commands:"
        echo "  $0 create <name>     - Create a rollback point"
        echo "  $0 list              - List available rollback points"
        echo "  $0 restore <file>   - Restore to a rollback point"
        echo ""
        echo "Examples:"
        echo "  $0 create before_email_update"
        echo "  $0 list"
        echo "  $0 restore .rollback/rollback_before_email_update_20260509_143000.json"
        echo ""
        list_rollback_points
        ;;
esac
