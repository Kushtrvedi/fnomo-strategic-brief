"""
reply_checker.py — FNOMO Inbox Reply Scanner
Polls Zoho Mail for replies to sent emails and appends findings to the daily AAR.

Usage:
  python reply_checker.py              # Check for new replies
  python reply_checker.py --days 7     # Look back N days (default: 7)

Requires ZohoMail.messages.READ scope on the OAuth token.
Add to cron / Task Scheduler alongside fnomo_engine.py.
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

ZOHO_CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "")
ZOHO_ACCOUNT_ID    = os.getenv("ZOHO_ACCOUNT_ID", "")
SENDER_EMAIL       = os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com")

TOKEN_URL    = "https://accounts.zoho.eu/oauth/v2/token"
MAIL_API     = f"https://mail.zoho.eu/api/accounts/{ZOHO_ACCOUNT_ID}"
STATE_FILE   = Path(__file__).parent / "fnomo_state.json"
AAR_FILE     = Path(os.path.expanduser("~")) / "Desktop" / "Fnomo_Daily_AAR.txt"
REPLIES_LOG  = Path(__file__).parent / "replies_log.json"


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_token() -> str:
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


# ── Load sent emails from state ────────────────────────────────────────────────
def load_sent_emails() -> list[dict]:
    if not STATE_FILE.exists():
        return []
    with open(STATE_FILE) as f:
        state = json.load(f)
    return state.get("sent_emails", [])


# ── Load existing replies log ──────────────────────────────────────────────────
def load_replies_log() -> dict:
    """Returns a dict keyed by message_id of already-seen replies."""
    if not REPLIES_LOG.exists():
        return {}
    with open(REPLIES_LOG) as f:
        return json.load(f)


def save_replies_log(log: dict):
    with open(REPLIES_LOG, "w") as f:
        json.dump(log, f, indent=2)


# ── Search inbox for replies ───────────────────────────────────────────────────
def search_inbox(token: str, days_back: int = 7) -> list[dict]:
    """
    Pull recent messages from the inbox folder.
    Zoho Mail API: GET /api/accounts/{id}/messages/view
    """
    since_ts = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
    headers  = {"Authorization": f"Zoho-oauthtoken {token}"}

    url    = f"{MAIL_API}/messages/view"
    params = {
        "folderId": "inbox",
        "limit":    50,
        "start":    0,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if not resp.ok:
            print(f"[REPLY] Inbox fetch failed: HTTP {resp.status_code}")
            print(f"[REPLY] {resp.text[:300]}")
            return []

        data = resp.json()
        messages = data.get("data", [])
        print(f"[REPLY] Found {len(messages)} messages in inbox")
        return messages

    except Exception as e:
        print(f"[REPLY] Error fetching inbox: {e}")
        return []


# ── Match replies against sent targets ────────────────────────────────────────
def match_replies(messages: list[dict], sent_emails: list[dict]) -> list[dict]:
    """
    Check if any inbox message is a reply from a firm we emailed.
    Match on: sender email address in our sent list.
    """
    sent_addrs = {e.get("email", "").lower().strip() for e in sent_emails if e.get("email")}
    replies    = []

    for msg in messages:
        from_addr = msg.get("fromAddress", "").lower().strip()
        subject   = msg.get("subject", "")
        received  = msg.get("receivedTime", "")

        if any(from_addr == addr for addr in sent_addrs):
            # Find matching sent lead
            lead = next((e for e in sent_emails if e.get("email", "").lower() == from_addr), {})
            replies.append({
                "message_id":  msg.get("messageId", ""),
                "from":        msg.get("fromAddress", ""),
                "firm":        lead.get("name", from_addr),
                "subject":     subject,
                "received":    received,
                "snippet":     msg.get("summary", "")[:200],
                "sent_subject": lead.get("subject", ""),
                "sent_date":   lead.get("send_time", ""),
            })

    return replies


# ── Append reply findings to AAR ──────────────────────────────────────────────
def append_to_aar(new_replies: list[dict]):
    if not new_replies:
        return

    lines = [
        "",
        "=" * 60,
        f"  REPLY SCAN — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        f"  New replies detected: {len(new_replies)}",
        "",
    ]

    for i, r in enumerate(new_replies, 1):
        lines += [
            f"  [{i}] FROM   : {r['from']} ({r['firm']})",
            f"       SUBJECT: {r['subject']}",
            f"       SNIPPET: {r['snippet'][:120]}",
            f"       RE: Our email → \"{r['sent_subject']}\"",
            "",
        ]

    lines += ["  ★ ACTION: Follow up within 24 hours", "=" * 60, ""]

    block = "\n".join(lines)

    # Append to AAR
    with open(AAR_FILE, "a", encoding="utf-8") as f:
        f.write(block)

    print(block)


# ── Main ──────────────────────────────────────────────────────────────────────
def main(days_back: int = 7):
    print(f"\n{'='*50}")
    print(f"  FNOMO Reply Checker — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Looking back {days_back} days")
    print(f"{'='*50}\n")

    sent_emails = load_sent_emails()
    if not sent_emails:
        print("[REPLY] No sent emails in state file. Run fnomo_engine.py first.")
        return

    print(f"[REPLY] Checking replies for {len(sent_emails)} sent emails...")
    seen_log = load_replies_log()

    token    = get_token()
    messages = search_inbox(token, days_back=days_back)

    if not messages:
        print("[REPLY] Inbox empty or unreachable.")
        return

    all_replies  = match_replies(messages, sent_emails)
    new_replies  = [r for r in all_replies if r["message_id"] not in seen_log]

    if not new_replies:
        print("[REPLY] No new replies found.")
    else:
        print(f"[REPLY] ★ {len(new_replies)} NEW REPLY/REPLIES DETECTED")
        append_to_aar(new_replies)

        # Update seen log so we don't double-report
        for r in new_replies:
            seen_log[r["message_id"]] = {
                "firm":     r["firm"],
                "received": r["received"],
                "logged":   datetime.now().isoformat(),
            }
        save_replies_log(seen_log)

    print(f"\n[REPLY] Done. AAR: {AAR_FILE}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default 7)")
    args = parser.parse_args()
    main(days_back=args.days)
