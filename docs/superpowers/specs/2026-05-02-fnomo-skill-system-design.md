---
title: Fnomo Skill System Design
date: 2026-05-02
status: approved-for-build
---

# Fnomo Skill System Design

## Overview

Fnomo Codex is not a loose collection of prompts or skills. It is a thinking-controlled, event-driven revenue operating system designed to produce founder-grade sales, GTM, marketing, operations, document, deck, and CRM execution for the Indian market.

The system must outperform generic AI outputs by enforcing three things before execution:

1. Decision-gap thinking
2. Human-quality commercial judgment
3. Structured next-action discipline

This design establishes the repo as the source of truth for all Fnomo skills, with local installation into the Codex-discoverable skills directory.

## Goals

1. Create a reusable, GitHub-backed Fnomo skill library for current and future commercial execution.
2. Ensure Codex auto-uses the right Fnomo skill when tasks match real-world GTM, sales, marketing, CRM, and operations signals.
3. Enforce a consistent Fnomo operating model:
   decision awareness -> trust -> conversion.
4. Make all specialist execution subordinate to a single top-level thinking and validation system.
5. Support future expansion without turning the system into an unmaintainable prompt bundle.

## Non-Goals

1. Build a full production CRM or database product inside this repo.
2. Implement persistent autonomous background services in v1.
3. Replace every existing external tool used by the user.
4. Over-engineer memory storage before the skill system proves its operating model.

## Core Principle

Fnomo Codex is a thinking-controlled, event-driven revenue operating system.

The locked core stack is:

Thinking Layer -> Orchestrator -> Event Engine -> Pipeline Intelligence

All specialist skills are subordinate execution units, not independent thinkers.

## Layer 0: Indu Quality Gate

Before any output is released, the system must validate:

1. Does this expose or deepen a decision gap?
2. Does this sharpen Fnomo positioning as a decision validation system?
3. Is this insight-led rather than generic or explanatory?
4. Is there a clear next action and owner when the task requires execution?
5. Does this feel human and commercially credible rather than AI-templated?

Hard rule:

If the output fails any condition, reject it, rewrite it, and validate again before release.

Additional hard rule:

If no decision moment is identifiable, do not force Fnomo into the output. Reframe the response or ask for the missing decision context.

## Layer 1: Thinking System

Before routing any Fnomo task, the orchestrator must answer:

1. What decision gap exists?
2. What belief or behavior must change?
3. What realization should the user or lead reach?

No execution is allowed without:

1. Clear thinking
2. A defined outcome
3. A mapped decision gap

## Layer 2: Orchestrator Logic

The top-level skill is `fnomo-orchestrator`.

Its responsibilities are:

1. Classify task type
2. Enforce the thinking layer
3. Apply the quality gate
4. Detect event triggers
5. Route to the correct specialist skill
6. Validate the output before release

### Routing Map

| Input Type | Skill |
|---|---|
| Sales leadership, deals, objections, commercial moves | `fnomo-sales-orchestrator` |
| Cold outreach, LinkedIn, WhatsApp, re-engagement | `fnomo-outreach-engine` |
| Reply handling, inbound signals, objections, classification | `fnomo-reply-handler` |
| Pipeline updates, stage logic, follow-up control, prioritization | `fnomo-pipeline-operator` |
| GTM planning, segmentation, channel strategy, execution design | `fnomo-gtm-strategy` |
| Partnerships, schools, institutions, strategic alliances | `fnomo-partnership-builder` |
| Executive assistance, reminders, summaries, coordination | `fnomo-executive-assistant` |
| Content creation, authority content, campaign narratives | `fnomo-content-creator` |
| Decks, slides, strategic presentations, partner decks | `fnomo-deck-builder` |
| Documents, proposals, agreements, letters, briefs | `fnomo-document-operator` |
| CRM, Excel, Sheets, trackers, lead sheets, reporting | `fnomo-crm-sheet-operator` |

## Layer 3: Event Engine

The system operates as:

Event -> Trigger -> Action

This is the execution model for pipeline and commercial operations.

### Example Events

