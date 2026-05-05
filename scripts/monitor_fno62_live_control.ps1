$ErrorActionPreference = "Stop"

$base = "http://127.0.0.1:3100/api"
$company = "a886e910-e92f-4a1c-8bd0-ff95b619cde1"
$fno62 = "89b798a8-c24d-4d53-9f57-1aa16d9f5233"
$fno58 = "d38a3328-3324-438e-aacb-b068897a2a8d"
$logDir = "C:\Users\kush_\.paperclip\instances\default\logs"
$statePath = Join-Path $logDir "fnomo-fno62-live-control-state.json"
$logPath = Join-Path $logDir "fnomo-fno62-live-control.log"
$proofLedgerPath = "C:\Users\kush_\.paperclip\instances\default\workspaces\514aebc7-f334-4659-a7c6-aff8adbbd7b0\fno62_followup1_send_batch_and_crm_writeback_2026-05-04.csv"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log($msg) {
  Add-Content -LiteralPath $logPath -Value ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg)
}

function Invoke-Api($method, $uri, $body = $null, $timeout = 20) {
  if ($null -eq $body) {
    return Invoke-RestMethod -Uri $uri -Method $method -TimeoutSec $timeout
  }
  return Invoke-RestMethod -Uri $uri -Method $method -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec $timeout
}

function Add-Comment($issueId, $body, $interrupt = $false) {
  Invoke-Api "Post" "$base/issues/$issueId/comments" @{ body = $body; interrupt = $interrupt } 30 | Out-Null
}

function Parse-SentCount($comments) {
  $best = $null
  foreach ($comment in $comments) {
    $body = [string]$comment.body
    foreach ($pattern in @(
      "(?im)^\s*[-*]?\s*(?:sent|sent count|processed count|messages sent|follow-ups sent)\s*[:=-]\s*(\d+)\b",
      "(?im)^\s*[-*]?\s*(?:progress|processed)\s*[:=-]\s*(\d+)\s*/\s*28\b"
    )) {
      $matches = [regex]::Matches($body, $pattern)
      foreach ($match in $matches) {
        $value = [int]$match.Groups[1].Value
        if ($null -eq $best -or $value -gt $best) { $best = $value }
      }
    }
  }
  if ($null -eq $best) { return 0 }
  return [Math]::Min($best, 28)
}

function Parse-ReplySummary($comments) {
  $replyCount = 0
  $classes = @{
    Interested = 0
    Curious = 0
    Objection = 0
    "Not Relevant" = 0
  }
  foreach ($comment in $comments) {
    $body = [string]$comment.body
    foreach ($pattern in @(
      "(?im)^\s*[-*]?\s*(?:replies|reply count|replies received)\s*[:=-]\s*(\d+)\b",
      "(?im)^\s*[-*]?\s*count\s*[:=-]\s*(\d+)\b"
    )) {
      $replyMatches = [regex]::Matches($body, $pattern)
      foreach ($match in $replyMatches) {
        $lineStart = [Math]::Max(0, $match.Index - 40)
        $lineContext = $body.Substring($lineStart, [Math]::Min(120, $body.Length - $lineStart))
        if ($pattern -match "count" -and $lineContext -notmatch "(?i)repl") { continue }
        $value = [int]$match.Groups[1].Value
        if ($value -le 28) {
          $replyCount = [Math]::Max($replyCount, $value)
        }
      }
    }
    foreach ($key in @("Interested", "Curious", "Objection", "Not Relevant")) {
      $classPattern = "(?im)^\s*[-*]?\s*$([regex]::Escape($key))\s*[:=]\s*(\d+)\b"
      $classMatches = [regex]::Matches($body, $classPattern)
      foreach ($match in $classMatches) {
        $value = [int]$match.Groups[1].Value
        if ($value -le 28) {
          $classes[$key] = [Math]::Max($classes[$key], $value)
        }
      }
    }
  }
  return @{ count = $replyCount; classes = $classes }
}

function Read-State {
  if (!(Test-Path $statePath)) { return $null }
  try {
    $raw = Get-Content -LiteralPath $statePath -Raw
    if (!$raw.Trim()) { return $null }
    return ($raw | ConvertFrom-Json)
  } catch {
    return $null
  }
}

