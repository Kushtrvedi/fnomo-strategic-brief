#!/usr/bin/env python3
"""
Convert the Fnomo Notion CRM from flat lead rows into a relational sales system.

Source of truth remains FNOMO_MASTER_PIPELINE. Notion becomes:
- Clients: one account per company
- Contacts: one person per account
- Execution: one current next-action task per contact/account
- Deals: untouched unless qualified monetary opportunities exist
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from sync_fnomo_notion import DEFAULT_WORKBOOK, canonical_leads, compact, parse_date


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "fnomo_notion_backend.json"
NOTION_VERSION = "2022-06-28"
SESSION = requests.Session()
CLIENTS_SCHEMA: dict[str, Any] = {}
TASKS_SCHEMA: dict[str, Any] = {}


CLIENTS_DB = "e8a8aa3c-b995-8368-8495-014b8ea295c3"
TASKS_DB = "6fb8aa3c-b995-82ec-806b-01b6cd1b2915"
DEALS_DB = "0be8aa3c-b995-822e-8a79-81e2d86e3f8b"
LEGACY_FLAT_LEADS_DB = "3548aa3c-b995-81dd-a33c-e48c87e3a007"
HISTORY_DB = "3548aa3c-b995-818a-8ede-ed9a5d99aac3"
PARENT_PAGE = "5818aa3c-b995-827e-af29-011d0732f5bc"


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
    response = SESSION.request(
        method,
        f"https://api.notion.com/v1/{path.lstrip('/')}",
        headers=headers(),
        json=payload,
        timeout=45,
    )
    if response.status_code == 429:
        time.sleep(2)
        return notion(method, path, payload)
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path} failed {response.status_code}: {response.text[:1000]}")
    return response.json()


def update_database(database_id: str, title: str | None = None, properties: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {}
    if title:
        payload["title"] = [{"type": "text", "text": {"content": title}}]
    if properties:
        payload["properties"] = properties
    if payload:
        notion("PATCH", f"databases/{database_id}", payload)


def get_database(database_id: str) -> dict[str, Any]:
    return notion("GET", f"databases/{database_id}")


def title_property(database: dict[str, Any]) -> str:
    for name, prop in database.get("properties", {}).items():
        if prop.get("type") == "title":
            return name
    die("Database has no title property.")


def plain(page: dict[str, Any], prop_name: str) -> str:
    prop = page.get("properties", {}).get(prop_name, {})
    prop_type = prop.get("type")
    if prop_type in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in prop.get(prop_type, [])).strip()
    if prop_type == "select":
        return (prop.get("select") or {}).get("name", "").strip()
    if prop_type == "status":
        return (prop.get("status") or {}).get("name", "").strip()
    if prop_type == "date":
        return ((prop.get("date") or {}).get("start") or "").strip()
    if prop_type == "email":
        return (prop.get("email") or "").strip()
    if prop_type == "phone_number":
        return (prop.get("phone_number") or "").strip()
    return ""


def all_pages(database_id: str) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    cursor = None
    while True:
        payload: dict[str, Any] = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        data = notion("POST", f"databases/{database_id}/query", payload)
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            return pages
        cursor = data.get("next_cursor")


def title_text(value: Any) -> dict[str, Any]:
    text = compact(value)[:200] or "Untitled"
    return {"title": [{"type": "text", "text": {"content": text}}]}


def rich_text(value: Any) -> dict[str, Any]:
    text = compact(value)[:1900]
    return {"rich_text": [{"type": "text", "text": {"content": text}}]} if text else {"rich_text": []}


def select_value(value: Any) -> dict[str, Any]:
    text = compact(value)[:100]
    return {"select": {"name": text}} if text else {"select": None}


def status_value(value: Any) -> dict[str, Any]:
    text = compact(value)[:100]
    return {"status": {"name": text}} if text else {"status": None}


def date_value(value: Any) -> dict[str, Any]:
    parsed = parse_date(value)
    return {"date": {"start": parsed}} if parsed else {"date": None}


def relation_value(page_id: str | None) -> dict[str, Any]:
    return {"relation": [{"id": page_id}]} if page_id else {"relation": []}


def norm(value: Any) -> str:
    return " ".join(compact(value).casefold().split())


def company_key(company: str) -> str:
    return norm(company)


def contact_key(name: str, company: str) -> str:
    return f"{norm(name)}::{norm(company)}"


def stage_rank(stage: str) -> int:
    order = {"New": 0, "Contacted": 1, "Engaged": 2, "Qualified": 3, "Converted": 4, "Lost": -1}
    return order.get(compact(stage), 0)


def max_stage(leads: list[dict[str, Any]]) -> str:
    return max((lead["stage"] for lead in leads if lead["stage"]), key=stage_rank, default="New")


def min_next_date(leads: list[dict[str, Any]]) -> str | None:
    dates = [lead["next_action_date"] for lead in leads if lead.get("next_action_date")]
    return min(dates) if dates else None


def max_last_contact(leads: list[dict[str, Any]]) -> str | None:
    dates = [lead["last_contact_date"] for lead in leads if lead.get("last_contact_date")]
    return max(dates) if dates else None


def account_notes(leads: list[dict[str, Any]]) -> str:
    snippets = []
    for lead in leads[:8]:
        who = lead["name"] or "Account-level"
        note = lead["notes"] or lead["next_action"]
        if note:
            snippets.append(f"{who}: {note[:240]}")
    return "\n".join(snippets)


def tier_to_priority(tier: str) -> str:
    return {"A": "High", "B": "Medium", "C": "Low"}.get(compact(tier).upper(), "Medium")


def stage_to_client_status(stage: str) -> str:
    if stage == "New":
        return "Lead"
    if stage in {"Contacted", "Engaged", "Qualified"}:
        return "Active"
    if stage == "Converted":
        return "Complete"
    if stage == "Lost":
        return "Churned"
    return "Lead"


def infer_role(lead: dict[str, Any]) -> str:
    text = lead.get("notes", "")
    match = re.search(r"(?:Role|Title):\s*([^|;\n]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()[:200]
    return compact(lead.get("lead_type", ""))


def infer_email(lead: dict[str, Any]) -> str:
    text = lead.get("notes", "")
    match = re.search(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def infer_phone(lead: dict[str, Any]) -> str:
    text = lead.get("notes", "")
    match = re.search(r"(?:Mobile|Phone|Contact):\s*([+\d][+\d\s().-]{7,})", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def infer_linkedin(lead: dict[str, Any]) -> str:
    text = lead.get("notes", "")
    match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s|]+", text, re.IGNORECASE)
    if not match:
        return ""
    value = match.group(0)
    return value if value.startswith("http") else f"https://{value}"


def ensure_clients_schema() -> str:
    db = get_database(CLIENTS_DB)
    title = title_property(db)
    props = db.get("properties", {})
    missing: dict[str, Any] = {}
    for name, spec in {
        "Stage": {"select": {}},
        "Next Action": {"rich_text": {}},
        "Next Action Date": {"date": {}},
        "Last Contact Date": {"date": {}},
        "Notes": {"rich_text": {}},
        "Channel": {"rich_text": {}},
        "Tier": {"select": {}},
    }.items():
        if name not in props:
            missing[name] = spec
    update_database(CLIENTS_DB, "Clients", missing)
    return title


def ensure_contacts_database() -> str:
    for block in all_child_blocks(PARENT_PAGE):
        if block.get("type") == "child_database" and block.get("child_database", {}).get("title") == "Contacts":
            return block["id"]
    payload = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE},
        "title": [{"type": "text", "text": {"content": "Contacts"}}],
        "properties": {
            "Name": {"title": {}},
            "Company": {"relation": {"database_id": CLIENTS_DB, "type": "single_property", "single_property": {}}},
            "Role": {"rich_text": {}},
            "LinkedIn": {"url": {}},
            "Email": {"email": {}},
            "Phone": {"phone_number": {}},
            "Stage": {"select": {}},
            "Last Contact Date": {"date": {}},
            "Next Action": {"rich_text": {}},
            "Next Action Date": {"date": {}},
            "Channel": {"rich_text": {}},
            "Tier": {"select": {}},
            "Notes": {"rich_text": {}},
        },
    }
    return notion("POST", "databases", payload)["id"]


def all_child_blocks(block_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    cursor = None
    while True:
        path = f"blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        data = notion("GET", path)
        children.extend(data.get("results", []))
        if not data.get("has_more"):
            return children
        cursor = data.get("next_cursor")


def ensure_execution_schema() -> str:
    db = get_database(TASKS_DB)
    title = title_property(db)
    props = db.get("properties", {})
    missing: dict[str, Any] = {}
    for name, spec in {
        "Contact": {"relation": {"database_id": ensure_contacts_database(), "type": "single_property", "single_property": {}}},
        "Stage Context": {"select": {}},
        "Client": {"relation": {"database_id": CLIENTS_DB, "type": "single_property", "single_property": {}}},
    }.items():
        if name not in props:
            missing[name] = spec
    update_database(TASKS_DB, "Execution", missing)
    return title


def build_client_props(title_prop: str, company: str, leads: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    stage = max_stage(leads)
    tier = "A" if any(lead["tier"].upper() == "A" for lead in leads) else ("B" if any(lead["tier"].upper() == "B" for lead in leads) else "C")
    next_action = next((lead["next_action"] for lead in sorted(leads, key=lambda x: x.get("next_action_date") or "9999") if lead.get("next_action")), "")
    props = {
        title_prop: title_text(company),
        "Status": status_value(stage_to_client_status(stage)),
        "Stage": select_value(stage),
        "Next Action": rich_text(next_action),
        "Next Action Date": date_value(min_next_date(leads)),
        "Last Contact Date": date_value(max_last_contact(leads)),
        "Notes": rich_text(account_notes(leads)),
        "Channel": rich_text("Sheet sync"),
        "Tier": select_value(tier),
        "Priority": select_value(tier_to_priority(tier)),
        "Last action": date_value(max_last_contact(leads)),
        "Next action": date_value(min_next_date(leads)),
        "Source": select_value("Other"),
    }
    return {k: v for k, v in props.items() if k in schema}


def upsert_clients(leads: list[dict[str, Any]]) -> tuple[dict[str, str], int, int, int]:
    title_prop = ensure_clients_schema()
    schema = get_database(CLIENTS_DB).get("properties", {})
    pages = all_pages(CLIENTS_DB)
    by_company = {
        company_key(plain(page, title_prop)): page["id"]
        for page in pages
        if plain(page, title_prop) and not plain(page, "Sync Key") and not plain(page, "Lead ID")
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    original_company: dict[str, str] = {}
    for lead in leads:
        key = company_key(lead["company"])
        grouped[key].append(lead)
        original_company[key] = lead["company"]
    created = updated = 0
    client_pages: dict[str, str] = {}
    for key, rows in grouped.items():
        company = original_company[key]
        props = build_client_props(title_prop, company, rows, schema)
        if key in by_company:
            notion("PATCH", f"pages/{by_company[key]}", {"properties": props})
            client_pages[key] = by_company[key]
            updated += 1
        else:
            page = notion("POST", "pages", {"parent": {"database_id": CLIENTS_DB}, "properties": props})
            client_pages[key] = page["id"]
            created += 1
    merged = len(leads) - len(grouped)
    return client_pages, created, updated, merged


def contact_props(lead: dict[str, Any], client_id: str) -> dict[str, Any]:
    return {
        "Name": title_text(lead["name"]),
        "Company": relation_value(client_id),
        "Role": rich_text(infer_role(lead)),
        "LinkedIn": {"url": infer_linkedin(lead) or None},
        "Email": {"email": infer_email(lead) or None},
        "Phone": {"phone_number": infer_phone(lead) or None},
        "Stage": select_value(lead["stage"] or "New"),
        "Last Contact Date": date_value(lead["last_contact_date"]),
        "Next Action": rich_text(lead["next_action"]),
        "Next Action Date": date_value(lead["next_action_date"]),
        "Channel": rich_text("Sheet sync"),
        "Tier": select_value(lead["tier"]),
        "Notes": rich_text(lead["notes"]),
    }


def upsert_contacts(leads: list[dict[str, Any]], client_pages: dict[str, str]) -> tuple[str, dict[str, str], int, int, int]:
    contacts_db = ensure_contacts_database()
    existing = {}
    for page in all_pages(contacts_db):
        name = plain(page, "Name")
        rel = page.get("properties", {}).get("Company", {}).get("relation", [])
        company_id = rel[0]["id"] if rel else ""
        existing[f"{norm(name)}::{company_id}"] = page["id"]
    contact_pages: dict[str, str] = {}
    created = updated = skipped = 0
    for lead in leads:
        if not lead["name"]:
            skipped += 1
            continue
        client_id = client_pages[company_key(lead["company"])]
        key = f"{norm(lead['name'])}::{client_id}"
        props = contact_props(lead, client_id)
        if key in existing:
            notion("PATCH", f"pages/{existing[key]}", {"properties": props})
            contact_pages[contact_key(lead["name"], lead["company"])] = existing[key]
            updated += 1
        else:
            page = notion("POST", "pages", {"parent": {"database_id": contacts_db}, "properties": props})
            existing[key] = page["id"]
            contact_pages[contact_key(lead["name"], lead["company"])] = page["id"]
            created += 1
    return contacts_db, contact_pages, created, updated, skipped


def task_type(action: str, stage: str) -> str:
    text = compact(action).casefold()
    if "call" in text or "escalate" in text:
        return "Call"
    if "follow" in text or compact(stage) == "Contacted":
        return "Follow-Up"
    return "Outreach"


def task_name(lead: dict[str, Any]) -> str:
    action_type = task_type(lead["next_action"], lead["stage"])
    name = lead["name"] or "account owner"
    return f"{action_type} with {name} ({lead['company']})"


def task_props(lead: dict[str, Any], client_id: str, contact_id: str | None, title_prop: str, schema: dict[str, Any]) -> dict[str, Any]:
    props = {
        title_prop: title_text(task_name(lead)),
        "Client": relation_value(client_id),
        "Contact": relation_value(contact_id),
        "Type": select_value(task_type(lead["next_action"], lead["stage"])),
        "Due date": date_value(lead["next_action_date"]),
        "Status": status_value("To Do"),
        "Priority": select_value(tier_to_priority(lead["tier"])),
        "Stage Context": select_value(lead["stage"]),
        "Additional Information": rich_text(lead["next_action"]),
    }
    return {k: v for k, v in props.items() if k in schema}


def archive_old_fnomo_tasks() -> int:
    archived = 0
    for page in all_pages(TASKS_DB):
        if plain(page, "Sync Key") or plain(page, "Lead Name"):
            notion("PATCH", f"pages/{page['id']}", {"archived": True})
            archived += 1
    return archived


def upsert_execution(leads: list[dict[str, Any]], client_pages: dict[str, str], contact_pages: dict[str, str]) -> tuple[int, int, int]:
    title_prop = ensure_execution_schema()
    schema = get_database(TASKS_DB).get("properties", {})
    archived = archive_old_fnomo_tasks()
    existing = {}
    for page in all_pages(TASKS_DB):
        task_title = plain(page, title_prop)
        existing[norm(task_title)] = page["id"]
    created = updated = 0
    for lead in leads:
        if not lead.get("next_action") or not lead.get("next_action_date"):
            continue
        client_id = client_pages[company_key(lead["company"])]
        contact_id = contact_pages.get(contact_key(lead["name"], lead["company"])) if lead["name"] else None
        if not contact_id:
            continue
        props = task_props(lead, client_id, contact_id, title_prop, schema)
        key = norm(task_name(lead))
        if key in existing:
            notion("PATCH", f"pages/{existing[key]}", {"properties": props})
            updated += 1
        else:
            page = notion("POST", "pages", {"parent": {"database_id": TASKS_DB}, "properties": props})
            existing[key] = page["id"]
            created += 1
    return created, updated, archived


def archive_flat_lead_storage() -> int:
    archived = 0
    for page in all_pages(CLIENTS_DB):
        if plain(page, "Sync Key") or plain(page, "Lead ID"):
            notion("PATCH", f"pages/{page['id']}", {"archived": True})
            archived += 1
    try:
        notion("PATCH", f"blocks/{LEGACY_FLAT_LEADS_DB}", {"archived": True})
        archived += 1
    except RuntimeError:
        pass
    return archived


def clean_visible_fields() -> list[str]:
    removed = []
    for db in (CLIENTS_DB, TASKS_DB):
        properties = get_database(db).get("properties", {})
        drops = {}
        for name in ("Row Hash", "Sync Key"):
            if name in properties:
                drops[name] = None
        if drops:
            try:
                update_database(db, properties=drops)
                removed.extend([f"{db}:{name}" for name in drops])
            except RuntimeError:
                pass
    return removed


def validation(leads: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "missing_stage": sum(1 for lead in leads if not lead.get("stage")),
        "missing_next_action": sum(1 for lead in leads if not lead.get("next_action")),
        "missing_next_action_date": sum(1 for lead in leads if not lead.get("next_action_date")),
        "missing_last_contact_for_contacted": sum(1 for lead in leads if lead.get("stage") == "Contacted" and not lead.get("last_contact_date")),
        "tier_a_new": sum(1 for lead in leads if lead.get("tier", "").upper() == "A" and lead.get("stage") == "New"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", default=str(DEFAULT_WORKBOOK))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    leads = canonical_leads(Path(args.workbook))
    company_count = len({company_key(lead["company"]) for lead in leads})
    contact_count = sum(1 for lead in leads if lead["name"])
    print(f"Sheet rows: {len(leads)}")
    print(f"Unique client accounts: {company_count}")
    print(f"Contact rows with person name: {contact_count}")
    print(f"Account-only rows without person: {len(leads) - contact_count}")
    print(f"Validation: {json.dumps(validation(leads), sort_keys=True)}")
    if args.dry_run:
        return 0

    client_pages, clients_created, clients_updated, merged_count = upsert_clients(leads)
    contacts_db, contact_pages, contacts_created, contacts_updated, skipped_contacts = upsert_contacts(leads, client_pages)
    tasks_created, tasks_updated, tasks_archived = upsert_execution(leads, client_pages, contact_pages)
    flat_archived = archive_flat_lead_storage()
    removed_fields = clean_visible_fields()

    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config.update(
        {
            "parent_page_id": PARENT_PAGE,
            "clients_database_id": CLIENTS_DB,
            "contacts_database_id": contacts_db,
            "execution_tasks_database_id": TASKS_DB,
            "deals_database_id": DEALS_DB,
            "legacy_flat_leads_database_id": LEGACY_FLAT_LEADS_DB,
            "source_of_truth": "FNOMO_MASTER_PIPELINE",
            "notion_role": "structured_visibility_layer",
            "relational_restructure_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")

    print(f"Clients created: {clients_created}, updated: {clients_updated}, merged lead rows into accounts: {merged_count}")
    print(f"Contacts created: {contacts_created}, updated: {contacts_updated}, skipped account-only rows: {skipped_contacts}")
    print(f"Execution tasks created: {tasks_created}, updated: {tasks_updated}, archived old mechanical tasks: {tasks_archived}")
    print(f"Flat lead storage archived: {flat_archived}")
    print(f"Visible internal fields removed where API allowed: {len(removed_fields)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
