@echo off
setlocal
REM run_debug.bat - Run the packaged server and capture stdout/stderr to files
REM Place this file in the same folder as the built artifact (dist) and run it.

set ROOT=%~dp0

echo Looking for executable in "%ROOT%" ...

if exist "%ROOT%start_server\start_server.exe" (
  echo Found onedir exe: "%ROOT%start_server\start_server.exe"
  "%ROOT%start_server\start_server.exe" > "%ROOT%run_output.txt" 2> "%ROOT%run_error.txt"
) else if exist "%ROOT%start_server.exe" (
  echo Found single-file exe: "%ROOT%start_server.exe"
  "%ROOT%start_server.exe" > "%ROOT%run_output.txt" 2> "%ROOT%run_error.txt"
) else (
  echo No executable found in %ROOT%
  pause
  exit /b 1
)

echo Logs written to "%ROOT%run_output.txt" and "%ROOT%run_error.txt"
pause
