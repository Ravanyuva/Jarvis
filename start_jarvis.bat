@echo off
title Jarvis Launcher
cd /d "%~dp0"

echo [1/2] Starting Backend Server...
start "Jarvis Backend" cmd /k "python server.py"

echo [2/2] Starting Frontend UI...
cd ui
start "Jarvis UI" cmd /k "npm run dev"

echo Done! Jarvis is booting up.
echo Backend: Check the "Jarvis Backend" window.
echo Frontend: Check the "Jarvis UI" window.
echo.
echo You can close this launcher window (the other two will stay open).
timeout /t 5
exit
