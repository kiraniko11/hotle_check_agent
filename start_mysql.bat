@echo off
title MySQL - Port 3306

echo ============================================
echo   Local MySQL 8.0 instance
echo   Port: 3306     Database: hotel_booking
echo   Stop: press Ctrl + C in this window
echo ============================================
echo.

"D:\mysql\mysql-8.0.46-winx64\bin\mysqld.exe" ^
  --basedir="D:/mysql/mysql-8.0.46-winx64" ^
  --datadir="D:/mysql/mysql-8.0.46-winx64/data" ^
  --port=3306 ^
  --bind-address=127.0.0.1 ^
  --character-set-server=utf8mb4 ^
  --collation-server=utf8mb4_unicode_ci ^
  --console

echo.
pause