function Test-Pattern($comments, [string[]]$patterns) {
  foreach ($comment in $comments) {
    $body = [string]$comment.body
    foreach ($pattern in $patterns) {
      if ($body -match $pattern) { return $true }
    }
  }
  return $false
}

function Parse-CoordinationSummary($comments) {
  $conflicts = 0
  $duplicateRisk = $false
  $crmIssue = $false
  foreach ($comment in $comments) {
    $body = [string]$comment.body
    foreach ($pattern in @(
      "(?im)^\s*[-*]?\s*(?:conflicts|conflict count)\s*[:=-]\s*(\d+)\b",
      "(?im)^\s*[-*]?\s*Coordination Check:.*?Conflicts\s*[:=-]\s*(\d+)\b"
    )) {
      $matches = [regex]::Matches($body, $pattern)
      foreach ($match in $matches) {
        $conflicts = [Math]::Max($conflicts, [int]$match.Groups[1].Value)
      }
    }
    if ($body -match "(?i)duplicate send|duplicate detected|same lead processed|ownership conflict|channel conflict") {
      $duplicateRisk = $true
      if ($conflicts -eq 0 -and $body -match "(?i)ownership conflict|channel conflict") { $conflicts = 1 }
    }
    if ($body -match "(?i)crm sync status\s*[:=-]\s*issue|crm\s+(gap|missing|failed|failure)|writeback\s+(gap|missing|failed|failure)") {
      $crmIssue = $true
    }
  }
  $crmStatus = if ($crmIssue) { "Issue" } else { "Clean" }
  return @{ conflicts = $conflicts; duplicateRisk = $duplicateRisk; crmStatus = $crmStatus }
}

function Parse-EngagementSummary($comments) {
  $count = 0
  $hasData = $false
  $confusion = $false
  foreach ($comment in $comments) {
    $body = [string]$comment.body
    foreach ($pattern in @(
      "(?im)^\s*[-*]?\s*(?:seen|read|seen/read|delivered|opens?|email opens|linkedin read|whatsapp seen|engagement signals?)\s*[:=-]\s*(\d+)\b"
    )) {
      $matches = [regex]::Matches($body, $pattern)
      foreach ($match in $matches) {
        $value = [int]$match.Groups[1].Value
        if ($value -le 28) {
          $count = [Math]::Max($count, $value)
          $hasData = $true
        }
      }
    }
    if ($body -match "(?i)confused|confusion|unclear|not clear|what do you mean|what is this|clarity issue") {
      $confusion = $true
    }
  }
  return @{ count = $count; hasData = $hasData; confusion = $confusion }
}

function Resolve-FirstSignalCheck($sent, $reply, $engagement, $previousState) {
  if ($null -ne $previousState -and $null -ne $previousState.firstSignalCheck -and $previousState.firstSignalCheck.locked) {
    return @{
      replies = [int]$previousState.firstSignalCheck.replies
      strength = [string]$previousState.firstSignalCheck.strength
      action = [string]$previousState.firstSignalCheck.action
      engagement = [string]$previousState.firstSignalCheck.engagement
      responseQuality = [string]$previousState.firstSignalCheck.responseQuality
      confusionSignals = [string]$previousState.firstSignalCheck.confusionSignals
      locked = $true
    }
  }

  $engagementText = if ($engagement.hasData) { [string]$engagement.count } else { "Unavailable" }
  $confusionText = if ($engagement.confusion) { "Yes" } else { "No" }

  if ($sent -lt 10) {
    return @{
      replies = "Pending"
      strength = "Pending"
      action = "Continue batch"
      engagement = $engagementText
      responseQuality = "Pending until first 10 sends"
      confusionSignals = $confusionText
      locked = $false
    }
  }

  $replyCount = [int]$reply.count
  if ($replyCount -ge 2) {
    $strength = "Strong"
    $quality = "2+ replies; continue normally"
  } elseif ($replyCount -eq 1) {
    $strength = "Neutral"
    $quality = "1 reply; continue and monitor closely"
  } else {
    $strength = "Weak"
    $quality = "0 replies; possible messaging weakness, observe only"
  }

  return @{
    replies = $replyCount
    strength = $strength
    action = "Continue batch"
    engagement = $engagementText
    responseQuality = $quality
    confusionSignals = $confusionText
    locked = $true
  }
}

