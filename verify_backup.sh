#!/bin/bash
# Verifies the most recent DB backup can be restored to a scratch database.

set -e
BACKUP_ROOT="$HOME/ai-opportunity-platform/backups"
TEST_DB="ai_opportunity_verify_$(date +%s)"
LATEST=$(ls -t "$BACKUP_ROOT"/db_ai_opportunity_db_*.sql 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "FAIL: No backup found in $BACKUP_ROOT"
    exit 1
fi

echo "[$(date)] Verifying: $LATEST"
echo "[$(date)] Creating scratch DB: $TEST_DB"

createdb "$TEST_DB"

echo "[$(date)] Restoring..."
if psql -q -d "$TEST_DB" < "$LATEST" > /dev/null 2>&1; then
    ROWS=$(psql -t -d "$TEST_DB" -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
    OPPS=$(psql -t -d "$TEST_DB" -c "SELECT COUNT(*) FROM opportunities;" | tr -d ' ')
    echo "[$(date)] OK: Restored successfully"
    echo "  Users: $ROWS"
    echo "  Opportunities: $OPPS"
    RESULT=0
else
    echo "[$(date)] FAIL: Restore failed"
    RESULT=1
fi

dropdb "$TEST_DB" 2>/dev/null

if [ $RESULT -eq 0 ]; then
    echo "[$(date)] Backup is RESTORABLE ✓"
    echo "$(date): OK — $LATEST" >> "$BACKUP_ROOT/verify.log"
else
    echo "[$(date)] Backup is CORRUPT ✗"
    echo "$(date): FAIL — $LATEST" >> "$BACKUP_ROOT/verify.log"
    exit 1
fi
