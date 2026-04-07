#!/bin/bash
set -e

echo "Initializing database..."
python -c "
from src.capm.domain.repositories import SQLiteMetricRepository
db = SQLiteMetricRepository()
print('Database initialized successfully')
"

exec "$@"