#!/bin/bash
BACKUP_DIR="$HOME/ai-opportunity-platform/backups"
DB_NAME="ai_opportunity_db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

mkdir -p "$BACKUP_DIR"
echo "[$(date)] Starting backup of $DB_NAME..."
pg_dump -d "$DB_NAME" > "$BACKUP_FILE" 2>&1

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup successful: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] Backup FAILED" >&2
    exit 1
fi

# Keep only the last 7 backups
cd "$BACKUP_DIR"
ls -t ${DB_NAME}_*.sql 2>/dev/null | tail -n +8 | xargs -r rm
echo "[$(date)] Cleanup done. Current backups:"
ls -lh ${DB_NAME}_*.sql 2>/dev/null | tail -5
