@echo off
title SmartFee Setup and Run
echo.
echo ========================================
echo   SMARTFEE SETUP AND RUN
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Install required packages
pip install flask flask-sqlalchemy flask-wtf python-dotenv

echo.
echo Dependencies installed. Starting application...
echo.

REM Run the application
python app.py

pause