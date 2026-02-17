@echo off
setlocal
echo ================================================
echo School Auto Chat - One-Click Launcher
echo ================================================

REM Try PowerShell Core (pwsh) first, then Windows PowerShell by full path
set "PS_CMD="
where pwsh >nul 2>&1 && set "PS_CMD=pwsh"
if not defined PS_CMD (
	if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
		set "PS_CMD=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
	)
)

if defined PS_CMD (
	"%PS_CMD%" -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0setup_and_run.ps1" %*
) else (
	echo No PowerShell executable found. Run setup_and_run.ps1 from PowerShell manually.
	pause
)