| Event | Action |
|---|---|
| New lead | assign owner + create outreach |
| No reply in 48h | follow-up 1 |
| Reply received | classify + route |
| Stage change | generate next action |
| No activity | escalate |

This layer exists to prevent manual pipeline drift.

## Layer 4: Pipeline Intelligence System

### Stage Model

Every stage must have:

1. Entry criteria
2. Exit criteria
3. Mandatory next action

### Stage Exit Criteria

| Stage | Exit Condition |
|---|---|
| Contacted | reply or 2+ engagement signals |
| Engaged | answered decision-process or decision-gap question |
| Qualified | admitted or demonstrated a decision gap |
| Converted | committed next step |

### Next Action Engine

| Stage | Auto Action |
|---|---|
| Contacted | follow-up in 48h |
| Engaged | deepen the decision gap |
| Qualified | push to call or committed next step |
| Silent | re-engagement sequence |

### Inactivity Detection

| Condition | Action |
|---|---|
| 3 days no reply | follow-up |
| 7 days no movement | escalate |
| 14 days stalled | cold |

### Lead Lifecycle

Active -> Nurture -> Dead

## Layer 5: Prioritization Engine

Daily priority scoring:

1. Tier A = +3
2. Recent reply = +3
3. Stale lead = +2
4. High-value segment = +2

The system must produce the top 5 priority actions daily when asked for operational review or execution prioritization.

## Layer 6: Data Schema

All pipeline-facing skills must align to this canonical lead structure:

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

This is the minimum canonical schema for skill output, sheets logic, and future automation.

## Layer 7: Context Memory

Each lead context should preserve:

1. Last conversation summary
2. Decision gap identified
3. Objections raised
4. Behavioral signals

V1 design decision:

Define the schema and expected behavior now, but keep implementation lightweight. Skills should read and write structured lead context when available, without requiring a heavy persistence framework inside the skill system itself.

## Layer 8: Metrics -> Decision Engine

The system must not only report metrics. It must explain what decisions should change.

It should analyze:

1. Reply rate
2. Stage conversion
3. Drop-off points
4. Segment performance
5. Messaging failure patterns

It must answer:

1. Where deals die
2. Why messaging fails
3. Which segment converts

## Layer 9: Failure And Cleanup Logic

| Condition | Action |
|---|---|
| Not relevant | Lost |
| No reply after sequence | Cold pool |
| Wrong ICP | Remove |

The system must not allow dead or invalid leads to remain disguised as active pipeline.

## Layer 10: Ownership Model

Every lead must have:

1. A clear owner
2. Responsibility for the next action

Without ownership, pipeline discipline collapses. Skills must preserve or assign ownership when producing operational outputs.

## Layer 11: Moment-Based Execution

Fnomo GTM is decision-moment driven, not merely funnel-driven.

The system must identify when a real decision is happening, such as:

1. Investor about to act
2. Advisor about to recommend
3. Student about to choose
4. Institution about to commit

Fnomo should be inserted at the decision moment, not bolted onto generic awareness content.

## Layer 12: Simplicity Override

If the system becomes too complex for consistent execution, simplify before release.

Reason:

1. Complexity kills adoption
2. Simplicity improves repeatability
3. Execution discipline is more valuable than theoretical sophistication

## Repo Structure

This repo is the source of truth for the Fnomo skill system.

```text
skills/
  fnomo-orchestrator/
  fnomo-sales-orchestrator/
  fnomo-outreach-engine/
  fnomo-reply-handler/
  fnomo-pipeline-operator/
  fnomo-gtm-strategy/
  fnomo-partnership-builder/
  fnomo-executive-assistant/
  fnomo-content-creator/
  fnomo-deck-builder/
  fnomo-document-operator/
  fnomo-crm-sheet-operator/
  fnomo-shared/
    references/
      positioning.md
      decision-gap-framework.md
      pipeline-schema.md
      followup-sla.md
      objection-taxonomy.md
      indian-market-gtm.md
      moment-based-triggering.md
      tone-and-style.md
      quality-gate.md

scripts/
  install_fnomo_skills.ps1
  validate_fnomo_skills.ps1
  sync_fnomo_skills.ps1
```

## Skill Design Standard

Each skill follows:

