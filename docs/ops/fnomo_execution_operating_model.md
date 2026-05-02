# Fnomo Execution Operating Model

## Command Structure

`Kush -> PA -> Codex -> agency agents -> skill allocation -> task execution -> task result -> confidence score -> done/loopback -> PA brief -> Kush`

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
7. Notion is a structured visibility layer, never an independent CRM

## Enforcement Contract

Every user update is interpreted as:

- `Name`
- `Company`
- `Action Taken`
- `Channel`
- `Date`
- `Outcome`
- `Next Step`

Missing fields must be inferred when low-risk or flagged when the inference would affect pipeline movement.

Every lead must always carry:

- stage
- last contact date
- next action
- next action date
- notes

Every execution-history row must carry:

- `Outcome`: one of `Interested`, `Curious`, `Objection`, `Not Relevant`, `No Response`
- `Outcome Notes`: free-text evidence supporting the classification

Allowed stages only:

`New -> Contacted -> Engaged -> Qualified -> Converted / Lost`

Rules:

- `Contacted` leads enter the follow-up clock.
- 48 hours with no reply -> Follow-up 1.
- 4 days with no reply -> Follow-up 2.
- 7 days with no reply -> escalate call or mark cold.
- `Interested`, `Curious`, or `Objection` -> move to `Engaged`.
- `Not Relevant` -> move to `Lost`.
- `No Response` -> remain `Contacted` and stay inside the follow-up SLA.
- Tier A leads cannot remain `New` for more than 24 hours.
- No lead can remain without a next action date.
- Deals are created only when a lead is `Qualified`, monetary value is visible, and a partnership discussion has started.

Output format for execution turns:

1. Update Summary
2. Pipeline Impact
3. Next Actions (Top Priority)

If the work becomes data-heavy and action-light, the execution loop has failed.

## PA Control Loop

This chat is the main command/control chat for Fnomo.

All project and automation outputs should be brought back here in short form before the next execution decision.

Control chain:

1. Kush gives instruction.
2. PA classifies and briefs the task.
3. Codex executes through the correct Fnomo skill or agent.
4. Agency agents may be used for bounded specialist work when needed.
5. Codex reports task result and confidence score.
6. If confidence is `8/10` or higher, mark done.
7. If confidence is below `8/10`, loop back through Codex/agent/skill allocation.
8. PA briefs Kush with the next decision.

Default PA brief:

1. `Execution made`
2. `Next plan for Codex`
3. `Next plan for Kush`
4. `Confidence score`

## Sunday Planning Rule

Sunday is planning-only.

Allowed on Sunday:

- prepare Monday queue
- update workbook/Notion planning state
- summarize automation results
- draft messages
- identify blockers

Not allowed on Sunday unless Kush explicitly overrides:

- outbound sends
- follow-up execution
- cold expansion
- call escalation

If any live execution is due on Sunday, move the due date to the next working day and mark it as Monday planning.

## Execution Spine Modes

Every Fnomo request must be routed into one primary execution mode before output:

1. `OUTREACH MODE`: generate a problem-led message that triggers decision awareness.
2. `REPLY HANDLING MODE`: classify the reply as `Interested`, `Curious`, `Objection`, or `Not Relevant`, then generate the response and next step.
3. `CONVERSATION MODE`: ask structured questions to expose the decision gap before explaining Fnomo.
4. `FOLLOW-UP MODE`: reference previous context and reopen the conversation naturally.
5. `CLOSING MODE`: reduce risk perception and move toward yearly commitment without discounting.
6. `FOUNDER ACTIVATION MODE`: generate low-effort founder actions that create usage, proof, and referrals.

Mode rule:

- if a request mixes modes, choose the one closest to the next commercial action.
- every mode output must have a next step.
- every mode must reinforce Fnomo as decision validation, not advice, education, or a generic tool.

## Notion Visibility Mapping

- `Clients` is the account layer: one company, one record.
- `Contacts` is the person layer: every named lead links to exactly one Client.
- `Execution` is the task layer: every current task links to both a Contact and a Client and carries stage context.
- `Deals` remains optional and is only used after engagement, when a partnership discussion has started.
- The old flat leads mirror is archived; duplicate person/company storage is not allowed.
- Sheet fields are mirrored into Notion, but the sheet remains the authority.

Execution views:

- `TODAY`: tasks due on the operating date.
- `FOLLOW-UP DUE`: overdue tasks that are not done.
- `TIER A PRIORITY`: high-priority task queue.
- `Fnomo GTM Command Dashboard`: board-facing read layer with reply rate, engagement rate, blockers, and learning narrative.

Board-facing metrics:

- `Reply Rate = replies / contacted`
- `Engagement Rate = engaged outcomes / contacted`
- A high contacted count with zero replies is a positioning failure, not a pipeline win.
- The command dashboard must include `What We Are Learning`, otherwise the data is not board-ready.

## Messaging Trigger Enforcement

Current GTM diagnosis:

- zero replies means a trigger problem, not a pipeline-volume problem.
- contacted/no-response leads should not receive more explanation.
- outreach must trigger memory of a wrong decision before describing Fnomo.

Messaging Test Batch 1:

