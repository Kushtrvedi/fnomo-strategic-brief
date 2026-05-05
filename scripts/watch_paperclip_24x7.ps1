param(
    [string]$HealthUrl = "http://127.0.0.1:3100/api/health",
    [string]$RepoRoot = "D:\Antigravity\eigent\Downloads\fnomo",
    [string]$CompanyId = "a886e910-e92f-4a1c-8bd0-ff95b619cde1",
    [string]$PaAgentId = "f4a60bf0-da00-4a11-834c-8b6e854f4389",
    [int]$IntervalSec = 300,
    [int]$AlertCooldownMinutes = 60,
    [int]$StaleRunMinutes = 180,
    [switch]$Once
)

$ErrorActionPreference = "Stop"

$paperclipDir = Join-Path $env:USERPROFILE ".paperclip"
$logDir = Join-Path $paperclipDir "instances\default\logs"
$logFile = Join-Path $logDir "fnomo-paperclip-watchdog.log"
$stateFile = Join-Path $logDir "fnomo-paperclip-watchdog-state.json"
$lockFile = Join-Path $logDir "fnomo-paperclip-watchdog.pid"
$startupScript = Join-Path $RepoRoot "scripts\start_paperclip_autostart.ps1"

if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Write-WatchdogLog {
    param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    Add-Content -Path $logFile -Value "[$stamp] $Message"
}

function Read-State {
    if (!(Test-Path $stateFile)) {
        return @{ alerts = @{} }
    }

    try {
        $raw = Get-Content -Path $stateFile -Raw
        if (!$raw.Trim()) {
            return @{ alerts = @{} }
        }
        $json = $raw | ConvertFrom-Json
        $state = @{ alerts = @{} }
        if ($json.alerts) {
            foreach ($prop in $json.alerts.PSObject.Properties) {
                $state.alerts[$prop.Name] = [datetime]$prop.Value
            }
        }
        return $state
    }
    catch {
        return @{ alerts = @{} }
    }
}

function Write-State {
    param([hashtable]$State)
    $alerts = @{}
    foreach ($key in $State.alerts.Keys) {
        $alerts[$key] = ([datetime]$State.alerts[$key]).ToString("o")
    }
    @{ alerts = $alerts; updatedAt = (Get-Date).ToString("o") } |
        ConvertTo-Json -Depth 5 |
        Set-Content -Path $stateFile -Encoding UTF8
}

function Test-PaperclipHealth {
    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 8
        return ($response.status -eq "ok")
    }
    catch {
        return $false
    }
}

function Invoke-PaperclipApi {
    param(
        [string]$Path,
        [string]$Method = "GET",
        [object]$Body = $null
    )

    $uri = "http://127.0.0.1:3100/api$Path"
    if ($Body -ne $null) {
        return Invoke-RestMethod -Uri $uri -Method $Method -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 12) -TimeoutSec 20
    }
    return Invoke-RestMethod -Uri $uri -Method $Method -TimeoutSec 20
}

function New-PaAlert {
    param(
        [string]$Key,
        [string]$Title,
        [string]$Description,
        [ValidateSet("critical", "high", "medium", "low")]
        [string]$Priority = "high"
    )

    $state = Read-State
    $now = Get-Date
    $last = $state.alerts[$Key]
    if ($last -and (($now - $last).TotalMinutes -lt $AlertCooldownMinutes)) {
        Write-WatchdogLog "Alert cooldown active for $Key; not creating duplicate PA issue."
        return
    }

    try {
        $body = @{
            title = "[PA ALERT] $Title"
            description = $Description
            status = "todo"
            priority = $Priority
            assigneeAgentId = $PaAgentId
            source = "api"
        }
        $created = Invoke-PaperclipApi -Path "/companies/$CompanyId/issues" -Method "POST" -Body $body
        $state.alerts[$Key] = $now
        Write-State -State $state
        Write-WatchdogLog "Created PA alert $($created.identifier): $Title"
    }
    catch {
        Write-WatchdogLog "ERROR creating PA alert for ${Key}: $($_.Exception.Message)"
    }
}

