<#
PowerShell orchestrator for one-click setup and run.
Usage: run.bat will call this script. It will:
- find a Python interpreter (embedded, py, python)
- create/activate .venv if needed
- install dependencies (prefers wheels/ if present)
- optionally build exe via PyInstaller
- choose a free port from config and optionally add firewall rule
- run server
#>

param(
    [string]$PortOverride
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $ScriptDir

Function Find-Python {
    if ($env:PYTHON_PATH) { return $env:PYTHON_PATH }
    if (Test-Path "$ScriptDir\embedded_python\python.exe") { return "$ScriptDir\embedded_python\python.exe" }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return "py -3" }
    # common install locations
    $candidates = @(
        "$env:ProgramFiles\Python\python.exe",
        "$env:ProgramFiles(x86)\Python\python.exe",
        "$env:LocalAppData\Programs\Python\Python39\python.exe",
        "$env:LocalAppData\Programs\Python\Python38\python.exe"
    )
    foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
    return $null
}

Function Test-PortFree {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch { return $false }
}

# Load config
$defaultConfig = @{ ports = @(5002,5003,8000,8888,5000,5001); openFirewall = $false; wheelsPriority = $true; buildExe = $false }
$configPath = Join-Path $ScriptDir 'setup_config.json'
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
    } catch { $cfg = $null }
}
if (-not $cfg) { $cfg = $defaultConfig }

# Parse args for /install and port formats
$installDeps = $true
foreach ($a in $args) {
    if ($a -match '^(?:/|-)?install$') { $installDeps = $true; continue }
    if ($a -match '^(?:/|-)?PORT:?(?<p>[0-9]+)$') { $PortOverride = $matches['p']; continue }
    if ($a -match '^[0-9]+$') { if (-not $PortOverride) { $PortOverride = $a }; continue }
}

# Determine python
$python = Find-Python
if (-not $python) {
    Write-Host "Python not found. Please install Python 3.8+ or place embeddable Python in embedded_python\" -ForegroundColor Red
    Pause
    Exit 1
}

Write-Host "Using python: $python"

# Create venv if not exists (prefer embeddable if present)
if (-not (Test-Path "$ScriptDir\.venv\Scripts\python.exe")) {
    if (Test-Path "$ScriptDir\embedded_python\python.exe") {
        Write-Host "embedded_python present - attempting ensurepip and using it for installations." -ForegroundColor Yellow
        & "$ScriptDir\embedded_python\python.exe" -m ensurepip 2>$null
    } else {
        Write-Host "Creating .venv using $python ..."
        if ($python -eq 'py -3') { & py -3 -m venv .venv } else { & $python -m venv .venv }
    }
}

$installerPython = if (Test-Path "$ScriptDir\.venv\Scripts\python.exe") { Join-Path $ScriptDir '.venv\Scripts\python.exe' } else { $python }
Write-Host "Installer python: $installerPython"

# Install dependencies (robust)
if ($installDeps) {
    if (Test-Path "$ScriptDir\wheels") {
        Write-Host "Installing dependencies from local wheels/ (offline) ..."
        & $installerPython -m pip install --upgrade pip setuptools wheel
        try {
            & $installerPython -m pip install --no-index --find-links="$ScriptDir\wheels" -r requirements.txt
        } catch {
            Write-Warning "Failed to install all packages from wheels. Falling back to installing runtime packages only."
            & $installerPython -m pip install --no-index --find-links="$ScriptDir\wheels" Flask Flask-SocketIO python-socketio eventlet
        }
    } else {
        Write-Host "Installing dependencies from PyPI (internet required) ..."
        & $installerPython -m pip install --upgrade pip setuptools wheel
        try {
            & $installerPython -m pip install -r requirements.txt
        } catch {
            Write-Warning "Failed to install from requirements.txt. Attempting to install runtime packages only."
            & $installerPython -m pip install Flask Flask-SocketIO python-socketio eventlet
        }
    }
} else {
    Write-Host "Skipping dependency installation (installDeps=false)"
}

