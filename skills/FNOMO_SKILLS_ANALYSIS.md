# FNOMO — Complete Skills Suite

## Source Documents Analyzed

| Document | Key Content Extracted |
|----------|----------------------|
| `docs/fnomo_24day_playbook_v2_.html` | 24-Day BD Playbook, daily quotas, partner tiers, follow-up sequences |
| `ppt/The_Intercept_Blueprint.pdf` | Core philosophy, Regret & Hesitation Curve, Intercept Habit Loop, 90-Day Roadmap, Rule-Based Governance, Solo Mode OS, Revenue Flow Network |
| `docs/Fnomo — Go-To-Market Execution Strategy.pdf` | 5-layer stakeholder architecture, 3 V1 decision engines, ICP, competitive analysis, objection handling, 20-target list, deal flow, channel CAC baselines, performance scenarios |
| `Images and content/llm-council/` | Python automation scaffold (main.py) — placeholder for future 500+/day automation |
| `EXCEL/social media influencers...xlsx` | Not accessible (bash unavailable) — would add specific influencer names/handles |
| `ppt/Fnomo — The Decision Layer.pptx` | Not accessible (bash unavailable) — likely visual version of Intercept Blueprint |
| `ppt/Fnomo — The Moment Before Action.pptx` | Not accessible (bash unavailable) — likely product/UX philosophy |

---

## Folder Structure

```
fnomo/
├── docs/
│   ├── Fnomo — Go-To-Market Execution Strategy.pdf  ← 54-page GTM bible
│   ├── FNOMO_24Day_BD_Playbook_v2.docx
│   └── fnomo_24day_playbook_v2_.html                ← Primary playbook source
├── ppt/
│   ├── The_Intercept_Blueprint.pdf                  ← Core philosophy (11 pages)
│   ├── Fnomo — The Decision Layer.pptx
│   ├── Fnomo — The Moment Before Action.pptx
│   └── Fnomo Mind Map.png
├── EXCEL/
│   └── social media influencers - instagram sep-2022.xlsx
├── Images and content/
│   └── llm-council/ (Python automation scaffold)
└── skills/                                          ← ALL SKILLS LIVE HERE
    ├── fnomo-decision-engine/          (UPDATED v2)
    ├── fnomo-outreach-generator/       (UPDATED v2)
    ├── fnomo-reply-classifier/         (v1 — complete)
    ├── fnomo-daily-briefing/           (v1 — complete)
    ├── fnomo-partner-engine/           (UPDATED v2)
    ├── fnomo-community-engine/         (NEW — highest priority channel)
    ├── fnomo-intercept-positioning/    (NEW — core philosophy)
    └── fnomo-revops-tracker/           (NEW — performance governance)
```

---

## Key Operational Facts

| Metric | Value |
|--------|-------|
| AUM Target | ₹100 Cr worth of decisions validated |
| Users Needed | 20,000 |
| Average Investment | ₹50K |
| Max Rev Share | 50% (Strategic tier — one partner only) |
| CAC Kill Threshold | > ₹500 |
| CAC Scale Threshold | < ₹300 |
| CAC Best Case Target | ₹150–₹250 |
| Daily Decision Responses | 10 |
| Daily Influencer DMs | 10 |
| Daily Advisor Convos | 5 |
| Daily Corporate Emails | 20 |
| Weekly Outreach Target | 100+ messages |
| Weekly Conversations | 25–40 |
| Weekly Deals Closed | 1–2 |
| North Star Metric | Pre-Action Usage Rate (target: 40%+ by Month 3) |

---

## Complete Skills Suite — 8 Skills

### 1. `fnomo-decision-engine` (UPDATED v2)
**What it does**: Produces FNOMO's core output for ANY financial decision type.

**Three Engines** (added in v2):
- **Investment Engine**: Score/Risk/Reason/Alternative for stocks, MFs, ETFs, crypto, bonds
- **Purchase Engine**: Affordability Score/Regret Probability/Smarter Alternative for big purchases, EMIs, loans
- **Trade Engine**: Risk Heat (🟢🟡🔴⚫)/Probability Band/Exposure Warning for trades and options

