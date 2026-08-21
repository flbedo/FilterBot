@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
    echo Creating virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Install Python 3.11+ and enable the py launcher.
        pause
        exit /b 1
    )
    call .venv\Scripts\python.exe -m pip install --upgrade pip
    call .venv\Scripts\python.exe -m pip install -r requirements.txt
)
if not exist .env (
    copy .env.example .env >nul
    echo .env created from .env.example. Fill in Telegram credentials and settings, then run again.
    pause
    exit /b 0
)
call .venv\Scripts\python.exe monitor.py live
pause
