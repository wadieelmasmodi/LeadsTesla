#!/bin/bash
set -euo pipefail

# Ensure data directory exists
mkdir -p /data

# Create database tables if they don't exist
echo "Initializing database tables..."
export PYTHONPATH=/app
python3 << 'EOF'
from app_factory import create_app
from models import db
app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables initialized successfully")
EOF

echo "Starting web server..."
export PYTHONPATH=/app
exec gunicorn --access-logfile - --error-logfile - web:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 2 --timeout 120 --log-level debug