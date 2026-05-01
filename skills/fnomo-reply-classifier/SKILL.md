---
name: fnomo-reply-classifier
description: >
  FNOMO's reply intelligence system. Use this skill whenever you receive a response from a lead —
  influencer, CA, corporate contact, or community member — and need to classify it and determine
  the exact next action. Trigger on: "they replied", "got a response from", "how should I respond to",
  "what do I say to", "they said [message]", "reply from [name]", "they're interested/curious/hesitant",
  "follow up on this reply", or when pasting any incoming message from a BD contact. This skill
  classifies the reply, recommends the next step, and generates the response message immediately.
  Never leave a reply without a classified action.
---

# FNOMO Reply Classifier

Every reply moves a lead closer to conversion or surfaces a legitimate stall. Your job is to
classify immediately, recommend the precise next action, and generate the response message.
No reply should sit without a classified action.

## Classification System

Classify every reply into one of four categories:

### 🟢 INTERESTED
**Signals**: Direct positive language, asks about how to get started, mentions their audience/clients,
asks for a call, says "this sounds interesting / relevant / useful", asks about the rev share details.

**Immediate action**: Push hard toward a specific call time. Don't ask "when works for you" —
propose a specific slot. Move fast — warm leads go cold in 24 hours.

**Response template**:
```
[Name] — great to hear. Let's talk this week. 
Are you free [Tuesday at 3pm / Wednesday at 11am]? 15 minutes, no deck — just a live demo 
on a decision from your [niche/client base].
```

**Pipeline update**: Stage → Engaged. Tier: Review and upgrade to A if not already. Book call within 48 hrs.

---

### 🟡 CURIOUS
**Signals**: Asking clarifying questions ("what exactly does it do?", "how does the scoring work?",
"who else is using this?", "what's the rev share structure?"), tentative positive tone but no commitment.

**Immediate action**: Don't answer with features. Mirror their curiosity back to their world.
Ask about their decision process. This deepens the engagement before you explain anything.

**Response template**:
```
Good question — before I explain what FNOMO does, can I ask you something? 
When your [audience/clients] come to you before making a financial move — what's the 
biggest uncertainty they bring to you? 
[Wait for their answer — this tells you exactly how to position the next message]
```

**Pipeline update**: Stage → Engaged. Next action: Continue conversation — get their decision 
process answer before any product explanation.

---

### 🔴 DEFENSIVE / OBJECTION
**Signals**: "I don't think this fits", "I'm not interested in promotions", "I already have 
something for this", "I don't want to recommend tools to my clients", "this sounds like a 
SEBI issue", "I need to think about it."

**Immediate action**: Do NOT defend, do NOT pitch harder. Reframe the gap without pushback.
Acknowledge their frame, then plant one specific thought that shifts the lens.

**Common objections and reframes**:

| Objection | Reframe |
|-----------|---------|
| "I don't promote products" | "This isn't a promotion ask — it's a tool you'd use in your own workflow, not push to your audience." |
| "My clients don't need this" | "Not for all clients — the specific moment is when someone calls you before making a decision you don't feel fully confident advising on. This gives you structured output in those moments." |
| "This sounds like SEBI/advisory issues" | "FNOMO doesn't give advice — it validates decisions. No recommendations, no predictions. Just a structured framework to help users think more clearly before acting." |
| "Not interested in promotions" | "Fair — I'm not asking for a promotion. I'm exploring whether the decision format itself is useful for your workflow. Happy to drop the partnership angle entirely and just show you the tool." |
| "Need to think about it" | "Of course — what's the main thing you'd want to understand better before deciding? I can address that directly rather than leaving it open." |

**Response structure for defensive replies**:
```
Totally understand [their concern restated in 1 line].
[One reframe that shifts the lens without arguing]
[Soft re-ask or open question — not a pitch]
```

**Pipeline update**: Stage stays at Contacted/Engaged. Note the objection. Next action: One more 
message in 4 days with a different angle. If defensive again → mark as Hold/Low priority.

---

### ⚫ NOT RELEVANT
**Signals**: "Wrong person", "we don't do this type of thing", "please don't contact me again",
complete topic mismatch, out-of-office with no future date, hard "no".

**Immediate action**: Do not follow up. Mark as Lost. If a graceful close makes sense, send one
final message to leave the door open (FNOMO will grow — don't burn bridges).

**Optional graceful close**:
```
Understood — thanks for the direct reply. I'll remove you from my outreach list. 
If FNOMO ever makes sense in the future, you know where to find me.
```

**Pipeline update**: Stage → Lost. No further follow-up. Keep contact data for reactivation 
6 months later if FNOMO has new social proof.

---

## Response Speed Rules

| Classification | Response Time |
|---------------|---------------|
| INTERESTED | Within 30 minutes |
| CURIOUS | Within 2 hours |
| DEFENSIVE | Within 4 hours (don't rush — think before replying) |
| NOT RELEVANT | Within 24 hours (graceful close only) |

Priority target replies (Investing Daddy, CA Rahul Jain, CA Sanjay Katuria): within 15 minutes.

## Full Output Format

For every reply you classify, output all three of:

**1. CLASSIFICATION**
```
Classification: [INTERESTED / CURIOUS / DEFENSIVE / NOT RELEVANT]
Reason: [1 line — what in their message led to this classification]
Priority: [High / Medium / Low]
```

**2. RECOMMENDED NEXT ACTION**
```
Next Action: [Specific action — e.g., "Propose call for Tuesday/Wednesday", 
              "Ask about their client decision process", "Reframe SEBI objection"]
Timeline: [When to execute this — e.g., "Within 30 mins", "Within 4 hours"]
```

**3. RESPONSE MESSAGE (ready to send)**
```
[Full message — ready to copy-paste into email/DM/WhatsApp with zero editing needed]
```

**4. PIPELINE UPDATE**
```
Name: [Name]
Stage: [New stage]
Last Contact: [Date]
Next Action: [Next step + date]
Notes: [Classification + key insight from their reply]
```

## Example

**Incoming reply from CA Rahul Jain**:
> "Interesting concept. How does the scoring work exactly? And who else is using this?"

**Output**:

**1. CLASSIFICATION**
```
Classification: CURIOUS
Reason: Asking about mechanism ("how does scoring work") and social validation 
        ("who else is using this") — interested but wants to understand before committing
Priority: High (named priority target)
```

**2. RECOMMENDED NEXT ACTION**
```
Next Action: Mirror his curiosity back to his client decision process before explaining 
             anything. Get his answer — this is the gold for positioning the follow-up.
Timeline: Within 30 minutes (priority target)
```

**3. RESPONSE MESSAGE**
```
Rahul — before I explain the scoring, can I ask you something first?

When a client calls you before making a major financial move — what's the one uncertainty 
they bring that you wish you had a cleaner framework for?

Your answer to that will tell me exactly which part of FNOMO is relevant to your practice.
```

**4. PIPELINE UPDATE**
```
Name: CA Rahul Jain
Stage: Contacted → Engaged
Last Contact: [Today]
Next Action: Wait for his answer → then position the scoring around the gap he describes
Notes: CURIOUS classification — asked about mechanism and social proof. High intent signal.
       Do not explain the product until he answers the decision process question.
```
