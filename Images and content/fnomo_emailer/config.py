"""
config.py — FNOMO Email System
Loads all credentials from .env file using python-dotenv.
Never hardcode secrets here — keep them in .env (which is git-ignored).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise SystemExit(
            f"\n[CONFIG ERROR] Missing required credential: {key}\n"
            f"  → Add it to your .env file in the fnomo_emailer\\ folder.\n"
            f"  → Run `python zoho_oauth_setup.py` to generate Zoho credentials.\n"
        )
    return val


# ── Zoho OAuth Credentials ────────────────────
ZOHO_CLIENT_ID     = _require("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = _require("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = _require("ZOHO_REFRESH_TOKEN")
ZOHO_ACCOUNT_ID    = _require("ZOHO_ACCOUNT_ID")
SENDER_EMAIL       = os.getenv("SENDER_EMAIL", "kush@mail.fnomo.com")
SENDER_NAME        = os.getenv("SENDER_NAME",  "Kush | FNOMO")

# ── LLM Provider (free alternatives to Anthropic) ────────────────
# LLM_PROVIDER options: groq | nvidia | anthropic
# Groq  (free): https://console.groq.com       → set GROQ_API_KEY
# NVIDIA (free): https://build.nvidia.com      → set NVIDIA_API_KEY
# Anthropic (paid): https://console.anthropic.com → set ANTHROPIC_API_KEY

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()

_DEFAULT_MODELS = {
    "groq":      "llama-3.3-70b-versatile",
    "nvidia":    "meta/llama-3.3-70b-instruct",
    "anthropic": "claude-sonnet-4-20250514",
}

LLM_MODEL = os.getenv("LLM_MODEL", _DEFAULT_MODELS.get(LLM_PROVIDER, "llama-3.3-70b-versatile")).strip()

# Pick the right key based on provider
_KEY_MAP = {
    "groq":      "GROQ_API_KEY",
    "nvidia":    "NVIDIA_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
LLM_API_KEY = os.getenv(_KEY_MAP.get(LLM_PROVIDER, "GROQ_API_KEY"), "").strip()

# Legacy — kept for backwards compatibility
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

# ── Excel Source ──────────────────────────────
EXCEL_PATH = os.getenv(
    "EXCEL_PATH",
    r"D:\Antigravity\eigent\Downloads\fnomo\EXCEL\FNOMO_CA_AGGRESSIVE_SCRAPE_86500.xlsx"
)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))

# ── Scheduling Rules ──────────────────────────
SCHEDULE_START_HOUR = int(os.getenv("SCHEDULE_START_HOUR", "10"))
SCHEDULE_END_HOUR   = int(os.getenv("SCHEDULE_END_HOUR",   "18"))
MIN_DELAY_MINUTES   = int(os.getenv("MIN_DELAY_MINUTES",    "7"))
MAX_DELAY_MINUTES   = int(os.getenv("MAX_DELAY_MINUTES",   "25"))
MAX_EMAILS_PER_DAY  = int(os.getenv("MAX_EMAILS_PER_DAY",  "25"))

# ── Compliance Footer ─────────────────────────
COMPLIANCE_FOOTER = (
    "\n\n---\n"
    "Fnomo is institutional research infrastructure for educational purposes. "
    "We do not provide investment advice, brokerage services, or performance guarantees. "
    "All decisions remain with the user."
)

# ── Zoho API Endpoints (EU data center) ──────────────────────────
ZOHO_TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
ZOHO_MAIL_URL  = "https://mail.zoho.eu/api/accounts/{account_id}/messages"