**When to use**: Any financial decision question — community responses, direct user queries, demo calls, partner demos. This IS the product.

**Trigger phrases**: "run a decision check", "score this", "should I buy/sell/hold", "pre-decision check", "validate this trade", "should I take this EMI", any financial instrument question.

---

### 2. `fnomo-outreach-generator` (UPDATED v2)
**What it does**: Generates personalized outreach for all 5 BD segments. Never generic.

**What's new in v2**:
- 20-Target Priority List with close probabilities
- Segment 5: Community Admins (Telegram/Reddit/TradingView)
- Objection Handling Framework (7 objections with reframe scripts)
- Platform-specific scripts for Zerodha/Groww/INDmoney/Smallcase
- Updated rev share communication (10–25% for influencers, not flat ₹200/activation)

**5 Segments**:
- Influencers: Content-referenced DM → 15-min call → 10–25% rev share
- CAs: LinkedIn note → WhatsApp call → 20–30% rev share
- Corporates: 3-wave email strategy (wellness → capital → social proof)
- Platforms: Integration concept pitch → 20-min exploratory call
- Community Admins: Value-first participation → admin DM after credibility built

---

### 3. `fnomo-reply-classifier` (v1 — complete)
**What it does**: Classifies every incoming reply into Interested/Curious/Defensive/Not Relevant and generates the exact response message, ready to send.

**When to use**: Every time a lead replies — before writing any response.

**Trigger phrases**: "they replied", "got a response from", "how should I respond to", "they said [message]".

**Classification → Action**:
| Classification | Response Time | Next Action |
|---------------|---------------|-------------|
| INTERESTED | 30 minutes | Propose specific call time |
| CURIOUS | 2 hours | Mirror back to their decision process |
| DEFENSIVE | 4 hours | Reframe without defending |
| NOT RELEVANT | 24 hours | Graceful close |

---

### 4. `fnomo-daily-briefing` (v1 — complete)
**What it does**: Morning pipeline review that generates Top 5 Priority Actions, follow-up list, today's outreach targets, and a time-blocked schedule.

**When to use**: Every morning, or whenever you need to know "what do I work on right now."

**Trigger phrases**: "daily briefing", "morning briefing", "what's my priority today", "pipeline review", "start my day".

**6 Output Sections**:
1. Top 5 Priority Actions
2. Follow-Up Required Today (with ready-to-send messages)
3. Today's Outreach Targets (named, with angles)
4. Pipeline Health Check (stage counts + alerts)
5. Time-blocked day schedule
6. Today's execution insight (phase-specific guidance)

---

### 5. `fnomo-partner-engine` (UPDATED v2)
**What it does**: Manages the full partner lifecycle — onboarding, earnings, tier upgrades, referral chains, strategic close.

