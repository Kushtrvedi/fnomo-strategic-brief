"""
zoho_draft_creator.py -- FNOMO Zoho Mail Draft Creator
Creates email drafts in Zoho Mail via REST API. Does NOT send.
Uses mode=draft on the messages endpoint (confirmed working).

Usage:
  python zoho_draft_creator.py --test      # single test draft to yourself
  python zoho_draft_creator.py             # batch from drafts_ready.json
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID",    "")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "")
ACCOUNT_ID    = os.getenv("ZOHO_ACCOUNT_ID",    "")
SENDER_EMAIL  = os.getenv("SENDER_EMAIL",        "kush@mail.fnomo.com")

TOKEN_URL   = "https://accounts.zoho.eu/oauth/v2/token"
DRAFTS_FILE = Path(__file__).parent / "drafts_ready.json"

BLOCKED_PREFIXES = {
    "info", "hr", "admin", "contact", "hello", "support",
    "enquiry", "mail", "office", "team", "careers", "jobs",
    "accounts", "reception", "general",
}


def get_access_token() -> str:
    print("[ZOHO] Refreshing access token...")
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"[ZOHO] Token refresh failed: {data}")
    print("[ZOHO] Token OK")
    return data["access_token"]


def _sanitise(text: str) -> str:
    return (text
        .replace("‘", "'").replace("’", "'")
        .replace("“", '"').replace("”", '"')
        .replace("—", "--").replace("–", "-")
        .replace("…", "...").replace(" ", " ")
        .encode("ascii", "ignore").decode("ascii")
    )


def _is_blocked(email: str) -> bool:
    prefix = email.split("@")[0].lower()
    return prefix in BLOCKED_PREFIXES


def create_draft(token: str, to: str, subject: str, body: str) -> dict:
    """Save a draft via Zoho Mail REST API using mode=draft. Does NOT send."""
    if _is_blocked(to):
        return {"success": False, "message": f"Blocked prefix: {to.split('@')[0]}"}

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "fromAddress": SENDER_EMAIL,
        "toAddress":   _sanitise(to),
        "subject":     _sanitise(subject),
        "content":     _sanitise(body),
        "mailFormat":  "plaintext",
        "mode":        "draft",
    }

    resp = requests.post(
        f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}/messages",
        headers=headers,
        json=payload,
        timeout=20,
    )

    if not resp.ok:
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:300]}"}

    data = resp.json()
    code = data.get("status", {}).get("code")
    if code == 200 and data.get("data", {}).get("mode") == "draft":
        return {"success": True, "message": "Draft saved", "messageId": data["data"].get("messageId")}
    else:
        return {"success": False, "message": json.dumps(data)}


def create_drafts_from_file(drafts_file: Path = DRAFTS_FILE) -> list[dict]:
    if not drafts_file.exists():
        raise FileNotFoundError(f"[ZOHO] {drafts_file} not found. Run fnomo_engine.py first.")

    with open(drafts_file, encoding="utf-8") as f:
        leads = json.load(f)

    print(f"[ZOHO] {len(leads)} draft(s) loaded from {drafts_file}")
    token   = get_access_token()
    results = []

    for i, lead in enumerate(leads, 1):
        name    = lead.get("name", "")
        email   = lead.get("email", "")
        subject = lead.get("subject", "")
        body    = lead.get("body", "")

        print(f"\n  [{i:02}/{len(leads)}] {name} <{email}>")
        print(f"   Subject : {subject}")

        res = create_draft(token, email, subject, body)

        if res["success"]:
            print(f"   Status  : Draft saved (id: {res.get('messageId', '?')})")
        else:
            print(f"   Status  : Failed -- {res['message']}")

        results.append({"name": name, "email": email, "subject": subject, "result": res})

    succeeded = sum(1 for r in results if r["result"]["success"])
    print(f"\n[ZOHO] Done. {succeeded}/{len(leads)} draft(s) saved.")
    print("[ZOHO] Open Zoho Mail -> Drafts to review before sending.\n")
    return results


def test_single_draft(token: str):
    print("\n[TEST] Creating a single test draft to verify Zoho API...")
    res = create_draft(
        token=token,
        to=SENDER_EMAIL,
        subject="[TEST] Zoho Draft API Check",
        body=(
            "This is a test draft created by zoho_draft_creator.py.\n\n"
            "If you can see this in your Zoho Drafts folder, the API is working.\n\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "-- FNOMO Engine\n\n---\n"
            "Fnomo is institutional research infrastructure for educational purposes. "
            "We do not provide investment advice, brokerage services, or performance guarantees. "
            "All decisions remain with the user."
        ),
    )
    if res["success"]:
        print("[TEST] Draft created. Check Zoho Mail -> Drafts.")
    else:
        print(f"[TEST] Failed: {res['message']}")
    return res


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FNOMO Zoho Draft Creator")
    parser.add_argument("--test", action="store_true", help="Create a single test draft")
    args = parser.parse_args()

    print(f"\n{'='*56}")
    print(f"  FNOMO -- Zoho Draft Creator")
    print(f"  Account : {ACCOUNT_ID}")
    print(f"  From    : {SENDER_EMAIL}")
    print(f"  Mode    : {'TEST' if args.test else 'BATCH (drafts_ready.json)'}")
    print(f"{'='*56}\n")

    token = get_access_token()

    if args.test:
        test_single_draft(token)
    else:
        create_drafts_from_file()
