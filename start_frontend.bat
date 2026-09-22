@echo off
title Vite Frontend - Port 5173
cd /d "%~dp0frontend"

if not exist "node_modules" goto nodeps

where npm >nul 2>nul
if errorlevel 1 goto nonpm

echo ============================================
echo   Vite dev server
echo   URL  : http://localhost:5173
echo   Stop : press Ctrl + C in this window
echo ============================================
echo.

call npm run dev

echo.
echo [Vite stopped]
echo ============================================
goto end

:nonpm
echo ============================================
echo [ERROR] npm not found in system PATH.
echo Install Node.js first: https://nodejs.org/
goto end

:nodeps
echo ============================================
echo [ERROR] node_modules folder is missing.
echo Run this in the frontend folder first: npm install

:end
pause
