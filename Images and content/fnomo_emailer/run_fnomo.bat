@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  run_fnomo.bat — FNOMO Daily Engine Launcher
REM  Called by Windows Task Scheduler every morning at 09:00.
REM  Pass --dry-run as first argument for preview-only mode.
REM ─────────────────────────────────────────────────────────────────────────────

cd /d "%~dp0"

REM Activate virtual environment if it exists, otherwise use system Python
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the engine — log output to a rolling log file
set LOG_DIR=%~dp0logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set LOG_FILE=%LOG_DIR%\fnomo_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

echo [%date% %time%] Starting FNOMO Engine >> "%LOG_FILE%"

if "%1"=="--dry-run" (
    python fnomo_engine.py --dry-run >> "%LOG_FILE%" 2>&1
) else (
    python fnomo_engine.py >> "%LOG_FILE%" 2>&1
)

echo [%date% %time%] Engine finished. Exit code: %ERRORLEVEL% >> "%LOG_FILE%"
