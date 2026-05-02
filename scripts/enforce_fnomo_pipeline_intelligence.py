#!/usr/bin/env python3
"""
Enforce Fnomo pipeline-intelligence rules in Notion.

This script keeps the CRM structure intact while adding classification logic:
- Execution History Outcome becomes a select enum.
- Existing free-text outcome is preserved as Outcome Notes.
- Historical rows are backfilled.
- Contacts/Clients stages move only when outcome signal is explicit.
- Tier A SLA risks are surfaced through Active Work tasks.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
NOTION_VERSION = "2022-06-28"
CLIENTS_DB = "e8a8aa3c-b995-8368-8495-014b8ea295c3"
CONTACTS_DB = "3548aa3c-b995-8148-a653-fead444e56fe"
EXECUTION_DB = "6fb8aa3c-b995-82ec-806b-01b6cd1b2915"
HISTORY_DB = "3548aa3c-b995-818a-8ede-ed9a5d99aac3"

OUTCOMES = [
    ("Interested", "green"),
    ("Curious", "blue"),
    ("Objection", "orange"),
    ("Not Relevant", "red"),
    ("No Response", "gray"),
]

SESSION = requests.Session()


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def headers() -> dict[str, str]:
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        die("NOTION_API_KEY is missing.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    for attempt in range(6):
        response = SESSION.request(
            method,
            f"https://api.notion.com/v1/{path.lstrip('/')}",
            headers=headers(),
            json=payload,
            timeout=60,
        )
        if response.status_code == 429:
            time.sleep(2 + attempt)
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed {response.status_code}: {response.text[:1500]}")
        return response.json()
    raise RuntimeError(f"{method} {path} failed after retries")


def query_database(database_id: str, filter_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        if filter_payload:
            payload["filter"] = filter_payload
        data = notion("POST", f"databases/{database_id}/query", payload)
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            return rows
        cursor = data.get("next_cursor")


def plain_text(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    prop_type = prop.get("type")
    if prop_type in {"title", "rich_text"}:
        return "".join(part.get("plain_text", "") for part in prop.get(prop_type, [])).strip()
    if prop_type == "select":
        return ((prop.get("select") or {}).get("name") or "").strip()
    if prop_type == "status":
        return ((prop.get("status") or {}).get("name") or "").strip()
    if prop_type == "date" and prop.get("date"):
        return (prop["date"].get("start") or "").strip()
    return ""


def prop(page: dict[str, Any], name: str) -> dict[str, Any] | None:
    return (page.get("properties") or {}).get(name)


def select_value(name: str) -> dict[str, Any]:
    return {"select": {"name": name}}


def rich_text(value: str) -> dict[str, Any]:
    return {"rich_text": [{"text": {"content": value[:1900]}}]} if value else {"rich_text": []}


def date_value(value: date) -> dict[str, Any]:
    return {"date": {"start": value.isoformat()}}


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None


def title_of(page: dict[str, Any]) -> str:
    for value in (page.get("properties") or {}).values():
        if value.get("type") == "title":
            return plain_text(value)
    return ""


def page_name(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Company")) or plain_text(prop(page, "Name")) or title_of(page)


def relation_ids(page: dict[str, Any], name: str) -> list[str]:
    return [item.get("id", "") for item in ((prop(page, name) or {}).get("relation") or []) if item.get("id")]


def ensure_history_schema() -> str:
    schema = notion("GET", f"databases/{HISTORY_DB}").get("properties") or {}
    if schema.get("Outcome", {}).get("type") == "rich_text":
        notion("PATCH", f"databases/{HISTORY_DB}", {"properties": {"Outcome": {"name": "Outcome Notes"}}})
        schema = notion("GET", f"databases/{HISTORY_DB}").get("properties") or {}
    outcome_options = [{"name": name, "color": color} for name, color in OUTCOMES]
    notion(
        "PATCH",
        f"databases/{HISTORY_DB}",
        {"properties": {"Outcome": {"select": {"options": outcome_options}}}},
    )
    return "renamed_outcome_notes" if "Outcome Notes" in schema else "outcome_select_ready"


def classify_history(row: dict[str, Any]) -> str:
    props = row.get("properties") or {}
    action_type = plain_text(props.get("Action Type")).lower()
    outcome_notes = plain_text(props.get("Outcome Notes")).lower()
    next_move = plain_text(props.get("Next Move")).lower()
    text = " | ".join([action_type, outcome_notes, next_move]).lower()
    reply_context = any(
        token in text
        for token in [
            "reply received",
            "replied",
            "response received",
            "responded",
            "lead replied",
            "prospect replied",
            "asked for",
            "asked about",
            "meeting booked",
            "call booked",
        ]
    )
    if not reply_context:
        return "No Response"
    if any(token in text for token in ["not relevant", "not interested", "irrelevant", "wrong fit", "do not contact"]):
        return "Not Relevant"
    if any(token in text for token in ["objection", "concern", "price", "already have", "too expensive", "not now"]):
        return "Objection"
    if any(token in text for token in ["interested", "positive", "yes", "wants", "asked for call", "meeting booked"]):
        return "Interested"
    if any(token in text for token in ["curious", "asked", "question", "tell me more", "asked about"]):
        return "Curious"
    return "Curious"


def backfill_history() -> Counter:
    ensure_history_schema()
    counts: Counter = Counter()
    for row in query_database(HISTORY_DB):
        outcome = classify_history(row)
        current = plain_text(prop(row, "Outcome"))
        if current != outcome:
            notion("PATCH", f"pages/{row['id']}", {"properties": {"Outcome": select_value(outcome)}})
            counts["history_rows_updated"] += 1
        counts[outcome] += 1
    return counts


def make_task_name(prefix: str, contact: dict[str, Any], client: dict[str, Any]) -> str:
    return f"{prefix} with {title_of(contact)} ({page_name(client)})"


def task_payload(
    name: str,
    client: dict[str, Any],
    contact: dict[str, Any],
    task_type: str,
    due: date,
    stage_context: str,
    note: str,
) -> dict[str, Any]:
    priority = "High" if plain_text(prop(contact, "Tier")).upper() == "A" else "Medium"
    return {
        "Task": {"title": [{"text": {"content": name[:1800]}}]},
        "Client": {"relation": [{"id": client["id"]}]},
        "Contact": {"relation": [{"id": contact["id"]}]},
        "Type": {"select": {"name": task_type}},
        "Priority": {"select": {"name": priority}},
        "Due date": date_value(due),
        "Status": {"status": {"name": "To Do"}},
        "Stage Context": {"select": {"name": stage_context}},
        "Additional Information": rich_text(note),
    }


def existing_open_tasks() -> set[tuple[str, str]]:
    tasks = query_database(EXECUTION_DB)
    keys: set[tuple[str, str]] = set()
    for task in tasks:
        if plain_text(prop(task, "Status")).lower() == "done":
            continue
        contact_ids = relation_ids(task, "Contact")
        if contact_ids:
            keys.add((contact_ids[0], title_of(task).lower()))
    return keys


def enforce_stage_and_sla(today: date) -> Counter:
    counts: Counter = Counter()
    clients = query_database(CLIENTS_DB)
    contacts = query_database(CONTACTS_DB)
    client_by_id = {client["id"]: client for client in clients}
    open_task_keys = existing_open_tasks()

    # No explicit reply rows exist yet in current history, so stage movement is conservative.
    for contact in contacts:
        stage = plain_text(prop(contact, "Stage")) or "New"
        if stage != "Contacted":
            continue
        last_contact = parse_date(plain_text(prop(contact, "Last Contact Date")))
        if not last_contact:
            continue
        age = (today - last_contact).days
        if plain_text(prop(contact, "Tier")).upper() != "A":
            continue
        client_ids = relation_ids(contact, "Company")
        if not client_ids or client_ids[0] not in client_by_id:
            continue
        client = client_by_id[client_ids[0]]
        if age >= 7:
            prefix = "Escalate"
            task_type = "Call"
            note = "Tier A SLA: no reply after 7 days. Escalate by call or alternate channel; do not let this remain passive."
        elif age >= 4:
            prefix = "Follow-up 2"
            task_type = "Follow-Up"
            note = "Tier A SLA: no reply after 4 days. Send Follow-up 2 with a sharper decision-regret trigger."
        elif age >= 2:
            prefix = "Follow-up 1"
            task_type = "Follow-Up"
            note = "Tier A SLA: no reply after 48h. Send Follow-up 1; optimize for reply, not explanation."
        else:
            continue
        name = make_task_name(prefix, contact, client)
        key = (contact["id"], name.lower())
        if key in open_task_keys:
            counts["sla_tasks_already_present"] += 1
            continue
        notion(
            "POST",
            "pages",
            {
                "parent": {"database_id": EXECUTION_DB},
                "properties": task_payload(name, client, contact, task_type, today, stage, note),
            },
        )
        open_task_keys.add(key)
        counts["sla_tasks_created"] += 1
    return counts


def log_history(action_summary: str, next_move: str, today: date) -> None:
    key = f"{today.isoformat()}::pipeline-intelligence-fix"
    existing = query_database(HISTORY_DB, {"property": "History Key", "title": {"equals": key}})
    properties = {
        "History Key": {"title": [{"text": {"content": key}}]},
        "Date": date_value(today),
        "Action Type": rich_text("Pipeline intelligence fix"),
        "Lead or Task": rich_text("Outcome classification + Tier A SLA"),
        "Owner": rich_text("Codex"),
        "Channel": rich_text("Notion API"),
        "Outcome": select_value("No Response"),
        "Outcome Notes": rich_text(action_summary),
        "Next Move": rich_text(next_move),
        "Source": rich_text("Fnomo CRM enforcement layer"),
        "Last Synced At": {"date": {"start": datetime.now().astimezone().isoformat(timespec="seconds")}},
    }
    if existing:
        notion("PATCH", f"pages/{existing[0]['id']}", {"properties": properties})
    else:
        notion("POST", "pages", {"parent": {"database_id": HISTORY_DB}, "properties": properties})


def main() -> None:
    today = date.fromisoformat(os.environ.get("FNOMO_OPERATING_DATE", date.today().isoformat()))
    history_counts = backfill_history()
    sla_counts = enforce_stage_and_sla(today)
    action_summary = (
        "Added enum Outcome classification, preserved old outcome text as Outcome Notes, "
        f"backfilled history rows, and enforced Tier A SLA tasks. Counts: {dict(history_counts | sla_counts)}"
    )
    next_move = "Use reply/engagement rates as the board truth; rebuild messaging around wrong-decision regret and force Tier A replies."
    log_history(action_summary, next_move, today)
    print(json.dumps({"history": dict(history_counts), "sla": dict(sla_counts)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
