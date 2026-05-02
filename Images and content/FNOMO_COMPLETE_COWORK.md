# FNOMO Email Pipeline — Complete Cowork Task
# Every file, every line of code, every command is written below.
# You have zero reasons to guess or hallucinate anything.
# Work through each section in order. Stop only when told to stop.

---

## STEP 0 — GRANT FOLDER ACCESS

Request access to these exact folders before doing anything else:
```
D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\
D:\Antigravity\eigent\Downloads\fnomo\EXCEL\
```

Do not proceed until both folders are accessible.

---

## STEP 1 — WRITE ALL PYTHON FILES

Write each file below exactly as shown. Do not paraphrase. Do not summarise.
Copy the content character-for-character into each file.
If a file already exists, overwrite it with the content below.

---

### FILE 1 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\config.py`

```python
"""
config.py — FNOMO Email System
Loads all credentials from .env file using python-dotenv.
Never hardcode secrets here — keep them in .env (which is git-ignored).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise SystemExit(
            f"\n[CONFIG ERROR] Missing required credential: {key}\n"
            f"  → Add it to your .env file in the fnomo_emailer\\ folder.\n"
            f"  → Run `python zoho_oauth_setup.py` to generate Zoho credentials.\n"
        )
    return val


# ── Zoho OAuth Credentials ────────────────────
ZOHO_CLIENT_ID     = _require("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = _require("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = _require("ZOHO_REFRESH_TOKEN")
ZOHO_ACCOUNT_ID    = _require("ZOHO_ACCOUNT_ID")
SENDER_EMAIL       = os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com")
SENDER_NAME        = os.getenv("SENDER_NAME",  "Kush | FNOMO")

# ── Anthropic API ─────────────────────────────
ANTHROPIC_API_KEY  = _require("ANTHROPIC_API_KEY")

# ── Excel Source ──────────────────────────────
EXCEL_PATH = os.getenv(
    "EXCEL_PATH",
    r"D:\Antigravity\eigent\Downloads\fnomo\EXCEL\FNOMO_CA_AGGRESSIVE_SCRAPE_86500.xlsx"
)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))

# ── Scheduling Rules ──────────────────────────
SCHEDULE_START_HOUR = int(os.getenv("SCHEDULE_START_HOUR", "10"))
SCHEDULE_END_HOUR   = int(os.getenv("SCHEDULE_END_HOUR",   "18"))
MIN_DELAY_MINUTES   = int(os.getenv("MIN_DELAY_MINUTES",    "7"))
MAX_DELAY_MINUTES   = int(os.getenv("MAX_DELAY_MINUTES",   "25"))
MAX_EMAILS_PER_DAY  = int(os.getenv("MAX_EMAILS_PER_DAY",  "25"))

# ── Compliance Footer ─────────────────────────
COMPLIANCE_FOOTER = (
    "\n\n---\n"
    "Fnomo is institutional research infrastructure for educational purposes. "
    "We do not provide investment advice, brokerage services, or performance guarantees. "
    "All decisions remain with the user."
)

# ── Zoho API Endpoints ────────────────────────
ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_MAIL_URL  = "https://mail.zoho.com/api/accounts/{account_id}/messages"
```

---

### FILE 2 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\lead_loader.py`

