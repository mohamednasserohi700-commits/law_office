@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed or not in PATH.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [2/3] Creating virtual environment...
  python -m venv .venv
)

echo [3/3] Installing requirements...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo Starting Flask app on http://127.0.0.1:5000
call ".venv\Scripts\python.exe" web_app.py

endlocal
