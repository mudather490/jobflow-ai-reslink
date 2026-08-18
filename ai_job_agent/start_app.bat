@echo off
title JobFlow AI - Autonomous Career Agent & ResLink Platform
cd /d "%~dp0"
echo ===================================================================
echo   Starting JobFlow AI & ResLink Autonomous Career Platform
echo ===================================================================
echo.
echo Local URLs:
echo   Dashboard:       http://127.0.0.1:8000/app
echo   Landing Page:    http://127.0.0.1:8000/
echo   Public ResLink:  http://127.0.0.1:8000/p/mudather-mohammed
echo   API Docs:        http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C to stop the server anytime.
echo ===================================================================
echo.

python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause
