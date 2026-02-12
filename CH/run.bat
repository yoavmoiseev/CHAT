@echo off
echo ================================================
echo School Auto Chat - Starting Server...
echo ================================================
echo.

REM Активировать виртуальное окружение
call .venv\Scripts\activate.bat

REM Запустить сервер
python server.py

pause
