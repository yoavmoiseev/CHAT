@echo off
setlocal enabledelayedexpansion
echo ================================================
echo Make Portable Package - School Auto Chat
echo ================================================

REM Этот скрипт создаёт portable пакет (exe) используя:
REM - embedded_python\python.exe если положите embeddable Python туда
REM - иначе системный python (python или py -3)
REM Для offline установки положите все wheel-файлы в папку wheels\

set "PY="
if exist "embedded_python\python.exe" (
  set "PY=embedded_python\python.exe"
  echo Using embedded Python: %PY%
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    py -3 --version >nul 2>&1
    if %ERRORLEVEL%==0 (
      set "PY=py -3"
    )
  )
)

if not defined PY (
  echo No Python interpreter found. Please install Python or place embeddable Python in embedded_python\
  pause
  exit /b 1
)

REM Если нет .venv и нет embedded_python, создаём .venv для сборки
if not exist ".venv\Scripts\activate.bat" (
  if exist "embedded_python\python.exe" (
    rem try to bootstrap pip in embeddable
    echo Found embedded Python; attempting to ensure pip...
    embedded_python\python.exe -m ensurepip >nul 2>&1 || echo ensurepip not available for embeddable build.
  ) else (
    echo Creating virtualenv .venv using %PY% ...
    %PY% -m venv .venv
  )
)

REM Select installer python for pip installs: prefer .venv\Scripts\python.exe if exists
set "INSTALL_PY=%PY%"
if exist ".venv\Scripts\python.exe" set "INSTALL_PY=.venv\Scripts\python.exe"

echo Using installer python: %INSTALL_PY%

REM Install dependencies: prefer wheels\ folder if exists
if exist "wheels\" (
  echo Installing dependencies from local wheels folder...
  %INSTALL_PY% -m pip install --no-index --find-links=wheels -r requirements.txt
) else (
  echo No local wheels/ folder found. Installing from PyPI (requires internet)...
  %INSTALL_PY% -m pip install -r requirements.txt
)

REM Ensure PyInstaller available
%INSTALL_PY% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
  echo Installing pyinstaller...
  if exist "wheels\pyinstaller*" (
    %INSTALL_PY% -m pip install --no-index --find-links=wheels pyinstaller
  ) else (
    %INSTALL_PY% -m pip install pyinstaller
  )
)

REM Build exe via PyInstaller (onedir -> folder with exe + data)
echo Building onedir package with PyInstaller...
%INSTALL_PY% -m pyinstaller --noconfirm --onedir --add-data "templates;templates" --add-data "static;static" --add-data "knowledge_base;knowledge_base" --add-data "users_db.json;." start_server.py

echo Build complete. See dist\start_server\ (folder with exe and data)
pause
REM Copy run_debug.bat into dist if present
if exist "run_debug.bat" (
  if exist "dist\start_server\" (
    copy /Y "run_debug.bat" "dist\start_server\" >nul
    echo Copied run_debug.bat to dist\start_server\
  ) else if exist "dist\start_server.exe" (
    copy /Y "run_debug.bat" "dist\" >nul
    echo Copied run_debug.bat to dist\
  )
)
