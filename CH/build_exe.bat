@echo off
setlocal
echo ================================================
echo Build EXE - School Auto Chat
echo ================================================

REM Activate venv if exists
if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
) else (
  echo Virtual environment not found. Creating .venv...
  python -m venv .venv
  call .venv\Scripts\activate.bat
)

echo Installing build-time dependencies...
pip install -r requirements.txt

echo Running PyInstaller (onedir) - this may take a while...
pyinstaller --noconfirm --onedir \
  --add-data "templates;templates" \
  --add-data "static;static" \
  --add-data "knowledge_base;knowledge_base" \
  --add-data "users_db.json;." \
  start_server.py

echo Build finished. See dist\start_server\ (folder with exe and data)
pause