```python
"""
lead_loader.py — Phase 1
Reads the Excel file and returns the first BATCH_SIZE valid leads
(rows that have both Email and Name populated).
"""

import re
import pandas as pd
from config import EXCEL_PATH, BATCH_SIZE


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(str(email).strip()))


def _is_valid_name(name: str) -> bool:
    return bool(name and str(name).strip() not in ("", "nan", "None"))


def load_leads(path: str = EXCEL_PATH, batch: int = BATCH_SIZE) -> list[dict]:
    """
    Returns a list of dicts with keys:
        name, email, company (optional), industry (optional), city (optional)
    Skips rows missing email or name, deduplicates by email.
    """
    print(f"[LOADER] Reading: {path}")
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except FileNotFoundError:
        raise SystemExit(f"[ERROR] Excel file not found: {path}")

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Find email / name columns
    email_col = next((c for c in df.columns if "email" in c), None)
    name_col  = next(
        (c for c in df.columns if c in ("name", "full_name", "first_name", "contact")), None
    )

    if not email_col:
        raise SystemExit("[ERROR] No email column found in Excel.")
    if not name_col:
        raise SystemExit("[ERROR] No name column found in Excel.")

    # Optional enrichment columns
    company_col  = next((c for c in df.columns if "company" in c or "firm" in c), None)
    industry_col = next((c for c in df.columns if "industry" in c or "sector" in c), None)
    city_col     = next((c for c in df.columns if c in ("city", "location", "region")), None)

    leads = []
    seen_emails: set[str] = set()

    for _, row in df.iterrows():
        email = str(row.get(email_col, "")).strip()
        name  = str(row.get(name_col, "")).strip()

        if not _is_valid_email(email):
            continue
        if not _is_valid_name(name):
            continue
        if email.lower() in seen_emails:
            continue

        seen_emails.add(email.lower())
        leads.append({
            "name":     name.title(),
            "email":    email.lower(),
            "company":  str(row[company_col]).strip()  if company_col  else "",
            "industry": str(row[industry_col]).strip() if industry_col else "",
            "city":     str(row[city_col]).strip()     if city_col     else "",
        })

        if len(leads) >= batch:
            break

    print(f"[LOADER] {len(leads)} valid leads loaded (batch cap: {batch})")
    return leads
```

---

### FILE 3 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\email_generator.py`

```python
"""
email_generator.py — Phase 2
Uses Claude to generate unique NEPQ-style emails for each lead.
Guarantees uniqueness by passing all prior subjects into each subsequent prompt.
"""

import json
import time
import anthropic
from config import ANTHROPIC_API_KEY, COMPLIANCE_FOOTER

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """
You are an expert B2B copywriter specialising in NEPQ (Neuro-Emotional Persuasion Questioning)
cold emails. Your emails NEVER sell directly — they provoke curiosity and invite a conversation.

STRUCTURE (must follow exactly):
1. Context observation   — one sentence that shows you understand their world
2. Decision gap          — surface a tension or blind spot they likely haven't named
3. Thought-provoking Q   — one open question that makes them reflect
4. Soft CTA              — a non-pushy next step (e.g. "Worth a quick look?")

HARD RULES:
- Subject: max 5 words, curiosity-driven, NO hype words (free, guaranteed, best)
- Body: 120-150 words ONLY
- No bullet points, no bold, plain text only
- Each email must be COMPLETELY different from all previous ones in this batch
- Do not mention "FNOMO" in the subject or body (the footer handles branding)
- Return ONLY valid JSON — no markdown, no preamble

JSON schema:
{
  "subject": "<5-word subject>",
  "body": "<120-150 word email body>"
}
"""


def _build_user_prompt(lead: dict, used_subjects: list[str]) -> str:
    context_parts = []
    if lead.get("company"):
        context_parts.append(f"Company: {lead['company']}")
    if lead.get("industry"):
        context_parts.append(f"Industry: {lead['industry']}")
    if lead.get("city"):
        context_parts.append(f"City: {lead['city']}")

    context_str  = " | ".join(context_parts) if context_parts else "No additional context"
    subjects_str = (
        "\n".join(f"  - {s}" for s in used_subjects[-20:])
        if used_subjects else "  None yet"
    )

    return f"""
Generate a cold outreach email for this lead.

Lead details:
  Name:    {lead['name']}
  {context_str}

Subjects already used in this batch (do NOT repeat or echo these):
{subjects_str}

Return ONLY the JSON object described in your instructions.
""".strip()


def generate_email(lead: dict, used_subjects: list[str], retries: int = 3) -> dict | None:
    for attempt in range(1, retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": _build_user_prompt(lead, used_subjects)}
                ],
            )

            raw = response.content[0].text.strip()

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
            if word_count < 100 or word_count > 180:
                raise ValueError(f"Body word count out of range: {word_count}")

            return {
                "subject":   subject,
                "body":      body,
                "full_body": body + COMPLIANCE_FOOTER,
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"  [GEN] Attempt {attempt}/{retries} failed for {lead['email']}: {e}")
            time.sleep(1)
        except anthropic.APIError as e:
            print(f"  [GEN] API error on attempt {attempt}: {e}")
            time.sleep(2)

    print(f"  [GEN] Skipping {lead['email']} — could not generate valid email")
    return None


def generate_all_emails(leads: list[dict]) -> list[dict]:
    results: list[dict]       = []
    used_subjects: list[str]  = []
    total = len(leads)

    print(f"\n[GENERATOR] Generating emails for {total} leads...\n")

    for i, lead in enumerate(leads, 1):
        print(f"  [{i:02}/{total}] Generating for: {lead['name']} <{lead['email']}>")
        email_data = generate_email(lead, used_subjects)

        if email_data:
            used_subjects.append(email_data["subject"])
            results.append({**lead, **email_data})
            print(f"         Subject: {email_data['subject']}")
        else:
            print(f"         SKIPPED")

        time.sleep(0.5)

    print(f"\n[GENERATOR] Done — {len(results)}/{total} emails generated\n")
    return results
```

