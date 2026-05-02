#!/usr/bin/env python3
"""
Apply the Founder Circle Activation Playbook as a CRM automation layer.

The CRM structure remains frozen. This adds founder activation fields,
tasks, dashboard content, workbook tracking, and outreach assets.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from shutil import copy2
from typing import Any

import requests
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "EXCEL" / "War Room_ Community Outreach Pipeline - FNOMO Master.xlsx"
PARENT_PAGE_ID = "5818aa3c-b995-827e-af29-011d0732f5bc"
CLIENTS_DB = "e8a8aa3c-b995-8368-8495-014b8ea295c3"
CONTACTS_DB = "3548aa3c-b995-8148-a653-fead444e56fe"
EXECUTION_DB = "6fb8aa3c-b995-82ec-806b-01b6cd1b2915"
HISTORY_DB = "3548aa3c-b995-818a-8ede-ed9a5d99aac3"
NOTION_VERSION = "2022-06-28"
PAGE_TITLE = "Founder Circle Activation Dashboard"

SESSION = requests.Session()

ARCHETYPE_CONFIG: dict[str, dict[str, Any]] = {
    "Mega Connector": {
        "cohort_target": "15-20%",
        "engine": "Public authority engine",
        "motivation": "Authority, visibility, being early in something valuable",
        "network": "Large weak-tie network across founders, investors and operators",
        "advocacy": "Public opinion-led posting and inbound conversations",
        "channel": "LinkedIn",
        "day1": "Ask founder to share one thought: why most investors make mistakes despite good information.",
        "day2": "Give LinkedIn post template: mistakes feel informed because inputs are not the same as decision validation.",
        "day4": "Ask founder to publish post and reply to comments with the decision-validation frame.",
        "day6": "Ask founder to DM 2-3 engaged commenters and open founder conversations.",
        "metrics": "Post published, 20+ comments, 3 inbound conversations, 2 sales by Day 14",
        "recognition": "Public leaderboard, LinkedIn shoutouts, Top Founder Voice tag",
    },
    "Trusted Advisor": {
        "cohort_target": "30-35%",
        "engine": "Relationship conversion engine",
        "motivation": "Client outcomes, credibility protection, professional edge",
        "network": "Small deep network of 20-200 high-trust relationships",
        "advocacy": "1:1 conversations, referrals and private groups",
        "channel": "Calls / 1:1 advice",
        "day1": "Ask: Which client recently made a decision that did not work?",
        "day2": "Give 1:1 script: Before you act on this, have you validated the decision?",
        "day4": "Ask advisor to use the validation prompt with 3 clients.",
        "day6": "Ask advisor to introduce Fnomo to 2 relevant clients.",
        "metrics": "3 client conversations, 2 intros, 1 conversion by Day 7, 3 conversions by Day 14",
        "recognition": "Private recognition, direct access to team, case-study feature",
    },
    "Operator Investor": {
        "cohort_target": "25-30%",
        "engine": "Private referral engine",
        "motivation": "Decision quality, avoiding mistakes, control",
        "network": "Closed high-value network of 5-20 strong relationships",
        "advocacy": "Private recommendations and WhatsApp conversations",
        "channel": "WhatsApp",
        "day1": "Ask: What decision are you evaluating this week?",
        "day2": "Ask founder to use Fnomo personally on the current decision.",
        "day4": "Give WhatsApp share: I have started validating decisions before investing - makes a difference.",
        "day6": "Ask founder to share privately with 2-3 peers.",
        "metrics": "1 usage, 2 shares, 1 referral by Day 7, 3 referrals by Day 14",
        "recognition": "Exclusive group access, silent recognition, priority decision support",
    },
    "Content Amplifier": {
        "cohort_target": "20%",
        "engine": "Narrative trust engine",
        "motivation": "Audience growth, content differentiation, thought leadership",
        "network": "Medium-reach engaged audience",
        "advocacy": "Content creation, explainers and storytelling",
        "channel": "Video / content",
        "day1": "Ask: What is the biggest mistake investors make?",
        "day2": "Give video script: Most investors think they need better stock ideas, but the real problem is not validating decisions before acting.",
        "day4": "Ask founder to create 1 reel or video.",
        "day6": "Ask founder to post and engage comments for founder conversations.",
        "metrics": "1 content piece, 1k+ views, 5 DMs by Day 7, 2 conversions by Day 14",
        "recognition": "Featured posts, co-branded content, audience growth support",
    },
}


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
    if prop_type == "multi_select":
        return "; ".join(item.get("name", "") for item in prop.get("multi_select", []))
    if prop_type == "number":
        value = prop.get("number")
        return "" if value is None else str(value)
    if prop_type == "checkbox":
        return "Yes" if prop.get("checkbox") else "No"
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


def checkbox(value: bool) -> dict[str, Any]:
    return {"checkbox": value}


def number(value: int) -> dict[str, Any]:
    return {"number": value}


def multi_select(existing_prop: dict[str, Any] | None, tags: list[str]) -> dict[str, Any]:
    existing: list[str] = []
    if existing_prop and existing_prop.get("type") == "multi_select":
        existing = [item["name"] for item in existing_prop.get("multi_select", []) if item.get("name")]
    for tag in tags:
        if tag not in existing:
            existing.append(tag)
    return {"multi_select": [{"name": tag} for tag in existing]}


def has_tag(page: dict[str, Any], tag: str) -> bool:
    return tag in plain_text(prop(page, "Tags"))


def ensure_contact_fields() -> None:
    properties = {
        "Founder Activation": {"checkbox": {}},
        "Validation Used": {"checkbox": {}},
        "Testimonial Captured": {"checkbox": {}},
        "Referrals Count": {"number": {"format": "number"}},
        "Advocacy Score": {"number": {"format": "number"}},
        "Advocacy Status": {
            "select": {
                "options": [
                    {"name": "Inactive", "color": "red"},
                    {"name": "Engaged", "color": "yellow"},
                    {"name": "Advocate", "color": "green"},
                ]
            }
        },
        "Activation Day": {"select": {"options": [{"name": f"Day {index}", "color": "blue"} for index in [1, 2, 4, 6, 10, 15, 22, 30]]}},
        "Founder Archetype": {
            "select": {
                "options": [
                    {"name": "Mega Connector", "color": "purple"},
                    {"name": "Trusted Advisor", "color": "green"},
                    {"name": "Operator Investor", "color": "orange"},
                    {"name": "Content Amplifier", "color": "pink"},
                    {"name": "Hybrid", "color": "gray"},
                ]
            }
        },
        "Secondary Archetype": {
            "select": {
                "options": [
                    {"name": "Mega Connector", "color": "purple"},
                    {"name": "Trusted Advisor", "color": "green"},
                    {"name": "Operator Investor", "color": "orange"},
                    {"name": "Content Amplifier", "color": "pink"},
                ]
            }
        },
        "Archetype Confidence": {"number": {"format": "percent"}},
        "Influence Channel": {
            "select": {
                "options": [
                    {"name": "LinkedIn", "color": "blue"},
                    {"name": "Calls / 1:1 advice", "color": "green"},
                    {"name": "WhatsApp", "color": "orange"},
                    {"name": "Video / content", "color": "pink"},
                    {"name": "Hybrid", "color": "gray"},
                ]
            }
        },
        "Archetype Evidence": {"rich_text": {}},
    }
    notion("PATCH", f"databases/{CONTACTS_DB}", {"properties": properties})


def score_contact(contact: dict[str, Any]) -> tuple[int, str]:
    score = 0
    if prop(contact, "Founder Activation") and prop(contact, "Founder Activation").get("checkbox"):
        score += 1
    if prop(contact, "Validation Used") and prop(contact, "Validation Used").get("checkbox"):
        score += 1
    if prop(contact, "Testimonial Captured") and prop(contact, "Testimonial Captured").get("checkbox"):
        score += 1
    try:
        referrals = int(float(plain_text(prop(contact, "Referrals Count")) or 0))
    except ValueError:
        referrals = 0
    if referrals >= 1:
        score += 1
    if referrals >= 3:
        score += 1
    if score <= 1:
        return score, "Inactive"
    if score <= 3:
        return score, "Engaged"
    return score, "Advocate"


def infer_archetype(contact: dict[str, Any], client: dict[str, Any] | None = None) -> tuple[str, str | None, float, str]:
    evidence_parts: list[str] = []
    segment = plain_text(prop(contact, "Segment")) or (plain_text(prop(client, "Segment")) if client else "")
    role = plain_text(prop(contact, "Role")) or plain_text(prop(contact, "Title"))
    company = page_name(client) if client else ""
    text_blob = " ".join([segment, role, company, title_of(contact)]).lower()
    if segment:
        evidence_parts.append(f"segment={segment}")
    if role:
        evidence_parts.append(f"role={role}")

    if any(word in text_blob for word in ["creator", "content", "influencer", "media", "youtube", "newsletter"]):
        return "Content Amplifier", "Mega Connector", 0.75, "; ".join(evidence_parts + ["content signal detected"])
    if any(word in text_blob for word in ["platform", "zomato", "blinkit", "swiggy", "practo", "mygate", "housing", "internshala", "collegedunia", "nobroker"]):
        return "Mega Connector", "Content Amplifier", 0.65, "; ".join(evidence_parts + ["platform/network leverage inferred"])
    if any(word in text_blob for word in ["ca ", "chartered", "advisor", "consultant", "association", "tax"]):
        return "Trusted Advisor", "Operator Investor", 0.70, "; ".join(evidence_parts + ["advisor/trust network inferred"])
    if any(word in text_blob for word in ["doctor", "healthcare", "hospital", "clinic"]):
        return "Operator Investor", "Trusted Advisor", 0.60, "; ".join(evidence_parts + ["closed high-trust HNI network inferred"])
    if any(word in text_blob for word in ["business", "corporate", "owner", "founder", "ceo", "director", "partner", "proprietor"]):
        return "Operator Investor", "Trusted Advisor", 0.65, "; ".join(evidence_parts + ["operator/capital decision-maker inferred"])
    return "Hybrid", None, 0.40, "; ".join(evidence_parts + ["screening questions required"])


def activation_next_action(contact: dict[str, Any], archetype: str) -> tuple[str, str]:
    config = ARCHETYPE_CONFIG.get(archetype, ARCHETYPE_CONFIG["Operator Investor"])
    if not prop(contact, "Founder Activation") or not prop(contact, "Founder Activation").get("checkbox"):
        return "Day 1", config["day1"]
    if not prop(contact, "Validation Used") or not prop(contact, "Validation Used").get("checkbox"):
        return "Day 2", config["day2"]
    if not prop(contact, "Testimonial Captured") or not prop(contact, "Testimonial Captured").get("checkbox"):
        return "Day 4", config["day4"]
    try:
        referrals = int(float(plain_text(prop(contact, "Referrals Count")) or 0))
    except ValueError:
        referrals = 0
    if referrals < 1:
        return "Day 6", config["day6"]
    if referrals < 3:
        return "Day 30", "Ask for two more high-quality referrals and one decision case."
    return "Day 30", "Recognize as advocate and request one story or public insight."


def apply_notion(today: date) -> dict[str, Any]:
    ensure_contact_fields()
    contacts = query_database(CONTACTS_DB)
    clients = query_database(CLIENTS_DB)
    client_by_id = {client["id"]: client for client in clients}
    counts: Counter = Counter()
    status_counts: Counter = Counter()
    archetype_counts: Counter = Counter()

    for contact in contacts:
        if not has_tag(contact, "Founder Circle Candidate"):
            continue
        score, status = score_contact(contact)
        client_ids = relation_ids(contact, "Company")
        client = client_by_id.get(client_ids[0]) if client_ids else None
        archetype, secondary, confidence, evidence = infer_archetype(contact, client)
        day, action = activation_next_action(contact, archetype)
        archetype_counts[archetype] += 1
        archetype_config = ARCHETYPE_CONFIG.get(archetype, {})
        note = (
            f"[{today.isoformat()}] Founder activation playbook active: {action} "
            f"Archetype: {archetype}. Expected engine: {archetype_config.get('engine', 'Hybrid founder engine')}."
        )
        properties: dict[str, Any] = {
            "Advocacy Score": number(score),
            "Advocacy Status": {"select": {"name": status}},
            "Activation Day": {"select": {"name": day}},
            "Founder Archetype": {"select": {"name": archetype}},
            "Archetype Confidence": {"number": confidence},
            "Influence Channel": {"select": {"name": archetype_config.get("channel", "Hybrid")}},
            "Archetype Evidence": rich_text(evidence),
            "Next Action": rich_text(action),
            "Next Action Date": date_value(today),
            "Notes": rich_text(append_note(plain_text(prop(contact, "Notes")), note)),
        }
        if secondary:
            properties["Secondary Archetype"] = {"select": {"name": secondary}}
        notion(
            "PATCH",
            f"pages/{contact['id']}",
            {"properties": properties},
        )
        counts["founder_contacts_updated"] += 1
        status_counts[status] += 1
        if client:
            create_or_update_activation_task(contact, client, today, day, action, archetype)
            counts["activation_tasks_upserted"] += 1

    create_or_replace_dashboard(today, counts, status_counts, archetype_counts)
    log_history(today, counts, status_counts, archetype_counts)
    return {"counts": dict(counts), "advocacy_status": dict(status_counts), "archetypes": dict(archetype_counts)}


def append_note(existing: str, note: str) -> str:
    if note in existing:
        return existing
    return (existing + " | " + note).strip(" |")


def create_or_update_activation_task(contact: dict[str, Any], client: dict[str, Any], today: date, day: str, action: str, archetype: str) -> None:
    title = f"Founder activation {day} - {title_of(contact)}"
    existing = query_database(
        EXECUTION_DB,
        {
            "and": [
                {"property": "Task", "title": {"equals": title}},
                {"property": "Contact", "relation": {"contains": contact["id"]}},
            ]
        },
    )
    props = {
        "Task": {"title": [{"text": {"content": title[:1800]}}]},
        "Client": {"relation": [{"id": client["id"]}]},
        "Contact": {"relation": [{"id": contact["id"]}]},
        "Type": {"select": {"name": "Follow-Up"}},
        "Priority": {"select": {"name": "High"}},
        "Due date": date_value(today),
        "Status": {"status": {"name": "To Do"}},
        "Stage Context": {"select": {"name": plain_text(prop(contact, "Stage")) or "Contacted"}},
        "Additional Information": rich_text(f"{archetype}: {action}"),
        "Tags": {"multi_select": [{"name": "Founder Circle Candidate"}, {"name": "Founder Activation"}, {"name": archetype}]},
    }
    if existing:
        notion("PATCH", f"pages/{existing[0]['id']}", {"properties": props})
    else:
        notion("POST", "pages", {"parent": {"database_id": EXECUTION_DB}, "properties": props})


def text(value: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": value[:1800]}}]


def block(block_type: str, value: str) -> dict[str, Any]:
    return {"object": "block", "type": block_type, block_type: {"rich_text": text(value)}}


def table(rows: list[list[Any]]) -> dict[str, Any]:
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
                    "table_row": {"cells": [text(str(value)) for value in row]},
                }
                for row in normalized
            ],
        },
    }


def find_page(title: str) -> str | None:
    data = notion("POST", "search", {"query": title, "filter": {"value": "page", "property": "object"}, "page_size": 20})
    for result in data.get("results", []):
        if title_of(result).lower() == title.lower():
            return result["id"]
    return None


def archive_children(page_id: str) -> None:
    cursor: str | None = None
    while True:
        path = f"blocks/{page_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        data = notion("GET", path)
        for child in data.get("results", []):
            notion("PATCH", f"blocks/{child['id']}", {"archived": True})
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")


def create_or_replace_dashboard(today: date, counts: Counter, status_counts: Counter, archetype_counts: Counter) -> None:
    page_id = find_page(PAGE_TITLE)
    properties = {"title": {"title": [{"text": {"content": PAGE_TITLE}}]}}
    if page_id:
        notion("PATCH", f"pages/{page_id}", {"archived": False, "is_locked": False, "properties": properties})
        archive_children(page_id)
    else:
        page = notion("POST", "pages", {"parent": {"page_id": PARENT_PAGE_ID}, "properties": properties})
        page_id = page["id"]
    children = [
        block("paragraph", f"Founder activation command layer generated {today.isoformat()}. Converts paid founders into decision-driven advocates."),
        block("heading_1", "Core Principle"),
        block("paragraph", "Founders advocate only after they experience a shift in how they think before making decisions. The 30-day job is usage -> realization -> proof -> advocacy -> growth."),
        block("heading_1", "Activation Metrics"),
        table(
            [
                ["Metric", "Current"],
                ["Founder contacts in activation", counts.get("founder_contacts_updated", 0)],
                ["Inactive", status_counts.get("Inactive", 0)],
                ["Engaged", status_counts.get("Engaged", 0)],
                ["Advocate", status_counts.get("Advocate", 0)],
            ]
        ),
        block("heading_1", "Founder Archetypes"),
        table(
            [["Archetype", "Current", "Target Mix", "Engine", "Expected Outcome"]]
            + [
                [
                    name,
                    archetype_counts.get(name, 0),
                    config["cohort_target"],
                    config["engine"],
                    {
                        "Mega Connector": "Awareness",
                        "Trusted Advisor": "Conversions",
                        "Operator Investor": "Referrals",
                        "Content Amplifier": "Content",
                    }.get(name, "Hybrid learning"),
                ]
                for name, config in ARCHETYPE_CONFIG.items()
            ]
        ),
        block("heading_1", "Customized 7-Day Paths"),
        table(
            [["Archetype", "Day 1 Ask", "Day 2-3 Tool", "Day 4-5 Action", "Day 6-7 Action", "Metrics"]]
            + [
                [name, config["day1"], config["day2"], config["day4"], config["day6"], config["metrics"]]
                for name, config in ARCHETYPE_CONFIG.items()
            ]
        ),
        block("heading_1", "Recognition System"),
        table(
            [["Archetype", "Motivation", "Recognition"]]
            + [[name, config["motivation"], config["recognition"]] for name, config in ARCHETYPE_CONFIG.items()]
        ),
        block("heading_1", "Assignment Logic"),
        table(
            [
                ["Question", "Signal", "Assignment"],
                ["How do you usually influence others?", "Public posts", "Mega Connector"],
                ["How do you usually influence others?", "1:1 advice", "Trusted Advisor"],
                ["How do you usually influence others?", "Private sharing", "Operator Investor"],
                ["How do you usually influence others?", "Content creation", "Content Amplifier"],
                ["Approx network size?", "5K+ audience", "Mega Connector"],
                ["Approx network size?", "Small but deep trusted network", "Trusted Advisor"],
                ["Preferred channel?", "WhatsApp", "Operator Investor"],
                ["Preferred channel?", "Video/content", "Content Amplifier"],
            ]
        ),
        block("heading_1", "Week-by-Week Sequence"),
        table(
            [
                ["Week", "Objective", "Actions", "Success Metric"],
                ["Week 1", "Activation + first value", "Decision shared, validation used, 1-line reflection, 1 referral", "70% activation, 50% usage"],
                ["Week 2", "Structure + identity", "Testimonial, founder channel, second referral", "50% testimonial, 40% referral activity"],
                ["Week 3", "Visibility + proof", "LinkedIn post or WhatsApp insight", "30% public proof, 60% continued usage"],
                ["Week 4", "Independent advocacy", "2+ referrals, 1 story, 1 decision case", "20-30% advocates"],
            ]
        ),
        block("heading_1", "Founder Checklist"),
        table(
            [
                ["Milestone", "Deadline", "Reward"],
                ["Submit 1 decision", "Day 2", "Activation tag"],
                ["Use validation once", "Day 5", "Priority support"],
                ["Refer 1 person", "Day 7", "Recognition"],
                ["Submit testimonial", "Day 10", "Featured founder"],
                ["Refer 3 people", "Day 30", "Inner circle"],
            ]
        ),
        block("heading_1", "Founder Email Sequence"),
        table(
            [
                ["Day", "Subject", "Core Ask"],
                ["0", "You're in - but this works differently", "What is one decision you are currently thinking about?"],
                ["2", "This is where most investors go wrong", "Before your next investment, pause and validate once."],
                ["4", "Quick question", "Did anything change in how you think before investing?"],
                ["6", "Someone else needs this", "Think of 1 person who invests regularly and second-guesses decisions."],
                ["10", "What being a founder actually means", "Share your experience; your input shapes how this evolves."],
            ]
        ),
        block("heading_1", "Social Proof Toolkit"),
        table(
            [
                ["Asset", "Prompt"],
                ["30-sec video", "I used to rely on inputs and research. I realised I never validated the decision. Now I pause and validate before acting."],
                ["Case study", "Wrong decision, why it felt right, what changed, what you would do differently."],
                ["LinkedIn", "Most investment mistakes do not feel reckless. They feel informed."],
                ["WhatsApp", "Biggest mistake is not wrong stock - it is not validating the decision before investing."],
            ]
        ),
    ]
    for index in range(0, len(children), 80):
        notion("PATCH", f"blocks/{page_id}/children", {"children": children[index : index + 80]})
    notion("PATCH", f"pages/{page_id}", {"is_locked": True})


def log_history(today: date, counts: Counter, status_counts: Counter, archetype_counts: Counter) -> None:
    key = f"{today.isoformat()}::founder-activation-playbook"
    existing = query_database(HISTORY_DB, {"property": "History Key", "title": {"equals": key}})
    properties = {
        "History Key": {"title": [{"text": {"content": key}}]},
        "Date": date_value(today),
        "Action Type": rich_text("Founder activation automation"),
        "Lead or Task": rich_text("0-30 day Founder Circle playbook"),
        "Owner": rich_text("Codex"),
        "Channel": rich_text("Workbook + Notion"),
        "Outcome": {"select": {"name": "No Response"}},
        "Outcome Notes": rich_text(f"Added founder activation fields, archetypes, tasks, dashboard, workbook checklist, proof capture and advocate loop. Counts: {dict(counts)}; status: {dict(status_counts)}; archetypes: {dict(archetype_counts)}"),
        "Next Move": rich_text("Send archetype-specific Day 1 prompts after founder payment; track activation, usage, testimonial, referrals and advocacy score."),
        "Source": rich_text("Founder Circle Activation Playbook"),
        "Last Synced At": {"date": {"start": datetime.now().astimezone().isoformat(timespec="seconds")}},
    }
    if existing:
        notion("PATCH", f"pages/{existing[0]['id']}", {"properties": properties})
    else:
        notion("POST", "pages", {"parent": {"database_id": HISTORY_DB}, "properties": properties})


def apply_workbook(today: date) -> dict[str, Any]:
    backup = WORKBOOK.parent / "backups" / f"{WORKBOOK.stem}.before-founder-activation.{datetime.now().strftime('%Y%m%d-%H%M%S')}{WORKBOOK.suffix}"
    backup.parent.mkdir(exist_ok=True)
    copy2(WORKBOOK, backup)
    wb = load_workbook(WORKBOOK)
    update_activation_sheet(wb, today)
    update_outreach_ready(wb, today)
    update_execution_tasks(wb, today)
    append_history(wb, today)
    wb.save(WORKBOOK)
    return {"backup": str(backup)}


def update_activation_sheet(wb: Any, today: date) -> None:
    if "FOUNDER_ACTIVATION_DASHBOARD" in wb.sheetnames:
        ws = wb["FOUNDER_ACTIVATION_DASHBOARD"]
        ws.delete_rows(1, ws.max_row)
    else:
        ws = wb.create_sheet("FOUNDER_ACTIVATION_DASHBOARD")
    navy = "1F4E79"
    amber = "FFF2CC"
    green = "E2F0D9"
    thin = Side(style="thin", color="D9E2F3")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def write(row: int, values: list[Any], fill: str | None = None, bold: bool = False) -> None:
        for column, value in enumerate(values, 1):
            cell = ws.cell(row, column)
            cell.value = value
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if fill:
                cell.fill = PatternFill("solid", fgColor=fill)
            if bold:
                cell.font = Font(bold=True, color="FFFFFF" if fill == navy else "000000")

    ws.merge_cells("A1:D1")
    ws["A1"] = "FOUNDER CIRCLE ACTIVATION DASHBOARD"
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=navy)
    ws["A2"] = f"Updated {today.isoformat()}. Usage -> realization -> proof -> advocacy -> growth."
    write(4, ["Metric", "Target", "Current Source", "Control"], navy, True)
    rows = [
        ["Week 1 activation", "70%", "Founder Activation checkbox", "Ask current decision on Day 1"],
        ["Week 1 usage", "50%", "Validation Used checkbox", "Prompt validation before next action"],
        ["Day 30 testimonials", "50%", "Testimonial Captured checkbox", "Ask after first value moment"],
        ["Referral participation", "40%", "Referrals Count", "Ask who else faces this problem"],
        ["Advocates", "20-30%", "Advocacy Score >= 4", "Recognize status, not discount"],
    ]
    for index, row in enumerate(rows, 5):
        write(index, row, amber if index in [5, 6] else None)
    start = 12
    write(start, ["Founder Checklist", "Deadline", "Reward", "CRM Field"], navy, True)
    checklist = [
        ["Submit 1 decision", "Day 2", "Activation tag", "Founder Activation"],
        ["Use validation once", "Day 5", "Priority support", "Validation Used"],
        ["Refer 1 person", "Day 7", "Recognition", "Referrals Count >= 1"],
        ["Submit testimonial", "Day 10", "Featured founder", "Testimonial Captured"],
        ["Refer 3 people", "Day 30", "Inner circle", "Referrals Count >= 3"],
    ]
    for index, row in enumerate(checklist, start + 1):
        write(index, row, green)
    start = 22
    write(start, ["Email Day", "Subject", "Core Ask", "Purpose"], navy, True)
    emails = [
        ["Day 0", "You're in - but this works differently", "What is one decision you are currently thinking about?", "Activation"],
        ["Day 2", "This is where most investors go wrong", "Before your next investment, pause and validate once.", "Usage"],
        ["Day 4", "Quick question", "Did anything change in how you think before investing?", "Proof"],
        ["Day 6", "Someone else needs this", "Think of 1 person who invests regularly and second-guesses decisions.", "Referral"],
        ["Day 10", "What being a founder actually means", "Share your experience.", "Identity"],
    ]
    for index, row in enumerate(emails, start + 1):
        write(index, row)
    start = 32
    write(start, ["Archetype", "Target Mix", "Motivation", "Advocacy Style"], navy, True)
    for index, (name, config) in enumerate(ARCHETYPE_CONFIG.items(), start + 1):
        write(index, [name, config["cohort_target"], config["motivation"], config["advocacy"]], amber if name in ["Trusted Advisor", "Operator Investor"] else None)
    start = 40
    write(start, ["Archetype", "Day 1 Ask", "Day 2-3 Tool", "Day 4-5 Action", "Day 6-7 Action"], navy, True)
    for index, (name, config) in enumerate(ARCHETYPE_CONFIG.items(), start + 1):
        write(index, [name, config["day1"], config["day2"], config["day4"], config["day6"]])
    start = 48
    write(start, ["Screening Question", "Signal", "Assignment", "Rule"], navy, True)
    assignment = [
        ["How do you usually influence others?", "Public posts", "Mega Connector", "Match 2/3 signals"],
        ["How do you usually influence others?", "1:1 advice", "Trusted Advisor", "Match 2/3 signals"],
        ["How do you usually influence others?", "Private sharing", "Operator Investor", "Match 2/3 signals"],
        ["How do you usually influence others?", "Content creation", "Content Amplifier", "Match 2/3 signals"],
        ["Approx network size?", "5K+ audience", "Mega Connector", "If mixed, assign primary + secondary"],
        ["Preferred communication channel?", "WhatsApp", "Operator Investor", "Use founder's natural behavior"],
        ["Preferred communication channel?", "Video/content", "Content Amplifier", "Do not force generic steps"],
    ]
    for index, row in enumerate(assignment, start + 1):
        write(index, row, green if index == start + 1 else None)
    for column, width in {"A": 28, "B": 18, "C": 48, "D": 34}.items():
        ws.column_dimensions[column].width = width
    ws.column_dimensions["E"].width = 48
    ws.freeze_panes = "A4"


def update_outreach_ready(wb: Any, today: date) -> None:
    ws = wb["FNOMO_OUTREACH_READY"]
    headers = {ws.cell(4, column).value: column for column in range(1, ws.max_column + 1) if ws.cell(4, column).value}
    rows = {
        "Founder Activation Email 1": ["Founder Activation Email 1", "Email", "Kush", today.isoformat(), "", "", "", "You're in - but this works differently", "You're part of the Founder Circle.\n\nFnomo is not for finding investments. It's for validating decisions before you act.\n\nWhat is one decision you're currently thinking about?\n\nReply with that. We'll help you think through it."],
        "Founder Activation Email 2": ["Founder Activation Email 2", "Email", "Kush", today.isoformat(), "", "", "", "This is where most investors go wrong", "Most people don't lose money because of bad information.\n\nThey lose because they act without validating their decision.\n\nBefore your next investment - pause. Ask: Have I actually validated this?\n\nReply if you try this once."],
        "Founder Activation Email 3": ["Founder Activation Email 3", "Email", "Kush", today.isoformat(), "", "", "", "Quick question", "After using this once - did anything change in how you think before investing?\n\nEven a small shift matters.\n\nReply in one line."],
        "Founder Activation Email 4": ["Founder Activation Email 4", "Email", "Kush", today.isoformat(), "", "", "", "Someone else needs this", "Most people around you are making decisions without validation.\n\nThink of 1 person who invests regularly and second-guesses decisions. Introduce them because they're already facing the problem."],
        "Founder Activation Email 5": ["Founder Activation Email 5", "Email", "Kush", today.isoformat(), "", "", "", "What being a founder actually means", "Founder Circle is not early access. It's early influence.\n\nWhat you share shapes how this evolves.\n\nIf you've used this once, share your experience."],
    }
    for archetype, config in ARCHETYPE_CONFIG.items():
        lead_name = f"Founder Archetype - {archetype}"
        rows[lead_name] = [
            lead_name,
            config["channel"],
            "Kush",
            today.isoformat(),
            "Archetype-specific founder activation",
            "",
            "",
            f"{archetype} founder prompt",
            f"{config['day1']}\n\nThen use this path:\nDay 2-3: {config['day2']}\nDay 4-5: {config['day4']}\nDay 6-7: {config['day6']}\n\nRecognition: {config['recognition']}",
        ]
    existing = {str(ws.cell(row, headers["Lead_Name"]).value or ""): row for row in range(5, ws.max_row + 1)}
    for lead_name, values in rows.items():
        row = existing.get(lead_name) or ws.max_row + 1
        for index, value in enumerate(values, 1):
            ws.cell(row, index).value = value
        existing[lead_name] = row


def update_execution_tasks(wb: Any, today: date) -> None:
    ws = wb["FNOMO_EXECUTION_TASKS"]
    headers = {ws.cell(4, column).value: column for column in range(1, ws.max_column + 1) if ws.cell(4, column).value}
    existing = {str(ws.cell(row, headers["Task"]).value or ""): row for row in range(5, ws.max_row + 1)}
    tasks = [
        ["TDA-FA-001", "Founder Day 1 activation prompt", "Kush", "A", "Ask every new paid founder: What decision are you currently thinking about?", today.isoformat(), "Execute Today", "Founder Activation", "Target 80% response."],
        ["TDA-FA-002", "Founder first validation loop", "Kush", "A", "Move founder to validate one real decision before acting.", (today + timedelta(days=2)).isoformat(), "Within 48h", "Founder Activation", "Target 60% usage activation."],
        ["TDA-FA-003", "Founder reflection capture", "Kush", "A", "Ask: Did anything change in how you think before acting?", (today + timedelta(days=4)).isoformat(), "Scheduled", "Founder Activation", "Capture 1-line proof."],
        ["TDA-FA-004", "Founder referral ask", "Kush", "A", "Ask: Who else do you know makes similar investment decisions?", (today + timedelta(days=6)).isoformat(), "Scheduled", "Founder Activation", "Recognition, not discount."],
        ["TDA-FA-005", "Founder proof asset capture", "Kush", "B", "Capture quote, voice note, LinkedIn insight, or before/after case.", (today + timedelta(days=10)).isoformat(), "Scheduled", "Founder Activation", "Ask for decision clarity shift, not product praise."],
        ["TDA-FA-006", "Assign founder archetypes", "Kush", "A", "Ask screening questions and confirm primary + secondary archetype: public posts, 1:1 advice, private sharing, or content creation.", today.isoformat(), "Execute Today", "Founder Activation", "Match 2/3 signals; if mixed, mark hybrid."],
    ]
    for task in tasks:
        row = existing.get(task[1]) or ws.max_row + 1
        for index, value in enumerate(task, 1):
            ws.cell(row, index).value = value
        existing[task[1]] = row


def append_history(wb: Any, today: date) -> None:
    ws = wb["FNOMO_EXECUTION_HISTORY"]
    for row_index in range(ws.max_row, 4, -1):
        if (
            str(ws.cell(row_index, 1).value or "") == today.isoformat()
            and str(ws.cell(row_index, 2).value or "") == "Founder Activation Automation"
            and str(ws.cell(row_index, 3).value or "") == "0-30 day Founder Circle playbook"
        ):
            ws.delete_rows(row_index, 1)
    row = ws.max_row + 1
    values = [
        today.isoformat(),
        "Founder Activation Automation",
        "0-30 day Founder Circle playbook",
        "Codex",
        "Workbook + Notion",
        "Added founder activation dashboard, CRM fields, archetypes, activation tasks, email sequence, proof capture, and advocate loop.",
        "Use after payment; confirm archetype with screening questions, then track activation, usage, testimonial, referrals and advocacy score.",
        "Founder Activation Playbook",
    ]
    for index, value in enumerate(values, 1):
        ws.cell(row, index).value = value


def main() -> None:
    today = date.fromisoformat(os.environ.get("FNOMO_OPERATING_DATE", date.today().isoformat()))
    notion_result = apply_notion(today)
    workbook_result = apply_workbook(today)
    print(json.dumps({"notion": notion_result, "workbook": workbook_result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
