#!/usr/bin/env python3
"""
Apply Fnomo Messaging Test Batch 1.

Rule:
- Do not expand pipeline.
- Target Tier A contacts already Contacted with no response.
- Override next action to re-engage with the wrong-decision trigger.
- Tag the contact/client/active work with Messaging Test Batch 1.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
NOTION_VERSION = "2022-06-28"
CLIENTS_DB = "e8a8aa3c-b995-8368-8495-014b8ea295c3"
CONTACTS_DB = "3548aa3c-b995-8148-a653-fead444e56fe"
EXECUTION_DB = "6fb8aa3c-b995-82ec-806b-01b6cd1b2915"
HISTORY_DB = "3548aa3c-b995-818a-8ede-ed9a5d99aac3"
TAG = "Messaging Test Batch 1"

SESSION = requests.Session()


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def headers() -> dict[str, str]:
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        die("NOTION_API_KEY missing")
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


def title_of(page: dict[str, Any] | None) -> str:
    if not page:
        return ""
    for value in (page.get("properties") or {}).values():
        if value.get("type") == "title":
            return plain_text(value)
    return ""


def page_name(page: dict[str, Any] | None) -> str:
    if not page:
        return ""
    return plain_text(prop(page, "Company")) or plain_text(prop(page, "Name")) or title_of(page)


def relation_ids(page: dict[str, Any], name: str) -> list[str]:
    return [item.get("id", "") for item in ((prop(page, name) or {}).get("relation") or []) if item.get("id")]


def rich_text(value: str) -> dict[str, Any]:
    return {"rich_text": [{"text": {"content": value[:1900]}}]} if value else {"rich_text": []}


def date_value(value: date) -> dict[str, Any]:
    return {"date": {"start": value.isoformat()}}


def multi_select(existing_prop: dict[str, Any] | None, tag: str) -> dict[str, Any]:
    existing = []
    if existing_prop and existing_prop.get("type") == "multi_select":
        existing = [item["name"] for item in existing_prop.get("multi_select", []) if item.get("name")]
    if tag not in existing:
        existing.append(tag)
    return {"multi_select": [{"name": name} for name in existing]}


def ensure_tag_fields() -> None:
    option = {"name": TAG, "color": "red"}
    for database_id in [CLIENTS_DB, CONTACTS_DB, EXECUTION_DB]:
        schema = notion("GET", f"databases/{database_id}").get("properties") or {}
        if schema.get("Tags", {}).get("type") != "multi_select":
            notion("PATCH", f"databases/{database_id}", {"properties": {"Tags": {"multi_select": {"options": [option]}}}})
        else:
            notion("PATCH", f"databases/{database_id}", {"properties": {"Tags": {"multi_select": {"options": [option]}}}})


def action_for_segment(segment: str) -> tuple[str, str]:
    if segment == "CA Firms & Associations":
        return (
            "Re-engage with new messaging angle: ask whether any client made an investment decision in the last 6 months that later turned out wrong.",
            "Version A: client mistake / advisory-risk trigger",
        )
    return (
        "Re-engage with new messaging angle: ask where confidence existed before the decision was properly validated.",
        "Version B: confidence-gap before commitment trigger",
    )


def open_task_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for task in query_database(EXECUTION_DB):
        if plain_text(prop(task, "Status")).lower() == "done":
            continue
        contact_ids = relation_ids(task, "Contact")
        if contact_ids:
            keys.add((contact_ids[0], title_of(task).lower()))
    return keys


def create_task(contact: dict[str, Any], client: dict[str, Any], due: date, note: str, keys: set[tuple[str, str]]) -> bool:
    name = f"Re-engage with {title_of(contact)} ({page_name(client)})"
    key = (contact["id"], name.lower())
    if key in keys:
        return False
    priority = "High" if plain_text(prop(contact, "Tier")).upper() == "A" else "Medium"
    notion(
        "POST",
        "pages",
        {
            "parent": {"database_id": EXECUTION_DB},
            "properties": {
                "Task": {"title": [{"text": {"content": name[:1800]}}]},
                "Client": {"relation": [{"id": client["id"]}]},
                "Contact": {"relation": [{"id": contact["id"]}]},
                "Type": {"select": {"name": "Follow-Up"}},
                "Priority": {"select": {"name": priority}},
                "Due date": date_value(due),
                "Status": {"status": {"name": "To Do"}},
                "Stage Context": {"select": {"name": "Contacted"}},
                "Additional Information": rich_text(note),
                "Tags": {"multi_select": [{"name": TAG}]},
            },
        },
    )
    keys.add(key)
    return True


def log_history(counts: Counter, today: date) -> None:
    key = f"{today.isoformat()}::messaging-test-batch-1"
    existing = query_database(HISTORY_DB, {"property": "History Key", "title": {"equals": key}})
    summary = (
        f"Paused cold expansion and tagged {counts['contacts_tagged']} Tier A contacted/no-response contacts for Messaging Test Batch 1. "
        f"Created {counts['tasks_created']} re-engagement tasks. CA contacts use client-mistake trigger; other Tier A contacts use confidence-gap trigger."
    )
    properties = {
        "History Key": {"title": [{"text": {"content": key}}]},
        "Date": date_value(today),
        "Action Type": rich_text("Messaging test enforcement"),
        "Lead or Task": rich_text("Tier A contacted / no-response cohort"),
        "Owner": rich_text("Codex"),
        "Channel": rich_text("Notion API"),
        "Outcome": {"select": {"name": "No Response"}},
        "Outcome Notes": rich_text(summary),
        "Next Move": rich_text("Send re-engagement messages; success target is first 5-10 replies, not demos or conversion."),
        "Source": rich_text("Pipeline trigger correction"),
        "Last Synced At": {"date": {"start": datetime.now().astimezone().isoformat(timespec="seconds")}},
    }
    if existing:
        notion("PATCH", f"pages/{existing[0]['id']}", {"properties": properties})
    else:
        notion("POST", "pages", {"parent": {"database_id": HISTORY_DB}, "properties": properties})


def main() -> None:
    today = date.fromisoformat(os.environ.get("FNOMO_OPERATING_DATE", date.today().isoformat()))
    ensure_tag_fields()
    clients = query_database(CLIENTS_DB)
    contacts = query_database(CONTACTS_DB)
    client_by_id = {client["id"]: client for client in clients}
    contacts_by_client: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for contact in contacts:
        for client_id in relation_ids(contact, "Company"):
            contacts_by_client[client_id].append(contact)

    task_keys = open_task_keys()
    counts: Counter = Counter()
    touched_clients: set[str] = set()
    segment_counts: Counter = Counter()
    for contact in contacts:
        if plain_text(prop(contact, "Stage")) != "Contacted":
            continue
        if plain_text(prop(contact, "Tier")).upper() != "A":
            continue
        client_ids = relation_ids(contact, "Company")
        if not client_ids or client_ids[0] not in client_by_id:
            continue
        client = client_by_id[client_ids[0]]
        segment = plain_text(prop(contact, "Segment")) or plain_text(prop(client, "Segment"))
        next_action, version = action_for_segment(segment)
        note = (
            f"{version}. Pause new cold volume. Goal: get a reply by triggering memory of a wrong decision, "
            "not by explaining Fnomo."
        )
        notion(
            "PATCH",
            f"pages/{contact['id']}",
            {
                "properties": {
                    "Next Action": rich_text(next_action),
                    "Next Action Date": date_value(today),
                    "Notes": rich_text((plain_text(prop(contact, "Notes")) + f" | [{today.isoformat()}] {TAG}: {version}").strip(" |")),
                    "Tags": multi_select(prop(contact, "Tags"), TAG),
                }
            },
        )
        counts["contacts_tagged"] += 1
        segment_counts[segment] += 1
        touched_clients.add(client["id"])
        if create_task(contact, client, today, note, task_keys):
            counts["tasks_created"] += 1
        else:
            counts["tasks_already_present"] += 1

    for client_id in touched_clients:
        client = client_by_id[client_id]
        next_action = "Re-engage Tier A contacted contacts with Messaging Test Batch 1; do not expand cold volume until replies appear."
        notion(
            "PATCH",
            f"pages/{client_id}",
            {
                "properties": {
                    "Next Action": rich_text(next_action),
                    "Next Action Date": date_value(today),
                    "Notes": rich_text((plain_text(prop(client, "Notes")) + f" | [{today.isoformat()}] {TAG}: trigger test active").strip(" |")),
                    "Tags": multi_select(prop(client, "Tags"), TAG),
                }
            },
        )
        counts["clients_tagged"] += 1

    log_history(counts, today)
    print(json.dumps({"counts": dict(counts), "segments": dict(segment_counts)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
