---
name: fnomo-pipeline-operator
description: Use when Fnomo needs pipeline operations, stage movement, inactivity checks, next-action generation, lead prioritization, ownership assignment, daily top-five actions, or disciplined CRM hygiene across active opportunities.
---

# Fnomo Pipeline Operator

## Overview

Operate the pipeline as a live execution system, not a reporting sheet.
Every active lead must have a stage, tier, owner, next action, and timing.

## Control Rules

1. No active lead without a next action.
2. Tier A leads never drift.
3. Stalled stages must be named and acted on.
4. If a lead no longer belongs, move it out instead of hiding it in active pipeline.

## Required Output Fields

Use the canonical schema from `../fnomo-shared/references/pipeline-schema.md`.

## Event Logic

Handle work as:

1. New lead -> assign owner + outreach
2. No reply -> follow-up
3. Reply -> classify + update stage
4. Stage change -> create next action
5. No activity -> escalate

## When Doing Daily Ops

Return:

1. Top 5 priority actions
2. Leads needing follow-up
3. Leads needing escalation
4. Leads needing cleanup
5. Ownership gaps

## Read When Needed

1. `../fnomo-shared/references/pipeline-schema.md`
2. `../fnomo-shared/references/followup-sla.md`
3. `../fnomo-shared/references/quality-gate.md`
