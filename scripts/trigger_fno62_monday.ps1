$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:3100/api"
$fno62 = "89b798a8-c24d-4d53-9f57-1aa16d9f5233"
$agent = "514aebc7-f334-4659-a7c6-aff8adbbd7b0"
$logDir = "C:\Users\kush_\.paperclip\instances\default\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "fnomo-fno62-monday-trigger.log"
function Write-Log($msg) { Add-Content -LiteralPath $log -Value ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg) }
try {
  $health = Invoke-RestMethod -Uri "$base/health" -Method Get -TimeoutSec 20
  if ($health.status -ne "ok") { throw "Paperclip health not ok: $($health | ConvertTo-Json -Compress)" }
  $issue = Invoke-RestMethod -Uri "$base/issues/$fno62" -Method Get -TimeoutSec 20
  $body = @"
MONDAY EXECUTION TRIGGER - START FNO-62 NOW

Execution window opened: Monday 2026-05-04 08:00 IST.

Execute without re-preparation:
- Send 28 Follow-up 1 messages using prepared plan.
- Channel split: 13 Email, 10 WhatsApp, 5 LinkedIn.
- Message rules: trigger memory of wrong decision; do not explain Fnomo; end with a question.
- Post-send per lead: Last Contact Date=2026-05-04, Next Action=Follow-up 2, Next Action Date=2026-05-08.
- Log every action in FNOMO_EXECUTION_HISTORY.
- No Tier B/C work. No new outreach. No skipped CRM updates.
- After batch: publish FNO-65 metrics.

LIVE RUN CONTROL MODE IS ACTIVE:
- 08:00-09:30: track sends, skipped leads, duplicates, correct channel, and CRM writeback after each send.
- After first 5 sends: watch replies/read signals/opens if available.
- After first 10 sends with no activity: flag possible messaging weakness, but do not change messaging mid-batch.
- After about 15 sends: post checkpoint with sent count, reply count, engagement quality, and issues.
- After 28/28 sends: verify 100% CRM updates and trigger FNO-65 metrics.
- Every live-control cycle must report: Progress, Replies, Issues, Next action.

EXECUTION PROOF MODE IS ACTIVE:
- A send is not complete unless send success, CRM writeback, and FNOMO_EXECUTION_HISTORY logging are visible.
- After each send, verify lead, founder owner, stage, next action, and next action date.
- Required proof values: Last Contact Date=2026-05-04, Next Action=Follow-up 2, Next Action Date=2026-05-08.
- After 28/28 sends, final proof must show total_sent=28, email=13, whatsapp=10, linkedin=5, rows_updated=28, missing_fields=0, history_entries=28.
- If it is not logged, it did not happen.
"@
  Invoke-RestMethod -Uri "$base/issues/$fno62/comments" -Method Post -ContentType "application/json" -Body (@{ body = $body; interrupt = $true } | ConvertTo-Json -Compress) -TimeoutSec 30 | Out-Null
  Invoke-RestMethod -Uri "$base/issues/$fno62" -Method Patch -ContentType "application/json" -Body (@{ status = "in_progress" } | ConvertTo-Json -Compress) -TimeoutSec 30 | Out-Null
  Invoke-RestMethod -Uri "$base/issues/$fno62/checkout" -Method Post -ContentType "application/json" -Body (@{ agentId = $agent; expectedStatuses = @("todo","backlog","blocked","in_review","in_progress") } | ConvertTo-Json -Depth 4 -Compress) -TimeoutSec 30 | Out-Null
  Write-Log "FNO-62 Monday execution trigger fired successfully. Previous status: $($issue.status)"
} catch {
  Write-Log "ERROR: $($_.Exception.Message)"
  try {
    $pa = "d38a3328-3324-438e-aacb-b068897a2a8d"
    $alert = "FNO-62 Monday trigger failed: $($_.Exception.Message). PA must inform Kush and restart execution manually."
    Invoke-RestMethod -Uri "$base/issues/$pa/comments" -Method Post -ContentType "application/json" -Body (@{ body = $alert; interrupt = $true } | ConvertTo-Json -Compress) -TimeoutSec 30 | Out-Null
  } catch {}
  throw
}
