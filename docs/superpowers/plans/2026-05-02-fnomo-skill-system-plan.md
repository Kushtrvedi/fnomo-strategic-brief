# Fnomo Skill System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-backed, installable Fnomo skill operating system with a master orchestrator, shared commercial doctrine, specialist execution skills, and local install/validation scripts.

**Architecture:** Replace the current loose Fnomo skill pack with an orchestrator-first system. Centralize doctrine in `fnomo-shared`, keep specialist skills subordinate and execution-focused, add installer and validator scripts, and validate against real Fnomo scenarios.

**Tech Stack:** Markdown skills, PowerShell install/validation scripts, local Git repo, Codex skill discovery via `SKILL.md` metadata.

---

## File Structure

### Existing Files To Audit Or Reuse

- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-decision-engine\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-outreach-generator\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-reply-classifier\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-partner-engine\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-daily-briefing\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-revops-tracker\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-community-engine\SKILL.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-intercept-positioning\SKILL.md`

### New Skill Directories To Create

- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-orchestrator\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-sales-orchestrator\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-outreach-engine\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-reply-handler\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-pipeline-operator\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-gtm-strategy\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-partnership-builder\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-executive-assistant\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-content-creator\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-deck-builder\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-document-operator\SKILL.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-crm-sheet-operator\SKILL.md`

### Shared References To Create

- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\positioning.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\decision-gap-framework.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\pipeline-schema.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\followup-sla.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\objection-taxonomy.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\indian-market-gtm.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\moment-based-triggering.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\tone-and-style.md`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\quality-gate.md`

### Support Scripts To Create

