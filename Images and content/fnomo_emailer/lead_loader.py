"""
lead_loader.py — Phase 1
Reads the Excel file and returns the first BATCH_SIZE valid leads
(rows that have both Email and Name populated).
"""

import re
import pandas as pd
from config import EXCEL_PATH, BATCH_SIZE


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Generic role-based prefixes that indicate an inbox, not a person.
# We want partner / founder / named emails only.
REJECTED_PREFIXES = (
    "info@", "hr@", "admin@", "contact@", "hello@", "support@",
    "enquiry@", "enquiries@", "mail@", "office@", "team@",
    "careers@", "jobs@", "accounts@", "reception@", "general@",
)


def _is_valid_email(email: str) -> bool:
    email = str(email).strip().lower()
    if not email or not EMAIL_RE.match(email):
        return False
    if any(email.startswith(prefix) for prefix in REJECTED_PREFIXES):
        return False
    return True


def _is_valid_name(name: str) -> bool:
    return bool(name and str(name).strip() not in ("", "nan", "None"))


def load_leads(path: str = EXCEL_PATH, batch: int = BATCH_SIZE) -> list[dict]:
    """
    Returns a list of dicts with keys:
        name, email, company (optional), industry (optional), city (optional)
    Skips rows missing email or name, deduplicates by email.
    """
    print(f"[LOADER] Reading: {path}")
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except FileNotFoundError:
        raise SystemExit(f"[ERROR] Excel file not found: {path}")

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Find email / name columns
    email_col = next((c for c in df.columns if "email" in c), None)
    name_col  = next(
        (c for c in df.columns if c in ("name", "full_name", "first_name", "contact")), None
    )

    if not email_col:
        raise SystemExit("[ERROR] No email column found in Excel.")
    if not name_col:
        raise SystemExit("[ERROR] No name column found in Excel.")

    # Optional enrichment columns
    company_col  = next((c for c in df.columns if "company" in c or "firm" in c), None)
    industry_col = next((c for c in df.columns if "industry" in c or "sector" in c), None)
    city_col     = next((c for c in df.columns if c in ("city", "location", "region")), None)

    leads = []
    seen_emails: set[str] = set()

    for _, row in df.iterrows():
        email = str(row.get(email_col, "")).strip()
        name  = str(row.get(name_col, "")).strip()

        if not _is_valid_email(email):
            if email and "@" in email:  # only log actual emails that were rejected (not blanks)
                print(f"[LOADER] Skipped generic inbox: {email}")
            continue
        if not _is_valid_name(name):
            continue
        if email.lower() in seen_emails:
            continue

        seen_emails.add(email.lower())
        leads.append({
            "name":     name.title(),
            "email":    email.lower(),
            "company":  str(row[company_col]).strip()  if company_col  else "",
            "industry": str(row[industry_col]).strip() if industry_col else "",
            "city":     str(row[city_col]).strip()     if city_col     else "",
        })

        if len(leads) >= batch:
            break

    print(f"[LOADER] {len(leads)} valid leads loaded (batch cap: {batch})")
    return leads
