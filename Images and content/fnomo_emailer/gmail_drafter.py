"""
gmail_drafter.py — FNOMO Gmail Draft Creator
Uses Gmail API (OAuth 2.0) to create email drafts and label them.

NO emails are sent. NO browser automation.
Drafts land in Gmail under the label: Fnomo_Outreach_Draft

SETUP (one-time):
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable Gmail API
  3. OAuth consent screen → Add scope: gmail.compose + gmail.labels
  4. Credentials → Create OAuth 2.0 Client (Desktop app)
  5. Download JSON → save as fnomo_emailer/credentials.json
  6. First run: browser opens for one-time authorisation → gmail_token.json is saved

REQUIRED PACKAGES:
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import base64
import json
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Auth config ───────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",   # create/modify drafts
    "https://www.googleapis.com/auth/gmail.labels",    # create/list labels
    "https://www.googleapis.com/auth/gmail.modify",    # apply labels to messages
]

BASE_DIR       = Path(__file__).parent
CREDS_FILE     = BASE_DIR / "credentials.json"
TOKEN_FILE     = BASE_DIR / "gmail_token.json"
DRAFT_LABEL    = "Fnomo_Outreach_Draft"
SENDER_EMAIL   = os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com")


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_gmail_service():
    """
    Authenticate and return a Gmail API service object.
    On first run, opens a browser for OAuth authorisation.
    Subsequent runs use the saved token (auto-refreshed).
    """
    if not CREDS_FILE.exists():
        raise FileNotFoundError(
            f"\n[GMAIL] credentials.json not found at: {CREDS_FILE}\n"
            "  1. Go to https://console.cloud.google.com/\n"
            "  2. Enable Gmail API → Create OAuth 2.0 Desktop credentials\n"
            "  3. Download JSON → save as fnomo_emailer/credentials.json\n"
            "  4. Re-run the engine.\n"
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[GMAIL] Refreshing access token...")
            creds.refresh(Request())
        else:
            print("[GMAIL] First-time auth — browser will open for Google sign-in...")
            flow  = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("[GMAIL] Token saved.")

    return build("gmail", "v1", credentials=creds)


# ── Label management ──────────────────────────────────────────────────────────
def get_or_create_label(service, label_name: str) -> str:
    """
    Returns the label ID for label_name.
    Creates the label if it doesn't exist.
    """
    try:
        result = service.users().labels().list(userId="me").execute()
        labels = result.get("labels", [])

        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]

        # Label doesn't exist — create it
        body = {
            "name":                  label_name,
            "labelListVisibility":   "labelShow",
            "messageListVisibility": "show",
            "color": {
                "backgroundColor": "#16a766",   # green
                "textColor":       "#ffffff",
            },
        }
        new_label = service.users().labels().create(userId="me", body=body).execute()
        print(f"[GMAIL] Created label: '{label_name}' (id: {new_label['id']})")
        return new_label["id"]

    except HttpError as e:
        print(f"[GMAIL] Label error: {e}")
        return ""


# ── Draft creation ────────────────────────────────────────────────────────────
def _build_raw_message(to: str, subject: str, body: str) -> str:
    """Encode a plain-text email as base64url for the Gmail API."""
    msg              = MIMEText(body, "plain", "utf-8")
    msg["to"]        = to
    msg["from"]      = SENDER_EMAIL
    msg["subject"]   = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")


def create_draft(service, lead: dict, label_id: str) -> dict:
    """
    Create one Gmail draft for a lead.
    Returns a result dict with success flag and draft_id.
    """
    result = {
        "name":     lead.get("name", ""),
        "email":    lead.get("email", ""),
        "subject":  lead.get("subject", ""),
        "success":  False,
        "draft_id": "",
        "message":  "",
    }

    try:
        raw = _build_raw_message(
            to=lead["email"],
            subject=lead["subject"],
            body=lead["body"],
        )

        # Step 1: Create the draft
        draft_body = {"message": {"raw": raw}}
        draft      = service.users().drafts().create(userId="me", body=draft_body).execute()
        draft_id   = draft["id"]
        msg_id     = draft["message"]["id"]

        # Step 2: Apply the Fnomo_Outreach_Draft label to the underlying message
        if label_id:
            service.users().messages().modify(
                userId="me",
                id=msg_id,
                body={"addLabelIds": [label_id]},
            ).execute()

        result["success"]  = True
        result["draft_id"] = draft_id
        result["message"]  = f"Draft created (id: {draft_id})"
        print(f"  [GMAIL] ✅ Draft saved: {lead['email']} — \"{lead['subject']}\"")

    except HttpError as e:
        result["message"] = f"Gmail API error: {e}"
        print(f"  [GMAIL] ❌ Failed: {lead['email']} — {e}")
    except Exception as e:
        result["message"] = f"Error: {e}"
        print(f"  [GMAIL] ❌ Error: {lead['email']} — {e}")

    return result


# ── Batch draft creation ──────────────────────────────────────────────────────
def create_drafts_batch(leads: list[dict]) -> list[dict]:
    """
    Main entry point. Accepts a list of lead dicts (from drafts_ready.json format).
    Creates a Gmail draft for each and applies the Fnomo_Outreach_Draft label.

    Expected lead dict keys: name, email, subject, body, score
    Returns list of result dicts.
    """
    if not leads:
        print("[GMAIL] No leads to draft.")
        return []

    print(f"\n[GMAIL] Connecting to Gmail API...")
    service  = get_gmail_service()
    label_id = get_or_create_label(service, DRAFT_LABEL)

    print(f"[GMAIL] Label: '{DRAFT_LABEL}' (id: {label_id})")
    print(f"[GMAIL] Creating {len(leads)} draft(s)...\n")

    results = []
    for i, lead in enumerate(leads, 1):
        print(f"  [{i:02}/{len(leads)}] {lead['name']} <{lead['email']}>")
        res = create_draft(service, lead, label_id)
        results.append(res)

    succeeded = sum(1 for r in results if r["success"])
    print(f"\n[GMAIL] Done. {succeeded}/{len(leads)} draft(s) created.")
    print(f"[GMAIL] Find them in Gmail → Label: '{DRAFT_LABEL}'\n")

    return results


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    """
    Run directly to test: python gmail_drafter.py
    Reads drafts_ready.json and pushes each to Gmail.
    """
    drafts_file = BASE_DIR / "drafts_ready.json"
    if not drafts_file.exists():
        print(f"[ERROR] {drafts_file} not found. Run fnomo_engine.py first.")
        raise SystemExit(1)

    with open(drafts_file, encoding="utf-8") as f:
        leads = json.load(f)

    print(f"[GMAIL] Loaded {len(leads)} draft(s) from {drafts_file}")
    create_drafts_batch(leads)
