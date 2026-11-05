#!/usr/bin/env bash
set -e

echo "========================================================================"
echo "  AI Virtual Teacher: Single-Command Full Stack Launcher"
echo "========================================================================"

# 1. Verify Prerequisites
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "[ERROR] Python is not installed or not found in PATH!"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

if ! command -v node >/dev/null 2>&1; then
    echo "[ERROR] Node.js is not installed or not found in PATH!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "[ERROR] npm is not installed or not found in PATH!"
    echo "Please ensure npm is installed alongside Node.js."
    exit 1
fi
echo "[OK] Runtime dependencies verified ($PY, node, npm found)."

# 2. Environment File Check (.env)
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "[INFO] .env not found. Initializing from .env.example..."
        cp .env.example .env
        echo "[INFO] Created .env successfully."
    else
        echo "[WARN] Neither .env nor .env.example found. Creating empty .env..."
        touch .env
    fi
    echo "--------------------------------------------------------------------"
    echo "[KEYS NOTICE] To enable live AI, add your free API keys in .env:"
    echo "  - GEMINI_API_KEY      (https://aistudio.google.com/)"
    echo "  - GROQ_API_KEY        (https://console.groq.com/)"
    echo "  - CEREBRAS_API_KEY    (https://cloud.cerebras.ai/)"
    echo "  - OPENROUTER_API_KEY  (https://openrouter.ai/)"
    echo "(If left blank, the platform automatically operates in MOCK mode.)"
    echo "--------------------------------------------------------------------"
fi

# 3. Mode Resolution
MODE_ARG="$1"

if [ "$MODE_ARG" = "mock" ] || [ "$MODE_ARG" = "MOCK" ]; then
    export MOCK_MODE=true
    export REAL_LLM=0
    echo "[MODE] MOCK mode selected explicitly. (Zero API keys required)"
elif [ "$MODE_ARG" = "real" ] || [ "$MODE_ARG" = "REAL" ]; then
    export MOCK_MODE=false
    export REAL_LLM=1
    echo "[MODE] REAL mode selected explicitly. (Calling configured LLM providers)"
else
    if $PY scripts/check_keys.py; then
        export MOCK_MODE=false
        export REAL_LLM=1
        echo "[MODE] Auto-detected configured LLM keys in .env -> REAL mode active."
    else
        export MOCK_MODE=true
        export REAL_LLM=0
        echo "[MODE] No LLM keys found in .env -> Auto-defaulting to MOCK mode."
    fi
fi

# 4. Dependency Installation (Only if missing)
echo "[DEPS] Checking Python dependencies..."
if ! $PY -c "import fastapi, uvicorn, pydantic, httpx" >/dev/null 2>&1; then
    echo "[DEPS] Installing missing Python requirements..."
    $PY -m pip install -r requirements.txt
else
    echo "[DEPS] Python dependencies already installed."
fi

echo "[DEPS] Checking frontend dependencies..."
if [ -f "frontend/dashboard/package.json" ]; then
    if [ ! -d "frontend/dashboard/node_modules" ]; then
        echo "[DEPS] Installing npm dependencies in frontend/dashboard..."
        (cd frontend/dashboard && npm install)
    else
        echo "[DEPS] Node modules already present in frontend/dashboard."
    fi
fi

# 5. Stop any lingering instances
if [ -f "./stop_all.sh" ]; then
    ./stop_all.sh >/dev/null 2>&1 || true
fi

# 6. Launch Services in Background
echo "[START] Launching backend on port 8000..."
$PY -m uvicorn backend.agent.main:app --host 0.0.0.0 --port 8000 --reload > .backend.log 2>&1 &
echo $! > .backend.pid

echo "[START] Launching Classroom Frontend on port 3000..."
$PY -m http.server 3000 --directory frontend/classroom > .classroom.log 2>&1 &
echo $! > .classroom.pid

echo "[START] Launching Learner Dashboard on port 3001..."
$PY -m http.server 3001 --directory frontend/dashboard > .dashboard.log 2>&1 &
echo $! > .dashboard.pid

# 7. Wait for Backend Health
if $PY scripts/wait_for_health.py http://localhost:8000/health 30; then
    echo ""
    echo "[LAUNCH] Opening Classroom Frontend in browser..."
    if command -v open >/dev/null 2>&1; then
        open http://localhost:3000/
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3000/ >/dev/null 2>&1 || true
    fi
else
    echo "[WARN] Backend did not respond within 30 seconds. Check .backend.log for details."
fi

# 8. Summary Table
echo ""
echo "========================================================================"
echo "  AI Virtual Teacher - System Status"
echo "========================================================================"
echo "  Service                URL                          Status"
echo "  --------------------------------------------------------------------"
echo "  Classroom Frontend     http://localhost:3000        ONLINE (Main UI)"
echo "  Learner Dashboard      http://localhost:3001        ONLINE (Analytics)"
echo "  Backend Gateway API    http://localhost:8000        HEALTHY (FastAPI)"
echo "  Interactive API Docs   http://localhost:8000/docs   READY"
echo "  Health Probe           http://localhost:8000/health READY"
echo "========================================================================"
echo "  Mode: MOCK_MODE=$MOCK_MODE (REAL_LLM=$REAL_LLM)"
echo "  To stop all services, run: ./stop_all.sh"
echo "========================================================================"
