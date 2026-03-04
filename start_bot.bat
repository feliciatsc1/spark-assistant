@echo off
title Spark Assistant
echo.
echo  ✨ Starting Spark Assistant...
echo  Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
pip install -r requirements.txt --quiet
python bot.py
pause
