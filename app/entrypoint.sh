#!/bin/bash
set -euo pipefail

# Ensure data directory exists
mkdir -p /data

echo "Starting web server in background..."
gunicorn web:app --bind 0.0.0.0:${PORT:-8000} --log-level info &
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