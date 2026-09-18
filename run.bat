@echo off
title PayProof AI Launcher
echo =====================================================================
echo  PayProof AI — Pre-Payment Verification System
echo  Single Entrypoint Launcher
echo =====================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python was not found on your PATH.
    echo [!] Please install Python 3.11+ and ensure 'Add to PATH' is checked.
    pause
    exit /b 1
)

python "%~dp0run.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] PayProof terminated with an error.
    pause
)