---

### FILE 4 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\scheduler.py`

```python
"""
scheduler.py — Phase 4
Generates randomised, human-like send timestamps within the allowed window.
"""

import random
from datetime import datetime, timedelta
from config import (
    SCHEDULE_START_HOUR,
    SCHEDULE_END_HOUR,
    MIN_DELAY_MINUTES,
    MAX_DELAY_MINUTES,
    MAX_EMAILS_PER_DAY,
)


def _next_working_day_start(from_dt: datetime) -> datetime:
    """Return 10 AM on the next calendar day."""
    return (from_dt + timedelta(days=1)).replace(
        hour=SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0
    )


def build_schedule(n_emails: int, start: datetime | None = None) -> list[datetime]:
    """
    Returns a list of n_emails datetime objects representing send times.
    Automatically spills into the next working day if the window fills up.
    """
    if start is None:
        now = datetime.now()
        if now.hour >= SCHEDULE_END_HOUR:
            start = _next_working_day_start(now)
        elif now.hour < SCHEDULE_START_HOUR:
            start = now.replace(hour=SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0)
        else:
            delay = random.randint(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)
            start = now + timedelta(minutes=delay)

    schedule: list[datetime] = []
    current   = start
    day_count = 0

    for _ in range(n_emails):
        window_end = current.replace(
            hour=SCHEDULE_END_HOUR, minute=0, second=0, microsecond=0
        )

        if current >= window_end or day_count >= MAX_EMAILS_PER_DAY:
            current   = _next_working_day_start(current)
            day_count = 0

        schedule.append(current)
        day_count += 1

        delay   = random.randint(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)
        current = current + timedelta(minutes=delay)

    return schedule


def format_schedule(schedule: list[datetime]) -> str:
    """Pretty-print the schedule for logging."""
    lines     = []
    prev_date = None
    for i, dt in enumerate(schedule, 1):
        if dt.date() != prev_date:
            lines.append(f"\n  {dt.strftime('%A, %B %d %Y')}")
            prev_date = dt.date()
        lines.append(f"     [{i:02}] {dt.strftime('%I:%M %p')}")
    return "\n".join(lines)
```

---

### FILE 5 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\zoho_sender.py`

