$ErrorActionPreference = "Stop"

$repoRoot = "D:\Antigravity\eigent\Downloads\fnomo"
$workbookPath = Join-Path $repoRoot "EXCEL\War Room_ Community Outreach Pipeline - FNOMO Master.xlsx"
$codexAutomationRoot = "C:\Users\kush_\.codex\automations"
$paperclipLogDir = "C:\Users\kush_\.paperclip\instances\default\logs"
$fno62LedgerPath = "C:\Users\kush_\.paperclip\instances\default\workspaces\514aebc7-f334-4659-a7c6-aff8adbbd7b0\fno62_followup1_send_batch_and_crm_writeback_2026-05-04.csv"
$outDir = Join-Path $codexAutomationRoot "fnomo-pa-automation-monitor"
$reportPath = Join-Path $outDir "latest_report.md"
$historyPath = Join-Path $outDir "memory.md"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Read-TomlValue([string]$content, [string]$key) {
  $pattern = "(?m)^\s*$([regex]::Escape($key))\s*=\s*`"([^`"]*)`""
  $match = [regex]::Match($content, $pattern)
  if ($match.Success) { return $match.Groups[1].Value }
  return ""
}

function Get-LatestMemoryBlock([string]$path) {
  if (!(Test-Path -LiteralPath $path)) { return "No memory.md found." }
  $text = Get-Content -LiteralPath $path -Raw -ErrorAction Stop
  if ([string]::IsNullOrWhiteSpace($text)) { return "memory.md is empty." }
  $matches = [regex]::Matches($text, "(?ms)^##\s+.+?(?=^##\s+|\z)")
  if ($matches.Count -gt 0) {
    return ($matches[$matches.Count - 1].Value.Trim())
  }
  $lines = $text -split "`r?`n"
  return (($lines | Select-Object -Last 30) -join "`n").Trim()
}

function Summarize-Block([string]$block) {
  $lines = ($block -split "`r?`n") | Where-Object { $_.Trim() }
  if ($lines.Count -eq 0) { return "No summary available." }
  return (($lines | Select-Object -First 9) -join "`n")
}

function Get-ScheduledTaskSummary {
  $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
    Where-Object { $_.TaskName -match 'Fnomo|FNOMO|Paperclip|Codex' } |
    Sort-Object TaskName

  $items = @()
  foreach ($task in $tasks) {
    $info = $task | Get-ScheduledTaskInfo
    $result = $info.LastTaskResult
    $status = if ($result -eq 0) { "OK" } elseif ($null -eq $result) { "UNKNOWN" } else { "FAILED" }
    $items += [PSCustomObject]@{
      TaskName = $task.TaskName
      State = [string]$task.State
      LastRunTime = $info.LastRunTime
      NextRunTime = $info.NextRunTime
      LastTaskResult = $result
      Status = $status
    }
  }
  return $items
}

function Get-PaperclipHealth {
  try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:3100/api/health" -Method Get -TimeoutSec 5
    if ($health.status -eq "ok") { return "Healthy" }
    return "At Risk: health returned $($health | ConvertTo-Json -Compress)"
  } catch {
    return "Blocked: $($_.Exception.Message)"
  }
}

function Get-Fno62LedgerSummary {
  if (!(Test-Path -LiteralPath $fno62LedgerPath)) {
    return [PSCustomObject]@{ Found = $false; Sent = 0; Pending = 0; Total = 0; ByChannel = ""; LastSent = "" }
  }

  $rows = Import-Csv -LiteralPath $fno62LedgerPath
  $sentRows = @($rows | Where-Object { $_.send_status -eq "SENT" })
  $pendingRows = @($rows | Where-Object { $_.send_status -ne "SENT" })
  $byChannel = ($sentRows | Group-Object channel | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join ", "
  $lastSent = ($sentRows | Sort-Object send_timestamp_ist -Descending | Select-Object -First 1)
  $lastText = if ($lastSent) { "$($lastSent.lead_id) $($lastSent.lead_name) at $($lastSent.send_timestamp_ist)" } else { "None" }
  return [PSCustomObject]@{
    Found = $true
    Sent = $sentRows.Count
    Pending = $pendingRows.Count
    Total = $rows.Count
    ByChannel = if ($byChannel) { $byChannel } else { "None" }
    LastSent = $lastText
  }
}

function Get-WorkbookHistoryTail {
  if (!(Test-Path -LiteralPath $workbookPath)) {
    return "Workbook missing."
  }
  $code = @"
from openpyxl import load_workbook
p = r'''$workbookPath'''
wb = load_workbook(p, read_only=True, data_only=False)
ws = wb['FNOMO_EXECUTION_HISTORY']
headers = [ws.cell(4, c).value for c in range(1, ws.max_column + 1)]
rows = []
for r in range(max(5, ws.max_row - 4), ws.max_row + 1):
    vals = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
    if any(v is not None for v in vals):
        rows.append(dict(zip(headers, vals)))
print('history_rows=' + str(ws.max_row))
for row in rows:
    print(f"- {row.get('Date')} | {row.get('Action_Type')} | {row.get('Lead_or_Task')} | {row.get('Outcome')}")
wb.close()
"@
  try {
    return ($code | python -)
  } catch {
    return "Workbook history read failed: $($_.Exception.Message)"
  }
}

$now = Get-Date
$paperclipHealth = Get-PaperclipHealth
$scheduled = @(Get-ScheduledTaskSummary)
$ledger = Get-Fno62LedgerSummary
$workbookInfo = if (Test-Path -LiteralPath $workbookPath) { Get-Item -LiteralPath $workbookPath } else { $null }
$workbookHistoryTail = Get-WorkbookHistoryTail

$automationSummaries = @()
foreach ($dir in Get-ChildItem -LiteralPath $codexAutomationRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name) {
  if ($dir.Name -like ".*") { continue }
  $tomlPath = Join-Path $dir.FullName "automation.toml"
  $memoryPath = Join-Path $dir.FullName "memory.md"
  if (!(Test-Path -LiteralPath $tomlPath)) { continue }
  $toml = Get-Content -LiteralPath $tomlPath -Raw
  $latestBlock = Get-LatestMemoryBlock $memoryPath
  $automationSummaries += [PSCustomObject]@{
    Id = Read-TomlValue $toml "id"
    Name = Read-TomlValue $toml "name"
    Status = Read-TomlValue $toml "status"
    Rule = Read-TomlValue $toml "rrule"
    MemoryLastWrite = if (Test-Path -LiteralPath $memoryPath) { (Get-Item -LiteralPath $memoryPath).LastWriteTime } else { $null }
    Latest = Summarize-Block $latestBlock
  }
}

$failedTasks = @($scheduled | Where-Object { $_.Status -eq "FAILED" })
$systemStatus = if ($paperclipHealth -like "Blocked:*" -or $failedTasks.Count -gt 0) { "At Risk" } else { "Healthy" }
$issue = if ($paperclipHealth -like "Blocked:*") {
  "Paperclip local server is unreachable; Paperclip-trigger/control jobs cannot post updates."
} elseif ($failedTasks.Count -gt 0) {
  "$($failedTasks.Count) scheduled Fnomo task(s) returned failure result."
} else {
  "None"
}

$lines = @()
$lines += "# Fnomo PA Automation Monitor"
$lines += ""
$lines += "- Checked at: $($now.ToString('yyyy-MM-dd HH:mm:ss zzz'))"
$lines += "- System Status: $systemStatus"
$lines += "- Issue: $issue"
$lines += "- Paperclip Health: $paperclipHealth"
$lines += "- Workbook: $workbookPath"
$lines += "- Workbook Last Modified: $(if ($workbookInfo) { $workbookInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') } else { 'Missing' })"
$lines += ""
$lines += "## What Automations Ran For"
foreach ($a in $automationSummaries) {
  $lines += ""
  $lines += "### $($a.Name)"
  $lines += "- ID: $($a.Id)"
  $lines += "- Status: $($a.Status)"
  $lines += "- Schedule: $($a.Rule)"
  $lines += "- Last Memory Update: $(if ($a.MemoryLastWrite) { $a.MemoryLastWrite.ToString('yyyy-MM-dd HH:mm:ss') } else { 'None' })"
  $lines += "- Latest Result:"
  foreach ($line in ($a.Latest -split "`r?`n")) {
    $lines += "  $line"
  }
}

$lines += ""
$lines += "## Scheduled Task Health"
foreach ($task in $scheduled) {
  $lines += "- $($task.TaskName): $($task.Status), state=$($task.State), last=$($task.LastRunTime), next=$($task.NextRunTime), result=$($task.LastTaskResult)"
}

$lines += ""
$lines += "## FNO-62 Execution Proof"
$lines += "- Ledger Found: $($ledger.Found)"
$lines += "- Sent: $($ledger.Sent)/$($ledger.Total)"
$lines += "- Pending: $($ledger.Pending)"
$lines += "- Sent By Channel: $($ledger.ByChannel)"
$lines += "- Last Sent: $($ledger.LastSent)"

$lines += ""
$lines += "## Workbook Execution History Tail"
$lines += ($workbookHistoryTail -split "`r?`n")

$lines += ""
$lines += "## PA Action"
if ($systemStatus -eq "Healthy") {
  $lines += "- Continue monitoring. Next priority is FNO-62 send completion and immediate CRM logging."
} else {
  $lines += "- Inform Kush: workbook automations are writing, but Paperclip control is degraded. Continue execution from workbook/ledger until Paperclip is reachable."
}

$report = ($lines -join "`r`n") + "`r`n"
Set-Content -LiteralPath $reportPath -Value $report -Encoding UTF8
Add-Content -LiteralPath $historyPath -Value ("`r`n" + $report) -Encoding UTF8
Write-Output $reportPath
