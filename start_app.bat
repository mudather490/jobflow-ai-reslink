@echo off
title JobFlow AI and ResLink Video Studio
cd /d "%~dp0ai_job_agent"
echo =========================================================
echo   Starting JobFlow AI and ResLink Video Studio Server...
echo   Open: http://127.0.0.1:8000/app
echo =========================================================
python start_server.py
pause