```python
"""
zoho_sender.py — Phase 3 + 5
Handles Zoho OAuth token refresh and email scheduling via the Zoho Mail API.
Includes per-email validation before scheduling.
"""

import json
import time
import requests
from datetime import datetime
from config import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    ZOHO_ACCOUNT_ID,
    SENDER_EMAIL,
    ZOHO_TOKEN_URL,
    ZOHO_MAIL_URL,
)


class ZohoTokenManager:
    """Refreshes the access token automatically when it expires."""

    def __init__(self):
        self._access_token: str | None = None
        self._expires_at: float        = 0.0

    def get_token(self) -> str:
        if time.time() < self._expires_at - 60:
            return self._access_token

        print("[ZOHO] Refreshing access token...")
        resp = requests.post(
            ZOHO_TOKEN_URL,
            params={
                "grant_type":    "refresh_token",
                "client_id":     ZOHO_CLIENT_ID,
                "client_secret": ZOHO_CLIENT_SECRET,
                "refresh_token": ZOHO_REFRESH_TOKEN,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"[ZOHO] Token refresh failed: {data}")

        self._access_token = data["access_token"]
        self._expires_at   = time.time() + int(data.get("expires_in", 3600))
        print("[ZOHO] Token refreshed")
        return self._access_token


_token_mgr = ZohoTokenManager()


def validate_payload(lead: dict, send_time: datetime) -> list[str]:
    errors = []
    if not lead.get("email"):
        errors.append("Missing email")
    if not lead.get("subject"):
        errors.append("Missing subject")
    if not lead.get("full_body"):
        errors.append("Missing body")
    elif "All decisions remain with the user" not in lead["full_body"]:
        errors.append("Compliance footer missing from body")
    if send_time is None:
        errors.append("Missing send time")
    return errors


def schedule_email(lead: dict, send_time: datetime, dry_run: bool = False) -> dict:
    result = {
        "lead_email": lead.get("email", "unknown"),
        "lead_name":  lead.get("name", ""),
        "subject":    lead.get("subject", ""),
        "send_time":  send_time.strftime("%Y-%m-%d %H:%M"),
        "success":    False,
        "message":    "",
    }

    errors = validate_payload(lead, send_time)
    if errors:
        result["message"] = f"SKIPPED — Validation failed: {'; '.join(errors)}"
        print(f"  [VALIDATE] {result['lead_email']}: {result['message']}")
        return result

    if dry_run:
        result["success"] = True
        result["message"] = "DRY RUN — not sent"
        print(f"  [DRY RUN] Would schedule: {lead['email']} at {result['send_time']}")
        return result

    send_epoch_ms = int(send_time.timestamp() * 1000)

    payload = {
        "fromAddress":  SENDER_EMAIL,
        "toAddress":    lead["email"],
        "subject":      lead["subject"],
        "content":      lead["full_body"],
        "mailFormat":   "plaintext",
        "scheduleTime": send_epoch_ms,
    }

    headers = {
        "Authorization": f"Zoho-oauthtoken {_token_mgr.get_token()}",
        "Content-Type":  "application/json",
    }

    url = ZOHO_MAIL_URL.format(account_id=ZOHO_ACCOUNT_ID)

    try:
        resp      = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        resp_data = resp.json()

        if resp_data.get("status", {}).get("code") in (200, 201):
            result["success"] = True
            result["message"] = "Scheduled"
            print(f"  [ZOHO] Scheduled: {lead['email']} at {result['send_time']}")
        else:
            result["message"] = f"API returned: {json.dumps(resp_data)}"
            print(f"  [ZOHO] Failed: {lead['email']}: {result['message']}")

    except requests.RequestException as e:
        result["message"] = f"Request error: {e}"
        print(f"  [ZOHO] Error: {lead['email']}: {result['message']}")

    return result


def schedule_batch(
    leads_with_emails: list[dict],
    schedule: list[datetime],
    dry_run: bool = False,
) -> list[dict]:
    results = []
    print(f"\n[SENDER] Scheduling {len(leads_with_emails)} emails...\n")

    for i, (lead, send_time) in enumerate(zip(leads_with_emails, schedule), 1):
        print(f"  [{i:02}/{len(leads_with_emails)}] {lead['name']} <{lead['email']}>")
        res = schedule_email(lead, send_time, dry_run=dry_run)
        results.append(res)
        time.sleep(0.3)

    return results
```

---

### FILE 6 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\zoho_oauth_setup.py`

