# Pipeline Schema

## Canonical Lead Structure

```json
{
  "lead_name": "",
  "segment": "",
  "stage": "",
  "tier": "",
  "last_contact": "",
  "next_action": "",
  "status": "",
  "notes": "",
  "last_insight": "",
  "objection_history": ""
}
```

## Required Fields

1. `stage`
2. `tier`
3. `last_contact`
4. `next_action`
5. `status`
6. `notes`

## Stage Model

1. New
2. Contacted
3. Engaged
4. Qualified
5. Converted
6. Lost

## Exit Logic

1. Contacted -> reply or 2+ engagement signals
2. Engaged -> answered decision-process question
3. Qualified -> admitted decision gap or committed evaluation
4. Converted -> committed next step

## Event Model

1. New lead -> assign + outreach
2. Reply -> classify + route
3. No reply -> follow-up
4. Stage stuck -> escalate
5. Converted -> activate next workflow
