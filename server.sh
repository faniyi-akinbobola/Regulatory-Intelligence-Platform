#!/bin/bash
# ──────────────────────────────────────────────────────────────
# Regulatory Intelligence Platform — Server Management
# ──────────────────────────────────────────────────────────────
# Usage:
#   bash server.sh          → kill existing + start fresh (foreground)
#   bash server.sh stop     → kill any running server on port 8000
#   bash server.sh status   → show what's on port 8000
# ──────────────────────────────────────────────────────────────

set -e
cd "$(dirname "$0")"

CMD=${1:-start}

case "$CMD" in
  stop)
    PIDS=$(lsof -ti:8000 2>/dev/null)
    if [ -z "$PIDS" ]; then
      echo "No server running on port 8000."
    else
      echo "Stopping server (PID: $PIDS)…"
      echo "$PIDS" | xargs kill -9
      echo "Done."
    fi
    ;;

  status)
    PIDS=$(lsof -ti:8000 2>/dev/null)
    if [ -z "$PIDS" ]; then
      echo "Port 8000 is free."
    else
      echo "Port 8000 in use by PID(s): $PIDS"
      lsof -i:8000
    fi
    ;;

  start|*)
    # Kill anything already holding port 8000
    PIDS=$(lsof -ti:8000 2>/dev/null)
    if [ -n "$PIDS" ]; then
      echo "Clearing port 8000 (PID: $PIDS)…"
      echo "$PIDS" | xargs kill -9
      sleep 1
    fi

    echo "Starting Regulatory Intelligence Platform…"
    echo "  Backend : http://localhost:8000"
    echo "  Docs    : http://localhost:8000/docs"
    echo "  Press Ctrl+C to stop."
    echo ""
    source .venv/bin/activate
    uvicorn app.main:app --port 8000
    ;;
esac
