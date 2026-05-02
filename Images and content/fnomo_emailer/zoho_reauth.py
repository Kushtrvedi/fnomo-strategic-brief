"""
zoho_reauth.py -- One-time Zoho OAuth re-authorization
Generates a new refresh token with full required scopes:
  - ZohoMail.messages.CREATE  (create/send messages)
  - ZohoMail.folders.READ     (list folders -> find Drafts folder ID)
  - ZohoMail.messages.READ    (read inbox for reply tracking)
  - ZohoMail.messages.UPDATE  (modify messages / apply labels)

Run once:
  python zoho_reauth.py

Then update .env with the new ZOHO_REFRESH_TOKEN printed at the end.
"""

import os
import webbrowser
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

CLIENT_ID     = os.getenv("ZOHO_CLIENT_ID",     "1000.SP0SD2VJL9TD4KTSOZZUR1Y4DC1BIF")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
ENV_FILE  = Path(__file__).parent / ".env"

SCOPES = ",".join([
    "ZohoMail.messages.CREATE",
    "ZohoMail.messages.READ",
    "ZohoMail.messages.UPDATE",
    "ZohoMail.folders.READ",
    "ZohoMail.accounts.READ",
])


def main():
    print(f"\n{'='*60}")
    print("  FNOMO -- Zoho OAuth Re-Authorization (Self Client)")
    print(f"{'='*60}\n")
    print("This uses Zoho Self Client -- no redirect URI needed.\n")
    print("Steps:")
    print("  1. Go to: https://api-console.zoho.eu/")
    print("  2. Click your client (the one with your CLIENT_ID)")
    print("  3. Click the 'Self Client' tab")
    print("  4. In 'Scope' field paste exactly:")
    print(f"\n     {SCOPES}\n")
    print("  5. Set Time Duration: 10 minutes")
    print("  6. Click 'Create' -- you'll get a grant token (looks like 1000.xxxx...)")
    print("  7. Copy that token and paste it below.\n")
    print("-" * 60)

    webbrowser.open("https://api-console.zoho.eu/")

    code = input("Paste the Self Client grant token here: ").strip()
    if not code:
        print("[ERROR] No token entered. Exiting.")
        return

    print(f"\n[ZOHO] Exchanging grant token for refresh token...")

    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          code,
    }, timeout=15)

    data = resp.json()

    if "refresh_token" not in data:
        print(f"[ERROR] Token exchange failed: {data}")
        return

    new_refresh_token = data["refresh_token"]
    new_access_token  = data.get("access_token", "")

    print(f"\n[ZOHO] SUCCESS")
    print(f"  New Refresh Token: {new_refresh_token}")
    print(f"  Access Token     : {new_access_token[:40]}...")

    # Auto-update .env with new refresh token
    set_key(str(ENV_FILE), "ZOHO_REFRESH_TOKEN", new_refresh_token)
    print(f"\n[ENV] .env updated with new ZOHO_REFRESH_TOKEN")

    # Fetch and permanently save the Drafts folder ID so we never need
    # ZohoMail.folders.READ again after this one-time setup
    print(f"\n[ZOHO] Fetching Drafts folder ID (one-time)...")
    try:
        folders_resp = requests.get(
            f"https://mail.zoho.eu/api/accounts/{os.getenv('ZOHO_ACCOUNT_ID', '8585832000000002002')}/folders",
            headers={"Authorization": f"Zoho-oauthtoken {new_access_token}"},
            timeout=15,
        )
        folders = folders_resp.json().get("data", [])
        drafts_folder = next(
            (f for f in folders
             if "draft" in str(f.get("folderName", "")).lower()
             or "draft" in str(f.get("folderType", "")).lower()),
            None
        )
        if drafts_folder:
            folder_id = str(drafts_folder.get("folderId", ""))
            set_key(str(ENV_FILE), "ZOHO_DRAFTS_FOLDER_ID", folder_id)
            print(f"[ENV] Drafts folder '{drafts_folder.get('folderName')}' ID saved: {folder_id}")
            print("      Future runs will use this ID directly — no folder lookups needed.")
        else:
            print("[WARN] Drafts folder not found in folder list — check your Zoho Mail folders.")
    except Exception as e:
        print(f"[WARN] Could not fetch folders: {e}")

    print(f"\n{'='*60}")
    print("  One-time setup complete.")
    print("  Run zoho_draft_creator.py --test to verify.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
