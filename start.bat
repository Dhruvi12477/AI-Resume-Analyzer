@echo off
title AI Resume Analyzer
cd /d "%~dp0"

echo ==========================================
echo       AI RESUME ANALYZER
echo ==========================================
echo.
echo Installing/checking dependencies...
python -m pip install -r backend\requirements.txt
echo.
echo Starting FastAPI server...
echo Open: http://127.0.0.1:8000
echo Press CTRL+C to stop.
echo.
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
pause
