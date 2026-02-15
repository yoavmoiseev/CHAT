<#
.SYNOPSIS
  Build a portable single-file EXE for School Auto Chat using a reproducible PowerShell flow.

USAGE
  Run from repository root in an elevated or normal PowerShell session:
    .\build_portable.ps1

DESCRIPTION
  - Prefer `embedded_python\python.exe` if present.
  - Otherwise use `py -3` or `python` from PATH.
  - Create `.venv` if missing and install wheels from `wheels\` when available.
  - Ensure PyInstaller is installed (from wheels or PyPI) and run it to produce `dist\start_server.exe`.
  - Binds server to localhost by default (no firewall prompts).
#>
Set-StrictMode -Version Latest
Write-Host "Starting portable build (PowerShell)" -ForegroundColor Cyan

Push-Location (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

function Find-Python {
    if (Test-Path "embedded_python\python.exe") {
        return "embedded_python\python.exe"
    }

    try { & py -3 --version > $null 2>&1; return 'py -3' } catch {}
    try { & python --version > $null 2>&1; return 'python' } catch {}
    return $null
}

$PY = Find-Python
if (-not $PY) {
    Write-Error "No Python interpreter found. Place embeddable Python in embedded_python\ or install Python."
    exit 1
}

Write-Host "Using Python: $PY"

# Create .venv if missing (use $PY to bootstrap)
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtualenv .venv..."
    & $PY -m venv .venv
}

$INSTALL_PY = ".venv\Scripts\python.exe"
if (-not (Test-Path $INSTALL_PY)) { $INSTALL_PY = $PY }

Write-Host "Installer Python: $INSTALL_PY"

if (Test-Path "wheels") {
    Write-Host "Installing dependencies from local wheels..."
    & $INSTALL_PY -m pip install --upgrade pip
    & $INSTALL_PY -m pip install --no-index --find-links=wheels -r requirements.txt
} else {
    Write-Host "Installing dependencies from PyPI (internet required)..."
    & $INSTALL_PY -m pip install --upgrade pip
    & $INSTALL_PY -m pip install -r requirements.txt
}

# Ensure PyInstaller
try {
    & $INSTALL_PY -m pip show pyinstaller > $null 2>&1
    if ($LASTEXITCODE -ne 0) { throw "no-pyinstaller" }
} catch {
    Write-Host "PyInstaller not found; installing..."
    if (Test-Path "wheels\pyinstaller*") {
        & $INSTALL_PY -m pip install --no-index --find-links=wheels pyinstaller
    } else {
        & $INSTALL_PY -m pip install pyinstaller
    }
}

Write-Host "Running PyInstaller (onedir)..."
& $INSTALL_PY -m PyInstaller --noconfirm --onedir --add-data "templates;templates" --add-data "static;static" --add-data "knowledge_base;knowledge_base" --add-data "users_db.json;." start_server.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build complete: dist\start_server\ (folder with exe and data)" -ForegroundColor Green
    # Copy run_debug.bat into the dist folder so users can run packaged exe and capture logs
    $src = Join-Path (Get-Location) 'run_debug.bat'
    $destOnedir = Join-Path (Join-Path (Get-Location) 'dist') 'start_server'
    $destSingle = Join-Path (Get-Location) 'dist'
    if (Test-Path $destOnedir) {
        Copy-Item $src -Destination $destOnedir -Force
        Write-Host "Copied run_debug.bat to $destOnedir"
    } elseif (Test-Path (Join-Path $destSingle 'start_server.exe')) {
        Copy-Item $src -Destination $destSingle -Force
        Write-Host "Copied run_debug.bat to $destSingle"
    } else {
        Write-Host "Could not find dist output to copy run_debug.bat"
    }
} else {
    Write-Error "PyInstaller failed"
}

Pop-Location
