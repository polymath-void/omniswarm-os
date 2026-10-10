#!/usr/bin/env bash
# ==============================================================================
# OmniSwarm Phone Agent Background Daemonizer
# Keeps phone_agent.py running in the background 24/7 without manual intervention.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.phone_agent.pid"
LOG_FILE="$SCRIPT_DIR/phone_agent.log"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo ">>> Phone Agent is already running (PID: $(cat "$PID_FILE"))."
      exit 0
    fi
    echo ">>> Starting OmniSwarm Phone Agent in the background..."
    setsid python3 -u phone_agent.py --loop-only >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    echo ">>> ✅ Phone Agent started successfully (PID: $(cat "$PID_FILE"))."
    echo ">>> Logs are actively streaming to: $LOG_FILE"
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      echo ">>> Stopping Phone Agent (PID: $PID)..."
      kill "$PID" 2>/dev/null || true
      rm -f "$PID_FILE"
      echo ">>> ✅ Phone Agent stopped."
    else
      echo ">>> No active Phone Agent PID file found. Checking process list..."
      pkill -f "phone_agent.py --loop-only" || echo ">>> Phone Agent is not running."
    fi
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo ">>> 🟢 Phone Agent is ACTIVE and RUNNING (PID: $(cat "$PID_FILE"))."
      echo ">>> Recent Activity Logs:"
      tail -n 10 "$LOG_FILE"
    else
      echo ">>> 🔴 Phone Agent is NOT running."
    fi
    ;;
  restart)
    bash "$0" stop
    sleep 1
    bash "$0" start
    ;;
  *)
    echo "Usage: bash daemonize_phone.sh {start|stop|status|restart}"
    exit 1
    ;;
esac
