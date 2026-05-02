@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  setup_task.bat — Register FNOMO Daily Engine with Windows Task Scheduler
REM
REM  Run this ONCE as Administrator:
REM    Right-click setup_task.bat → "Run as administrator"
REM
REM  What it creates:
REM    Task Name : FNOMO_Daily_Engine
REM    Trigger   : Daily at 09:00 AM
REM    Action    : Runs run_fnomo.bat (live send mode)
REM    Log       : fnomo_emailer\logs\fnomo_YYYYMMDD.log
REM    AAR       : %USERPROFILE%\Desktop\Fnomo_Daily_AAR.txt  (updated each run)
REM ─────────────────────────────────────────────────────────────────────────────

set TASK_NAME=FNOMO_Daily_Engine
set BAT_PATH=%~dp0run_fnomo.bat
set START_TIME=09:00

echo.
echo  ============================================================
echo   FNOMO Task Scheduler Setup
echo  ============================================================
echo   Task  : %TASK_NAME%
echo   Script: %BAT_PATH%
echo   Time  : %START_TIME% daily
echo  ============================================================
echo.

REM Delete existing task if it exists (allows re-registration)
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [INFO] Removing existing task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul
)

REM Register the task
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%BAT_PATH%\"" ^
    /sc DAILY ^
    /st %START_TIME% ^
    /rl HIGHEST ^
    /f

if %ERRORLEVEL%==0 (
    echo.
    echo  [SUCCESS] Task registered successfully!
    echo.
    echo  Next steps:
    echo    1. Run a dry-run preview now:
    echo       python fnomo_engine.py --dry-run
    echo.
    echo    2. Check the AAR on your Desktop:
    echo       %USERPROFILE%\Desktop\Fnomo_Daily_AAR.txt
    echo.
    echo    3. When satisfied, the task will auto-run at %START_TIME% each morning.
    echo.
    echo    4. To run manually (live send):
    echo       run_fnomo.bat
    echo.
    echo    5. To check task status:
    echo       schtasks /query /tn %TASK_NAME%
    echo.
) else (
    echo.
    echo  [ERROR] Task registration failed.
    echo  Make sure you ran this script as Administrator.
    echo.
    pause
    exit /b 1
)

pause
