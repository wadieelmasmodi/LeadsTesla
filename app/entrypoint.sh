#!/bin/bash
set -euo pipefail

# Entrypoint that keeps the Flask web server in foreground so the container
# stays alive. The scraper (one-shot) runs in background and its failures
# won't mark the container as degraded.

# Ensure data directory exists
mkdir -p /data

echo "Starting scraper in background..."
nohup python main.py > /data/scraper.log 2>&1 &
SCRAPER_PID=$!
echo "Scraper started (pid=$SCRAPER_PID). Logs: /data/scraper.log"

echo "Starting Flask web server in foreground..."
# Run Flask in foreground (this will be the main container process)
export FLASK_APP=web.py
export PYTHONPATH=/app
exec python -m flask run --host=0.0.0.0 --port=${PORT:-8000}