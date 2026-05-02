"""
fnomo_engine.py — FNOMO Daily Outreach Engine
Runs the complete daily pipeline: load → score → generate → export.

NO EMAIL SENDING. This engine generates, scores, and exports the top 5
qualifying emails (combined hook + clarity score >= 7) to drafts_ready.json.
You review the drafts file, then send manually or via a separate sender script.

Daily mix: 5 CA Partners + 5 Corporate + 5 Influencer (all export-only)
Output: drafts_ready.json  (top 5, score >= 7 only)
        Fnomo_Daily_AAR.txt (full report on Desktop)

Usage:
  python fnomo_engine.py               # Generate, score, export
  python fnomo_engine.py --day 2       # Force a specific day number in the AAR
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from email_scorer        import score_email, format_score_block
from war_room_updater    import append_results
from lead_loader         import load_leads
from zoho_draft_creator  import create_drafts_from_file

# ── Config ────────────────────────────────────────────────────────────────────
NVIDIA_API_KEY  = os.getenv("NVIDIA_API_KEY", "")
SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com")
SENDER_NAME     = os.getenv("SENDER_NAME", "Kush | FNOMO")
EXCEL_PATH      = os.getenv("EXCEL_PATH", r"D:\Antigravity\eigent\Downloads\fnomo\EXCEL\FNOMO_CA_AGGRESSIVE_SCRAPE_86500.xlsx")
STATE_FILE      = Path(__file__).parent / "fnomo_state.json"
AAR_FILE        = Path(os.path.expanduser("~")) / "Desktop" / "Fnomo_Daily_AAR.txt"
DRAFTS_FILE     = Path(__file__).parent / "drafts_ready.json"

# Minimum combined score (hook_strength + clarity_score) to qualify for Zoho draft
DRAFT_MIN_SCORE = 7

COMPLIANCE_FOOTER = (
    "\n\n---\n"
    "Fnomo is institutional research infrastructure for educational purposes. "
    "We do not provide investment advice, brokerage services, or performance guarantees. "
    "All decisions remain with the user."
)

# ── State management (tracks progress across days) ────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"day": 0, "ca_offset": 0, "total_sent": 0, "sent_emails": []}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

# ── NVIDIA LLM client ─────────────────────────────────────────────────────────
def get_llm_client() -> OpenAI:
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY,
    )

def sanitise(text: str) -> str:
    """Strip non-ASCII characters that cause Zoho 500 errors."""
    return (text
        .replace("‘", "'").replace("’", "'")
        .replace("“", '"').replace("”", '"')
        .replace("—", "--").replace("–", "-")
        .replace("…", "...").replace(" ", " ")
        .encode("ascii", "ignore").decode("ascii")
    )

# ── Email generation prompts ───────────────────────────────────────────────────
CA_SYSTEM = """
You write cold outreach emails to Indian Chartered Accountant (CA) firms using NEPQ technique.
Your audience: CA firm partners managing audit, tax, advisory, compliance, or forensic practices.

NEPQ: Surface a tension the reader already feels but hasn't articulated — then ask one question that makes them reflect. Never pitch. Open a conversation.

STRUCTURE (write ALL four parts fully):
1. Opening observation (2-3 sentences): Specific insight about challenges at their stage
2. Decision gap (2-3 sentences): A quiet tension or trade-off they haven't named
3. Reflective question (1-2 sentences): One open question that makes them think
4. Soft CTA (1-2 sentences): Low-pressure opening — no demo requests

HARD RULES:
- Subject: 3-6 words, NEPQ curiosity hook — NO city names, NO generic "Business/Growth/Trends"
- Body: 120-150 words, all four sections
- Plain text only — no bullets, no bold
- Do not mention FNOMO in subject or body
- Return ONLY valid JSON: {"subject": "...", "body": "..."}
"""

INFLUENCER_SYSTEM = """
You write short, sharp DM-style outreach messages to Indian finance content creators (YouTube, Instagram, Telegram).
Audience: Finance influencers with 10K-500K followers who create content about stocks, mutual funds, or personal finance.