- pause new cold expansion.
- target `Tier A + Contacted + No Response` first.
- tag the cohort as `Messaging Test Batch 1`.
- set next action to `Re-engage with new messaging angle`.
- CA Version A opens with: `In the last few months, have you had a client take an investment decision that didn't work out as expected?`
- Version B tests the confidence-gap frame before capital is committed.
- success target is first 5-10 replies, not demos or conversion.

## Founder Circle Activation Automation

Founder Circle is the pre-launch trust layer for the India Membership yearly package. It should convert paid founders into decision-driven advocates, not passive subscribers.

Core rule:

- founder advocacy begins after a decision-clarity shift, not after a generic ask.
- the operating sequence is `usage -> realization -> proof -> advocacy -> growth`.
- do not request a testimonial before the founder has used validation on a real decision.

Contact fields maintained in Notion:

- `Founder Activation`: founder has submitted one current decision.
- `Validation Used`: founder has run one real decision through validation.
- `Testimonial Captured`: founder has given text, voice, public post, or case proof.
- `Referrals Count`: number of relevant referrals introduced.
- `Advocacy Score`: activation score from 0 to 5.
- `Advocacy Status`: `Inactive`, `Engaged`, or `Advocate`.
- `Activation Day`: current playbook step.
- `Founder Archetype`: primary influence pattern.
- `Secondary Archetype`: backup/hybrid influence pattern.
- `Archetype Confidence`: confidence in assignment.
- `Influence Channel`: natural activation channel.
- `Archetype Evidence`: why the assignment was made.

Scoring:

- `0-1` -> Inactive.
- `2-3` -> Engaged.
- `4+` -> Advocate.

Activation triggers:

- Day 1: ask `What is one investment or capital decision you are currently thinking about?`
- Day 2: ask founder to validate one real decision before acting.
- Day 4: ask `Did anything change in how you think before acting?`
- Day 6: ask `Who else do you know makes similar investment decisions?`
- Day 10: capture proof only after a value moment.
- Day 30: request two more high-quality referrals and one decision case.

Founder archetypes:

- `Mega Connector`: public authority engine. Use LinkedIn thought prompts, public posts, comment replies, and DMs to engaged commenters. Expected outcome: awareness.
- `Trusted Advisor`: relationship conversion engine. Use client decision stories, 1:1 prompts, private referrals, and case-study proof. Expected outcome: conversions.
- `Operator Investor`: private referral engine. Use personal decision validation, WhatsApp sharing, and closed peer introductions. Expected outcome: referrals.
- `Content Amplifier`: narrative trust engine. Use video scripts, reels, explainers, and comment-to-DM flows. Expected outcome: content.

Screening questions:

- `How do you usually influence others?` Public posts -> Mega Connector; 1:1 advice -> Trusted Advisor; private sharing -> Operator Investor; content creation -> Content Amplifier.
- `Approx network size?` 5K+ -> Mega Connector; small but deep -> Trusted Advisor; closed high-value -> Operator Investor; medium audience -> Content Amplifier.
- `Preferred communication channel?` LinkedIn -> Mega Connector; calls/meetings -> Trusted Advisor; WhatsApp -> Operator Investor; video/content -> Content Amplifier.

Assignment rule:

- match 2 of 3 signals to assign the primary archetype.
- if mixed, assign a primary and secondary archetype.
- explain to the founder: `We have mapped your strength as [Archetype], so instead of generic steps we will focus on what works best for how you naturally influence people.`

Workbook control surfaces:

- `FOUNDER_ACTIVATION_DASHBOARD` tracks the 0-30 day operating system.
- `FNOMO_OUTREACH_READY` stores the five founder activation emails.
- `FNOMO_EXECUTION_TASKS` stores Day 1, Day 2, Day 4, Day 6, and Day 10 founder activation work.
- `FNOMO_EXECUTION_HISTORY` records each activation-system update.

Notion control surfaces:

- `Founder Circle Activation Dashboard` is the operator read layer for the activation playbook.
- `Contacts` carries the founder activation fields.
- `Active Work` carries one current activation task per founder candidate.

Success thresholds:

- Week 1 activation: 70%.
- Week 1 usage: 50%.
- Day 30 testimonials: 50%.
- Referral participation: 40%.
- Advocates: 20-30%.

## Working Loop

When Kush sends an update, Codex should:

1. read the update
2. map it to one or more rows in `To do`, `FNOMO_MASTER_PIPELINE`, or `FNOMO_EXECUTION_TASKS`
3. update sent dates, stage movement, notes, and blockers
4. identify the next best move
5. if the task is medium/high stakes, run an available review layer when practical
6. if the output is weak or incomplete, reroute the task through a specialist execution pass
7. write the result back into the workbook and repo snapshots
8. include it in `FNOMO_EXECUTION_HISTORY`
9. roll it into the EOD report

## Review Gate

Use the local Fnomo review engine for medium/high tasks when available:

`D:\Antigravity\eigent\Downloads\fnomo\Images and content\llm-council\.venv\Scripts\python.exe D:\Antigravity\eigent\Downloads\fnomo\Images and content\fnomo_engine.py "<task>"`

Notes:

- low tasks can execute directly
- medium/high tasks should be reviewed first when practical
- review output should never override workbook/CRM truth without explicit execution evidence

## Specialist Execution Model

Codex routes work using the Fnomo skills already created:

- `fnomo-execution-spine`
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
