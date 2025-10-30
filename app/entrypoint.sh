#!/bin/bash
set -e

# Ensure data directory exists
mkdir -p /data

# Start Flask web server in background
python web.py &
WEB_PID=$!

# Start the main scraper
python main.py &
SCRAPER_PID=$!

# Trap SIGTERM and forward it to the processes
trap "kill $WEB_PID $SCRAPER_PID" SIGTERM

# Wait for either process to exit
wait -n $WEB_PID $SCRAPER_PID

# If we get here, one of the processes died, kill the other and exit with error
kill $WEB_PID $SCRAPER_PID 2>/dev/null || true
exit 1