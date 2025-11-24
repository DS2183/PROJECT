@echo off
REM Setup script for LLM Analysis Quiz project

echo ========================================
echo LLM Analysis Quiz - Setup Script
echo ========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Installing Playwright browsers...
playwright install chromium
if errorlevel 1 (
    echo ERROR: Failed to install Playwright browsers
    pause
    exit /b 1
)

echo [5/5] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo.
    echo ========================================
    echo IMPORTANT: Configure your .env file
    echo ========================================
    echo Please edit .env and add:
    echo   - STUDENT_EMAIL
    echo   - STUDENT_SECRET
    echo   - OPENAI_API_KEY
    echo.
) else (
    echo .env file already exists, skipping...
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Run: uvicorn app:app --reload
echo 3. Test: python test_endpoint.py
echo.
pause
