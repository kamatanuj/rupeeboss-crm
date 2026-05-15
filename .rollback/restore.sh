#!/bin/bash
# Rupeeboss CRM Rollback Script
# Usage: ./restore.sh [backup-file]

if [ -z "$1" ]; then
    echo "Available backups:"
    ls -lt ./*.tar.gz 2>/dev/null || echo "No backups found"
    echo ""
    echo "Usage: ./restore.sh rupeeboss-crm-YYYYMMDD_HHMMSS.tar.gz"
    exit 1
fi

BACKUP="$1"
if [ ! -f "$BACKUP" ]; then
    echo "Error: Backup file not found: $BACKUP"
    exit 1
fi

echo "Restoring from $BACKUP..."
cd ..
tar -xzf .rollback/"$BACKUP"
echo "✅ Restore complete!"
echo "Deploy with: npx wrangler pages deploy public --project-name=rupeeboss-crm --branch=main"
