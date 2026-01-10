@echo off
title JAI Website (FastAPI)
set PYTHONUTF8=1
REM Set JAI_CORS_ORIGINS and JAI_MOBILE_TOKEN in your .env
uvicorn --app-dir "c:\Users\Abdul Rahman\Documents\JAI_Assistant" main:app --host 0.0.0.0 --port 8080
pause
