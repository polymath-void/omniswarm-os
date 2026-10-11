#!/usr/bin/env bash
# ==============================================================================
# OmniSwarm Cockpit UI Launcher & Background Daemonizer
# Turnkey script to boot the token-free Cockpit UI on Android Termux & Linux
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.omniswarm_ui.pid"
LOG_FILE="$SCRIPT_DIR/omniswarm_ui.log"
PORT=8765

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo ">>> OmniSwarm Cockpit is already running (PID: $(cat "$PID_FILE"))."
      echo ">>> Access URL: http://localhost:$PORT"
      exit 0
    fi
    pkill -f "omniswarm_ui_server.py" 2>/dev/null || true
    echo ">>> Starting OmniSwarm Cockpit UI daemon..."
    setsid python3 -u omniswarm_ui_server.py >> "$LOG_FILE" 2>&1 &
    sleep 0.8
    PID=$(pgrep -f "omniswarm_ui_server.py" 2>/dev/null | tail -n 1)
    if [ -n "$PID" ]; then
      echo "$PID" > "$PID_FILE"
      echo ">>> ✅ Cockpit Server started successfully (PID: $PID)."
    else
      echo ">>> ✅ Cockpit Server started."
    fi
    echo ">>> 🌐 Local Access : http://localhost:$PORT"
    echo ">>> 📱 LAN Access   : http://192.168.0.103:$PORT"
    echo ">>> 📄 Logs         : $LOG_FILE"
    
    # Auto-open in Android browser if termux-open-url is available
    if command -v termux-open-url >/dev/null 2>&1; then
      echo ">>> 🚀 Launching browser..."
      termux-open-url "http://localhost:$PORT"
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "http://localhost:$PORT" 2>/dev/null || true
    fi
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      echo ">>> Stopping Cockpit Server (PID: $PID)..."
      kill "$PID" 2>/dev/null || true
      rm -f "$PID_FILE"
      echo ">>> ✅ Cockpit Server stopped."
    fi
    pkill -f "omniswarm_ui_server.py" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo ">>> ✅ Cleared active Cockpit processes."
    ;;
  status)
    CURRENT_PID=""
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      CURRENT_PID=$(cat "$PID_FILE")
    else
      FALLBACK_PID=$(pgrep -f "omniswarm_ui_server.py" 2>/dev/null | head -n 1)
      if [ -n "$FALLBACK_PID" ]; then
        CURRENT_PID=$FALLBACK_PID
        echo "$CURRENT_PID" > "$PID_FILE"
      fi
    fi

    if [ -n "$CURRENT_PID" ]; then
      echo ">>> 🟢 Cockpit UI Server is ACTIVE and RUNNING (PID: $CURRENT_PID)."
      echo ">>> 🌐 Local Access : http://localhost:$PORT"
      echo ">>> 📱 LAN Access   : http://192.168.0.103:$PORT"
      echo ">>> Recent Logs:"
      tail -n 8 "$LOG_FILE" 2>/dev/null || true
    else
      echo ">>> 🔴 Cockpit UI Server is NOT running."
    fi
    ;;
  restart)
    bash "$0" stop
    sleep 1
    bash "$0" start
    ;;
  open)
    if command -v termux-open-url >/dev/null 2>&1; then
      termux-open-url "http://localhost:$PORT"
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "http://localhost:$PORT" 2>/dev/null || true
    fi
    ;;
  *)
    echo "Usage: bash omniswarm_ui.sh {start|stop|status|restart|open}"
    exit 1
    ;;
esac
