# Fnomo Notion Backend Sync

This setup mirrors Fnomo execution data into Notion using an internal integration token.

## Source Of Truth

The operating source remains:

- Google Sheet export of `FNOMO_MASTER_PIPELINE`, when `FNOMO_MASTER_PIPELINE_CSV_URL`, `FNOMO_GOOGLE_SHEET_CSV_URL`, or `FNOMO_GOOGLE_SHEET_ID` + `FNOMO_MASTER_PIPELINE_GID` is set.
- Google Sheet export of `FNOMO_EXECUTION_HISTORY`, when `FNOMO_EXECUTION_HISTORY_CSV_URL` or `FNOMO_GOOGLE_SHEET_ID` + `FNOMO_EXECUTION_HISTORY_GID` is set.
- Local workbook fallback: `EXCEL/War Room_ Community Outreach Pipeline - FNOMO Master.xlsx`.

Notion is the database backend mirror. It should not become a second manual source of truth.

## Required Environment

```powershell
$env:FNOMO_NOTION_API_KEY = "ntn_..."
$env:NOTION_FNOMO_CLIENTS_DATABASE_ID = "e8a8aa3c-b995-8368-8495-014b8ea295c3"
$env:NOTION_FNOMO_CONTACTS_DATABASE_ID = "3548aa3c-b995-8148-a653-fead444e56fe"
$env:NOTION_FNOMO_EXECUTION_TASKS_DATABASE_ID = "6fb8aa3c-b995-82ec-806b-01b6cd1b2915"
$env:NOTION_FNOMO_EXECUTION_HISTORY_DATABASE_ID = "3548aa3c-b995-818a-8ede-ed9a5d99aac3"
$env:FNOMO_GOOGLE_SHEET_ID = "..."
$env:FNOMO_MASTER_PIPELINE_GID = "..."
$env:FNOMO_EXECUTION_HISTORY_GID = "..."
```

Current Notion parent:

- `Fnomo Sales CRM`: `5818aa3c-b995-827e-af29-011d0732f5bc`
- Clients database: `e8a8aa3c-b995-8368-8495-014b8ea295c3`
- Contacts database: `3548aa3c-b995-8148-a653-fead444e56fe`
- Execution database, renamed from template `Tasks`: `6fb8aa3c-b995-82ec-806b-01b6cd1b2915`
- Deals database: `0be8aa3c-b995-822e-8a79-81e2d86e3f8b`
- Execution history mirror database: `3548aa3c-b995-818a-8ede-ed9a5d99aac3`
- Legacy flat leads mirror database, archived and no longer primary: `3548aa3c-b995-81dd-a33c-e48c87e3a007`

If the Notion databases do not exist yet, share the parent Notion page with the internal integration, then run:

```powershell
$env:NOTION_FNOMO_PARENT_PAGE_ID = "..."
python scripts/sync_fnomo_notion.py --create-databases
```

The current token must be attached to the same Notion integration that has access to the Fnomo CRM page. Fnomo must use the `Fnomo` integration token, not a separate workspace integration such as `RE-YOU OS`.

The sync scripts look for tokens in this order:

1. `FNOMO_NOTION_API_KEY`
2. `NOTION_FNOMO_API_KEY`

The generic `NOTION_API_KEY` is intentionally not used for Fnomo sync. This prevents a separate integration such as `RE-YOU OS` from being used against the Fnomo Sales CRM by mistake.

If Notion returns `object_not_found`, either the wrong integration token is loaded or the page/database has not been shared with that integration.

## Run

Validate without writing:

```powershell
python scripts/sync_fnomo_notion.py --dry-run
```

Sync:

```powershell
python scripts/sync_fnomo_notion.py
```

Sync leads plus execution tasks:

```powershell
python scripts/sync_fnomo_notion.py --sync-execution
```

Relational rebuild:

```powershell
python scripts/restructure_fnomo_notion_relational.py
```

## Mirrored Data

`FNOMO_MASTER_PIPELINE` maps into Notion as a relational sales model.

Account fields in `Clients`:

- Name
- Company
- Stage
- Last Contact Date
- Next Action
- Next Action Date
- Notes
- Channel
- Tier

Person fields in `Contacts`:

- Name
- Company
- Role
- LinkedIn
- Email
- Phone
- Stage
- Last Contact Date
- Next Action
- Next Action Date
- Notes
- Channel
- Tier

Execution task fields:

- Task
- Client
- Contact
- Type
- Priority
- Due date
- Status
- Stage Context
- Additional Information

Required execution views:

- `TODAY`: due date equals the current operating date.
- `FOLLOW-UP DUE`: overdue and not done.
- `TIER A PRIORITY`: priority equals High.

`FNOMO_EXECUTION_HISTORY` maps into a Notion database keyed by a generated `History Key`.

Mirrored fields:

- Date
- Action Type
- Lead or Task
- Owner
- Channel
- Outcome
- Next Move
- Source
- Row Hash
- Last Synced At

## Data Rules

- Sheet remains the source of truth.
- Notion is only the structured visibility layer.
- One company must have one Client record.
- Every named person must live in Contacts and relate to one Client.
- Execution tasks must relate to both Client and Contact.
- Deals are created only after engagement and partnership discussion.
- Internal duplicate-control fields such as row hashes and sync keys must not be visible in the operator-facing Notion schema.
