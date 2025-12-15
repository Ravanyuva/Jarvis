@echo off
title Ultimate Jarvis Agent
cd /d "%~dp0"

echo [Initializing Jarvis Agent...]
echo.
echo Mode: Standalone (SQLite + Vision + Voice)
echo.

python jarvis_advanced.py

pause