```python
"""
zoho_oauth_setup.py
One-time OAuth setup to obtain your Zoho refresh token.
Run ONCE. Paste output values into your .env file. Never run again.

Usage:
  1. Fill ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET in .env
  2. Run: python zoho_oauth_setup.py
  3. A browser opens — grant access — paste the redirect URL back here
  4. Copy the printed ZOHO_REFRESH_TOKEN and ZOHO_ACCOUNT_ID into .env
"""

import urllib.parse
import webbrowser
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

ZOHO_CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_TOKEN_URL     = "https://accounts.zoho.com/oauth/v2/token"
REDIRECT_URI       = "https://www.zoho.com"
SCOPES             = "ZohoMail.messages.CREATE,ZohoMail.accounts.READ"


def get_auth_url() -> str:
    params = {
        "response_type": "code",
        "client_id":     ZOHO_CLIENT_ID,
        "scope":         SCOPES,
        "redirect_uri":  REDIRECT_URI,
        "access_type":   "offline",
    }
    return "https://accounts.zoho.com/oauth/v2/auth?" + urllib.parse.urlencode(params)


def exchange_code(auth_code: str) -> dict:
    resp = requests.post(
        ZOHO_TOKEN_URL,
        params={
            "grant_type":    "authorization_code",
            "client_id":     ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "redirect_uri":  REDIRECT_URI,
            "code":          auth_code,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_account_id(access_token: str) -> str:
    resp = requests.get(
        "https://mail.zoho.com/api/accounts",
        headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    accounts = resp.json().get("data", [])
    if not accounts:
        raise RuntimeError("No Zoho Mail accounts found.")
    return str(accounts[0]["accountId"])


if __name__ == "__main__":
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        raise SystemExit(
            "[ERROR] ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET must be set in .env before running this script.\n"
            "Get them from: https://api-console.zoho.com/ → Self Client"
        )

    print("=" * 60)
    print("  FNOMO — Zoho OAuth Setup")
    print("=" * 60)

    auth_url = get_auth_url()
    print(f"\nStep 1: Opening browser for authorisation...")
    print(f"        {auth_url}\n")
    webbrowser.open(auth_url)

    redirect_url = input("Step 2: After granting access, paste the full redirect URL here:\n> ").strip()
    parsed       = urllib.parse.urlparse(redirect_url)
    auth_code    = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]

    if not auth_code:
        raise SystemExit("[ERROR] Could not extract auth code from URL.")

    print("\nStep 3: Exchanging code for tokens...")
    tokens = exchange_code(auth_code)

    if "refresh_token" not in tokens:
        raise SystemExit(f"[ERROR] Token exchange failed: {tokens}")

    access_token  = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    print("\nStep 4: Fetching your Zoho Account ID...")
    account_id = get_account_id(access_token)

    print("\n" + "=" * 60)
    print("  COPY THESE INTO YOUR .env FILE")
    print("=" * 60)
    print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
    print(f"ZOHO_ACCOUNT_ID={account_id}")
    print("=" * 60)
```

---

### FILE 7 OF 7 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\main.py`

