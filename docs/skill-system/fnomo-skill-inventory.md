# Fnomo Skill Inventory

## Current Source-Of-Truth Skills

1. `fnomo-orchestrator`
2. `fnomo-shared`
3. `fnomo-sales-orchestrator`
4. `fnomo-outreach-engine`
5. `fnomo-reply-handler`
6. `fnomo-pipeline-operator`
7. `fnomo-gtm-strategy`
8. `fnomo-partnership-builder`
9. `fnomo-executive-assistant`
10. `fnomo-content-creator`
11. `fnomo-deck-builder`
12. `fnomo-document-operator`
13. `fnomo-crm-sheet-operator`

## Legacy Skills And Migration Map

| Legacy Skill | New Home |
|---|---|
| `fnomo-outreach-generator` | `fnomo-outreach-engine` |
| `fnomo-reply-classifier` | `fnomo-reply-handler` |
| `fnomo-revops-tracker` | `fnomo-pipeline-operator` and `fnomo-sales-orchestrator` |
| `fnomo-partner-engine` | `fnomo-partnership-builder` |
| `fnomo-daily-briefing` | `fnomo-pipeline-operator` and `fnomo-executive-assistant` |
| `fnomo-community-engine` | `fnomo-outreach-engine` and `fnomo-content-creator` |
| `fnomo-intercept-positioning` | `fnomo-shared` and `fnomo-gtm-strategy` |
| `fnomo-decision-engine` | retained as separate legacy/product skill, not part of the new core commercial operating system |

## Installation Rule

Only the source-of-truth skills listed above should be installed by the Fnomo install script.
