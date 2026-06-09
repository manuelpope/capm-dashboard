#!/bin/bash
set -e

echo "Initializing database..."
mkdir -p /app/data

export DB_PATH=/app/data/capm.db
export PYTHONPATH=/app/.venv/lib/python3.12/site-packages:/app

/usr/local/bin/python3 -c "
from src.capm.domain.repositories import SQLiteMetricRepository
db = SQLiteMetricRepository()
print('Database initialized successfully')
"

# Run uvicorn directly with proper environment
echo "Starting uvicorn..."
exec /usr/local/bin/python3 -m uvicorn src.capm.main:app --host 0.0.0.0 --port 8000