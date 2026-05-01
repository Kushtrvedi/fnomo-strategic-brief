param(
    [string]$RepoSkillRoot = (Join-Path $PSScriptRoot "..\\skills"),
    [string]$TargetRoot = "C:\\Users\\kush_\\.codex\\skills"
)

& (Join-Path $PSScriptRoot "install_fnomo_skills.ps1") -RepoSkillRoot $RepoSkillRoot -TargetRoot $TargetRoot
