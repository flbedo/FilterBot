@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\python.exe monitor.py history
pause
