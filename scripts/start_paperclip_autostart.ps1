param(
    [string]$HealthUrl = "http://127.0.0.1:3100/api/health",
    [string]$RepoRoot = "D:\Antigravity\eigent\Downloads\fnomo"
)

$ErrorActionPreference = "Stop"

$paperclipDir = Join-Path $env:USERPROFILE ".paperclip"
$logDir = Join-Path $paperclipDir "instances\default\logs"
$logFile = Join-Path $logDir "fnomo-paperclip-autostart.log"

if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Write-StartupLog {
    param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    Add-Content -Path $logFile -Value "[$stamp] $Message"
}

function Test-PaperclipHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 8
        return ($response.StatusCode -eq 200 -and $response.Content -match '"status"\s*:\s*"ok"')
    }
    catch {
        return $false
    }
}

if (Test-PaperclipHealth) {
    Write-StartupLog "Paperclip already healthy; startup skipped."
    exit 0
}

$npxCandidates = @(
    "C:\Program Files\nodejs\npx.cmd",
    (Join-Path $env:APPDATA "npm\npx.cmd")
)

$npx = $npxCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (!$npx) {
    $command = Get-Command npx.cmd -ErrorAction SilentlyContinue
    if ($command) {
        $npx = $command.Source
    }
}

if (!$npx) {
    Write-StartupLog "ERROR: npx.cmd not found; Paperclip not started."
    exit 1
}

$paperclipRunLog = Join-Path $logDir "fnomo-paperclip-run.log"
$commandLine = '"' + $npx + '" paperclipai run >> "' + $paperclipRunLog + '" 2>&1'
Start-Process -FilePath $env:ComSpec -ArgumentList "/d", "/c", $commandLine -WorkingDirectory $RepoRoot -WindowStyle Hidden

for ($i = 1; $i -le 18; $i++) {
    Start-Sleep -Seconds 5
    if (Test-PaperclipHealth) {
        Write-StartupLog "Paperclip started and health check passed after $($i * 5) seconds."
        exit 0
    }
}

Write-StartupLog "Paperclip start issued, but health check did not pass after 90 seconds."
exit 0