# Optionally build exe
if ($cfg.buildExe -eq $true) {
    Write-Host "Ensuring PyInstaller is installed..."
    & $installerPython -m pip show pyinstaller 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        try {
            & $installerPython -m pip install pyinstaller
        } catch {
            Write-Warning "Failed to install PyInstaller. Skipping exe build."
        }
    }
    if ((Get-Command "$installerPython" -ErrorAction SilentlyContinue) -and (Get-Command pyinstaller -ErrorAction SilentlyContinue -ErrorAction SilentlyContinue)) {
        Write-Host "Building exe via PyInstaller..."
        & $installerPython -m PyInstaller --noconfirm --onefile --add-data "templates;templates" --add-data "static;static" --add-data "knowledge_base;knowledge_base" --add-data "users_db.json;." start_server.py
    } else {
        Write-Warning "PyInstaller not available; skipping exe build."
    }
}

# Choose port
$chosen = $null
if ($PortOverride) {
    $po = $PortOverride.ToString()
    # support formats: 5002, /PORT:5002, -PORT:5002, PORT:5002
    if ($po -match '^(?:/|-)?PORT:[:]?([0-9]+)$') {
        $chosen = [int]$matches[1]
    } elseif ($po -match '^([0-9]+)$') {
        $chosen = [int]$po
    } else {
        Write-Warning "Unrecognized port override format: '$po'"
    }
}
if (-not $chosen) {
    foreach ($p in $cfg.ports) { if (Test-PortFree -Port $p) { $chosen = $p; break } }
    if (-not $chosen) { $sock = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any,0); $sock.Start(); $chosen = $sock.LocalEndpoint.Port; $sock.Stop() }
}

Write-Host "Chosen port: $chosen"

# Ask to open firewall
$open = $cfg.openFirewall
if ($open -ne $true) {
    $ans = Read-Host "Open TCP port $chosen in Windows Firewall now? (Y/N)"
    if ($ans -match '^[Yy]') { $open = $true }
}

if ($open) {
    Write-Host "Attempting to add firewall rule (requires elevation)..."
    $ruleName = "SchoolAutoChat_$chosen"
    $cmd = "netsh advfirewall firewall add rule name=$ruleName dir=in action=allow protocol=TCP localport=$chosen"
    try {
        Start-Process -FilePath powershell -ArgumentList "-NoProfile -Command \"$cmd\"" -Verb RunAs -Wait
        Write-Host "Firewall rule added." -ForegroundColor Green
    } catch {
        Write-Warning "Failed to add firewall rule automatically. Run this as Administrator or add rule manually: $cmd"
    }
}

# Run server with logging and safe exit
$logPath = Join-Path $ScriptDir 'server.log'
"==== Start: $(Get-Date) ==== " | Out-File -FilePath $logPath -Encoding utf8 -Append
try {
    Start-Transcript -Path $logPath -Append -ErrorAction SilentlyContinue
} catch {
    # Start-Transcript might fail in some hosts; ignore
}

Write-Host "Starting server... (logging to $logPath)"
try {
    if (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
        & "$ScriptDir\.venv\Scripts\python.exe" .\server.py $chosen
    } elseif (Test-Path "$ScriptDir\embedded_python\python.exe") {
        & "$ScriptDir\embedded_python\python.exe" .\server.py $chosen
    } else {
        if ($python -eq 'py -3') { & py -3 .\server.py $chosen } else { & $python .\server.py $chosen }
    }
} catch {
    Write-Host "Server exited with error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $_ | Out-String | Out-File -FilePath $logPath -Append
} finally {
    try { Stop-Transcript } catch {}
    "==== End: $(Get-Date) ==== " | Out-File -FilePath $logPath -Encoding utf8 -Append
    Write-Host "Server process exited. See log: $logPath"
    Read-Host "Press Enter to close"
}

Pop-Location
