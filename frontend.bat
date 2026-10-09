@echo off
cd /d "%~dp0frontend"

if not exist "node_modules\" (
    echo.
    echo [SETUP] Dependencies not installed. Running npm install...
    echo.
    call npm install
    if errorlevel 1 (
        echo.
        echo [ERROR] npm install failed. See the output above.
        echo.
        pause
        exit /b 1
    )
)

npm run dev
