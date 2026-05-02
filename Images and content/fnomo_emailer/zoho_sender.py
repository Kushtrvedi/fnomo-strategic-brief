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
        "body":       lead.get("body", ""),
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

    def _sanitise(text: str) -> str:
        """Strip non-ASCII chars that cause Zoho 500 errors in plaintext mode."""
        return (text
            .replace("‘", "'").replace("’", "'")
            .replace("“", '"').replace("”", '"')
            .replace("—", "--").replace("–", "-")
            .replace("…", "...").replace(" ", " ")
            .encode("ascii", "ignore").decode("ascii")
        )

    payload = {
        "fromAddress":  SENDER_EMAIL,
        "toAddress":    lead["email"],
        "subject":      _sanitise(lead["subject"]),
        "content":      _sanitise(lead["full_body"]),
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
