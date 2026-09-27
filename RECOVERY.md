# Recovery Procedures

## Overview

This document describes how to restore the AI Opportunity Discovery Platform from backups.

## Backup Locations

- Database dumps: ~/ai-opportunity-platform/backups/db_ai_opportunity_db_YYYYMMDD_HHMMSS.sql
- Config archives: ~/ai-opportunity-platform/backups/config_YYYYMMDD_HHMMSS.tar.gz
- Verification log: ~/ai-opportunity-platform/backups/verify.log
- Application logs: ~/ai-opportunity-platform/backend/logs/app_YYYY-MM-DD.log

Backups run daily at 3:30 AM via launchd (~/Library/LaunchAgents/com.aod.backup.plist).
Retention: last 7 of each.

## Scenario 1: Restore Database (Corruption)

    cd ~/ai-opportunity-platform

    # 1. Stop backend
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true

    # 2. List available backups
    ls -lh backups/db_*.sql

    # 3. Drop and recreate
    dropdb ai_opportunity_db
    createdb ai_opportunity_db

    # 4. Restore (pick the latest)
    psql -d ai_opportunity_db < backups/db_ai_opportunity_db_YYYYMMDD_HHMMSS.sql

    # 5. Restart backend
    bash start-backend.sh

## Scenario 2: Restore Configuration

    tar -xzf backups/config_YYYYMMDD_HHMMSS.tar.gz -C ~/
    ls -la .env backend/.env

## Scenario 3: Full Rebuild (Fresh Machine)

    git clone https://github.com/lalith2k5/ai-opportunity-platform.git
    cd ai-opportunity-platform
    tar -xzf /path/to/config_*.tar.gz -C ~/
    dropdb ai_opportunity_db 2>/dev/null
    createdb ai_opportunity_db
    psql -d ai_opportunity_db < backups/db_ai_opportunity_db_YYYYMMDD_HHMMSS.sql

    cd backend
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    cd ..

    cd frontend
    npm install
    cd ..

    bash start-all.sh

## Scenario 4: Docker Stack Restore

    cd ~/ai-opportunity-platform
    docker compose down
    docker compose up -d postgres
    sleep 15
    docker exec -i aod_postgres psql -U aod_user -d ai_opportunity_db < backups/db_ai_opportunity_db_YYYYMMDD_HHMMSS.sql
    docker compose up -d

## Verification

Always verify backups before relying on them:

    bash verify_backup.sh

This creates a scratch database, restores the latest backup, checks row counts, and reports success/failure.

## Scheduling

The launchd plist at ~/Library/LaunchAgents/com.aod.backup.plist runs backup.sh daily at 3:30 AM.

To view the schedule:

    launchctl list | grep aod

To disable:

    launchctl unload ~/Library/LaunchAgents/com.aod.backup.plist

To re-enable:

    launchctl load ~/Library/LaunchAgents/com.aod.backup.plist

## Logs

- Backup runs: ~/ai-opportunity-platform/backups/launchd.log
- Errors: ~/ai-opportunity-platform/backups/launchd.err
- Verification: ~/ai-opportunity-platform/backups/verify.log

## Emergency Contacts

- Project maintainer: Lalith Vajja (lalithvajja@gmail.com)
- Repository: https://github.com/lalith2k5/ai-opportunity-platform
