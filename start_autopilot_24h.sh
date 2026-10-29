#!/usr/bin/env bash
# ==============================================================================
# 24/7 Autonomous Career Agent Launcher (Zero-Cost, Multi-Agent Loop)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.autopilot.pid"
LOG_FILE="$SCRIPT_DIR/autopilot_24h.log"

PY_BIN="/opt/anaconda3/bin/python3"
if [ ! -x "$PY_BIN" ]; then
  PY_BIN="python3"
fi

case "${1:-run}" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "⚡ Autopilot daemon is already running (PID: $(cat "$PID_FILE"))."
      exit 0
    fi
    echo "🚀 Starting 24-Hour Autonomous Career Agent in background (using $PY_BIN)..."
    PYTHONUNBUFFERED=1 nohup "$PY_BIN" "$SCRIPT_DIR/scripts/autopilot_24h_agent.py" --job-interval-minutes 5.0 --email-interval 5.0 --min-score 30 >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ Agent started with PID $(cat "$PID_FILE")."
    echo "📄 Streaming logs to $LOG_FILE"
    ;;

  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        echo "🛑 Stopping Autopilot daemon (PID: $PID)..."
        kill -TERM "$PID"
        rm -f "$PID_FILE"
        echo "✓ Agent stopped."
      else
        echo "⚠️ Stale PID file found. Removing."
        rm -f "$PID_FILE"
      fi
    else
      echo "ℹ️ No running agent found."
    fi
    ;;

  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "🟢 Autopilot daemon is RUNNING (PID: $(cat "$PID_FILE"))."
    else
      echo "🔴 Autopilot daemon is STOPPED."
    fi
    "$PY_BIN" "$SCRIPT_DIR/scripts/autopilot_24h_agent.py" --status
    ;;

  logs)
    if [ -f "$LOG_FILE" ]; then
      echo "📋 Following live 24/7 Autopilot logs (Press Ctrl+C to exit log view):"
      tail -f "$LOG_FILE"
    else
      echo "⚠️ No log file found yet at $LOG_FILE"
    fi
    ;;

  once)
    echo "🔄 Running a single execution cycle (job fetch + tailor + email audit + excel sync)..."
    "$PY_BIN" "$SCRIPT_DIR/scripts/autopilot_24h_agent.py" --once
    ;;

  *)
    echo "Usage: $0 {start|stop|status|logs|once}"
    exit 1
    ;;
esac
