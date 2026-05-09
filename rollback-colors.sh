#!/bin/bash
# Rollback to previous color scheme (dark theme)
# Usage: ./rollback-colors.sh

cd "$(dirname "$0")"

# Find the most recent backup
BACKUP=$(ls -t .rollback/index_backup_before_color_scheme_*.html 2>/dev/null | head -1)

if [ -z "$BACKUP" ]; then
    echo "❌ No color scheme backup found"
    echo "Available backups:"
    ls -la .rollback/index_backup_before_color_scheme_*.html 2>/dev/null || echo "None"
    exit 1
fi

echo "🔄 Rolling back to previous color scheme..."
echo "📄 Backup file: $BACKUP"

# Backup current state before rollback
cp public/index.html .rollback/index_current_before_rollback_$(date +%Y%m%d_%H%M%S).html

# Restore the old color scheme
cp "$BACKUP" public/index.html

# Commit and push
git add public/index.html
git commit -m "Rollback: Restore previous dark color scheme from $BACKUP"
git push origin main

echo "✅ Color scheme rolled back successfully!"
echo "🌐 Changes will be live in 2-3 minutes"
echo "📊 URL: https://rupeeboss-crm.pages.dev"
