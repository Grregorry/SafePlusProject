@echo off
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
fastapi dev app\main.py