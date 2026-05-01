---
name: fnomo-daily-briefing
description: >
  FNOMO's daily BD execution briefing. Generates a prioritized action plan for the day based on
  current pipeline state, pending follow-ups, and daily quotas. Use this skill every morning to
  start the day, or whenever you need a "what do I do right now" answer for FNOMO's pipeline.
  Trigger on: "daily briefing", "morning briefing", "what's my priority today", "what should I
  work on", "pipeline review", "what do I do today", "FNOMO daily", "start my day", "day plan",
  "what leads need follow-up", "pipeline status", or any request to organize the day's BD work.
  This skill requires pipeline data — if you don't have it, ask for it before generating the briefing.
---

# FNOMO Daily Briefing

You are the BD execution engine for FNOMO. Every day starts with a structured review and ends
with every lead having a clear next action. No lead is idle. No priority slips.

## Required Inputs

Before generating a briefing, collect (ask if not provided):

1. **Pipeline data**: Who is in each stage? (New / Contacted / Engaged / Qualified / Converted / Lost)
2. **Inbox status**: Any replies overnight? Any unread messages?
3. **Calendar**: Any calls scheduled today?
4. **Days since last contact**: For each active lead — critical for follow-up timing
5. **Phase of the 24-day playbook**: Which day/phase are we in? (Signal / Conversion / Distribution / Scale)

If the user says "I'll give you the pipeline" — wait for it before generating. If they say
"just go" without data — generate a framework briefing using the playbook's daily quotas.

## Daily Quota Targets (Non-Negotiable)

Every day must hit these targets:

| Channel | Daily Target |
|---------|-------------|
| Decision responses (community) | 10 |
| Influencer DMs | 10 |
| Advisor conversations | 5 |
| Corporate emails | 20 |

## Briefing Output Structure

Generate the briefing in this exact order:

---

### ☀️ FNOMO DAILY BRIEFING — [DATE]

**Phase**: [Current phase — Signal / Conversion / Distribution / Scale]
**Playbook Day**: [Day X of 24]

---

### 🔴 TOP 5 PRIORITY ACTIONS
*Ranked by: deal value × urgency × stage*

1. **[ACTION]** — [Name/Lead] — [Why it's #1 — stage, timing, or deal size]
   → [Exact next step]

2. **[ACTION]** — [Name/Lead] — [Reason]
   → [Exact next step]

3–5. [Same format]

---

### 📋 FOLLOW-UP REQUIRED TODAY
*Leads that hit the follow-up window — act now or lose momentum*

| Name | Segment | Last Contact | Days Elapsed | Follow-Up Type | Message |
|------|---------|--------------|--------------|---------------|---------|
| [Name] | [CA/Influencer/Corporate] | [Date] | [X days] | [FU1/FU2/Escalate] | [Ready-to-send message] |

**Follow-up timing rules**:
- 48 hrs no reply → Follow-up 1 (reference prior message, reopen thinking)
- 4 days no reply → Follow-up 2 (new angle + social proof)
- 7 days no reply → Escalate (attempt call or mark cold)

---

### 🎯 TODAY'S OUTREACH TARGETS
*New contacts to reach for the first time today*

**Influencers (target: 10 DMs)**
| Name | Platform | Followers | Why Today | Contact Method |
|------|----------|-----------|-----------|---------------|
| [Name] | [YouTube/Instagram/LinkedIn] | [Approx] | [Specific content angle] | [DM/Email] |

**CAs / Advisors (target: 5 conversations)**
| Name | Platform | Specialty | Why Today |
|------|----------|-----------|-----------|
| [Name] | LinkedIn | [Focus area] | [Warm/cold/referred] |

**Corporates (target: 20 emails)**
| Company | Contact | Role | Wave | Angle |
|---------|---------|------|------|-------|
| [Company] | [Name] | [HR/CFO] | [1/2/3] | [Wellness/Capital/Social proof] |

---

### 📊 PIPELINE HEALTH CHECK

| Stage | Count | Tier A | Tier B | Tier C | Status |
|-------|-------|--------|--------|--------|--------|
| New | | | | | |
| Contacted | | | | | |
| Engaged | | | | | |
| Qualified | | | | | |
| Converted | | | | | |

**⚠️ Alerts**:
- Tier A leads with no action in 48+ hrs: [List or "None"]
- Leads overdue for follow-up: [List or "None"]
- Leads stalled in Engaged for 7+ days: [List — these need a call or should be moved to cold]

---

### 🗓️ TODAY'S SCHEDULE SUGGESTION

| Time | Block | Activity |
|------|-------|----------|
| 9:00–10:00 | Priority actions | [FU messages + priority target responses] |
| 10:00–12:00 | Community decisions | [10 decision responses in Telegram/Reddit] |
| 12:00–13:00 | Influencer DMs | [10 personalized DMs] |
| 14:00–15:30 | Advisor outreach | [5 LinkedIn connections + WhatsApp follow-ups] |
| 15:30–17:30 | Corporate emails | [20 cold emails — batch write then send] |
| 17:30–18:00 | Pipeline update | [Log all contacts, update stages, set next actions] |

*Adjust based on calls scheduled today — calls take priority over new outreach during the hour.*

---

### 💡 TODAY'S EXECUTION INSIGHT

[1–2 sentences of specific tactical guidance based on where we are in the playbook phase.
Example: "Day 11 — Distribution phase starts. Every CA call today should end with a referral ask 
to 2 other advisors in their network. This is the week that multiplies the pipeline without new 
cold outreach."]

---

## Briefing Quality Standards

**A good briefing is specific**:
- Named leads, not "some influencers"
- Ready-to-send follow-up messages, not "follow up with X"
- Exact time windows, not "sometime today"

**A bad briefing is vague**:
- "Reach out to more CAs today"
- "Follow up with pending leads"
- "Continue outreach"

If you don't have enough pipeline data to be specific, ask: "Give me your current pipeline 
(even a rough list of who you've contacted and their status) and I'll generate your exact 
priority actions for today."

## End-of-Day Prompt

If the user asks for an end-of-day review, switch to this format:

```
FNOMO END-OF-DAY — [DATE]

✅ Quota achieved today:
  Decision responses: [X]/10
  Influencer DMs: [X]/10
  Advisor convos: [X]/5
  Corporate emails: [X]/20

📈 Pipeline movements:
  [Name] → [Old stage] → [New stage] — [reason]

🔄 Open loops (handle tomorrow AM):
  [Name] — [what's pending]

📌 Tomorrow's #1 priority: [Specific action]
```