function Resolve-ExecutionProof($reply) {
  $expectedChannels = @{ Email = 13; WhatsApp = 10; LinkedIn = 5 }
  $channelSent = @{ Email = 0; WhatsApp = 0; LinkedIn = 0 }
  $missingFields = 0
  $rowsUpdated = 0
  $historyEntries = 0
  $ledgerRows = 0
  $totalSent = 0
  $proofIssues = @()

  if (!(Test-Path -LiteralPath $proofLedgerPath)) {
    return @{
      status = "Pending"
      ledgerFound = $false
      totalSent = 0
      email = 0
      whatsapp = 0
      linkedin = 0
      rowsUpdated = 0
      missingFields = 0
      historyEntries = 0
      repliesTotal = $reply.count
      interested = $reply.classes.Interested
      curious = $reply.classes.Curious
      objection = $reply.classes.Objection
      notRelevant = $reply.classes.'Not Relevant'
      issues = "Ledger not found"
    }
  }

  $rows = @(Import-Csv -LiteralPath $proofLedgerPath)
  $ledgerRows = $rows.Count

  foreach ($row in $rows) {
    $sendStatus = ([string]$row.send_status).Trim()
    if ($sendStatus -ne "SENT") { continue }

    $totalSent += 1
    $channel = ([string]$row.channel).Trim()
    if ($channelSent.ContainsKey($channel)) {
      $channelSent[$channel] += 1
    }

    $required = @(
      [string]$row.lead_id,
      [string]$row.lead_name,
      [string]$row.owner,
      [string]$row.stage_after_send,
      [string]$row.crm_next_action_type,
      [string]$row.crm_next_action_date
    )
    foreach ($value in $required) {
      if (-not $value.Trim()) { $missingFields += 1 }
    }

    $crmOk = (
      ([string]$row.crm_last_contact_date).Trim() -eq "2026-05-04" -and
      ([string]$row.crm_next_action_type).Trim() -eq "Follow-up 2" -and
      ([string]$row.crm_next_action_date).Trim() -eq "2026-05-08" -and
      ([string]$row.stage_after_send).Trim()
    )
    if ($crmOk) { $rowsUpdated += 1 }

    if (([string]$row.fnomo_execution_history_entry).Trim()) {
      $historyEntries += 1
    }
  }

  foreach ($channel in $expectedChannels.Keys) {
    if ($totalSent -ge 28 -and $channelSent[$channel] -ne $expectedChannels[$channel]) {
      $proofIssues += "$channel sent $($channelSent[$channel])/$($expectedChannels[$channel])"
    }
  }
  if ($totalSent -ge 28 -and $rowsUpdated -ne 28) { $proofIssues += "CRM rows updated $rowsUpdated/28" }
  if ($totalSent -ge 28 -and $missingFields -ne 0) { $proofIssues += "missing fields $missingFields" }
  if ($totalSent -ge 28 -and $historyEntries -ne 28) { $proofIssues += "history entries $historyEntries/28" }

  $status = if ($totalSent -lt 28) {
    "Pending"
  } elseif ($proofIssues.Count -eq 0) {
    "Complete"
  } else {
    "Incomplete"
  }

  $issueText = if ($proofIssues.Count) { $proofIssues -join "; " } else { "None" }
  return @{
    status = $status
    ledgerFound = $true
    ledgerRows = $ledgerRows
    totalSent = $totalSent
    email = $channelSent.Email
    whatsapp = $channelSent.WhatsApp
    linkedin = $channelSent.LinkedIn
    rowsUpdated = $rowsUpdated
    missingFields = $missingFields
    historyEntries = $historyEntries
    repliesTotal = $reply.count
    interested = $reply.classes.Interested
    curious = $reply.classes.Curious
    objection = $reply.classes.Objection
    notRelevant = $reply.classes.'Not Relevant'
    issues = $issueText
  }
}

