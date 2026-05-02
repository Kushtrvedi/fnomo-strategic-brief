"""
email_generator.py — Phase 2
Generates unique NEPQ-style cold emails for each lead.

Supports multiple free LLM providers via LLM_PROVIDER in .env:
  - groq     : Free — Llama 3.3 70B via api.groq.com (recommended, fastest)
  - nvidia   : Free — Llama/Mistral via build.nvidia.com NIM
  - anthropic: Paid — Claude Sonnet (legacy, only if you have the key)

Set mock=True to skip the API entirely and use template emails for testing.
"""

import json
import time
from config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, COMPLIANCE_FOOTER

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    if not LLM_API_KEY:
        raise SystemExit(
            f"\n[CONFIG ERROR] No API key set for provider '{LLM_PROVIDER}'.\n"
            f"  → Set {_key_name()} in your .env file.\n"
            f"  → Or run with --mock-ai to skip AI generation.\n"
            f"\n  Free API keys:\n"
            f"    Groq  : https://console.groq.com  (LLM_PROVIDER=groq)\n"
            f"    NVIDIA: https://build.nvidia.com   (LLM_PROVIDER=nvidia)\n"
        )

    provider = LLM_PROVIDER.lower()

    if provider == "anthropic":
        import anthropic
        _client = anthropic.Anthropic(api_key=LLM_API_KEY)

    elif provider in ("groq", "nvidia"):
        from openai import OpenAI
        base_urls = {
            "groq":   "https://api.groq.com/openai/v1",
            "nvidia": "https://integrate.api.nvidia.com/v1",
        }
        _client = OpenAI(api_key=LLM_API_KEY, base_url=base_urls[provider])

    else:
        raise SystemExit(
            f"\n[CONFIG ERROR] Unknown LLM_PROVIDER='{LLM_PROVIDER}'.\n"
            f"  → Supported values: groq, nvidia, anthropic\n"
        )

    print(f"[LLM] Provider: {LLM_PROVIDER.upper()} | Model: {LLM_MODEL}")
    return _client


