@echo off
setlocal
echo ================================================
echo Build EXE - School Auto Chat
echo ================================================

REM Activate venv if it exists, otherwise create it
if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
) else (
  echo Virtual environment not found. Creating .venv...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
)

echo Installing / upgrading build-time dependencies...
pip install -r requirements.txt

echo.
echo Running PyInstaller from SchoolAutoChat.spec ...
echo (this may take a few minutes)
pyinstaller --noconfirm SchoolAutoChat.spec

if errorlevel 1 (
  echo.
  echo ERROR: PyInstaller failed. See output above for details.
  pause
  exit /b 1
)

echo.
echo ================================================
echo Build finished!
echo EXE is at:  dist\SchoolAutoChat.exe
echo ================================================
echo.
pause