```python
"""
main.py — FNOMO Email Execution System
Orchestrates all phases end-to-end.

Usage:
  python main.py              # live mode — schedules real emails
  python main.py --dry-run    # simulate without hitting Zoho API
"""

import sys
import json
import argparse
from datetime import datetime

from lead_loader     import load_leads
from email_generator import generate_all_emails
from scheduler       import build_schedule, format_schedule
from zoho_sender     import schedule_batch, _token_mgr


SEPARATOR = "=" * 62


def print_header(phase: str):
    print(f"\n{SEPARATOR}")
    print(f"  {phase}")
    print(SEPARATOR)


def phase0_connection_check() -> bool:
    print_header("PHASE 0 — Zoho Connection Check")
    try:
        token = _token_mgr.get_token()
        if token:
            print("[OK] Zoho access token obtained")
            return True
    except Exception as e:
        print(f"[FAIL] Cannot get Zoho token: {e}")
        print("\n  Action required:")
        print("  1. Open .env and confirm ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET are filled in")
        print("  2. Run: python zoho_oauth_setup.py")
        print("  3. Paste ZOHO_REFRESH_TOKEN and ZOHO_ACCOUNT_ID into .env")
        print("  4. Re-run: python main.py")
    return False


def phase6_report(results: list[dict], schedule: list[datetime], skipped_leads: list[dict]):
    print_header("PHASE 5 — Output Report")

    scheduled = [r for r in results if r.get("success")]
    failed    = [r for r in results if not r.get("success")]
    total     = len(scheduled) + len(failed) + len(skipped_leads)

    status = (
        "Completed" if not failed and not skipped_leads
        else "Partial" if scheduled
        else "Failed"
    )

    print(f"\n  STATUS:  {status}")
    print(f"\n  OUTPUT:")
    print(f"    Total leads loaded :  {total}")
    print(f"    Emails generated   :  {len(scheduled) + len(failed)}")
    print(f"    Emails scheduled   :  {len(scheduled)}")

    if scheduled:
        days = sorted(set(r["send_time"][:10] for r in scheduled))
        for d in days:
            day_emails = [r for r in scheduled if r["send_time"][:10] == d]
            print(f"      {d}  ->  {len(day_emails)} emails")

    print(f"\n  ISSUES:")
    if skipped_leads:
        print(f"    Generation failures ({len(skipped_leads)}):")
        for lead in skipped_leads:
            print(f"      - {lead.get('name','?')} <{lead.get('email','?')}>")
    if failed:
        print(f"    Scheduling failures ({len(failed)}):")
        for r in failed:
            print(f"      - {r['lead_email']}: {r['message']}")
    if not skipped_leads and not failed:
        print("    None")

    print(f"\n  NEXT STEP:")
    if scheduled:
        last_slot = max(r["send_time"] for r in scheduled)
        print(f"    Last scheduled slot: {last_slot}")
        print(f"    Run again for the next batch.")
    else:
        print("    No emails were scheduled. Check errors above.")

    print(f"\n{SEPARATOR}\n")

    log = {
        "run_at":              datetime.now().isoformat(),
        "status":              status,
        "scheduled":           scheduled,
        "failed":              failed,
        "skipped_generation":  [{"name": l.get("name"), "email": l.get("email")} for l in skipped_leads],
    }
    log_path = f"fnomo_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"  [LOG] Run log saved to: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="FNOMO Email Execution System")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate and schedule without calling Zoho API")
    args = parser.parse_args()

    print(f"\n{'*' * 62}")
    print(f"  FNOMO EMAIL EXECUTION SYSTEM")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*' * 62}")

    if not args.dry_run:
        ok = phase0_connection_check()
        if not ok:
            sys.exit(1)
    else:
        print("\n[DRY RUN] Skipping Phase 0 connection check.")

    print_header("PHASE 1 — Loading Leads")
    leads = load_leads()

    print_header("PHASE 2 — Generating NEPQ Emails")
    generated = generate_all_emails(leads)

    generated_emails = {l["email"] for l in generated}
    skipped_leads    = [l for l in leads if l["email"] not in generated_emails]

    print_header("PHASE 3+4 — Building Schedule")
    schedule = build_schedule(len(generated))
    print(f"\n  {len(schedule)} slots assigned:")
    print(format_schedule(schedule))

    print_header("PHASE 5 — Validation + Scheduling via Zoho")
    results = schedule_batch(generated, schedule, dry_run=args.dry_run)

    phase6_report(results, schedule, skipped_leads)


if __name__ == "__main__":
    main()
```

---

### FILE 8 OF 8 — Write this to: `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\requirements.txt`

