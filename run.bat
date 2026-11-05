@echo off
echo ==========================================
echo Starting AI Virtual Teacher (MOCK_MODE=true)
echo ==========================================

set MOCK_MODE=true
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000

echo Backend starting on http://localhost:%BACKEND_PORT%
echo API Docs available at http://localhost:%BACKEND_PORT%/docs
echo Contracts stored in /contracts

python -m uvicorn backend.agent.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload
