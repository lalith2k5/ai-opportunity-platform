#!/bin/bash
# Full backup: PostgreSQL + configs + ChromaDB metadata + env templates

set -e
BACKUP_ROOT="$HOME/ai-opportunity-platform/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_opportunity_db"
DB_FILE="$BACKUP_ROOT/db_${DB_NAME}_${TIMESTAMP}.sql"
CONFIG_FILE="$BACKUP_ROOT/config_${TIMESTAMP}.tar.gz"
PROJECT_ROOT="$HOME/ai-opportunity-platform"

mkdir -p "$BACKUP_ROOT"

echo "[$(date)] === Backup started ==="

# 1. PostgreSQL dump
echo "[$(date)] Dumping database..."
pg_dump -d "$DB_NAME" > "$DB_FILE"
DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
echo "[$(date)] DB backup: $DB_FILE ($DB_SIZE)"

# 2. Config files (env files, docker-compose, scripts, README)
echo "[$(date)] Archiving configs..."
CONFIG_PATHS=(
    "$PROJECT_ROOT/.env"
    "$PROJECT_ROOT/.env.example"
    "$PROJECT_ROOT/docker-compose.yml"
    "$PROJECT_ROOT/backup.sh"
    "$PROJECT_ROOT/start-all.sh"
    "$PROJECT_ROOT/start-backend.sh"
    "$PROJECT_ROOT/start-frontend.sh"
    "$PROJECT_ROOT/README.md"
    "$PROJECT_ROOT/backend/.env"
    "$PROJECT_ROOT/backend/.env.example"
    "$PROJECT_ROOT/backend/requirements.txt"
    "$PROJECT_ROOT/frontend/package.json"
)
tar -czf "$CONFIG_FILE" \
    --exclude='node_modules' --exclude='venv' --exclude='__pycache__' \
    $(printf '%s\n' "${CONFIG_PATHS[@]}" | while read f; do [ -f "$f" ] && echo "$f"; done) \
    2>/dev/null || true
CONFIG_SIZE=$(du -h "$CONFIG_FILE" | cut -f1)
echo "[$(date)] Config backup: $CONFIG_FILE ($CONFIG_SIZE)"

# 3. Retention: keep last 7 DB dumps, last 7 config archives
cd "$BACKUP_ROOT"
ls -t db_${DB_NAME}_*.sql 2>/dev/null | tail -n +8 | xargs -r rm
ls -t config_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo "[$(date)] === Backup complete ==="
echo "Current backups:"
ls -lh "$BACKUP_ROOT" | tail -20
