# Project Map (Truth Map)

This file exists to make the repo understandable in GitHub without moving files around.

## Canonical Execution Surface

- Workbook: `EXCEL/War Room_ Community Outreach Pipeline - FNOMO Master.xlsx`
  - Sheets used as the operating system:
    - `FNOMO_MASTER_PIPELINE`: lead rows + stage/tier/next-action tracking
    - `FNOMO_OUTREACH_READY`: ready-to-send messages (templates + addenda)
    - `FNOMO_EXECUTION_TASKS`: internal execution queue derived from `To do`
    - `FNOMO_EXECUTION_HISTORY`: append-only execution log
    - `Dashboard`: reporting surface

## What Is Automation vs What Is Manual

- Spreadsheet formulas exist (mainly in `Dashboard`), but there are no embedded VBA macros.
- Outreach sending, reply ingestion, and stage movement must be logged manually unless an external mail/CRM system is wired in.

## Where “Reality” Lives

- Leads + next actions: `EXCEL/War Room_ Community Outreach Pipeline - FNOMO Master.xlsx` (`FNOMO_MASTER_PIPELINE`)
- What is ready to send: same workbook (`FNOMO_OUTREACH_READY`)
- What was actually executed: same workbook (`FNOMO_EXECUTION_HISTORY`) plus any send logs under `docs/`

## Naming Guidance (Non-Blocking)

Prefer descriptive filenames for new artifacts:

- `exec_YYYY-MM-DD_<topic>.<ext>`
- `decision_YYYY-MM-DD_<topic>.<ext>`

