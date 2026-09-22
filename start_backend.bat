@echo off
title Django Backend - Port 8000
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" goto novenv

echo ============================================
echo   Django dev server
echo   URL  : http://127.0.0.1:8000
echo   Stop : press Ctrl + C in this window
echo ============================================
echo.

".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

echo.
echo [Django stopped]
echo ============================================
goto end

:novenv
echo ============================================
echo [ERROR] .venv\Scripts\python.exe not found.
echo Make sure the "backend" folder of this project is complete.

:end
pause