```
anthropic>=0.25.0
pandas>=2.0.0
openpyxl>=3.1.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## STEP 2 — CREATE THE .env FILE

Check if `D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer\.env` exists.

**If it does NOT exist**, create it with this exact content:

```
ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
ZOHO_ACCOUNT_ID=
ANTHROPIC_API_KEY=
SENDER_EMAIL=kush@mail.fnomo.com
SENDER_NAME=Kush | FNOMO
```

Then stop and tell the user exactly this:

"All 8 Python files have been written. I also created your `.env` file in the fnomo_emailer folder.

Before I can continue, you need to fill in 5 values in that `.env` file:

**ZOHO_CLIENT_ID** and **ZOHO_CLIENT_SECRET**:
→ Go to https://api-console.zoho.com/
→ Click Add Client → Self Client
→ Copy the Client ID and Secret into .env

**ZOHO_REFRESH_TOKEN** and **ZOHO_ACCOUNT_ID**:
→ After filling in CLIENT_ID and CLIENT_SECRET in .env, open a terminal in the fnomo_emailer folder
→ Run: `python zoho_oauth_setup.py`
→ It opens a browser, you click Allow, paste the redirect URL back, and it prints your REFRESH_TOKEN and ACCOUNT_ID
→ Paste both into .env

**ANTHROPIC_API_KEY**:
→ Go to https://console.anthropic.com/
→ API Keys → Create Key
→ Paste it into .env

Once all 5 values are filled in, tell me and I will install dependencies and run the pipeline."

Then wait. Do not proceed until the user tells you .env is filled in.

**If .env already exists**, open it and read the values. Check each of the 5 required keys:
- ZOHO_CLIENT_ID
- ZOHO_CLIENT_SECRET
- ZOHO_REFRESH_TOKEN
- ZOHO_ACCOUNT_ID
- ANTHROPIC_API_KEY

If any are empty → tell the user which specific ones are missing and wait.
If all 5 have values → report "Credentials confirmed. Proceeding." and go to Step 3.

---

## STEP 3 — INSTALL DEPENDENCIES

Open a terminal. Navigate to the fnomo_emailer folder:
```
cd D:\Antigravity\eigent\Downloads\fnomo\fnomo_emailer
```

Run:
```
pip install -r requirements.txt
```

Wait for it to complete. If it errors, report the exact error message.
If it succeeds, report: "Dependencies installed. Proceeding to pipeline."

---

## STEP 4 — DRY RUN FIRST

Run:
```
python main.py --dry-run
```

This runs the full pipeline safely — no emails are sent. Watch the output.

Expected output sequence:
```
FNOMO EMAIL EXECUTION SYSTEM
Mode: DRY RUN
...
PHASE 1 — Loading Leads
[LOADER] Reading: D:\...\FNOMO_CA_AGGRESSIVE_SCRAPE_86500.xlsx
[LOADER] N valid leads loaded (batch cap: 50)
...
PHASE 2 — Generating NEPQ Emails
[01/N] Generating for: Name <email>
       Subject: <generated subject>
...
PHASE 3+4 — Building Schedule
N slots assigned:
  Monday, April 28 2025
     [01] 10:07 AM
     [02] 10:24 AM
...
PHASE 5 — Validation + Scheduling via Zoho
[DRY RUN] Would schedule: email at YYYY-MM-DD HH:MM
...
PHASE 5 — Output Report
STATUS: Completed
```

Report what you see. If there are any errors, paste them exactly and stop.
If dry run completes successfully, show the full schedule to the user and ask:

"Dry run complete. Here is the full schedule:
[paste schedule]

Ready to send live? Type YES to execute, or NO to cancel."

Wait for explicit YES.

---

## STEP 5 — LIVE RUN (only after user types YES)

Run:
```
python main.py
```

Monitor terminal output. Report each line as it appears.
When complete, read the newest `fnomo_run_*.json` file in the fnomo_emailer folder.

Print this final report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FNOMO RUN REPORT — [date from log]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATUS:  [value from log: Completed / Partial / Failed]

OUTPUT:
  Leads loaded        :  [total from log]
  Emails generated    :  [count from log]
  Emails scheduled    :  [count of successful from log]
  [for each date in log] → [N] emails ([first slot] – [last slot])

ISSUES:
  Generation skipped  :  [count] — [names or "None"]
  Scheduling failed   :  [count] — [emails or "None"]

NEXT STEP:
  ➜  Paste this file into Cowork again to run the next batch
  ➜  Next available slot: [last send_time from log, +1 interval]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## IF ANYTHING GOES WRONG

Do not guess. Do not improvise. Do not try to fix errors silently.
Paste the exact error message, state which step it occurred in, and wait for instructions.