try {
  $health = Invoke-Api "Get" "$base/health"
  if ($health.status -ne "ok") { throw "Paperclip health not ok" }

  $previousState = Read-State
  $issue = Invoke-Api "Get" "$base/issues/$fno62"
  $comments = @(Invoke-Api "Get" "$base/issues/$fno62/comments?limit=20")
  $activeRun = Invoke-Api "Get" "$base/issues/$fno62/active-run"

  $sent = Parse-SentCount $comments
  $reply = Parse-ReplySummary $comments
  $coordination = Parse-CoordinationSummary $comments
  $engagement = Parse-EngagementSummary $comments
  $firstSignal = Resolve-FirstSignalCheck $sent $reply $engagement $previousState
  $proof = Resolve-ExecutionProof $reply
  if ($proof.ledgerFound -and $proof.totalSent -gt $sent) { $sent = $proof.totalSent }
  if ($sent -eq 0) {
    $coordination.conflicts = 0
    $coordination.duplicateRisk = $false
    $coordination.crmStatus = "Clean"
  }
  $now = Get-Date
  $issueUpdated = [datetime]$issue.updatedAt
  $minutesSinceIssueUpdate = [int](New-TimeSpan -Start $issueUpdated -End $now).TotalMinutes

  $issues = @()
  $failSafeIssues = @()
  $corrections = 0
  if ($issue.status -eq "blocked") {
    $issues += "FNO-62 is blocked during live execution window."
    $failSafeIssues += "SEND FAILURE / EXECUTION BLOCK: FNO-62 is blocked."
  }
  if ($now.Hour -eq 9 -and $now.Minute -ge 10 -and $sent -eq 0 -and $null -eq $activeRun) {
    $issues += "No active FNO-62 run or sends visible after trigger window."
    $failSafeIssues += "MONITOR/SEND FAILURE: no active run or sends visible after trigger."
  }
  if ($issue.status -eq "in_progress" -and $minutesSinceIssueUpdate -ge 20 -and $sent -lt 28) {
    $issues += "FNO-62 appears stale for $minutesSinceIssueUpdate minutes before completion."
    $failSafeIssues += "PARTIAL EXECUTION FAILURE: batch appears stale before completion."
  }
  # First Signal Control handles 0 replies after 10 sends as observation, not intervention.
  if ($null -ne $previousState -and $sent -lt 28 -and $sent -eq [int]$previousState.sent -and $issue.status -eq "in_progress") {
    $lastRunAt = [datetime]$previousState.lastRunAt
    $minutesSinceLastCycle = [int](New-TimeSpan -Start $lastRunAt -End $now).TotalMinutes
    if ($minutesSinceLastCycle -ge 20) {
      $failSafeIssues += "PARTIAL EXECUTION FAILURE: sent count unchanged for $minutesSinceLastCycle minutes."
    }
  }
  if (Test-Pattern $comments @("(?i)crm\\s+(gap|missing|failed|failure)", "(?i)writeback\\s+(gap|missing|failed|failure)", "(?i)next action\\s+(missing|incorrect)", "(?i)next action date\\s+(missing|incorrect)")) {
    $failSafeIssues += "CRM FAILURE: comment stream indicates writeback or next-action issue."
  }
  if (Test-Pattern $comments @("(?i)unhandled reply", "(?i)reply delay", "(?i)reply.+idle", "(?i)no response generated")) {
    $failSafeIssues += "REPLY DELAY FAILURE: comment stream indicates reply handling delay."
  }
  if ($coordination.conflicts -gt 0 -or $coordination.duplicateRisk -or $coordination.crmStatus -eq "Issue") {
    $failSafeIssues += "COORDINATION FAILURE: conflict, duplicate risk, or CRM sync issue detected."
  }
  if ($sent -ge 28 -and $proof.status -ne "Complete") {
    $failSafeIssues += "EXECUTION PROOF FAILURE: $($proof.issues)"
  }

  $phase = if ($sent -ge 28) { "Completion Control" } elseif ($sent -ge 15) { "Mid-Run Checkpoint" } elseif ($sent -ge 5) { "Early Signal Monitoring" } else { "Execution Control" }
  if ($sent -gt 0 -and $sent -le 10) { $phase = "First Signal Control" }
  $nextAction = if ($sent -ge 28) {
    if ($proof.status -eq "Complete") { "Trigger FNO-65 metrics." } else { "Correct execution proof gaps before FNO-65." }
  } elseif ($issue.status -eq "blocked") {
    "PA to unblock FNO-62 immediately."
  } else {
    "Continue batch without message changes; verify each send and CRM update."
  }

  $issueText = if ($issues.Count -gt 0) { ($issues -join " ") } else { "None" }
  $failSafeDetected = if ($failSafeIssues.Count -gt 0) { "Yes" } else { "No" }
  $riskLevel = if ($failSafeIssues.Count -ge 2 -or ($failSafeIssues -match "CRM FAILURE|REPLY DELAY|SEND FAILURE").Count -gt 0) { "High" } elseif ($failSafeIssues.Count -eq 1) { "Medium" } else { "Low" }
  if ($failSafeIssues.Count -gt 0) { $corrections = 1 }
  $failSafeText = if ($failSafeIssues.Count -gt 0) { ($failSafeIssues -join " ") } else { "None" }
  $duplicateRiskText = if ($coordination.duplicateRisk) { "Yes" } else { "No" }
  $classesText = "Interested=$($reply.classes.Interested), Curious=$($reply.classes.Curious), Objection=$($reply.classes.Objection), Not Relevant=$($reply.classes.'Not Relevant')"
  $cycle = @"
LIVE CONTROL CYCLE - FNO-62

1. Progress:
- $sent / 28
- Phase: $phase
- Status: $($issue.status)

2. Replies:
- Count: $($reply.count)
- Classification: $classesText

3. Issues:
- $issueText

4. Next action:
- $nextAction

Fail-Safe Check:
- Issues detected: $failSafeDetected
- Issues corrected: $corrections
- Risk level: $riskLevel
- Detail: $failSafeText

Coordination Check:
- Conflicts: $($coordination.conflicts)
- Duplicate risk: $duplicateRiskText
- CRM sync status: $($coordination.crmStatus)

First Signal Check:
- Replies (first 10): $($firstSignal.replies)
- Signal Strength: $($firstSignal.strength)
- Seen/read: $($firstSignal.engagement)
- Initial response quality: $($firstSignal.responseQuality)
- Confusion signals: $($firstSignal.confusionSignals)
- Action: $($firstSignal.action)

Execution Proof:
- Status: $($proof.status)
- Send Proof: total_sent=$($proof.totalSent); email=$($proof.email); whatsapp=$($proof.whatsapp); linkedin=$($proof.linkedin)
- CRM Integrity: rows_updated=$($proof.rowsUpdated); missing_fields=$($proof.missingFields)
- Execution Log: FNOMO_EXECUTION_HISTORY entries=$($proof.historyEntries)
- Reply Snapshot: replies_total=$($proof.repliesTotal); Interested=$($proof.interested); Curious=$($proof.curious); Objection=$($proof.objection); Not Relevant=$($proof.notRelevant)
- Proof Issues: $($proof.issues)
"@

  $state = @{
    lastRunAt = $now.ToString("s")
    issueStatus = $issue.status
    sent = $sent
    replies = $reply.count
    issues = $issues
    failSafeIssues = $failSafeIssues
    riskLevel = $riskLevel
    coordination = $coordination
    firstSignalCheck = $firstSignal
    executionProof = $proof
  }
  $state | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statePath -Encoding UTF8
  Add-Comment $fno62 $cycle $false
  Write-Log "Cycle posted. sent=$sent replies=$($reply.count) status=$($issue.status) issues=$($issues.Count) failsafe=$($failSafeIssues.Count) risk=$riskLevel conflicts=$($coordination.conflicts) duplicateRisk=$duplicateRiskText crmSync=$($coordination.crmStatus) firstSignal=$($firstSignal.strength) proof=$($proof.status)"

  if ($issues.Count -gt 0 -or $failSafeIssues.Count -gt 0) {
    Add-Comment $fno58 ("PA ALERT - FNO-62 live control issue: " + $issueText + " Fail-safe: " + $failSafeText + " Coordination: conflicts=" + $coordination.conflicts + ", duplicateRisk=" + $duplicateRiskText + ", crmSync=" + $coordination.crmStatus + ". Execution proof=" + $proof.status + ". Next action: " + $nextAction) $true
  }
} catch {
  Write-Log "ERROR: $($_.Exception.Message)"
  try {
    Add-Comment $fno58 ("PA ALERT - FNO-62 live control monitor failed: $($_.Exception.Message)") $true
  } catch {}
  throw
}
