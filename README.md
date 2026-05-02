# Fnomo Workspace (GTM + Pipeline)

This repository is the working workspace for Fnomo GTM execution: pipeline artifacts, outreach assets, and supporting docs.

## Start Here

1. Pipeline / execution workbook (primary operating surface):
   - `EXCEL/War Room_ Community Outreach Pipeline - FNOMO Master.xlsx`
   - If Excel shows a repair prompt, use: `EXCEL/War Room_ Community Outreach Pipeline - FNOMO Master.OPENXML_REPAIRED.xlsx`
2. Pipeline docs and references:
   - `docs/`
3. Slides and pitch material:
   - `ppt/`

## Repo Map (High Level)

- `EXCEL/`: Lead/pipeline workbooks and data exports used during execution.
- `docs/`: Operating model, outreach scripts, briefs, and working notes.
- `ppt/`: Partnership decks and policy slides.
- `Images and content/`: Creative assets and automation/tooling used for content + outreach ops.
- `agents/`: Agent instructions / helpers (if present).
- `plugins/`: Local plugin/tooling folders (sources only; virtualenvs/node_modules ignored).

## Commit Naming (So Changes Are Readable)

Use one of these formats:

- `decision(YYYY-MM-DD): <decision name>`
- `exec(YYYY-MM-DD): <execution name>`

Commit body should include:
- `Context:` what triggered this
- `Change:` what changed in reality
- `Next:` the next required action