**What's new in v2**:
- Partner Type C: Fintech/Platform Partners (INDmoney, Smallcase) with 5–15% rev share
- Partner Type D: Community Admins with 10–20% rev share
- 40% Flexibility Cap rule (don't default to max rev share)
- Updated influencer rev share: 10–25% (not flat ₹200/activation)
- Full revenue share reference table across all partner types

**Revenue Share by Type**:
| Type | Entry | Performing | Strategic |
|------|-------|------------|-----------|
| CAs | 20–30% | 30–40% | Up to 50% |
| Influencers | 10–25% | 25–35% | Up to 40% |
| Community Admins | 10–20% | 20–30% | Up to 40% |
| Fintech Platforms | 5–15% | 15–25% | Negotiated |

---

### 6. `fnomo-community-engine` (NEW)
**What it does**: FNOMO's primary acquisition channel — community-based decision response and credibility building. Highest close probability (70% Telegram, 65% Reddit, 60% TradingView). CAC ₹80–₹200.

**When to use**: Any community engagement — Telegram response, Reddit comment, TradingView reply, admin partnership approach.

**Trigger phrases**: "respond to this community post", "Telegram group response", "Reddit reply", "community decision response", "approach this admin".

**3-Phase Strategy**:
1. Enter as value creator (Days 1–5) — no branding, just decision checks
2. Establish presence (Days 6–15) — credibility builds, members recognize format
3. Admin partnership (Days 10–20) — formal rev share arrangement

---

### 7. `fnomo-intercept-positioning` (NEW)
**What it does**: The Intercept Blueprint philosophy for any pitch, stakeholder conversation, or competitive comparison.

**When to use**: Explaining FNOMO to anyone, handling "how is this different from X?", partner pitch conversations, investor conversations.

**Trigger phrases**: "how do I explain FNOMO", "pitch FNOMO to", "what is FNOMO", "how is this different from Zerodha/Groww/MoneyControl", "competitive positioning", "investor pitch".

**Key Content**:
- The Core Thesis: "Capture behavior at the point of decision, not attention at the point of discovery"
- The Regret & Hesitation Curve narrative
- 5-Layer Ecosystem Architecture
- The Intercept Habit Loop
- Competitive positioning table (Zerodha/Groww/MoneyControl/Paytm/creators)
- Pitch scripts by stakeholder type
- What FNOMO Is and Is Not
- Positioning safeguards (what never to say)

---

### 8. `fnomo-revops-tracker` (NEW)
**What it does**: Revenue operations — pipeline metrics, CAC tracking, channel performance review, kill/scale decisions.

**When to use**: Weekly performance review, channel audit, kill/scale decisions, quota tracking, 90-day milestone check.

**Trigger phrases**: "weekly metrics", "pipeline health", "CAC review", "channel performance", "should we scale or kill", "weekly review", "how are we tracking".

**Core Framework**:
- Kill/Scale Governance: CAC thresholds, activation rate thresholds, retention thresholds
- Channel CAC Benchmarks: Communities ₹80–₹200, Intent Search ₹150–₹300, Mid-Influencer ₹300–₹700, Paid Social avoid
- Weekly RevOps Format: Full review template with kill/scale/hold decisions
- 90-Day Milestone Tracking: Phase 1/2/3 targets
- Solo Mode Operations: Time allocation by role (Strategy / BD / RevOps / Product)

---

## How to Use These Skills

Reference them in conversation by saying:
- "Run a decision check on [stock/purchase/trade]" → `fnomo-decision-engine`
- "Write outreach to [name/segment]" → `fnomo-outreach-generator`
- "They replied with [message]" → `fnomo-reply-classifier`
- "Daily briefing" → `fnomo-daily-briefing`
- "Send earnings update to [partner]" → `fnomo-partner-engine`
- "Respond to this Telegram post" → `fnomo-community-engine`
- "How do I explain FNOMO to [person]" → `fnomo-intercept-positioning`
- "Weekly review / channel audit" → `fnomo-revops-tracker`

---

## Priority Targets (Act This Week)

1. **Investing Daddy** — YouTube + Instagram (YouTube About email + Instagram DM)
2. **CA Rahul Jain** — LinkedIn → WhatsApp
3. **CA Sanjay Katuria** — LinkedIn → WhatsApp
4. **Top 5 Telegram Trading Group Admins** — Direct DM with value-first approach
5. **Reddit r/IndiaInvestments Mods** — DM to mod team
6. **Blinkit BD team** — LinkedIn outreach
7. **IndiaMART BD team** — LinkedIn outreach

---

## Automation Opportunity (llm-council)

The `llm-council` Python project (`Images and content/llm-council/main.py`) is a scaffold.
This aligns with Day 23 of the playbook — automating manual decision responses from 10/day to 500+/day.

**When ready to build**:
- Connect to NVIDIA NIM API (free tier available — see memory: reference_nvidia_api.md)
- Input: Community post with decision question
- Output: Auto-generated FNOMO decision check in community response format
- Flag: High-engagement responses for manual follow-up and conversion

This removes the 10 responses/day ceiling without removing human judgment from high-value conversations.
