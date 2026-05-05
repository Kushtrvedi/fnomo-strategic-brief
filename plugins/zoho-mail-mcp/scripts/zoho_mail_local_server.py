"""
Local Zoho Mail MCP server for Fnomo.

This server loads Zoho credentials from an existing env file and exposes
core mailbox operations over FastMCP so local Codex/plugin setups can use
Zoho Mail even when no managed connector is available.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


def _load_env() -> None:
    env_path = os.getenv("ZOHO_ENV_PATH", "").strip()
    if env_path:
        load_dotenv(dotenv_path=Path(env_path), override=False)
        return

    plugin_root = Path(__file__).resolve().parents[1]
    candidate = plugin_root / ".env"
    if candidate.exists():
        load_dotenv(dotenv_path=candidate, override=False)
        return

    repo_default = plugin_root.parents[1] / "Images and content" / "fnomo_emailer" / ".env"
    if repo_default.exists():
        load_dotenv(dotenv_path=repo_default, override=False)


_load_env()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "")
ACCOUNT_ID = os.getenv("ZOHO_ACCOUNT_ID", "")
DRAFTS_FOLDER_ID = os.getenv("ZOHO_DRAFTS_FOLDER_ID", "")
MAIL_ADDRESS = os.getenv("ZOHO_MAIL_ADDRESS", os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com"))
REGION = os.getenv("ZOHO_REGION", "eu").strip().lower() or "eu"
CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "draft_cache.json"
SUNDAY_SEND_OVERRIDE = os.getenv("FNOMO_ALLOW_SUNDAY_SEND", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "override",
}

TOKEN_URL = f"https://accounts.zoho.{REGION}/oauth/v2/token"
MAIL_BASE = f"https://mail.zoho.{REGION}/api/accounts/{ACCOUNT_ID}"

mcp = FastMCP("zoho-mail-local")


def _assert_configured() -> None:
    missing = [
        name
        for name, value in {
            "ZOHO_CLIENT_ID": CLIENT_ID,
            "ZOHO_CLIENT_SECRET": CLIENT_SECRET,
            "ZOHO_REFRESH_TOKEN": REFRESH_TOKEN,
            "ZOHO_ACCOUNT_ID": ACCOUNT_ID,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Zoho configuration: {', '.join(missing)}")


def _get_access_token() -> str:
    _assert_configured()
    response = requests.post(
        TOKEN_URL,
        params={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Zoho token refresh failed: {payload}")
    return token


def _headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {token}"}


def _sunday_send_blocked() -> bool:
    return datetime.now().weekday() == 6 and not SUNDAY_SEND_OVERRIDE


def _safe_json(response: requests.Response) -> Dict[str, Any]:
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


def _normalize_text(text: str) -> str:
    return (
        str(text)
        .replace("â€˜", "'")
        .replace("â€™", "'")
        .replace("â€œ", '"')
        .replace("â€", '"')
        .replace("â€”", "--")
        .replace("â€“", "-")
        .replace("â€¦", "...")
        .replace("Â ", " ")
        .strip()
    )


def _request(method: str, url: str, *, params: Dict[str, Any] | None = None, json_body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    token = _get_access_token()
    response = requests.request(
        method,
        url,
        headers=_headers(token),
        params=params,
        json=json_body,
        timeout=25,
    )
    if not response.ok:
        raise RuntimeError(f"Zoho API {response.status_code}: {_safe_json(response)}")
    return _safe_json(response)


def _read_cache() -> List[Dict[str, Any]]:
    if not CACHE_PATH.exists():
        return []
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_cache(items: List[Dict[str, Any]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


@mcp.tool()
def get_account_info() -> str:
    """Return connected Zoho account details."""
    data = _request("GET", f"https://mail.zoho.{REGION}/api/accounts")
    return json.dumps(
        {
            "mailAddress": MAIL_ADDRESS,
            "accountId": ACCOUNT_ID,
            "accounts": data.get("data", []),
        },
        indent=2,
    )


@mcp.tool()
def list_folders() -> str:
    """List Zoho mail folders and IDs."""
    data = _request("GET", f"{MAIL_BASE}/folders")
    folders: List[Dict[str, Any]] = data.get("data", [])
    if not folders:
        return "No folders returned."
    lines = []
    for folder in folders:
        lines.append(
            f"{folder.get('folderName', 'N/A')} | ID: {folder.get('folderId', 'N/A')} | "
            f"Messages: {folder.get('messageCount', 0)}"
        )
    return "\n".join(lines)


@mcp.tool()
def list_drafts(limit: int = 10) -> str:
    """List recent drafts created through this local MCP plugin."""
    messages = _read_cache()
    if not messages:
        return "No locally tracked drafts yet."
    messages = list(reversed(messages))[: min(max(limit, 1), 50)]
    lines = []
    for message in messages:
        lines.append(
            f"ID: {message.get('messageId', 'N/A')} | "
            f"To: {message.get('toAddress', 'N/A')} | "
            f"Subject: {message.get('subject', 'N/A')}"
        )
    return "\n".join(lines)


@mcp.tool()
def create_draft(to_email: str, subject: str, body: str) -> str:
    """Create a Zoho draft without sending it."""
    payload = {
        "fromAddress": MAIL_ADDRESS,
        "toAddress": _normalize_text(to_email),
        "subject": _normalize_text(subject),
        "content": _normalize_text(body),
        "mailFormat": "plaintext",
        "mode": "draft",
    }
    data = _request("POST", f"{MAIL_BASE}/messages", json_body=payload)
    if data.get("status", {}).get("code") == 200 and data.get("data", {}).get("mode") == "draft":
        cache = _read_cache()
        cache.append(
            {
                "messageId": data.get("data", {}).get("messageId"),
                "toAddress": payload["toAddress"],
                "subject": payload["subject"],
                "fromAddress": payload["fromAddress"],
            }
        )
        _write_cache(cache)
    return json.dumps(data, indent=2)


@mcp.tool()
def send_draft(message_id: str) -> str:
    """Send an existing draft by message ID."""
    if _sunday_send_blocked():
        return (
            "BLOCKED: Sunday is planning-only for Fnomo. "
            "Use draft/read operations today or set FNOMO_ALLOW_SUNDAY_SEND=1 for an explicit override."
        )

    token = _get_access_token()
    response = requests.put(
        f"{MAIL_BASE}/messages/{message_id}/action",
        headers=_headers(token),
        data={"mode": "sendmessage"},
        timeout=25,
    )
    if not response.ok:
        raise RuntimeError(f"Zoho API {response.status_code}: {_safe_json(response)}")
    return json.dumps(_safe_json(response), indent=2)


@mcp.tool()
def search_messages(query: str, limit: int = 10) -> str:
    """Search locally tracked draft metadata by subject or recipient."""
    query_lower = query.lower().strip()
    messages = [
        item
        for item in _read_cache()
        if query_lower in str(item.get("subject", "")).lower()
        or query_lower in str(item.get("toAddress", "")).lower()
    ]
    if not messages:
        return "No locally tracked drafts matched the search."
    messages = list(reversed(messages))[: min(max(limit, 1), 50)]
    lines = []
    for message in messages:
        lines.append(
            f"ID: {message.get('messageId', 'N/A')} | "
            f"From: {message.get('fromAddress', 'N/A')} | "
            f"Subject: {message.get('subject', 'N/A')}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
