"""
zoho_test_send.py
Quick single-email test to verify the Zoho API is working correctly.
Sends ONE real email to a test address so you can confirm delivery
before running the full batch.

Usage:
  python zoho_test_send.py
"""

import requests
import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ── Credentials from .env ──────────────────────────────────────────
CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "")
ACCOUNT_ID    = os.getenv("ZOHO_ACCOUNT_ID", "")
SENDER_EMAIL  = os.getenv("SENDER_EMAIL", "")

# ── IMPORTANT: Change this to your own email to receive the test ───
TEST_RECIPIENT = "info@busybulls.com"

# ── Correct Zoho EU endpoints (no /v1/ in path) ───────────────────
TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
MAIL_URL  = f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}/messages"


def get_access_token() -> str:
    print("[1/3] Refreshing Zoho access token...")
    resp = requests.post(
        TOKEN_URL,
        params={
            "grant_type":    "refresh_token",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"[ERROR] Token refresh failed: {data}")
    print("      ✓ Token OK")
    return data["access_token"]


def send_test_email(access_token: str):
    print(f"[2/3] Sending test email to {TEST_RECIPIENT}...")

    # Correct payload — field names that Zoho EU /messages endpoint expects
    payload = {
        "fromAddress": SENDER_EMAIL,
        "toAddress":   TEST_RECIPIENT,
        "subject":     "Zoho API Test — fnomo_emailer",
        "content":     (
            "This is a test email sent via the Zoho Mail API.\n\n"
            "If you received this, the API connection is working correctly.\n\n"
            "You can now run the full batch."
        ),
        "mailFormat":  "plaintext",
    }

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type":  "application/json",
    }

    resp = requests.post(MAIL_URL, headers=headers, json=payload, timeout=20)

    print(f"      HTTP {resp.status_code}")
    print(f"      Response: {resp.text[:500]}")

    data = resp.json()
    code = data.get("status", {}).get("code")

    if code in (200, 201):
        print("\n✅  SUCCESS — Test email sent! Check your inbox.")
    else:
        print(f"\n❌  FAILED — Zoho returned code {code}")
        print("    Full response:", data)
        print("\n  Common fixes:")
        print("  • If EXTRA_KEY_FOUND_IN_JSON: payload fields are wrong (this script fixes that)")
        print("  • If URL_RULE_NOT_CONFIGURED: you used /sendMail or /v1/ — use /messages instead")
        print("  • If invalid_client: check CLIENT_ID and CLIENT_SECRET in .env")
        print("  • If invalid_code: refresh token expired — re-run zoho_oauth_setup.py")


if __name__ == "__main__":
    print("=" * 55)
    print("  Zoho API Connection Test")
    print("=" * 55)
    print(f"  Endpoint : {MAIL_URL}")
    print(f"  From     : {SENDER_EMAIL}")
    print(f"  To       : {TEST_RECIPIENT}")
    print("=" * 55 + "\n")

    token = get_access_token()
    send_test_email(token)

    print("\n[3/3] Done.")
