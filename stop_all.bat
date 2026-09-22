@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Stop hotel booking services: frontend / backend / MySQL
echo ============================================================
echo.

if not exist "backend\.venv\Scripts\python.exe" goto NO_PYTHON
if not exist "stop_services.py" goto NO_SCRIPT

"backend\.venv\Scripts\python.exe" "stop_services.py"
set RC=%ERRORLEVEL%

echo.
if not "%RC%"=="0" goto FAILED

echo Done. You can close this window.
pause
exit /b 0

:FAILED
echo [ERROR] Stop script returned code %RC%
pause
exit /b %RC%

:NO_PYTHON
echo [ERROR] Python virtual environment not found:
echo         backend\.venv\Scripts\python.exe
echo         Run start_backend.bat once to recreate or verify it.
pause
exit /b 1

:NO_SCRIPT
echo [ERROR] stop_services.py not found in the current folder:
echo         %CD%
pause
exit /b 1