```text
skill-name/
  SKILL.md
  scripts/            # optional
  references/         # optional
  agents/openai.yaml  # optional
```

### Trigger Principle

`description` in `SKILL.md` is the activation system, not documentation.

Descriptions must be precise enough that Codex can:

1. Trigger the right skill for the right Fnomo task
2. Avoid false activation for unrelated work
3. Preserve clean routing through `fnomo-orchestrator`

## Shared Knowledge Model

The shared reference layer provides the common commercial doctrine for all specialist skills.

Recommended files:

1. `positioning.md`
2. `decision-gap-framework.md`
3. `pipeline-schema.md`
4. `followup-sla.md`
5. `objection-taxonomy.md`
6. `indian-market-gtm.md`
7. `moment-based-triggering.md`
8. `tone-and-style.md`
9. `quality-gate.md`

Recommended addition:

`fnomo-shared` should be a real skill wrapper with a `SKILL.md`, not only a folder, so shared rules can be loaded intentionally and predictably.

## Installation Model

The repo remains the source of truth.

### `install_fnomo_skills.ps1`

Responsibilities:

1. Scan the repo skill directories
2. Copy Fnomo skills into the discoverable local Codex skills directory
3. Preserve skill structure
4. Allow repeatable installation on future machines

### `validate_fnomo_skills.ps1`

Checks:

1. YAML frontmatter
2. Naming
3. Required files
4. Basic trigger metadata presence
5. Installability assumptions

### `sync_fnomo_skills.ps1`

Responsibilities:

1. Update local installed skills from repo versions
2. Preserve current source-of-truth workflow
3. Support ongoing improvements through GitHub

## Auto-Use Behavior

Auto-use should come from:

1. Precise `description` trigger fields in each skill
2. Explicit routing logic inside `fnomo-orchestrator`

Rule:

Precise triggers enable correct activation. Vague triggers create system failure.

## Validation Model

Validation is split into two categories.

### Authoring Validation

Checks:

1. Folder structure
2. Valid `SKILL.md`
3. Naming compliance
4. Required files
5. Install and sync behavior

### Behavior Validation

Checks:

1. Right task -> right skill
2. Wrong task -> no trigger
3. Thinking layer applied before execution
4. Quality gate blocks weak output
5. Specialist output preserves Fnomo positioning

Representative scenarios:

1. Follow-up for a silent Tier A lead
2. CRM update with next actions
3. Founder briefing for a meeting
4. Partnership deck creation
5. Objection handling for a CA firm
6. LinkedIn authority post from a decision gap

## GitHub Workflow

Workflow:

1. Build skills in this repo
2. Validate locally
3. Install through scripts
4. Test against real scenarios
5. Commit improvements
6. Sync across environments

This repo is the permanent operating base for future Fnomo skill evolution.

## Initial Build Scope

Core-first rollout:

1. `fnomo-orchestrator`
2. `fnomo-shared`
3. `fnomo-sales-orchestrator`
4. `fnomo-outreach-engine`
5. `fnomo-reply-handler`
6. `fnomo-pipeline-operator`
7. `fnomo-gtm-strategy`
8. `fnomo-executive-assistant`
9. `fnomo-content-creator`
10. `fnomo-deck-builder`
11. `fnomo-document-operator`
12. `fnomo-crm-sheet-operator`
13. `fnomo-partnership-builder`

These cover the user's current operating needs while preserving room for future specialist additions.

## Risks

1. Overly long skill bodies may harm triggering efficiency and increase noise.
2. Weak descriptions may cause incorrect activation.
3. Too much independent logic inside specialist skills may undermine the orchestrator.
4. Attempting to solve persistence fully in v1 may slow adoption and increase complexity.

## Mitigations

1. Keep descriptions short, high-signal, and trigger-oriented.
2. Centralize doctrine in `fnomo-shared`.
3. Keep specialist skills execution-focused and subordinate.
4. Validate with realistic scenarios before considering the system complete.

## Final Outcome

The finished system should behave as:

1. Thinking-controlled
2. Founder-aligned
3. Event-driven
4. Pipeline-disciplined
5. Installable
6. GitHub-backed
7. Scalable for future Fnomo commercial operations
