@echo off
chcp 65001 >nul
title School Auto Chat - Offline Build

echo.
echo  ================================================
echo   School Auto Chat - Offline Build Script
echo  ================================================
echo.
echo  This script creates a standalone offline package with Python inside.
echo  Requires internet (only for downloading Python and packages).
echo  Result: ChatApp-Offline.zip (~50 MB)
echo.
pause

python --version >nul 2>&1
if %ERRORLEVEL%==0 (
    set PY=python
) else (
    py -3 --version >nul 2>&1
    if %ERRORLEVEL%==0 (
        set PY=py -3
    ) else (
        echo ERROR: Python not found! Install Python 3.8+ from https://python.org
        pause
        exit /b 1
    )
)

echo  Using: %PY%
echo.
%PY% build_offline.py
echo.
pause