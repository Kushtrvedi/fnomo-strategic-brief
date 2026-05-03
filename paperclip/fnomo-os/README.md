# Fnomo Paperclip Operating System

This package configures Paperclip as the Fnomo orchestration layer.

Flow:

Kush -> PA -> Paperclip -> Codex -> Specialized Agents -> CRM truth.

Rules:

- Every task maps to a Fnomo pipeline event.
- Every task produces a next action.
- No generic outputs.
- No outreach is sent on Sunday.
- Sheets are the source of truth.
- Paperclip health must be checked start of day, mid-cycle, and end of day.
- Major execution briefs append System Check status, issue, correction, and next priority.
