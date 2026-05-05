from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

ROOT = Path(r"D:\Antigravity\eigent\Downloads\fnomo")
LEDGER = Path(r"C:\Users\kush_\.paperclip\instances\default\workspaces\514aebc7-f334-4659-a7c6-aff8adbbd7b0\fno62_followup1_send_batch_and_crm_writeback_2026-05-04.csv")
STATE = ROOT / "data" / "fnomo_context_state.json"
DRAFT_QUEUE = ROOT / "data" / "whatsapp_draft_queue.jsonl"

mcp = FastMCP("fnomo-context")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_state() -> dict[str, Any]:
    if not STATE.exists():
        return {"reserved": {}, "processed": {}, "conversation_state": {}}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"reserved": {}, "processed": {}, "conversation_state": {}}


def write_state(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def read_ledger() -> list[dict[str, str]]:
    if not LEDGER.exists():
        return []
    with LEDGER.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def find_lead(lead_id: str) -> dict[str, str] | None:
    for row in read_ledger():
        if row.get("lead_id") == lead_id:
            return row
    return None


@mcp.tool()
def get_lead_context(lead_id: str) -> dict[str, Any]:
    """Return FNO-62 lead context by lead_id."""
    row = find_lead(lead_id)
    state = read_state()
    return {
        "found": row is not None,
        "lead": row or {},
        "reserved": state.get("reserved", {}).get(lead_id),
        "processed": state.get("processed", {}).get(lead_id),
        "conversation_state": state.get("conversation_state", {}).get(lead_id, {}),
    }


@mcp.tool()
def check_duplicate(lead_id: str) -> dict[str, Any]:
    """Check whether lead_id is already reserved or processed."""
    state = read_state()
    return {
        "lead_id": lead_id,
        "reserved": lead_id in state.get("reserved", {}),
        "processed": lead_id in state.get("processed", {}),
        "reservation": state.get("reserved", {}).get(lead_id),
        "processed_record": state.get("processed", {}).get(lead_id),
    }


@mcp.tool()
def reserve_lead(lead_id: str, channel: str, owner: str) -> dict[str, Any]:
    """Reserve a lead for a channel owner before send/draft."""
    state = read_state()
    if lead_id in state.get("processed", {}):
        return {"ok": False, "reason": "already_processed", "record": state["processed"][lead_id]}
    existing = state.get("reserved", {}).get(lead_id)
    if existing and existing.get("channel") != channel:
        return {"ok": False, "reason": "ownership_conflict", "record": existing}
    state.setdefault("reserved", {})[lead_id] = {"channel": channel, "owner": owner, "reserved_at": now()}
    write_state(state)
    return {"ok": True, "lead_id": lead_id, "channel": channel, "owner": owner}


@mcp.tool()
def mark_processed(lead_id: str, channel: str, owner: str, proof: str) -> dict[str, Any]:
    """Mark a lead processed only when send proof exists."""
    if not proof.strip():
        return {"ok": False, "reason": "proof_required"}
    state = read_state()
    state.setdefault("processed", {})[lead_id] = {
        "channel": channel,
        "owner": owner,
        "proof": proof,
        "processed_at": now(),
    }
    write_state(state)
    return {"ok": True, "lead_id": lead_id}


@mcp.tool()
def create_whatsapp_draft(lead_id: str) -> dict[str, Any]:
    """Create a draft-only WhatsApp queue item for a lead."""
    row = find_lead(lead_id)
    if not row:
        return {"ok": False, "reason": "lead_not_found"}
    if row.get("channel") != "WhatsApp":
        return {"ok": False, "reason": "not_whatsapp_lead", "channel": row.get("channel")}
    draft = {
        "created_at": now(),
        "mode": "draft_only",
        "lead_id": lead_id,
        "lead_name": row.get("lead_name", ""),
        "message": row.get("followup1_message", ""),
        "manual_send_instruction": "Kush sends manually from WhatsApp; no automation send performed.",
        "status": "draft_ready",
    }
    DRAFT_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with DRAFT_QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(draft, ensure_ascii=False) + "\n")
    return {"ok": True, "draft": draft, "queue_path": str(DRAFT_QUEUE)}


if __name__ == "__main__":
    mcp.run()
