param(
    [string]$RepoSkillRoot = (Join-Path $PSScriptRoot "..\\skills"),
    [string]$TargetRoot = "C:\\Users\\kush_\\.codex\\skills"
)

$skillNames = @(
    "fnomo-orchestrator",
    "fnomo-shared",
    "fnomo-sales-orchestrator",
    "fnomo-outreach-engine",
    "fnomo-reply-handler",
    "fnomo-pipeline-operator",
    "fnomo-gtm-strategy",
    "fnomo-partnership-builder",
    "fnomo-executive-assistant",
    "fnomo-content-creator",
    "fnomo-deck-builder",
    "fnomo-document-operator",
    "fnomo-crm-sheet-operator"
)

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

foreach ($skill in $skillNames) {
    $source = Join-Path $RepoSkillRoot $skill
    $target = Join-Path $TargetRoot $skill

    if (-not (Test-Path $source)) {
        throw "Missing source skill: $source"
    }

    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
    }

    Copy-Item -Recurse -Force $source $target
    Write-Host "[OK] Installed $skill"
}