function Ensure-SingleInstance {
    if (Test-Path $lockFile) {
        $existingPid = (Get-Content -Path $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($existingPid -match "^\d+$") {
            $existing = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
            if ($existing) {
                Write-WatchdogLog "Watchdog already running as PID $existingPid; exiting duplicate."
                exit 0
            }
        }
    }
    Set-Content -Path $lockFile -Value $PID -Encoding ASCII
}

function Get-RecentRunAgeMinutes {
    try {
        $runs = Invoke-PaperclipApi -Path "/companies/$CompanyId/heartbeat-runs?limit=20"
        if (!$runs -or $runs.Count -eq 0) {
            return $null
        }

        $latest = $runs |
            Where-Object { $_.createdAt } |
            Sort-Object { [datetime]$_.createdAt } -Descending |
            Select-Object -First 1

        if (!$latest) {
            return $null
        }

        return ((Get-Date).ToUniversalTime() - [datetime]$latest.createdAt).TotalMinutes
    }
    catch {
        Write-WatchdogLog "ERROR checking recent runs: $($_.Exception.Message)"
        return $null
    }
}

function Invoke-WatchdogCycle {
    $healthy = Test-PaperclipHealth
    if (!$healthy) {
        Write-WatchdogLog "Paperclip health failed; attempting restart."
        if (Test-Path $startupScript) {
            Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$startupScript`"" -WindowStyle Hidden
            Start-Sleep -Seconds 20
            $healthy = Test-PaperclipHealth
        }

        if (!$healthy) {
            New-PaAlert -Key "paperclip-down" -Title "Paperclip is down" -Priority "critical" -Description @"
Paperclip health check failed and automatic restart did not recover it.

Required PA action:
1. Inform Kush immediately.
2. Restart Paperclip manually.
3. Do not assume Fnomo execution is running.
"@
            return
        }
    }

    try {
        $dashboard = Invoke-PaperclipApi -Path "/companies/$CompanyId/dashboard"
        $agents = Invoke-PaperclipApi -Path "/companies/$CompanyId/agents"
        $issues = Invoke-PaperclipApi -Path "/companies/$CompanyId/issues?limit=150&includeRoutineExecutions=true"

        $erroredAgents = @($agents | Where-Object { $_.status -eq "error" })
        if ($erroredAgents.Count -gt 0) {
            $names = ($erroredAgents | Select-Object -ExpandProperty name) -join ", "
            New-PaAlert -Key "agent-error" -Title "Paperclip agent error" -Priority "critical" -Description @"
Agents in error: $names

Required PA action:
1. Inform Kush.
2. Pause dependent execution.
3. Reroute active tasks or repair the failed agent.
"@
        }

        $attentionBlocked = @($issues | Where-Object {
            $_.status -eq "blocked" -and
            $_.blockerAttention -and
            $_.blockerAttention.state -ne "covered"
        })
        if ($attentionBlocked.Count -gt 0) {
            $sample = ($attentionBlocked | Select-Object -First 8 | ForEach-Object { "$($_.identifier): $($_.title)" }) -join "`n"
            New-PaAlert -Key "blocked-issues" -Title "$($attentionBlocked.Count) Paperclip issues need PA attention" -Priority "high" -Description @"
Blocked issues need PA triage:
$sample

Required PA action:
1. Break stuck work into smaller sub-issues.
2. Reroute unclear tasks.
3. Brief Kush only with the top blocker and correction.
"@
        }

        $heartbeatEnabled = @($agents | Where-Object {
            $_.runtimeConfig -and
            $_.runtimeConfig.heartbeat -and
            $_.runtimeConfig.heartbeat.enabled -eq $true
        })
        if ($heartbeatEnabled.Count -eq 0) {
            New-PaAlert -Key "heartbeat-disabled" -Title "No Paperclip agent heartbeat is enabled" -Priority "medium" -Description @"
Paperclip server is healthy, but no agent heartbeat is enabled.

Current dashboard:
- Open: $($dashboard.tasks.open)
- In progress: $($dashboard.tasks.inProgress)
- Blocked: $($dashboard.tasks.blocked)

Required PA action:
1. Keep external watchdog active.
2. Confirm whether PA heartbeat should remain enabled.
3. Do not let tasks sit without next action.
"@
        }

        $age = Get-RecentRunAgeMinutes
        if ($age -eq $null) {
            New-PaAlert -Key "no-runs" -Title "No Paperclip runs found" -Priority "high" -Description "No heartbeat runs were returned. PA must verify execution is not idle."
        }
        elseif ($age -gt $StaleRunMinutes -and $dashboard.tasks.inProgress -gt 0) {
            New-PaAlert -Key "stale-runs" -Title "Paperclip execution appears stale" -Priority "high" -Description @"
No recent run in the last $([math]::Round($age, 1)) minutes while $($dashboard.tasks.inProgress) tasks remain in progress.

Required PA action:
1. Inform Kush.
2. Re-run or reroute the most important active task.
3. Keep Tier A execution priority.
"@
        }

        Write-WatchdogLog "OK health=true agents=$($agents.Count) open=$($dashboard.tasks.open) in_progress=$($dashboard.tasks.inProgress) blocked=$($dashboard.tasks.blocked) live_runs=$($dashboard.agents.running)"
    }
    catch {
        Write-WatchdogLog "ERROR during dashboard cycle: $($_.Exception.Message)"
        New-PaAlert -Key "watchdog-cycle-error" -Title "Paperclip watchdog cycle failed" -Priority "high" -Description "The watchdog could not complete a Paperclip dashboard cycle: $($_.Exception.Message)"
    }
}

Ensure-SingleInstance
Write-WatchdogLog "Watchdog started. IntervalSec=$IntervalSec Once=$Once"

try {
    do {
        Invoke-WatchdogCycle
        if ($Once) {
            break
        }
        Start-Sleep -Seconds $IntervalSec
    } while ($true)
}
finally {
    if (Test-Path $lockFile) {
        $lockedPid = (Get-Content -Path $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($lockedPid -eq "$PID") {
            Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
        }
    }
}