def _key_name() -> str:
    mapping = {
        "groq":      "GROQ_API_KEY",
        "nvidia":    "NVIDIA_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    return mapping.get(LLM_PROVIDER.lower(), "LLM_API_KEY")


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You write cold outreach emails to Indian Chartered Accountant (CA) firms using NEPQ technique.
Your audience: CA firm partners/principals managing audit, tax, advisory, compliance, or forensic practices.

NEPQ means you surface a tension the reader already feels but hasn't articulated — then ask a question that makes them reflect. You never pitch. You open a conversation.

CA PAIN POINTS to draw from (pick whichever fits the firm naturally):
- Regulatory overload: GST amendments, MCA filings, SEBI circulars, RBI norms shifting constantly
- Audit quality pressure: NFRA scrutiny, peer reviews, documentation burden increasing
- Client retention: advisory clients comparing value vs Big 4 / boutique alternatives
- Talent and team: senior staff attrition, articled clerk management, succession planning
- Revenue ceiling: billing models stuck on compliance retainers, advisory not monetised
- Technology lag: Excel-based workflows, manual reconciliations, no client portal
- Partner bandwidth: partners buried in execution, no time for business development
- Seasonality trap: Q4 overload, idle capacity in off-season, cash flow gaps

STRUCTURE (write ALL four parts — do not skip or condense any):
1. Opening observation (2-3 sentences): A specific, insightful observation about the challenges a firm at their level faces — show you understand their world without flattering them
2. Decision gap (2-3 sentences): Surface a quiet tension or trade-off they likely haven't named — something that feels true when they read it
3. Reflective question (1-2 sentences): One open, non-rhetorical question that makes them think about their own situation
4. Soft CTA (1-2 sentences): A low-pressure next step — no demo requests, no calls booked, just an opening

HARD RULES:
- Subject line: 3-6 words, NEPQ curiosity hook — NO city names, NO "Mumbai/Delhi/Bangalore", NO generic words like "Business Growth/Trends/Outlook/Insights", NO hype words
- Good subject examples: "The billing ceiling question", "When advisory doesn't convert", "The quiet attrition risk", "Beyond the compliance retainer"
- Body: 120-150 words — write fully, do not truncate
- Plain text only — no bullets, no bold, no formatting
- Use the firm's name naturally once if it fits; never feel generic or templated
- Each email must feel written for THIS firm, not copy-pasted
- Do not mention FNOMO in subject or body
- Return ONLY valid JSON, no markdown fences, no explanation

JSON schema:
{
  "subject": "<3-6 word NEPQ subject>",
  "body": "<120-150 word personalised email body>"
}
"""


def _build_user_prompt(lead: dict, used_subjects: list[str]) -> str:
    name     = lead.get("name", "")
    company  = lead.get("company", "") or name
    industry = lead.get("industry", "")
    city     = lead.get("city", "")

    # Build a rich context block so the model has enough to personalise
    context_lines = [f"Firm name: {company}"]
    if industry and industry.lower() not in ("nan", "none", ""):
        context_lines.append(f"Practice area / industry tag: {industry}")
    if city and city.lower() not in ("nan", "none", ""):
        context_lines.append(f"Location: {city} (do NOT use this in the subject line)")
    context_lines.append(
        "Audience: Partner or principal of an Indian CA firm — qualified CA, likely 10+ years in practice"
    )

    context_str  = "\n".join(f"  {l}" for l in context_lines)
    subjects_str = (
        "\n".join(f"  - {s}" for s in used_subjects[-20:])
        if used_subjects else "  None yet"
    )

    return f"""
Write a personalised NEPQ cold email for this CA firm.

Lead context:
{context_str}

Subjects already used — do NOT repeat, echo, or rhyme with these:
{subjects_str}

Requirements:
- Subject: curiosity-driven, NO city/location references, NOT generic
- Body: exactly 120-150 words, all four NEPQ sections written in full
- Personalise the pain point to fit this firm's likely practice area
- Return ONLY the JSON object, no other text
""".strip()


# ── Mock mode (no API) ────────────────────────────────────────────────────────

_MOCK_SUBJECTS = [
    "Blind spot in your workflow",
    "What most firms overlook",
    "The question nobody asks",
    "One gap worth exploring",
    "A pattern we keep seeing",
    "Something worth reconsidering",
    "Where the risk hides",
    "The decision before the decision",
    "What the data misses",
    "A shift worth noticing",
]


def _generate_mock_email(lead: dict, used_subjects: list[str]) -> dict:
    name     = lead.get("name", "there").split()[0]
    company  = lead.get("company", "your firm")
    industry = lead.get("industry", "your industry")

    subject = next(
        (s for s in _MOCK_SUBJECTS if s not in used_subjects),
        f"A thought for {name}"
    )

    body = (
        f"Hi {name},\n\n"
        f"Most {industry} operators we speak with are managing growth without a clear view of "
        f"where the next friction point will emerge — not because they lack data, but because "
        f"the signals don't surface until it's already costing them.\n\n"
        f"At {company}, I'd be curious: when a process quietly breaks down, how does your team "
        f"typically find out — and how much runway do you usually have to course-correct?\n\n"
        f"Worth a quick look at what that gap might mean for you right now?"
    )

    return {
        "subject":   subject,
        "body":      body,
        "full_body": body + COMPLIANCE_FOOTER,
    }


# ── Live generation ───────────────────────────────────────────────────────────

def _call_api(lead: dict, used_subjects: list[str]) -> str:
    """Returns raw text from whichever provider is configured."""
    client   = _get_client()
    provider = LLM_PROVIDER.lower()
    prompt   = _build_user_prompt(lead, used_subjects)

    if provider == "anthropic":
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    else:
        # Groq and NVIDIA both use the OpenAI-compatible chat endpoint
        kwargs = dict(
            model=LLM_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.5,
            top_p=0.9,
        )
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content.strip()


def generate_email(lead: dict, used_subjects: list[str], retries: int = 3) -> dict | None:
    for attempt in range(1, retries + 1):
        try:
            raw = _call_api(lead, used_subjects)

            # Strip markdown code fences if model wrapped JSON in them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data    = json.loads(raw)
            subject = data.get("subject", "").strip()
            body    = data.get("body", "").strip()

            word_count = len(body.split())
            if not subject or not body:
                raise ValueError("Empty subject or body")
            if word_count < 40:
                raise ValueError(f"Body too short ({word_count} words) — retry")
            if word_count > 300:
                raise ValueError(f"Body too long ({word_count} words)")
            if word_count < 100:
                print(f"  [GEN] Note: body is {word_count} words (target 120-150) — accepting")

            # Enforce subject uniqueness — if duplicate, force a retry
            if subject in used_subjects:
                raise ValueError(f"Duplicate subject '{subject}' — regenerating")

            return {
                "subject":   subject,
                "body":      body,
                "full_body": body + COMPLIANCE_FOOTER,
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"  [GEN] Attempt {attempt}/{retries} for {lead['email']}: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"  [GEN] Attempt {attempt}/{retries} API error: {e}")
            time.sleep(2)

    # Fallback — use a personalised mock rather than skipping entirely
    print(f"  [GEN] AI failed after {retries} tries — using personalised fallback for {lead['email']}")
    return _generate_mock_email(lead, used_subjects)


# ── Batch entry point ─────────────────────────────────────────────────────────

def generate_all_emails(leads: list[dict], mock: bool = False) -> list[dict]:
    results: list[dict]      = []
    used_subjects: list[str] = []
    total = len(leads)

    mode_label = "MOCK (no API call)" if mock else f"{LLM_PROVIDER.upper()} API"
    print(f"\n[GENERATOR] Generating emails for {total} leads  [{mode_label}]...\n")

    for i, lead in enumerate(leads, 1):
        print(f"  [{i:02}/{total}] {lead['name']} <{lead['email']}>")

        email_data = _generate_mock_email(lead, used_subjects) if mock else generate_email(lead, used_subjects)

        if email_data:
            used_subjects.append(email_data["subject"])
            results.append({**lead, **email_data})
            print(f"         Subject: {email_data['subject']}")
        else:
            print(f"         SKIPPED")

        if not mock:
            time.sleep(0.3)

    print(f"\n[GENERATOR] Done — {len(results)}/{total} emails generated\n")
    return results
