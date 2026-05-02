"""
batch1_send.py — Batch 1 Direct Send
Generates and sends 5 personalised NEPQ emails to the verified CA firm targets.
Context hooks researched and embedded per firm.

Usage:
  python batch1_send.py --dry-run    # preview emails, no send
  python batch1_send.py              # live send via Zoho
"""

import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

import os
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
ZOHO_CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "")
ZOHO_ACCOUNT_ID    = os.getenv("ZOHO_ACCOUNT_ID", "")
SENDER_EMAIL       = os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com")
SENDER_NAME        = os.getenv("SENDER_NAME", "Kush | FNOMO")

TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
MAIL_URL  = f"https://mail.zoho.eu/api/accounts/{ZOHO_ACCOUNT_ID}/messages"

COMPLIANCE_FOOTER = (
    "\n\n---\n"
    "Fnomo is institutional research infrastructure for educational purposes. "
    "We do not provide investment advice, brokerage services, or performance guarantees. "
    "All decisions remain with the user."
)

# ── Batch 1 Targets with researched context hooks ────────────────────────────
TARGETS = [
    {
        "name":    "Chokshi & Co",
        "email":   "hr@chokshi.com",
        "city":    "Mumbai",
        "hook":    "Multi-disciplinary firm with 100+ professionals (CAs, MBAs, PhDs) — strong in transaction advisory, M&A, and cross-border work including Singapore and Middle East operations",
        "angle":   "cross-border advisory scaling and partner bandwidth constraints",
    },
    {
        "name":    "Batliboi & Co",
        "email":   "info@batliboi.com",
        "city":    "Mumbai",
        "hook":    "Established 1907 — one of India's oldest CA firms, 12 partners, 200+ staff. Deep practice in statutory audit, forensic, FEMA, SEBI/MCA compliance, IFRS, valuations and due diligence",
        "angle":   "NFRA audit quality scrutiny and forensic practice differentiation in a post-UDIN environment",
    },
    {
        "name":    "Lakhani & Co",
        "email":   "info@lakhani.com",
        "city":    "Mumbai",
        "hook":    "Mid-tier Mumbai practice — positioned between boutique and Big 4, a segment facing the sharpest pressure on advisory monetisation and client retention",
        "angle":   "advisory-vs-compliance revenue ceiling that mid-size CA firms rarely address directly",
    },
    {
        "name":    "G D Apte & Co",
        "email":   "hr@gdapte.com",
        "city":    "Mumbai",
        "hook":    "Established 1930, grew from 7 to 13 partners between 2012 and 2020, 200+ staff. Heavy PSU audit portfolio, manufacturing and BFSI clients — a legacy firm navigating NFRA-era documentation standards",
        "angle":   "legacy firm modernisation and PSU audit margin pressure under increased regulatory scrutiny",
    },
    {
        "name":    "Kochar & Co",
        "email":   "info@kochar.com",
        "city":    "Mumbai",
        "hook":    "Founded 1977 by S.A. Kochar — 47-year-old founder-led Dadar practice focused on tax and compliance. Firms at this stage face succession planning and technology transition simultaneously",
        "angle":   "founder succession and technology lag in a long-tenure practice approaching a transition inflection point",
    },
]

SYSTEM_PROMPT = """
You write cold outreach emails to Indian Chartered Accountant (CA) firms using NEPQ technique.
Your audience: CA firm partners managing audit, tax, advisory, compliance, or forensic practices.

NEPQ means you surface a tension the reader already feels but hasn't articulated — then ask one question that makes them reflect. You never pitch. You open a conversation.

STRUCTURE (write ALL four parts fully):
1. Opening observation (2-3 sentences): Specific insight about the challenges a firm at their stage faces — show you understand their world
2. Decision gap (2-3 sentences): A quiet tension or trade-off they likely haven't named — something that feels true when they read it
3. Reflective question (1-2 sentences): One open question that makes them think about their own situation
4. Soft CTA (1-2 sentences): Low-pressure next step — no demo, no call booking, just an opening

HARD RULES:
- Subject: 3-6 words, curiosity-driven NEPQ hook — NO city names, NO generic words like "Business/Growth/Trends/Outlook"
- Body: 120-150 words, all four sections in full
- Plain text only — no bullets, no bold
- Do not mention FNOMO in subject or body
- Return ONLY valid JSON, no markdown

JSON schema:
{
  "subject": "<3-6 word NEPQ subject>",
  "body": "<120-150 word personalised email body>"
}
"""


