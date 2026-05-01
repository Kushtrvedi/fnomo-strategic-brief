# Fnomo Execution Operating Model

## Command Structure

`Kush -> Codex -> specialist execution -> review gate -> workbook update -> EOD report`

`To do` is the main truth source for execution priority.

The rest of the workbook remains important, but it serves as an intelligence layer:

- `Institutional School Outreach` -> school names, principals, emails, phones
- `influential_data_for _corporate` -> platform and company contacts
- `Corporate Pilot Outreach` -> enterprise targets
- `Influencer Hit List` -> creator opportunities
- `Telegram_War_Room`, `Reddit_War_Room`, `Outreach_Database` -> community/channel inventory

## Source of Truth Rules

1. `To do` = execution mandate
2. `FNOMO_MASTER_PIPELINE` = live lead system
3. `FNOMO_EXECUTION_TASKS` = internal work queue
4. `FNOMO_OUTREACH_READY` = ready-to-send message bank
5. `FNOMO_EXECUTION_HISTORY` = cumulative executed-action log
6. other sheets = enrichment only

## Working Loop

When Kush sends an update, Codex should:

1. read the update
2. map it to one or more rows in `To do`, `FNOMO_MASTER_PIPELINE`, or `FNOMO_EXECUTION_TASKS`
3. update sent dates, stage movement, notes, and blockers
4. identify the next best move
5. if the task is medium/high stakes, run LLM Council review first
6. if the output is weak or incomplete, reroute the task through a specialist execution pass
7. write the result back into the workbook and repo snapshots
8. include it in `FNOMO_EXECUTION_HISTORY`
9. roll it into the EOD report

## Review Gate

Use the local Fnomo engine through the LLM Council environment for medium/high tasks:

`D:\Antigravity\eigent\Downloads\fnomo\Images and content\llm-council\.venv\Scripts\python.exe D:\Antigravity\eigent\Downloads\fnomo\Images and content\fnomo_engine.py "<task>"`

Notes:

- low tasks can execute directly
- medium/high tasks should be reviewed first when practical
- `G0DM0D3` should be treated as an alternate multi-model reasoning reference layer, not the primary source of truth

## Specialist Execution Model

Codex routes work using the Fnomo skills already created:

- `fnomo-pipeline-operator`
- `fnomo-crm-sheet-operator`
- `fnomo-outreach-engine`
- `fnomo-reply-handler`
- `fnomo-sales-orchestrator`
- `fnomo-executive-assistant`

Sub-agents should be created on demand for bounded tasks such as:

- contact enrichment
- outreach drafting
- report synthesis
- cleanup and classification

## Automation Targets

Morning automation:

- read `To do`
- refresh lead/task sheets
- identify top priorities
- prepare outreach due today

Evening automation:

- capture movement from the day
- refresh follow-ups
- update execution history
- produce EOD summary

## Kush Responsibilities

- update Codex with what was actually sent, contacted, replied to, or completed
- keep `To do` current
- handle live human sending when needed
- take meetings once booked

## Codex Responsibilities

- maintain workbook structure and discipline
- update pipeline and task sheets
- suggest next moves
- prepare outreach and follow-ups
- keep cumulative execution history
- maintain GitHub-backed snapshots
- produce EOD reporting