- Create: `D:\Antigravity\eigent\Downloads\fnomo\scripts\install_fnomo_skills.ps1`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\scripts\validate_fnomo_skills.ps1`
- Create: `D:\Antigravity\eigent\Downloads\fnomo\scripts\sync_fnomo_skills.ps1`

### Documentation To Create Or Update

- Create: `D:\Antigravity\eigent\Downloads\fnomo\docs\skill-system\fnomo-skill-inventory.md`
- Modify: `D:\Antigravity\eigent\Downloads\fnomo\docs\superpowers\specs\2026-05-02-fnomo-skill-system-design.md`

## Task 1: Build The Shared Doctrine Layer

**Files:**
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\SKILL.md`
- Create: all files under `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-shared\references\`

- [ ] Extract reusable Fnomo doctrine from the approved spec and existing skill content.
- [ ] Write `fnomo-shared\SKILL.md` so it triggers when Codex needs shared Fnomo commercial rules, quality gates, or positioning context.
- [ ] Write `quality-gate.md` with explicit reject-and-rewrite rules.
- [ ] Write `pipeline-schema.md` using the approved canonical schema and event logic.
- [ ] Write `tone-and-style.md` for premium Indian-market human output standards.
- [ ] Validate that no specialist-specific logic is stored here unless it is truly shared.

## Task 2: Create The Master Orchestrator Skill

**Files:**
- Create: `D:\Antigravity\eigent\Downloads\fnomo\skills\fnomo-orchestrator\SKILL.md`

- [ ] Write `fnomo-orchestrator\SKILL.md` to enforce the thinking layer before execution.
- [ ] Add routing logic for all approved specialist domains.
- [ ] Add the Indu quality gate, event engine framing, and simplicity override.
- [ ] Ensure the orchestrator references `fnomo-shared` rather than duplicating long doctrine inline.
- [ ] Ensure the description is written as a precise trigger, not as documentation.

## Task 3: Refactor Existing Skill Content Into New Skill Names

**Files:**
- Modify or source from:
  - `skills\fnomo-outreach-generator\SKILL.md`
  - `skills\fnomo-reply-classifier\SKILL.md`
  - `skills\fnomo-revops-tracker\SKILL.md`
  - `skills\fnomo-partner-engine\SKILL.md`
  - `skills\fnomo-community-engine\SKILL.md`
  - `skills\fnomo-intercept-positioning\SKILL.md`
- Create:
  - `skills\fnomo-outreach-engine\SKILL.md`
  - `skills\fnomo-reply-handler\SKILL.md`
  - `skills\fnomo-pipeline-operator\SKILL.md`
  - `skills\fnomo-partnership-builder\SKILL.md`
  - `skills\fnomo-sales-orchestrator\SKILL.md`
  - `skills\fnomo-gtm-strategy\SKILL.md`

- [ ] Migrate reusable content from legacy Fnomo skills into the approved orchestrator-first naming model.
- [ ] Rewrite each skill so it is execution-focused and subordinate to orchestrator control.
- [ ] Remove or avoid founder-misaligned positioning from inherited content.
- [ ] Ensure descriptions trigger on real business requests and not vague generic requests.
- [ ] Keep skills concise and move long doctrine to `fnomo-shared\references`.

## Task 4: Create The Missing Executive And Production Skills

**Files:**
- Create:
  - `skills\fnomo-executive-assistant\SKILL.md`
  - `skills\fnomo-content-creator\SKILL.md`
  - `skills\fnomo-deck-builder\SKILL.md`
  - `skills\fnomo-document-operator\SKILL.md`
  - `skills\fnomo-crm-sheet-operator\SKILL.md`

- [ ] Write the executive assistant skill for scheduling support, summaries, reminders, stakeholder prep, and execution discipline.
- [ ] Write the content creator skill for premium authority content, campaigns, founder voice, and distribution assets.
- [ ] Write the deck builder skill for strategic slides and PPT outputs.
- [ ] Write the document operator skill for formal docs, proposals, briefs, and redlines.
- [ ] Write the CRM and sheet operator skill for trackers, Excel/Sheets execution, cleanup, and reporting.

## Task 5: Add Install, Sync, And Validation Scripts

**Files:**
- Create: `scripts\install_fnomo_skills.ps1`
- Create: `scripts\validate_fnomo_skills.ps1`
- Create: `scripts\sync_fnomo_skills.ps1`

- [ ] Create the scripts directory.
- [ ] Implement `install_fnomo_skills.ps1` to copy repo-backed Fnomo skills into `C:\Users\kush_\.codex\skills`.
- [ ] Implement `sync_fnomo_skills.ps1` to refresh installed skills from the repo.
- [ ] Implement `validate_fnomo_skills.ps1` to check folder presence, `SKILL.md` presence, frontmatter keys, and naming rules.
- [ ] Make scripts safe, idempotent, and non-destructive outside Fnomo skill folders.

## Task 6: Inventory And Deconflict The Legacy Skill Set

**Files:**
- Create: `docs\skill-system\fnomo-skill-inventory.md`
- Modify or archive usage intent for existing folders under `skills\`

- [ ] Document which old skills are replaced by the new names.
- [ ] Decide whether legacy folders remain as raw material, redirects, or deprecated assets.
- [ ] Ensure the new suite is the only one intended for installation.
- [ ] Record the migration map so future maintenance is clear.

## Task 7: Validate Skill Quality And Trigger Behavior

**Files:**
- Test against all new skills and scripts

- [ ] Run authoring validation using `validate_fnomo_skills.ps1`.
- [ ] Manually review descriptions for trigger precision.
- [ ] Check that orchestrator-first behavior is reflected in the skill bodies.
- [ ] Validate representative scenarios:
  - follow-up for a Tier A silent lead
  - objection reply for a CA
  - founder briefing
  - partnership deck request
  - CRM cleanup request
  - LinkedIn authority post request
- [ ] Fix any trigger ambiguity or quality-gate gaps.

## Task 8: Install Locally And Prepare GitHub-Backed Usage

**Files:**
- Use scripts under `scripts\`

- [ ] Install the Fnomo skills into `C:\Users\kush_\.codex\skills`.
- [ ] Confirm the installed structure matches the repo source.
- [ ] Stage the design doc, plan doc, skill files, references, and scripts in Git.
- [ ] Commit with a message that clearly marks the Fnomo skill operating system bootstrap.

## Task 9: Final Review

**Files:**
- Review all newly created files

- [ ] Check spec coverage against the approved design.
- [ ] Check for placeholders, contradictions, and duplicated doctrine.
- [ ] Confirm the system now functions as a thinking-controlled, event-driven revenue operating system rather than a loose skill pack.
- [ ] Summarize any remaining future enhancements separately from the completed core build.
