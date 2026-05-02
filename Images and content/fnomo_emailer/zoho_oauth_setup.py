"""
zoho_oauth_setup.py
One-time OAuth setup for a Zoho SELF CLIENT app.
Self Client gives you a code directly in the API Console — no browser redirect needed.

Usage:
  1. Go to https://api-console.zoho.eu/
  2. Open your Self Client app
  3. Click "Generate Code"
  4. Paste these scopes: ZohoMail.messages.CREATE,ZohoMail.accounts.READ
  5. Set duration to "10 minutes"
  6. Click CREATE — copy the code shown
  7. Run: python zoho_oauth_setup.py
  8. Paste the code when prompted
  9. Copy the printed values into your .env file
"""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

ZOHO_CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_TOKEN_URL     = "https://accounts.zoho.eu/oauth/v2/token"
REDIRECT_URI       = "https://www.zoho.com"


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
    data = resp.json()
    print(f"\n[DEBUG] Zoho token response: {data}\n")
    return data


def get_account_id(access_token: str) -> str:
    resp = requests.get(
        "https://mail.zoho.eu/api/accounts",
        headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"[DEBUG] Accounts response: {data}\n")
    accounts = data.get("data", [])
    if not accounts:
        raise RuntimeError("No Zoho Mail accounts found.")
    return str(accounts[0]["accountId"])


if __name__ == "__main__":
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        raise SystemExit(
            "[ERROR] ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET must be set in .env\n"
        )

    print("=" * 60)
    print("  FNOMO — Zoho Self Client OAuth Setup")
    print("=" * 60)
    print("""
BEFORE running this script, do this in your browser:

  1. Go to: https://api-console.zoho.eu/
  2. Click on your Self Client app
  3. Click the tab: "Generate Code"
  4. Paste this into the Scope box:
       ZohoMail.messages.CREATE,ZohoMail.accounts.READ
  5. Set Time Duration to: 10 minutes
  6. Click CREATE
  7. Copy the code shown on screen
""")

    auth_code = input("Paste the code here: ").strip()

    if not auth_code:
        raise SystemExit("[ERROR] No code entered.")

    print("\nExchanging code for tokens...")
    tokens = exchange_code(auth_code)

    if "access_token" not in tokens or "refresh_token" not in tokens:
        raise SystemExit(
            f"[ERROR] Token exchange failed. Full response:\n{tokens}\n\n"
            "Common causes:\n"
            "  - Code already used (codes are single-use — generate a new one)\n"
            "  - Code expired (you have ~10 min — generate a new one)\n"
            "  - Client ID / Secret mismatch"
        )

    access_token  = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    print("Fetching your Zoho Account ID...")
    account_id = get_account_id(access_token)

    print("=" * 60)
    print("  SUCCESS — COPY THESE INTO YOUR .env FILE")
    print("=" * 60)
    print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
    print(f"ZOHO_ACCOUNT_ID={account_id}")
    print("=" * 60)
