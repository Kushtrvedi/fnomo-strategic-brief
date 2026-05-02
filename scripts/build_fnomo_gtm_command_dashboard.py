#!/usr/bin/env python3
"""
Build the board-facing Fnomo GTM Command Dashboard in Notion.

This is a read layer above the existing CRM. It does not mutate Clients,
Contacts, Execution, Deals, or Execution History records.
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
CONFIG_PATH = ROOT / "data" / "fnomo_notion_backend.json"
NOTION_VERSION = "2022-06-28"
PARENT_PAGE_ID = "5818aa3c-b995-827e-af29-011d0732f5bc"
CLIENTS_DB = "e8a8aa3c-b995-8368-8495-014b8ea295c3"
CONTACTS_DB = "3548aa3c-b995-8148-a653-fead444e56fe"
EXECUTION_DB = "6fb8aa3c-b995-82ec-806b-01b6cd1b2915"
HISTORY_DB = "3548aa3c-b995-818a-8ede-ed9a5d99aac3"
DASHBOARD_TITLE = "Fnomo GTM Command Dashboard"


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
    raise RuntimeError(f"{method} {path} failed after rate-limit retries")


def query_database(database_id: str, filter_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {"page_size": 100}
        if filter_payload:
            payload["filter"] = filter_payload
        if cursor:
            payload["start_cursor"] = cursor
        data = notion("POST", f"databases/{database_id}/query", payload)
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            return results
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


def parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None


def page_title(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    for prop in props.values():
        if prop.get("type") == "title":
            return plain_text(prop)
    return ""


def prop(page: dict[str, Any], name: str) -> dict[str, Any] | None:
    return (page.get("properties") or {}).get(name)


def cell(text: Any) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": str(text)[:1800]}}]


def paragraph(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": cell(text)}}


def heading(level: int, text: str) -> dict[str, Any]:
    block_type = f"heading_{level}"
    return {"object": "block", "type": block_type, block_type: {"rich_text": cell(text)}}


def bulleted(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": cell(text)}}


def divider() -> dict[str, Any]:
    return {"object": "block", "type": "divider", "divider": {}}


def table_block(rows: list[list[Any]]) -> dict[str, Any]:
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": [
                {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {"cells": [cell(value) for value in row]},
                }
                for row in normalized
            ],
        },
    }


def extract_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "clients": query_database(CLIENTS_DB),
        "contacts": query_database(CONTACTS_DB),
        "execution": query_database(EXECUTION_DB),
        "history": query_database(HISTORY_DB),
    }


def action_text(history_page: dict[str, Any]) -> str:
    props = history_page.get("properties") or {}
    return " | ".join(
        plain_text(props.get(key))
        for key in ["Action Type", "Lead or Task", "Channel", "Outcome", "Next Move"]
    ).lower()


def classify_history(rows: list[dict[str, Any]], start: date, today: date) -> dict[str, int | float]:
    recent = []
    for row in rows:
        row_date = parse_iso_date(plain_text(prop(row, "Date")))
        if row_date and start <= row_date <= today:
            recent.append(row)

    messages_sent = 0
    followups = 0
    meetings = 0
    replies = 0
    interested = 0
    curious = 0
    objection = 0
    not_relevant = 0
    for row in recent:
        props = row.get("properties") or {}
        action_type = plain_text(props.get("Action Type")).lower()
        outcome_class = plain_text(props.get("Outcome")) or "No Response"
        outcome = outcome_class.lower()
        outcome_notes = plain_text(props.get("Outcome Notes")).lower()
        next_move = plain_text(props.get("Next Move")).lower()
        text = " | ".join([action_type, outcome_notes, next_move]).lower()
        if "whatsapp outreach" in action_type or "marked contacted" in outcome_notes:
            messages_sent += extract_count(outcome_notes) or 1
        elif "platform partnership update" in action_type:
            messages_sent += extract_named_count(outcome_notes, "contacted") or extract_count(outcome_notes) or 1
        elif "email sent" in outcome_notes or "email sent" in action_type:
            messages_sent += extract_count(outcome_notes) or 1

        if (
            "follow-up sent" in outcome_notes
            or "followup sent" in outcome_notes
            or "follow-up executed" in outcome_notes
            or "follow-up sent" in action_type
        ):
            followups += extract_count(outcome_notes) or 1
        if any(token in text for token in ["meeting booked", "call booked", "scheduled meeting"]):
            meetings += extract_count(text) or 1
        if outcome_class != "No Response":
            replies += 1
        if outcome_class == "Interested":
            interested += 1
        if outcome_class == "Curious":
            curious += 1
        if outcome_class == "Objection":
            objection += 1
        if outcome_class == "Not Relevant":
            not_relevant += 1

    engagement_rate = round((replies / messages_sent) * 100, 1) if messages_sent else 0.0
    return {
        "messages_sent": messages_sent,
        "followups": followups,
        "meetings": meetings,
        "replies": replies,
        "interested": interested,
        "curious": curious,
        "objection": objection,
        "not_relevant": not_relevant,
        "engagement_rate": engagement_rate,
        "engaged_outcomes": interested + curious + objection,
    }


def extract_count(text: str) -> int | None:
    match = re.search(r"\b(\d{1,4})\s+(?:leads?|contacts?|messages?|emails?|replies?|follow-ups?|meetings?)\b", text)
    return int(match.group(1)) if match else None


def extract_named_count(text: str, name: str) -> int | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*(\d{{1,4}})\b", text)
    return int(match.group(1)) if match else None


def stage(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Stage")) or "New"


def tier(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Tier"))


def segment(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Segment")) or "Unsegmented"


def status(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Status"))


def relation_ids(page: dict[str, Any], name: str) -> list[str]:
    relation = (prop(page, name) or {}).get("relation") or []
    return [item.get("id", "") for item in relation if item.get("id")]


def company_name(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Company")) or plain_text(prop(page, "Name")) or page_title(page)


def contact_name(page: dict[str, Any]) -> str:
    return plain_text(prop(page, "Name")) or page_title(page)


def build_metrics(data: dict[str, list[dict[str, Any]]], today: date) -> dict[str, Any]:
    clients = data["clients"]
    contacts = data["contacts"]
    execution = data["execution"]
    history = data["history"]
    start = today - timedelta(days=6)

    active_clients = [p for p in clients if stage(p).lower() not in {"lost"}]
    contacted_recent = [
        p
        for p in contacts
        if stage(p).lower() == "contacted"
        and (parse_iso_date(plain_text(prop(p, "Last Contact Date"))) or date.min) >= start
    ]
    stage_counts = Counter(stage(p) for p in contacts)
    overdue_tasks = [
        p
        for p in execution
        if (parse_iso_date(plain_text(prop(p, "Due date"))) or date.max) < today
        and status(p).lower() != "done"
    ]

    client_by_id = {p["id"]: p for p in clients}
    contacts_by_client: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for contact in contacts:
        for client_id in relation_ids(contact, "Company"):
            contacts_by_client[client_id].append(contact)

    segment_rows = []
    by_segment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for client in active_clients:
        by_segment[segment(client)].append(client)
    for name in sorted(by_segment):
        rows = by_segment[name]
        segment_stage_counts = Counter(stage(p) for p in rows)
        distribution = ", ".join(f"{key}: {segment_stage_counts[key]}" for key in sorted(segment_stage_counts))
        segment_rows.append(
            [
                name,
                len(rows),
                sum(1 for p in rows if tier(p).upper() == "A"),
                segment_stage_counts.get("Contacted", 0),
                segment_stage_counts.get("Engaged", 0),
                distribution,
            ]
        )

    tier_a_clients = sorted(
        [p for p in active_clients if tier(p).upper() == "A"],
        key=lambda p: plain_text(prop(p, "Next Action Date")) or "9999-12-31",
    )
    priority_rows = []
    for client in tier_a_clients[:15]:
        contacts_for_client = contacts_by_client.get(client["id"], [])
        primary_contact = contacts_for_client[0] if contacts_for_client else None
        blocker = infer_blocker(client, contacts_for_client, today)
        priority_rows.append(
            [
                company_name(client),
                contact_name(primary_contact) if primary_contact else "",
                stage(client),
                plain_text(prop(client, "Last Contact Date")),
                plain_text(prop(client, "Next Action")),
                plain_text(prop(client, "Next Action Date")),
                blocker,
            ]
        )

    velocity = classify_history(history, start, today)
    new_contacts = sum(1 for p in contacts if parse_iso_date(p.get("created_time", "")) and parse_iso_date(p["created_time"]) >= start)
    velocity["new_contacts"] = new_contacts
    contacted_count = len(contacted_recent)
    velocity["reply_rate"] = round((velocity["replies"] / contacted_count) * 100, 1) if contacted_count else 0.0
    velocity["true_engagement_rate"] = (
        round((velocity["engaged_outcomes"] / contacted_count) * 100, 1) if contacted_count else 0.0
    )

    overdue_contact_rows = []
    today_contact_rows = []
    for contact in contacts:
        next_date = parse_iso_date(plain_text(prop(contact, "Next Action Date")))
        if not next_date:
            continue
        row = contact_followup_row(contact, client_by_id)
        if next_date < today:
            overdue_contact_rows.append(row)
        elif next_date == today:
            today_contact_rows.append(row)

    blockers = infer_blockers(clients, contacts, execution, client_by_id, today)

    return {
        "snapshot": {
            "Total Active Pipeline": len(active_clients),
            "Tier A Accounts": sum(1 for p in active_clients if tier(p).upper() == "A"),
            "Contacted (Last 7 Days)": len(contacted_recent),
            "Reply Rate": f"{velocity['reply_rate']}%",
            "Engagement Rate": f"{velocity['true_engagement_rate']}%",
            "Engaged": stage_counts.get("Engaged", 0),
            "Qualified": stage_counts.get("Qualified", 0),
            "Converted": stage_counts.get("Converted", 0),
            "Lost": stage_counts.get("Lost", 0),
            "Overdue Follow-ups": len(overdue_tasks),
        },
        "segment_rows": segment_rows,
        "priority_rows": priority_rows,
        "velocity": velocity,
        "overdue_rows": overdue_contact_rows[:30],
        "today_rows": today_contact_rows[:30],
        "blockers": blockers[:20],
        "meta": {
            "today": today.isoformat(),
            "start": start.isoformat(),
            "clients": len(clients),
            "contacts": len(contacts),
            "execution": len(execution),
            "history": len(history),
            "duplicate_clients": duplicate_client_count(clients),
            "tier_a_missing_next_action": sum(
                1 for p in active_clients if tier(p).upper() == "A" and not plain_text(prop(p, "Next Action"))
            ),
            "contacted_recent": contacted_count,
        },
    }


def duplicate_client_count(clients: list[dict[str, Any]]) -> int:
    names = [company_name(p).strip().lower() for p in clients if company_name(p).strip()]
    return len(names) - len(set(names))


def infer_blocker(client: dict[str, Any], contacts: list[dict[str, Any]], today: date) -> str:
    next_date = parse_iso_date(plain_text(prop(client, "Next Action Date")))
    notes = plain_text(prop(client, "Notes")).lower()
    if next_date and next_date < today:
        return "Overdue next step"
    if not contacts:
        return "No named contact"
    if any(not plain_text(prop(contact, "Email")) and not plain_text(prop(contact, "Phone")) for contact in contacts):
        return "Missing contact data"
    if "no reply" in notes or "if no reply" in plain_text(prop(client, "Next Action")).lower():
        return "Awaiting response"
    return ""


def contact_followup_row(contact: dict[str, Any], client_by_id: dict[str, dict[str, Any]]) -> list[str]:
    client = None
    ids = relation_ids(contact, "Company")
    if ids:
        client = client_by_id.get(ids[0])
    return [
        company_name(client) if client else "",
        contact_name(contact),
        tier(contact),
        stage(contact),
        plain_text(prop(contact, "Next Action")),
        plain_text(prop(contact, "Next Action Date")),
    ]


def infer_blockers(
    clients: list[dict[str, Any]],
    contacts: list[dict[str, Any]],
    execution: list[dict[str, Any]],
    client_by_id: dict[str, dict[str, Any]],
    today: date,
) -> list[list[str]]:
    blockers: list[list[str]] = []
    contacts_by_client: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for contact in contacts:
        for client_id in relation_ids(contact, "Company"):
            contacts_by_client[client_id].append(contact)

    for client in clients:
        if tier(client).upper() == "A" and stage(client).lower() == "new":
            blockers.append([company_name(client), "Tier A idle risk", "Tier A is still New.", "High"])
        next_date = parse_iso_date(plain_text(prop(client, "Next Action Date")))
        if next_date and next_date < today:
            blockers.append([company_name(client), "Overdue next step", "Next Action Date has passed.", "High"])
        related = contacts_by_client.get(client["id"], [])
        if not related:
            blockers.append([company_name(client), "No decision-maker reached", "Account has no linked contact.", "High"])
        elif any(not plain_text(prop(c, "Email")) and not plain_text(prop(c, "Phone")) for c in related):
            blockers.append([company_name(client), "Missing contact data", "At least one linked contact has no email or phone.", "Medium"])

    for task in execution:
        due = parse_iso_date(plain_text(prop(task, "Due date")))
        if due and due < today and status(task).lower() != "done":
            client_ids = relation_ids(task, "Client")
            lead = company_name(client_by_id.get(client_ids[0])) if client_ids and client_ids[0] in client_by_id else page_title(task)
            blockers.append([lead, "No response / overdue follow-up", "Open execution task is overdue.", "High"])
    deduped: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    for row in blockers:
        key = (row[0], row[1])
        if key not in seen:
            deduped.append(row)
            seen.add(key)
    return deduped


def find_dashboard_page() -> str | None:
    payload = {
        "query": DASHBOARD_TITLE,
        "filter": {"value": "page", "property": "object"},
        "page_size": 20,
    }
    data = notion("POST", "search", payload)
    for item in data.get("results", []):
        if page_title(item).strip().lower() == DASHBOARD_TITLE.lower():
            return item["id"]
    return None


def archive_existing_children(page_id: str) -> None:
    cursor: str | None = None
    while True:
        path = f"blocks/{page_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        data = notion("GET", path)
        for block in data.get("results", []):
            notion("PATCH", f"blocks/{block['id']}", {"archived": True})
        if not data.get("has_more"):
            return
        cursor = data.get("next_cursor")


def create_or_replace_page() -> str:
    existing = find_dashboard_page()
    if existing:
        notion(
            "PATCH",
            f"pages/{existing}",
            {"archived": False, "is_locked": False, "properties": title_properties(DASHBOARD_TITLE)},
        )
        archive_existing_children(existing)
        return existing
    page = notion(
        "POST",
        "pages",
        {
            "parent": {"page_id": PARENT_PAGE_ID},
            "properties": title_properties(DASHBOARD_TITLE),
        },
    )
    return page["id"]


def title_properties(title: str) -> dict[str, Any]:
    return {"title": {"title": [{"type": "text", "text": {"content": title}}]}}


def append_blocks(page_id: str, blocks: list[dict[str, Any]]) -> None:
    for index in range(0, len(blocks), 80):
        notion("PATCH", f"blocks/{page_id}/children", {"children": blocks[index : index + 80]})


def build_blocks(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot = metrics["snapshot"]
    velocity = metrics["velocity"]
    today = metrics["meta"]["today"]
    start = metrics["meta"]["start"]

    blocks: list[dict[str, Any]] = [
        paragraph(
            f"Board-facing command layer generated from live CRM data on {today}. "
            "CRM remains the execution system; this page translates it into momentum, leakage, blockers, and next moves."
        ),
        divider(),
        heading(1, "1. Pipeline Snapshot"),
        table_block([["Metric", "Value"]] + [[key, value] for key, value in snapshot.items()]),
        paragraph("Read: account totals come from Clients; stage movement comes from Contacts; overdue follow-ups come from Active Work."),
        heading(1, "2. Segment Breakdown"),
        table_block(
            [["Segment", "Total Leads", "Tier A Count", "Contacted", "Engaged", "Stage Distribution"]]
            + metrics["segment_rows"]
        ),
        heading(1, "3. Tier A Priority Accounts"),
        table_block(
            [["Company", "Primary Contact", "Stage", "Last Contact", "Next Step", "Next Action Date", "Blocker"]]
            + metrics["priority_rows"]
        ),
        paragraph("Limit applied: top 15 Tier A accounts sorted by earliest Next Action Date."),
        heading(1, "4. Outreach Velocity (Last 7 Days)"),
        table_block(
            [
                ["Metric", "Value"],
                ["Messages Sent", velocity["messages_sent"]],
                ["New Contacts Added", velocity["new_contacts"]],
                ["Follow-ups Executed", velocity["followups"]],
                ["Meetings Booked", velocity["meetings"]],
            ]
        ),
        paragraph(f"Window: {start} to {today}. New contacts reflect records added to the CRM, not necessarily newly sourced relationships."),
        heading(1, "5. Engagement Signals"),
        table_block(
            [
                ["Signal", "Value"],
                ["Replies Received", velocity["replies"]],
                ["Interested", velocity["interested"]],
                ["Curious", velocity["curious"]],
                ["Objection", velocity["objection"]],
                ["Not Relevant", velocity["not_relevant"]],
                ["Reply Rate %", velocity["reply_rate"]],
                ["Engagement Rate %", velocity["true_engagement_rate"]],
            ]
        ),
        paragraph("Classification now comes from the Execution History Outcome enum: Interested, Curious, Objection, Not Relevant, No Response."),
        heading(1, "6. Follow-ups Due"),
        heading(2, "A. Overdue"),
        table_block([["Company", "Contact", "Tier", "Stage", "Next Step", "Next Action Date"]] + safe_rows(metrics["overdue_rows"])),
        heading(2, "B. Due Today"),
        table_block([["Company", "Contact", "Tier", "Stage", "Next Step", "Next Action Date"]] + safe_rows(metrics["today_rows"])),
        heading(1, "7. Blockers"),
        table_block([["Lead", "Issue Type", "Description", "Impact"]] + safe_rows(metrics["blockers"])),
        heading(1, "8. What We Are Learning"),
        table_block(
            [
                ["Question", "Current Signal"],
                [
                    "Messaging that is failing",
                    "High contacted volume with zero classified replies means current outreach is not provoking a wrong-decision memory.",
                ],
                [
                    "Segments not responding",
                    "CA, Corporate, Doctors, and Platforms have contact activity but no validated engagement yet.",
                ],
                [
                    "Hypothesis",
                    "The copy is explaining Fnomo too early instead of making the prospect reflect on a costly decision that looked informed but was not validated.",
                ],
                [
                    "What changes now",
                    "Tier A follow-ups must open with past wrong decision, regret/loss trigger, and validation gap. No new volume until reply signal moves.",
                ],
            ]
        ),
        heading(1, "9. Next 7 Days (Execution Plan)"),
        table_block(
            [
                ["Field", "Board Narrative"],
                ["Priority Segment", "Tier A only across CA Firms, Platform Partnerships, Corporates, and Doctors. Do not expand pipeline."],
                ["Tier A Focus", "Force first engagement from contacted Tier A accounts; move New Tier A only after overdue follow-ups are clean."],
                [
                    "Execution Plan",
                    "1. Send Follow-up 1 where 48h elapsed. 2. Send Follow-up 2 where 4 days elapsed. 3. Escalate by call/alternate channel after 7 days. 4. Classify every reply by Outcome enum.",
                ],
                [
                    "Experiments",
                    "Replace informative copy with reflection-trigger copy: last wrong decision, regret/loss, and missing validation step.",
                ],
                [
                    "Expected Outcome",
                    "First measurable reply signal; Reply Rate and Engagement Rate must move above 0 before adding more lead volume.",
                ],
            ]
        ),
        divider(),
        heading(2, "Data Rules"),
        bulleted("Dashboard is a read layer. Clients, Contacts, Active Work, and Execution History remain the only operating databases."),
        bulleted("No duplicate Client records were created by this build."),
        bulleted("Manual sections: What We Are Learning and Next 7 Days narrative. Numeric sections are generated from CRM data at build time."),
    ]
    return blocks


def safe_rows(rows: list[list[Any]]) -> list[list[Any]]:
    return rows if rows else [["-", "-", "-", "-", "-", "-"]]


def validate(metrics: dict[str, Any]) -> dict[str, Any]:
    meta = metrics["meta"]
    return {
        "duplicate_clients": meta["duplicate_clients"],
        "tier_a_missing_next_action": meta["tier_a_missing_next_action"],
        "overdue_followups": metrics["snapshot"]["Overdue Follow-ups"],
        "source_counts": {
            "clients": meta["clients"],
            "contacts": meta["contacts"],
            "execution": meta["execution"],
            "history": meta["history"],
        },
    }


def main() -> None:
    today_value = date.fromisoformat(os.environ.get("FNOMO_OPERATING_DATE", date.today().isoformat()))
    data = extract_rows()
    metrics = build_metrics(data, today_value)
    page_id = create_or_replace_page()
    append_blocks(page_id, build_blocks(metrics))
    notion("PATCH", f"pages/{page_id}", {"is_locked": True})

    output = {
        "page_id": page_id,
        "url": f"https://www.notion.so/{page_id.replace('-', '')}",
        "snapshot": metrics["snapshot"],
        "segment_rows": metrics["segment_rows"],
        "velocity": metrics["velocity"],
        "validation": validate(metrics),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