def build_prompt(target: dict) -> str:
    return f"""
Write a personalised NEPQ cold email for this CA firm.

Firm: {target['name']}
Location: {target['city']}
Researched context: {target['hook']}
NEPQ angle to explore: {target['angle']}

The email should feel written specifically for this firm based on their history and position.
Return ONLY the JSON object.
""".strip()


def generate_email(target: dict) -> dict:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY,
    )
    for attempt in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": build_prompt(target)},
                ],
                temperature=0.5,
                top_p=0.9,
                max_tokens=1024,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data    = json.loads(raw)
            subject = data.get("subject", "").strip()
            body    = data.get("body", "").strip()

            if not subject or not body or len(body.split()) < 40:
                raise ValueError(f"Invalid output on attempt {attempt}")

            # Sanitise — replace smart quotes and em-dashes with ASCII equivalents
            # Zoho's server rejects non-ASCII characters in plaintext emails
            def sanitise(text: str) -> str:
                return (text
                    .replace("’", "'").replace("‘", "'")
                    .replace("“", '"').replace("”", '"')
                    .replace("—", "--").replace("–", "-")
                    .replace("…", "...").replace(" ", " ")
                    .encode("ascii", "ignore").decode("ascii")
                )
            subject  = sanitise(subject)
            body     = sanitise(body)
            footer   = sanitise(COMPLIANCE_FOOTER)

            return {"subject": subject, "body": body, "full_body": body + footer}

        except Exception as e:
            print(f"  [GEN] Attempt {attempt}/3 failed: {e}")
            time.sleep(1)

    raise RuntimeError(f"Failed to generate email for {target['name']} after 3 attempts")


def get_zoho_token() -> str:
    resp = requests.post(TOKEN_URL, params={
        "grant_type":    "refresh_token",
        "client_id":     ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "refresh_token": ZOHO_REFRESH_TOKEN,
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token refresh failed: {data}")
    return data["access_token"]


def send_email(token: str, target: dict, email_data: dict) -> bool:
    payload = {
        "fromAddress": SENDER_EMAIL,
        "toAddress":   target["email"],
        "subject":     email_data["subject"],
        "content":     email_data["full_body"],
        "mailFormat":  "plaintext",
    }
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type":  "application/json",
    }
    resp = requests.post(MAIL_URL, headers=headers, json=payload, timeout=20)

    # Don't crash on HTTP errors — log the full response so we can diagnose
    if not resp.ok:
        print(f"  [ZOHO ERROR] HTTP {resp.status_code}")
        print(f"  [ZOHO ERROR] Response: {resp.text[:500]}")
        return False

    result = resp.json()
    code = result.get("status", {}).get("code")
    if code not in (200, 201):
        print(f"  [ZOHO ERROR] API code {code}: {result}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "LIVE SEND"
    print(f"\n{'='*60}")
    print(f"  FNOMO — Batch 1 CA Outreach  [{mode}]")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    token = None
    if not args.dry_run:
        print("[ZOHO] Refreshing access token...")
        token = get_zoho_token()
        print("[ZOHO] Token OK\n")

    results = []

    for i, target in enumerate(TARGETS, 1):
        print(f"[{i}/5] {target['name']} <{target['email']}>")
        print(f"  Hook: {target['hook'][:80]}...")

        print(f"  Generating NEPQ email via NVIDIA...")
        email_data = generate_email(target)

        print(f"  Subject : {email_data['subject']}")
        print(f"  Body    : {email_data['body'][:120]}...")
        print(f"  Words   : {len(email_data['body'].split())}")

        if args.dry_run:
            print(f"  [DRY RUN] Would send to {target['email']}")
            status = "DRY RUN"
            success = True
        else:
            success = send_email(token, target, email_data)
            status = "SENT ✅" if success else "FAILED ❌"
            print(f"  Zoho    : {status}")
            time.sleep(3)  # space sends

        results.append({
            "firm":    target["name"],
            "email":   target["email"],
            "subject": email_data["subject"],
            "body":    email_data["body"],
            "status":  status,
            "time":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        print()

    print(f"{'='*60}")
    print(f"  BATCH 1 COMPLETE")
    print(f"  Sent: {sum(1 for r in results if r['status'] not in ['FAILED ❌', 'DRY RUN'])}")
    print(f"  Total: {len(results)}")
    print(f"{'='*60}\n")

    log_path = f"batch1_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[LOG] Results saved to {log_path}")

    # Print full email preview
    print("\n── EMAIL PREVIEW ──────────────────────────────────────────")
    for r in results:
        print(f"\nTO: {r['firm']} <{r['email']}>")
        print(f"SUBJECT: {r['subject']}")
        print(f"BODY:\n{r['body']}")
        print("-"*60)


if __name__ == "__main__":
    main()
