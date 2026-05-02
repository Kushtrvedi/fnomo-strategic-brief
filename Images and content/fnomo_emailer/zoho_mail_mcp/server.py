"""
zoho_mail_mcp/server.py -- FNOMO Zoho Mail MCP Server
Exposes Zoho Mail operations as MCP tools so Claude can call them directly.

Tools:
  zoho_create_draft   -- Save email to Zoho Drafts folder (no send)
  zoho_list_drafts    -- List drafts in the Drafts folder
  zoho_list_folders   -- List all mail folders with their IDs
  zoho_send_draft     -- Send an existing draft by draft message ID
  zoho_get_token      -- Refresh and return current access token (debug)

Run:
  python server.py

Install deps:
  pip install fastmcp requests python-dotenv --break-system-packages
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# -- Credentials ---------------------------------------------------------------
CLIENT_ID        = os.getenv("ZOHO_CLIENT_ID",        "")
CLIENT_SECRET    = os.getenv("ZOHO_CLIENT_SECRET",     "")
REFRESH_TOKEN    = os.getenv("ZOHO_REFRESH_TOKEN",     "")
ACCOUNT_ID       = os.getenv("ZOHO_ACCOUNT_ID",        "")
SENDER_EMAIL     = os.getenv("SENDER_EMAIL",            "kush@mail.fnomo.com")
DRAFTS_FOLDER_ID = os.getenv("ZOHO_DRAFTS_FOLDER_ID",  "")

TOKEN_URL     = "https://accounts.zoho.eu/oauth/v2/token"
BASE_URL      = f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}"
DRAFT_API_URL = f"https://mail360.zoho.com/api/accounts/{ACCOUNT_ID}/drafts"

mcp = FastMCP("zoho-mail-fnomo")


# -- Auth ----------------------------------------------------------------------
def _get_token() -> str:
    resp = requests.post(TOKEN_URL, params={
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token refresh failed: {data}")
    return data["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Zoho-oauthtoken {token}"}


def _sanitise(text: str) -> str:
    return (text
        .replace("‘", "'").replace("’", "'")
        .replace("“", '"').replace("”", '"')
        .replace("—", "--").replace("–", "-")
        .replace("…", "...").replace(" ", " ")
        .encode("ascii", "ignore").decode("ascii")
    )


# -- Tools ---------------------------------------------------------------------

@mcp.tool()
def zoho_create_draft(
    to_email: str,
    subject: str,
    body: str,
) -> str:
    """
    Save an email as a draft in Zoho Mail. Does NOT send.
    Draft appears in Zoho Mail -> Drafts folder.

    Args:
        to_email: Recipient email address (named/partner emails only, no info@/hr@)
        subject:  Email subject line
        body:     Full plain-text email body including compliance footer
    Returns:
        Success or failure message with details
    """
    token = _get_token()
    url   = DRAFT_API_URL

    payload = {
        "fromAddress": SENDER_EMAIL,
        "toAddress":   _sanitise(to_email),
        "subject":     _sanitise(subject),
        "content":     _sanitise(body),
        "mailFormat":  "plaintext",
    }

    resp = requests.post(url, headers=_headers(token), json=payload, timeout=20)

    if not resp.ok:
        return f"FAILED: HTTP {resp.status_code} -- {resp.text[:300]}"

    data = resp.json()
    code = data.get("status", {}).get("code")
    if code in (200, 201):
        return f"Draft saved in Zoho Drafts -- to: {to_email} | subject: {subject}"
    else:
        return f"FAILED: {json.dumps(data)}"


@mcp.tool()
def zoho_list_drafts(limit: int = 10) -> str:
    """
    List recent drafts from the Zoho Mail Drafts folder.

    Args:
        limit: Number of drafts to return (default 10, max 50)
    Returns:
        Formatted list of drafts with subject, recipient, and message ID
    """
    token = _get_token()
    url   = f"{BASE_URL}/folders/{DRAFTS_FOLDER_ID}/messages"

    resp = requests.get(url, headers=_headers(token),
                        params={"limit": min(limit, 50), "start": 0}, timeout=15)

    if not resp.ok:
        return f"FAILED: HTTP {resp.status_code} -- {resp.text[:200]}"

    messages = resp.json().get("data", [])
    if not messages:
        return "Drafts folder is empty."

    lines = [f"Zoho Drafts ({len(messages)} found):\n"]
    for m in messages:
        lines.append(
            f"  ID      : {m.get('messageId', 'N/A')}\n"
            f"  To      : {m.get('toAddress', 'N/A')}\n"
            f"  Subject : {m.get('subject', 'N/A')}\n"
            f"  Date    : {m.get('receivedTime', 'N/A')}\n"
        )
    return "\n".join(lines)


@mcp.tool()
def zoho_list_folders() -> str:
    """
    List all Zoho Mail folders with their IDs.
    Useful for finding folder IDs for Inbox, Sent, Drafts, etc.

    Returns:
        Formatted list of folders with name, ID, and message count
    """
    token = _get_token()
    resp  = requests.get(f"{BASE_URL}/folders", headers=_headers(token), timeout=15)

    if not resp.ok:
        return f"FAILED: HTTP {resp.status_code} -- {resp.text[:200]}"

    folders = resp.json().get("data", [])
    lines   = ["Zoho Mail Folders:\n"]
    for f in folders:
        lines.append(
            f"  {f.get('folderName', 'N/A'):20} "
            f"ID: {f.get('folderId', 'N/A'):20} "
            f"Messages: {f.get('messageCount', 0)}"
        )
    return "\n".join(lines)


@mcp.tool()
def zoho_send_draft(message_id: str) -> str:
    """
    Send an existing draft by its message ID.
    Use zoho_list_drafts to find message IDs.

    Args:
        message_id: The messageId of the draft to send
    Returns:
        Success or failure message
    """
    token   = _get_token()
    url     = f"{BASE_URL}/messages/{message_id}/action"
    payload = {"mode": "sendmessage"}

    resp = requests.put(url, headers=_headers(token), data=payload, timeout=20)

    if not resp.ok:
        return f"FAILED: HTTP {resp.status_code} -- {resp.text[:300]}"

    data = resp.json()
    code = data.get("status", {}).get("code")
    if code in (200, 201):
        return f"Draft {message_id} sent successfully."
    else:
        return f"FAILED: {json.dumps(data)}"


@mcp.tool()
def zoho_get_token() -> str:
    """
    Refresh and return the current Zoho access token.
    Use for debugging auth issues.

    Returns:
        First 40 characters of the access token (truncated for security)
    """
    token = _get_token()
    return f"Token OK: {token[:40]}..."


# -- Entry point ---------------------------------------------------------------
if __name__ == "__main__":
    print(f"[MCP] Starting FNOMO Zoho Mail MCP Server")
    print(f"[MCP] Account : {ACCOUNT_ID}")
    print(f"[MCP] Sender  : {SENDER_EMAIL}")
    print(f"[MCP] Drafts  : folder {DRAFTS_FOLDER_ID}")
    print(f"[MCP] Tools   : zoho_create_draft, zoho_list_drafts, zoho_list_folders, zoho_send_draft")
    mcp.run()
