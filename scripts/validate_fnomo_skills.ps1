param(
    [string]$RepoSkillRoot = (Join-Path $PSScriptRoot "..\\skills")
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

$errors = @()

foreach ($skill in $skillNames) {
    if ($skill -notmatch '^[a-z0-9-]+$') {
        $errors += "Invalid skill name: $skill"
    }

    $path = Join-Path $RepoSkillRoot $skill
    $skillFile = Join-Path $path "SKILL.md"

    if (-not (Test-Path $path)) {
        $errors += "Missing skill folder: $path"
        continue
    }

    if (-not (Test-Path $skillFile)) {
        $errors += "Missing SKILL.md: $skillFile"
        continue
    }

    $content = Get-Content $skillFile -Raw

    if ($content -notmatch '(?s)^---\s*.*?name:\s*.+?description:\s*.+?---') {
        $errors += "Invalid or missing frontmatter in: $skillFile"
    }
}

$sharedRefs = @(
    "positioning.md",
    "decision-gap-framework.md",
    "pipeline-schema.md",
    "followup-sla.md",
    "objection-taxonomy.md",
    "indian-market-gtm.md",
    "moment-based-triggering.md",
    "tone-and-style.md",
    "quality-gate.md"
)

$sharedRoot = Join-Path $RepoSkillRoot "fnomo-shared\\references"
foreach ($ref in $sharedRefs) {
    $refPath = Join-Path $sharedRoot $ref
    if (-not (Test-Path $refPath)) {
        $errors += "Missing shared reference: $refPath"
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Host "[ERROR] $_" }
    throw "Fnomo skill validation failed."
}

Write-Host "[OK] Fnomo skills validation passed."
