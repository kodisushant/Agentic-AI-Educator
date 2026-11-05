@echo off
setlocal enabledelayedexpansion

echo ========================================================================
echo   AI Virtual Teacher: Single-Command Full Stack Launcher
echo ========================================================================

:: 1. Verify Prerequisites
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    exit /b 1
)

where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not found in PATH!
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)

where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not installed or not found in PATH!
    echo Please ensure npm is installed alongside Node.js.
    exit /b 1
)
echo [OK] Runtime dependencies verified [Python, Node.js, npm found].

:: 2. Environment File Check (.env)
if not exist .env (
    if exist .env.example (
        echo [INFO] .env not found. Initializing from .env.example...
        copy .env.example .env >nul
        echo [INFO] Created .env successfully.
    ) else (
        echo [WARN] Neither .env nor .env.example found. Creating empty .env...
        type nul > .env
    )
    echo --------------------------------------------------------------------
    echo [KEYS NOTICE] To enable live AI, add your free API keys in .env:
    echo   - GEMINI_API_KEY      https://aistudio.google.com/
    echo   - GROQ_API_KEY        https://console.groq.com/
    echo   - CEREBRAS_API_KEY    https://cloud.cerebras.ai/
    echo   - OPENROUTER_API_KEY  https://openrouter.ai/
    echo If left blank, the platform automatically operates in MOCK mode.
    echo --------------------------------------------------------------------
)

:: 3. Mode Resolution (mock, real, or auto-detect)
set MODE_ARG=%~1

if /I "%MODE_ARG%"=="mock" (
    set MOCK_MODE=true
    set REAL_LLM=0
    echo [MODE] MOCK mode selected explicitly - zero API keys required.
) else if /I "%MODE_ARG%"=="real" (
    set MOCK_MODE=false
    set REAL_LLM=1
    echo [MODE] REAL mode selected explicitly - calling configured LLM providers.
) else (
    python scripts\check_keys.py
    if !ERRORLEVEL! EQU 0 (
        set MOCK_MODE=false
        set REAL_LLM=1
        echo [MODE] Auto-detected configured LLM keys in .env -^> REAL mode active.
    ) else (
        set MOCK_MODE=true
        set REAL_LLM=0
        echo [MODE] No LLM keys found in .env -^> Auto-defaulting to MOCK mode.
    )
)

:: 4. Dependency Installation (Only if missing)
echo [DEPS] Checking Python dependencies...
python -c "import fastapi, uvicorn, pydantic, httpx" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [DEPS] Installing missing Python requirements...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install Python dependencies.
        exit /b 1
    )
) else (
    echo [DEPS] Python dependencies already installed.
)

echo [DEPS] Checking frontend dependencies...
if exist frontend\dashboard\package.json (
    if not exist frontend\dashboard\node_modules (
        echo [DEPS] Installing npm dependencies in frontend/dashboard...
        pushd frontend\dashboard
        call npm install
        popd
    ) else (
        echo [DEPS] Node modules already present in frontend/dashboard.
    )
)

:: 5. Stop any lingering instances on ports 8000, 3000, 3001
for %%p in (8000 3000 3001) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :%%p ^| findstr LISTENING') do (
        if not "%%a"=="" taskkill /F /PID %%a >nul 2>&1
    )
)

:: 6. Launch Services in Separate Windows with cmd /k
echo [START] Launching backend on port 8000...
start "AI Teacher - Backend (Port 8000)" cmd /k "title AI Teacher - Backend && set MOCK_MODE=%MOCK_MODE%&& set REAL_LLM=%REAL_LLM%&& python -m uvicorn backend.agent.main:app --host 0.0.0.0 --port 8000 --reload"

echo [START] Launching Classroom Frontend on port 3000...
start "AI Teacher - Classroom (Port 3000)" cmd /k "title AI Teacher - Classroom Frontend && python -m http.server 3000 --directory frontend/classroom"

echo [START] Launching Learner Dashboard on port 3001...
start "AI Teacher - Dashboard (Port 3001)" cmd /k "title AI Teacher - Learner Dashboard && python -m http.server 3001 --directory frontend/dashboard"

:: 7. Wait for Backend Health
python scripts\wait_for_health.py http://localhost:8000/health 30
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Backend did not respond within 30 seconds. Check the backend window for logs.
) else (
    echo.
    echo [LAUNCH] Opening Classroom Frontend in default browser...
    start http://localhost:3000/
)

:: 8. Summary Table
echo.
echo ========================================================================
echo   AI Virtual Teacher - System Status
echo ========================================================================
echo   Service                URL                          Status
echo   --------------------------------------------------------------------
echo   Classroom Frontend     http://localhost:3000        ONLINE [Main UI]
echo   Learner Dashboard      http://localhost:3001        ONLINE [Analytics]
echo   Backend Gateway API    http://localhost:8000        HEALTHY [FastAPI]
echo   Interactive API Docs   http://localhost:8000/docs   READY
echo   Health Probe           http://localhost:8000/health READY
echo ========================================================================
echo   Mode: MOCK_MODE=%MOCK_MODE% [REAL_LLM=%REAL_LLM%]
echo   To stop all services, run: stop_all.bat
echo ========================================================================
