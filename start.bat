@echo off
REM Nexus6 Healthcare Data Generator - Windows Startup Script
REM Handles dependency installation and launches web interface

setlocal enabledelayedexpansion

echo 🏥 Nexus6 Healthcare Data Generator
echo ==================================
echo.

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed or not in PATH
        echo [ERROR] Please install Python 3.9+ from https://python.org
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Get Python version
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if pip is installed
echo [INFO] Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    pip3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] pip is not installed
        echo [ERROR] Please install pip: %PYTHON_CMD% -m ensurepip --upgrade
        pause
        exit /b 1
    ) else (
        set PIP_CMD=pip3
    )
) else (
    set PIP_CMD=pip
)
echo [SUCCESS] pip found

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

REM Install dependencies
echo [INFO] Installing Python dependencies...
%PIP_CMD% install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install some dependencies. Trying with --user flag...
    %PIP_CMD% install --user -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        echo [ERROR] Try running: %PIP_CMD% install --upgrade pip
        echo [ERROR] Then run this script again
        pause
        exit /b 1
    )
)
echo [SUCCESS] Dependencies installed successfully

REM Check if server file exists
if not exist "integrated_chatbot_server.py" (
    echo [ERROR] integrated_chatbot_server.py not found
    pause
    exit /b 1
)

echo.
echo [INFO] Setup complete! Starting web server...
echo.

REM Start the server
echo [INFO] Starting Nexus6 Healthcare Data Generator web server...
start /b %PYTHON_CMD% integrated_chatbot_server.py

REM Wait a moment for server to start
timeout /t 5 /nobreak >nul

REM Open browser
echo [INFO] Opening browser to http://localhost:5000
start http://localhost:5000

echo [SUCCESS] Nexus6 Healthcare Data Generator is running!
echo.
echo 🌐 Web Interface: http://localhost:5000
echo 📊 Upload CSV/Excel files to analyze healthcare data
echo 🤖 Chat with AI models about your data
echo.
echo [INFO] Press any key to stop the server and exit
pause >nul

REM Kill any Python processes (this is a simple approach)
echo [INFO] Shutting down server...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im python3.exe >nul 2>&1
echo [SUCCESS] Server stopped

endlocal