NEPQ: Surface the tension between the creator's role (educating about decisions) and what happens after the audience acts.

FORMAT:
- 3-4 sentences max (this is a DM, not an email)
- Reference ONE specific piece of their content
- Surface the gap: "Your audience hears the content — but who validates their decision before they act?"
- Soft ask: 15-min call, no pitch deck, no sponsorship
- Return ONLY valid JSON: {"subject": "DM", "body": "..."}
"""

CORPORATE_SYSTEM = """
You write cold outreach messages to HR/L&D directors at large Indian corporations.
Audience: Senior HR directors at companies like Tata, Infosys, Reliance — they get hundreds of pitches weekly.

NEPQ: Surface the gap between employee wellness programs (physical, mental) and financial decision anxiety — an unaddressed productivity drain.

FORMAT:
- 4-5 sentences
- Reference ONE specific company initiative (wellness program, leadership pipeline, etc.)
- Frame Fnomo as an institutional validation layer, not financial advice
- Soft ask: 45-minute "Decision X-Ray" pilot session for leadership team
- Return ONLY valid JSON: {"subject": "...", "body": "..."}
"""

# Subjects containing these terms are considered generic and trigger a retry
GENERIC_SUBJECT_TERMS = [
    "audit practice", "compliance complexity", "tax season", "audit workflow",
    "managing audit", "sustainable growth", "business growth", "firm growth",
    "market trends", "industry outlook", "practice efficiency", "audit efficiency",
    "tax challenges", "accounting challenges", "ca practice", "firm outlook",
    "advisory trends", "growth strategy", "regulatory challenges",
    "audit challenges", "tax compliance", "financial advisory",
]


def _is_generic_subject(subject: str) -> bool:
    """Return True if the subject looks like a generic template."""
    s = subject.lower().strip()
    # Reject if it matches any known generic phrase
    if any(term in s for term in GENERIC_SUBJECT_TERMS):
        return True
    # Reject if it's just 1-2 generic nouns with no curiosity/tension
    words = s.split()
    if len(words) <= 3 and not any(c in s for c in ("?", "when", "why", "what", "who", "how")):
        # Very short subject with no curiosity signal is likely generic
        return True
    return False


def generate_email(client: OpenAI, system: str, lead: dict, used_subjects: list) -> dict | None:
    name    = lead.get("name", lead.get("company", ""))
    context = lead.get("hook", lead.get("industry", ""))
    city    = lead.get("city", "")

    prompt = f"""
Write a personalised outreach message for:
  Name/Firm: {name}
  Context: {context}
  Location: {city} (do NOT mention city in subject)
  Used subjects (avoid duplicating): {used_subjects[-10:]}

SUBJECT MUST: use a curiosity gap, contrast, or implicit question — NOT a noun phrase.
BAD subjects: "Audit Complexity", "Tax Season Challenges", "Managing Workflow"
GOOD subjects: "When the partner can't delegate", "What NFRA changed that the manual didn't"

