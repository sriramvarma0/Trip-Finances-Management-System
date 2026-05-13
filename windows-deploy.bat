@echo off
REM ============================================================
REM Trip Finances Management System - Windows Deployment
REM ============================================================
REM This script prepares your system, clones the repo, installs
REM dependencies, and runs the app.
REM
REM Usage: Double-click this file or run from Command Prompt
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Trip Finances - Windows Deployment
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from: https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python is installed

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo Warning: Git is not installed. Installation may fail.
    echo Download from: https://git-scm.com
    echo Press Ctrl+C to cancel, or any other key to continue...
    pause >nul
)

REM Clone or update repository
echo.
echo [>] Cloning/updating repository...
if exist "%USERPROFILE%\Trip-Finances-Management-System" (
    cd /d "%USERPROFILE%\Trip-Finances-Management-System"
    echo [OK] Repository already exists, pulling updates...
    git pull origin main >nul 2>&1
) else (
    cd /d "%USERPROFILE%"
    git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
    cd Trip-Finances-Management-System
)
echo [OK] Repository ready

REM Create virtual environment
echo [>] Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo [>] Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo [OK] Dependencies installed

REM Get local IP
for /f "tokens=2 delims=: " %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    set "LOCAL_IP=%%a"
    goto :got_ip
)
:got_ip
if not defined LOCAL_IP set "LOCAL_IP=<your-local-ip>"

REM Summary
echo.
echo ==========================================
echo [OK] Setup Complete!
echo ==========================================
echo.
echo Local IP: %LOCAL_IP%
echo.
echo To start the app, this window will launch the server.
echo.
echo Access the app:
echo   Local:  http://localhost:8000
echo   Remote: http://%LOCAL_IP%:8000
echo.
echo Press any key to start the app...
pause >nul

echo.
echo [>] Starting app...
echo.
python app.py
