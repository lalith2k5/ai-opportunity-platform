#!/bin/bash
cd ~/ai-opportunity-platform/backend
source venv/bin/activate

# Ensure PostgreSQL is running
if ! pg_isready -q 2>/dev/null; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@17
    sleep 3
fi

echo "Starting backend on http://localhost:8000"
uvicorn app.main:app --reload --port 8000
