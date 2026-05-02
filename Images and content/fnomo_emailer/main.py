"""
main.py — FNOMO Email Execution System
Orchestrates all phases end-to-end.

Usage:
  python main.py              # live mode — schedules real emails
  python main.py --dry-run    # simulate without hitting Zoho API
"""

import sys
import json
import argparse
from datetime import datetime

from lead_loader     import load_leads
from email_generator import generate_all_emails
from scheduler       import build_schedule, format_schedule
from zoho_sender     import schedule_batch, _token_mgr


SEPARATOR = "=" * 62


def print_header(phase: str):
    print(f"\n{SEPARATOR}")
    print(f"  {phase}")
    print(SEPARATOR)


def phase0_connection_check() -> bool:
    print_header("PHASE 0 — Zoho Connection Check")
    try:
        token = _token_mgr.get_token()
        if token:
            print("[OK] Zoho access token obtained")
            return True
    except Exception as e:
        print(f"[FAIL] Cannot get Zoho token: {e}")
        print("\n  Action required:")
        print("  1. Open .env and confirm ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET are filled in")
        print("  2. Run: python zoho_oauth_setup.py")
        print("  3. Paste ZOHO_REFRESH_TOKEN and ZOHO_ACCOUNT_ID into .env")
        print("  4. Re-run: python main.py")
    return False


def phase6_report(results: list[dict], schedule: list[datetime], skipped_leads: list[dict]):
    print_header("PHASE 5 — Output Report")

    scheduled = [r for r in results if r.get("success")]
    failed    = [r for r in results if not r.get("success")]
    total     = len(scheduled) + len(failed) + len(skipped_leads)

    status = (
        "Completed" if not failed and not skipped_leads
        else "Partial" if scheduled
        else "Failed"
    )

    print(f"\n  STATUS:  {status}")
    print(f"\n  OUTPUT:")
    print(f"    Total leads loaded :  {total}")
    print(f"    Emails generated   :  {len(scheduled) + len(failed)}")
    print(f"    Emails scheduled   :  {len(scheduled)}")

    if scheduled:
        days = sorted(set(r["send_time"][:10] for r in scheduled))
        for d in days:
            day_emails = [r for r in scheduled if r["send_time"][:10] == d]
            print(f"      {d}  ->  {len(day_emails)} emails")

    print(f"\n  ISSUES:")
    if skipped_leads:
        print(f"    Generation failures ({len(skipped_leads)}):")
        for lead in skipped_leads:
            print(f"      - {lead.get('name','?')} <{lead.get('email','?')}>")
    if failed:
        print(f"    Scheduling failures ({len(failed)}):")
        for r in failed:
            print(f"      - {r['lead_email']}: {r['message']}")
    if not skipped_leads and not failed:
        print("    None")

    print(f"\n  NEXT STEP:")
    if scheduled:
        last_slot = max(r["send_time"] for r in scheduled)
        print(f"    Last scheduled slot: {last_slot}")
        print(f"    Run again for the next batch.")
    else:
        print("    No emails were scheduled. Check errors above.")

    print(f"\n{SEPARATOR}\n")

    log = {
        "run_at":              datetime.now().isoformat(),
        "status":              status,
        "scheduled":           scheduled,
        "failed":              failed,
        "skipped_generation":  [{"name": l.get("name"), "email": l.get("email")} for l in skipped_leads],
        "email_preview":       [
            {
                "to":      r["lead_email"],
                "name":    r["lead_name"],
                "subject": r["subject"],
                "body":    r.get("body", ""),
            }
            for r in scheduled[:5]   # first 5 for quick review
        ],
    }
    log_path = f"fnomo_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"  [LOG] Run log saved to: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="FNOMO Email Execution System")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate and schedule without calling Zoho API")
    parser.add_argument("--mock-ai", action="store_true",
                        help="Use template emails instead of Claude API (no ANTHROPIC_API_KEY needed)")
    args = parser.parse_args()

    print(f"\n{'*' * 62}")
    print(f"  FNOMO EMAIL EXECUTION SYSTEM")
    modes = []
    if args.dry_run:  modes.append("DRY RUN")
    if args.mock_ai:  modes.append("MOCK AI")
    print(f"  Mode: {' + '.join(modes) if modes else 'LIVE'}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*' * 62}")

    if not args.dry_run:
        ok = phase0_connection_check()
        if not ok:
            sys.exit(1)
    else:
        print("\n[DRY RUN] Skipping Phase 0 connection check.")

    print_header("PHASE 1 — Loading Leads")
    leads = load_leads()

    print_header("PHASE 2 — Generating NEPQ Emails")
    generated = generate_all_emails(leads, mock=args.mock_ai)

    generated_emails = {l["email"] for l in generated}
    skipped_leads    = [l for l in leads if l["email"] not in generated_emails]

    print_header("PHASE 3+4 — Building Schedule")
    schedule = build_schedule(len(generated))
    print(f"\n  {len(schedule)} slots assigned:")
    print(format_schedule(schedule))

    print_header("PHASE 5 — Validation + Scheduling via Zoho")
    results = schedule_batch(generated, schedule, dry_run=args.dry_run)

    phase6_report(results, schedule, skipped_leads)


if __name__ == "__main__":
    main()
