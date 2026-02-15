param(
    [string]$Version = '4.6.0'
)

$url = "https://cdn.socket.io/$Version/socket.io.min.js"
$out = Join-Path -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) -ChildPath "..\static\socket.io.min.js"
$out = [System.IO.Path]::GetFullPath($out)

Write-Host "Downloading Socket.IO client $Version from $url to $out"
try {
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -ErrorAction Stop
    Write-Host "Downloaded to $out"
} catch {
    Write-Error "Failed to download: $_"
    exit 1
}
