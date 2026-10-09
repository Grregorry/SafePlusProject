@echo off
cd /d "%~dp0backend"

if not exist ".venv\" (
    echo.
    echo [SETUP REQUIRED] No Python virtual environment found.
    echo.
    echo Run these commands from the backend folder first:
    echo    python -m venv .venv
    echo    .venv\Scripts\activate
    echo    pip install -r requirements-dev.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo [SETUP REQUIRED] No .env file found.
    echo.
    echo Copy the example and fill in your values:
    echo    copy .env.example .env
    echo.
    echo DATABASE_URL and JWT_SECRET are both required.
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
fastapi dev app\main.py
