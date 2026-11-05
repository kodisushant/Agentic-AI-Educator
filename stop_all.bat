@echo off
setlocal enabledelayedexpansion

echo ========================================================================
echo   Stopping AI Virtual Teacher Services on Ports 8000, 3000, 3001
echo ========================================================================

set STOPPED=0
for %%p in (8000 3000 3001) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :%%p ^| findstr LISTENING') do (
        if not "%%a"=="" (
            echo Stopping service on port %%p - PID: %%a
            taskkill /F /PID %%a >nul 2>&1
            set STOPPED=1
        )
    )
)

if %STOPPED%==0 (
    echo No active services found on ports 8000, 3000, or 3001.
) else (
    echo All AI Virtual Teacher services have been stopped.
)

echo ========================================================================
