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
    pkill -f "phone_agent.py --loop-only" 2>/dev/null || true
    echo ">>> Starting OmniSwarm Phone Agent in the background..."
    setsid python3 -u phone_agent.py --loop-only >> "$LOG_FILE" 2>&1 &
    sleep 0.5
    PID=$(pgrep -f "phone_agent.py --loop-only" 2>/dev/null | tail -n 1)
    if [ -n "$PID" ]; then
      echo $PID > "$PID_FILE"
      echo ">>> ✅ Phone Agent started successfully (PID: $PID)."
    else
      echo ">>> ✅ Phone Agent started."
    fi
    echo ">>> Logs are actively streaming to: $LOG_FILE"
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      echo ">>> Stopping Phone Agent (PID: $PID)..."
      kill "$PID" 2>/dev/null || true
      rm -f "$PID_FILE"
      echo ">>> ✅ Phone Agent stopped."
    fi
    pkill -f "phone_agent.py --loop-only" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo ">>> ✅ Checked process list and cleared active agent processes."
    ;;
  status)
    CURRENT_PID=""
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      CURRENT_PID=$(cat "$PID_FILE")
    else
      FALLBACK_PID=$(pgrep -f "phone_agent.py --loop-only" 2>/dev/null | head -n 1)
      if [ -n "$FALLBACK_PID" ]; then
        CURRENT_PID=$FALLBACK_PID
        echo $CURRENT_PID > "$PID_FILE"
      fi
    fi

    if [ -n "$CURRENT_PID" ]; then
      echo ">>> 🟢 Phone Agent is ACTIVE and RUNNING (PID: $CURRENT_PID)."
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
