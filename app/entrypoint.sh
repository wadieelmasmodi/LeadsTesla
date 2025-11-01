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

echo "Starting web server in background..."
export PYTHONPATH=/app
gunicorn --access-logfile - --error-logfile - web:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 2 --timeout 120 --log-level debug &
WEB_PID=$!
echo "Web server started (pid=$WEB_PID)"

echo "Starting scraper in background..."
nohup python main.py > /data/scraper.log 2>&1 &
SCRAPER_PID=$!
echo "Scraper started (pid=$SCRAPER_PID). Logs: /data/scraper.log"

# Wait for any process to exit
wait -n
# Exit with status of process that exited first
exit $?
export PYTHONPATH=/app
exec python -m flask run --host=0.0.0.0 --port=${PORT:-8000}