Return ONLY the JSON object.
""".strip()

    for attempt in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.7,   # higher = more creative subjects
                top_p=0.95,
                max_tokens=1024,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data    = json.loads(raw)
            subject = sanitise(data.get("subject", "").strip())
            body    = sanitise(data.get("body", "").strip())

            if not subject or not body or len(body.split()) < 40:
                raise ValueError(f"Output too short on attempt {attempt}")
            if subject in used_subjects:
                raise ValueError("Duplicate subject")
            if _is_generic_subject(subject):
                raise ValueError(f"Generic subject rejected: '{subject}'")

            return {
                "subject":   subject,
                "body":      body,
                "full_body": body + sanitise(COMPLIANCE_FOOTER),
            }
        except Exception as e:
            print(f"    [GEN] Attempt {attempt}/3: {e}")
            time.sleep(2)   # back off between retries
    return None

# ── Drafts pipeline: select → save JSON → push to Zoho ────────────────────────
def push_to_zoho_drafts(results: list[dict]) -> int:
    """
    1. Filter to emails with combined score >= DRAFT_MIN_SCORE.
    2. Sort descending, take top 5.
    3. Save to drafts_ready.json (audit trail).
    4. Push each to Zoho Mail as a draft in the Drafts folder.
    Returns number of drafts successfully created in Zoho.
    """
    qualified = []
    for r in results:
        scores   = r.get("scores", {})
        combined = scores.get("hook_strength", 0) + scores.get("clarity_score", 0)
        if combined >= DRAFT_MIN_SCORE:
            qualified.append({"combined_score": combined, "result": r})

    if not qualified:
        print(f"\n[DRAFTS] No emails met the minimum threshold ({DRAFT_MIN_SCORE}/10 combined)")
        return 0

    qualified.sort(key=lambda x: x["combined_score"], reverse=True)
    top5 = qualified[:5]

    if len(qualified) > 5:
        print(f"[DRAFTS] {len(qualified)} qualified — keeping top 5 by score")

    # Build the payload list (also written to JSON for audit trail)
    leads_to_draft = []
    for item in top5:
        r      = item["result"]
        scores = r.get("scores", {})
        leads_to_draft.append({
            "name":    r.get("name", ""),
            "email":   r.get("email", ""),
            "subject": r.get("subject", ""),
            "body":    r.get("full_body", r.get("body", "")),
            "score":   (
                f"Hook {scores.get('hook_strength', 0)}/5 | "
                f"Clarity {scores.get('clarity_score', 0)}/5 | "
                f"Spam {scores.get('spam_risk', 'N/A')} | "
                f"Combined {item['combined_score']}/10"
            ),
        })

    # Save audit JSON first (zoho_draft_creator reads this file)
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads_to_draft, f, indent=2, ensure_ascii=False)
    print(f"\n[DRAFTS] Saved {len(leads_to_draft)} qualifying draft(s) -> {DRAFTS_FILE}")

    # Push to Zoho Mail Drafts folder
    zoho_results = create_drafts_from_file(DRAFTS_FILE)
    succeeded    = sum(1 for r in zoho_results if r.get("result", {}).get("success"))
    return succeeded


# ── AAR writer ────────────────────────────────────────────────────────────────
def write_aar(day: int, results: list[dict], drafted: int):
    today    = date.today().strftime("%Y-%m-%d")
    scored   = [r for r in results if r.get("scores")]
    errors   = [r for r in results if r.get("gen_status") == "FAILED"]
    top3     = [r["name"] for r in results[:3]]

    lines = [
        "=" * 62,
        f"  FNOMO DAILY AAR — Day {day} — {today}",
        f"  Mode: GENERATE + SCORE + EXPORT (no sending)",
        "=" * 62,
        "",
        f"  Total Generated    : {len(scored)}/15",
        f"  Zoho Drafts Created: {drafted} (score >= {DRAFT_MIN_SCORE}/10, saved in Zoho Drafts folder)",
        f"  Generation Errors  : {len(errors)}",
        f"  Top 3 Targets      : {', '.join(top3)}",
        "",
        f"  Drafts File        : {DRAFTS_FILE}",
        "",
        "── EMAIL DETAILS ────────────────────────────────────────────",
        "",
    ]

    for i, r in enumerate(results, 1):
        scores   = r.get("scores", {})
        combined = scores.get("hook_strength", 0) + scores.get("clarity_score", 0) if scores else 0
        in_draft = combined >= DRAFT_MIN_SCORE
        lines += [
            f"[{i:02}] {r['name']} <{r['email']}>",
            f"  Type    : {r.get('type', 'CA')}",
            f"  Subject : {r.get('subject', 'N/A')}",
            f"  Draft   : {'EXPORTED to Zoho' if in_draft else f'BELOW THRESHOLD ({combined}/10)'}",
            format_score_block(scores) if scores else "  Scores  : Not scored",
            "",
            f"  BODY:",
            "",
        ]
        body = r.get("body", "")
        for line in body.split("\n"):
            lines.append(f"    {line}")
        lines.append("")
        lines.append("-" * 62)
        lines.append("")

    # Social payloads section (Corporate + Influencer — copy-paste ready)
    social = [r for r in results if r.get("type") in ("Corporate", "Influencer")]
    if social:
        lines += [
            "── SOCIAL PAYLOADS (copy-paste to LinkedIn / Telegram) ──────",
            "",
        ]
        for r in social:
            lines += [
                f"▶ {r['name']} ({r.get('type')}) — {r.get('channel', 'LinkedIn')}",
                f"Subject/Thread: {r.get('subject', '')}",
                "",
                r.get("body", ""),
                "",
                "─" * 40,
                "",
            ]

    if errors:
        lines += [
            "── GENERATION ERRORS ────────────────────────────────────────",
            "",
        ]
        for r in errors:
            lines.append(f"  [FAIL] {r['name']} <{r['email']}> -- {r.get('error', 'unknown')}")
        lines.append("")

    lines += [
        "=" * 62,
        "  NEXT STEP: Open Zoho Mail → Drafts folder",
        "  Review each draft, then click Send manually.",
        "=" * 62,
    ]

    report = "\n".join(lines)
    AAR_FILE.write_text(report, encoding="utf-8")
    print(f"\n[AAR] Report saved: {AAR_FILE}")
    return report

# ── Main pipeline ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="FNOMO Daily Outreach Engine — Generate, Score, Export")
    parser.add_argument("--day", type=int, default=None, help="Override day number in AAR")
    args = parser.parse_args()

    state     = load_state()
    day       = args.day or (state["day"] + 1)
    ca_offset = state.get("ca_offset", 0)

    print(f"\n{'*' * 62}")
    print(f"  FNOMO ENGINE — Day {day}")
    print(f"  Mode: GENERATE + SCORE + EXPORT (no sending)")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*' * 62}\n")

    client        = get_llm_client()
    results       = []
    used_subjects = list(state.get("used_subjects", []))

    # ── Load CA leads (5 per day from the scrape file) ────────────────────────
    print("[PHASE 1] Loading CA leads...")
    all_ca_leads = load_leads(path=EXCEL_PATH, batch=ca_offset + 5)
    ca_leads     = all_ca_leads[ca_offset:ca_offset + 5]
    print(f"  Loaded {len(ca_leads)} CA leads (offset {ca_offset})")

    # ── Generate + Score CA emails ────────────────────────────────────────────
    print("\n[PHASE 2] Generating CA emails via NVIDIA...\n")
    for lead in ca_leads:
        print(f"  Generating: {lead['name']} <{lead['email']}>")
        email_data = generate_email(client, CA_SYSTEM, lead, used_subjects)

        if not email_data:
            results.append({
                **lead,
                "type":       "CA",
                "gen_status": "FAILED",
                "error":      "Generation failed after 3 retries",
                "scores":     {},
            })
            continue

        scores = score_email(lead, email_data)
        used_subjects.append(email_data["subject"])
        combined = scores["hook_strength"] + scores["clarity_score"]

        print(f"    Subject  : {email_data['subject']}")
        print(f"    Hook     : {scores['hook_strength']}/5 | Clarity: {scores['clarity_score']}/5 | Combined: {combined}/10 | Spam: {scores['spam_risk']}")
        print(f"    Draft    : {'[OK] QUALIFIES' if combined >= DRAFT_MIN_SCORE else f'[NO] below threshold ({combined}/10)'}")

        results.append({
            **lead,
            **email_data,
            "type":       "CA",
            "focus_area": "CA Partner Pipeline",
            "gen_status": "OK",
            "scores":     scores,
        })
        print()

    # ── Generate corporate + influencer payloads ──────────────────────────────
    social_placeholders = [
        {"name": "Corporate Slot 1", "email": "tbd@corporate.com", "type": "Corporate",
         "channel": "LinkedIn", "hook": "Leadership wellness initiative"},
        {"name": "Corporate Slot 2", "email": "tbd@corporate.com", "type": "Corporate",
         "channel": "LinkedIn", "hook": "Employee financial anxiety program"},
        {"name": "Corporate Slot 3", "email": "tbd@corporate.com", "type": "Corporate",
         "channel": "LinkedIn", "hook": "L&D director outreach"},
        {"name": "Corporate Slot 4", "email": "tbd@corporate.com", "type": "Corporate",
         "channel": "LinkedIn", "hook": "Executive wellness program"},
        {"name": "Corporate Slot 5", "email": "tbd@corporate.com", "type": "Corporate",
         "channel": "LinkedIn", "hook": "Leadership development initiative"},
        {"name": "Influencer Slot 1", "email": "tbd@influencer.com", "type": "Influencer",
         "channel": "Instagram/Telegram", "hook": "Finance community protection"},
        {"name": "Influencer Slot 2", "email": "tbd@influencer.com", "type": "Influencer",
         "channel": "YouTube", "hook": "Audience decision validation"},
        {"name": "Influencer Slot 3", "email": "tbd@influencer.com", "type": "Influencer",
         "channel": "Instagram", "hook": "Community panic-selling prevention"},
        {"name": "Influencer Slot 4", "email": "tbd@influencer.com", "type": "Influencer",
         "channel": "Telegram", "hook": "Finance group engagement"},
        {"name": "Influencer Slot 5", "email": "tbd@influencer.com", "type": "Influencer",
         "channel": "Instagram", "hook": "Creator audience trust"},
    ]

    print("[PHASE 2b] Generating social payloads...\n")
    for lead in social_placeholders:
        system     = CORPORATE_SYSTEM if lead["type"] == "Corporate" else INFLUENCER_SYSTEM
        time.sleep(3)   # avoid 429 rate limits between API calls
        email_data = generate_email(client, system, lead, used_subjects)
        if email_data:
            used_subjects.append(email_data["subject"])
            scores   = score_email(lead, email_data)
            combined = scores["hook_strength"] + scores["clarity_score"]
            results.append({
                **lead, **email_data,
                "gen_status": "OK",
                "scores":     scores,
            })

    # ── Push top 5 qualifying drafts to Zoho Mail ────────────────────────────
    print("\n[PHASE 3] Pushing qualifying drafts to Zoho Mail Drafts folder...")
    drafted = push_to_zoho_drafts(results)

    # ── Update War Room (all generated, not just sent) ────────────────────────
    print("[PHASE 4] Updating War Room...")
    append_results([r for r in results if r.get("gen_status") == "OK"])

    # ── Generate AAR ───────────────────────────────────────────────────────────
    print("[PHASE 5] Writing AAR...")
    write_aar(day, results, drafted)

    # ── Update state ───────────────────────────────────────────────────────────
    state["day"]           = day
    state["ca_offset"]     = ca_offset + len(ca_leads)
    state["used_subjects"] = used_subjects[-100:]
    save_state(state)

    # ── Summary ────────────────────────────────────────────────────────────────
    total  = len(results)
    failed = len([r for r in results if r.get("gen_status") == "FAILED"])

    print(f"\n{'='*62}")
    print(f"  DAY {day} COMPLETE")
    print(f"  Generated : {total - failed}/{total}")
    print(f"  Zoho Drafts Created  : {drafted}")
    print(f"  Location  : Zoho Mail -> Drafts folder")
    print(f"  AAR       : {AAR_FILE}")
    print(f"{'='*62}")
    print(f"\n  NEXT: Open Zoho Mail (mail.zoho.eu) -> Drafts folder\n"
          f"        Review each draft, then click Send manually.\n")


if __name__ == "__main__":
    main()
