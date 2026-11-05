#!/usr/bin/env bash
echo "========================================================================"
echo "  Stopping AI Virtual Teacher Services (Ports 8000, 3000, 3001)..."
echo "========================================================================"

STOPPED=0
for PORT in 8000 3000 3001; do
    if command -v lsof >/dev/null 2>&1; then
        PIDS=$(lsof -ti :$PORT 2>/dev/null)
        if [ -n "$PIDS" ]; then
            echo "Stopping service on port $PORT (PID: $PIDS)..."
            kill -9 $PIDS 2>/dev/null || true
            STOPPED=1
        fi
    elif command -v fuser >/dev/null 2>&1; then
        echo "Stopping service on port $PORT..."
        fuser -k $PORT/tcp 2>/dev/null || true
        STOPPED=1
    fi
done

for PIDFILE in .backend.pid .classroom.pid .dashboard.pid; do
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Killing process $PID from $PIDFILE..."
            kill -9 "$PID" 2>/dev/null || true
            STOPPED=1
        fi
        rm -f "$PIDFILE"
    fi
done

if [ "$STOPPED" -eq 0 ]; then
    echo "No active services found on ports 8000, 3000, or 3001."
else
    echo "All AI Virtual Teacher services have been stopped."
fi
echo "========================================================================"
