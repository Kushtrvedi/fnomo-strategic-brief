"""
Fnomo — Bhopal Outreach RETRY for 28 failed contacts.
Failure reason: Zoho rate-limit (550 5.4.6 "Unusual sending activity").
Fix: longer delays + token refresh every 10 emails.
"""

import time
import requests

# ── Zoho credentials ────────────────────────────────────────────────────────
CLIENT_ID     = "1000.NMT7FVPCB4JSSUFI1WSA99RWCQ8LBD"
CLIENT_SECRET = "6d1c4808abcac57ede83724738e5f568ae40771fc4"
REFRESH_TOKEN = "1000.26bcc31d7a1ddc141689c7a11044d34e.73afd2939c5f5ce4940ac697e1ed49d3"
ACCOUNT_ID    = "8585832000000002002"
FROM_ADDRESS  = "kush@mail.fnomo.com"

LOG_FILE = r"C:\Users\kush_\Antigravity\eigent\Downloads\fnomo\bhopal_retry_log.txt"

SIGNATURE = "\n\nWarm regards,\nKush Trivedi\nBusiness Head, Fnomo.com\n+91 93403 92140"

ACADEMIC_HOSPITALS = ["aiims", "gmc", "bhel", "kasturba", "government medical", "mansarovar"]

SURGEON_SPECIALTIES = [
    "surgery", "ctvs", "orthopaedics", "orthopedics", "ortho",
    "ent", "neurosurgery", "urology", "plastic", "transplant"
]

PHYSICIAN_SPECIALTIES = [
    "cardiology", "neurology", "internal med", "medicine",
    "gastroenterology", "nephrology", "pulmonology", "endocrinology",
    "anesthesiology", "anaesthesia", "pediatrics", "paediatrics",
    "child neuro", "psychiatry", "oncology", "gynaecology", "gynecology",
    "dermatology", "ophthalmology", "rheumatology", "haematology", "diabetology"
]

# ── 28 failed contacts from previous run ────────────────────────────────────
FAILED_CONTACTS = [
    ("Dr. Neeraj Kumar",        "Surgery",         "Noble Multispeciality",    "neeraj.k@noblebhopal.com"),
    ("Dr. Pooja Sharma",        "Pathology",       "Noble Multispeciality",    "pooja.s@noblebhopal.com"),
    ("Dr. Sameer Gupta",        "Radiology",       "Noble Multispeciality",    "sameer.g@noblebhopal.com"),
    ("Dr. Arun Kumar",          "Orthopaedics",    "Sahara Fracture Hosp",     "arun.k@saharaortho.com"),
    ("Dr. K.K. Shrivastava",    "Orthopaedics",    "Sahara Fracture Hosp",     "kk.s@saharaortho.com"),
    ("Dr. Santosh Choudhary",   "Ophthalmology",   "Sagar Multispeciality",    "contact@smhbhopal.com"),
    ("Dr. Jai Prakash Paliwal", "Surgery",         "Paliwal Hospital",         "paliwal.hospital@gmail.com"),
    ("Dr. Shashi Gandhi",       "Microbiology",    "GMC Bhopal",               "shashi.gandhi@gmc.edu.in"),
    ("Dr. Roopesh Jain",        "Medicine",        "JK Hospital",              "roopesh.jain@jkhospital.org"),
    ("Dr. Ram Kumar Agrawal",   "Orthopaedics",    "Kasturba BHEL",            "rk.agrawal@bhel.in"),
    ("Dr. Sheela Malani",       "Internal Med",    "Kasturba BHEL",            "sheela.malani@bhel.in"),
    ("Dr. Atulya Saurabh",      "Medicine",        "Kasturba BHEL",            "atulya.saurabh@bhel.in"),
    ("Dr. Sunil Rathore",       "Plastic Surgery", "Bansal Hospital",          "sunil.rathore@bansalhospital.com"),
    ("Dr. Mayur Agarwal",       "Endocrinology",   "Gulmohar Clinic",          "mayur.endo@gmail.com"),
    ("Dr. Pankaj Kumar Mishra", "Nephrology",      "Bansal Hospital",          "pankaj.mishra@bansalhospital.com"),
    ("Dr. Alok Gupta",          "Oncology",        "Navodaya Oncology",        "alokguptaonco@gmail.com"),
    ("Dr. Nitya Bisarya",       "Anaesthesia",     "Apollo Sage Hospital",     "nitya.bisarya@apollosage.in"),
    ("Dr. Manoj Paliwal",       "Microbiology",    "GMC Bhopal",               "manoj.paliwal@gmc.edu.in"),
    ("Dr. Richa Sharma",        "Medicine",        "Mansarovar Medical Col",   "richa.sharma@mansarovarmc.com"),
    ("Dr. Ashutosh Badwik",     "Medicine",        "Mansarovar Medical Col",   "admin@mansarovarmc.com"),
    ("Dr. Nirendra Kumar Rai",  "Neurology",       "Apollo Sage Hospital",     "nirendra.rai@apollosage.in"),
    ("Dr. Sandeep Choudhary",   "Psychiatry",      "Chirayu Hospital",         "sandeep.c@cmchbhopal.com"),
    ("Dr. Alpa Prabhu",         "Gynaecology",     "Sagar Multispeciality",    "spsgn@spsbhopal.ac.in"),
    ("Dr. Shraddha Kanungo",    "Gynaecology",     "Sagar Multispeciality",    "shraddhakanungo@spsbhopal.ac.in"),
    ("Dr. Prachi Varma",        "Gynaecology",     "Sagar Multispeciality",    "prachi.v@smhbhopal.com"),
    ("Dr. Ashish Saraogi",      "Surgery",         "LBS Hospital",             "ashish.saraogi@lbshospital.com"),
    ("Dr. Avadhesh N Khare",    "Cardiology",      "LBS Hospital",             "avadhesh.khare@lbshospital.com"),
    ("Dr. A D Suri",            "Nephrology",      "LBS Hospital",             "ad.suri@lbshospital.com"),
]


def build_contacts():
    contacts = []
    for full_name, specialty, hospital, email in FAILED_CONTACTS:
        name_parts = full_name.replace("Dr. ", "").strip().split()
        greeting = f"Hi Dr. {name_parts[-1]}" if name_parts else f"Hi {full_name}"
        contacts.append({"full_name": full_name, "specialty": specialty,
                         "hospital": hospital, "email": email, "greeting": greeting})
    return contacts


def get_template(greeting, specialty, hospital):
    s = specialty.lower()
    h = hospital.lower()

    if any(a in h for a in ACADEMIC_HOSPITALS):
        subject = "Evidence-based investing — does this exist?"
        body = (
            f"{greeting},\n\n"
            "You've spent years building clinical judgment on evidence. But financial "
            "decisions — where to put your savings, whether to act on a broker's advice "
            "— rarely get the same rigor.\n\n"
            "Fnomo is a stock analysis platform (not trading, not advisory) that puts "
            "structured financial data in front of you the same way lab results put "
            "clinical data in front of you — clearly, without jargon.\n\n"
            "Flat subscription. No commissions. No conflict of interest.\n\n"
            "Would a 15-minute walkthrough be useful? Happy to set one up at your convenience.\n\n"
            "You can explore it here: https://fnomo.com (free sign-up)"
        )
        return subject, body + SIGNATURE

    if any(sp in s for sp in SURGEON_SPECIALTIES):
        subject = "For doctors who don't have time to watch the market"
        body = (
            f"{greeting},\n\n"
            "Between back-to-back procedures, tracking your investments is nearly "
            "impossible — and most of us end up just trusting whatever our broker or CA says.\n\n"
            "Fnomo is a stock analysis platform that helps you do a two-minute sanity "
            "check on any stock before you put money in, or before you act on someone's tip.\n\n"
            "Color-coded, plain language. Not trading — flat subscription, so we earn "
            "on that, not when you invest.\n\n"
            "If a short demo would be useful, I'm happy to set one up at your convenience.\n\n"
            "Explore here: https://fnomo.com (free sign-up)"
        )
        return subject, body + SIGNATURE

    if any(sp in s for sp in PHYSICIAN_SPECIALTIES):
        subject = "You read data for a living — what about your portfolio?"
        body = (
            f"{greeting},\n\n"
            f"As a {specialty.lower()} specialist, you're used to reading complex data "
            "and making accurate calls on limited time. But most investment tools make "
            "that nearly impossible when it comes to your own money.\n\n"
            "Fnomo is a stock analysis platform that presents financial data the way "
            "you'd want it — structured, color-coded, no jargon. Not trading, not "
            "advisory. Just clear information so you can verify decisions yourself.\n\n"
            "Flat subscription. No commissions. No conflict of interest.\n\n"
            "Would a 15-minute walkthrough work? Happy to set it up.\n\n"
            "Explore here: https://fnomo.com (free sign-up)"
        )
        return subject, body + SIGNATURE

    subject = "A tool built for busy professionals — like you"
    body = (
        f"{greeting},\n\n"
        "Managing patient care and your own finances at the same time is genuinely "
        "hard — most of us end up delegating investments to someone else and hoping for the best.\n\n"
        "Fnomo is a stock analysis platform (not trading) that lets you do a quick, "
        "clear check on any investment before you commit. Color-coded, no finance background needed.\n\n"
        "We earn on subscription, not when you trade — no conflict of interest.\n\n"
        "If a short demo would be useful, I'm happy to set one up.\n\n"
        "Explore here: https://fnomo.com (free sign-up)"
    )
    return subject, body + SIGNATURE


def refresh_token():
    resp = requests.post(
        "https://accounts.zoho.eu/oauth/v2/token",
        data={
            "grant_type":    "refresh_token",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        }
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token refresh failed: {data}")
    return data["access_token"]


def send_email(token, to_address, subject, body):
    resp = requests.post(
        f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}/messages",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
        json={
            "fromAddress": FROM_ADDRESS,
            "toAddress":   to_address,
            "subject":     subject,
            "content":     body,
            "mailFormat":  "plaintext",
            "mode":        "send",
        }
    )
    return resp.status_code, resp.json()


def main():
    contacts = build_contacts()
    print(f"Retrying {len(contacts)} failed contacts (with rate-limit-safe pacing)\n")

    print("Refreshing Zoho token...")
    token = refresh_token()
    print("Token OK. Starting sends...\n")

    sent = 0
    failed = 0
    log_lines = []

    for i, c in enumerate(contacts, 1):
        subject, body = get_template(c["greeting"], c["specialty"], c["hospital"])

        # Retry up to 3 times on 500 errors
        for attempt in range(1, 4):
            status, resp_data = send_email(token, c["email"], subject, body)
            if status == 200:
                break
            if attempt < 3:
                print(f"   ↻ Attempt {attempt} failed ({status}), retrying in 15s...")
                time.sleep(15)
                token = refresh_token()
            else:
                print(f"   ✗ All 3 attempts failed for {c['email']}")

        if status == 200:
            sent += 1
            result = "SENT"
        else:
            failed += 1
            result = f"FAIL({status})"

        line = f"[{i:02d}/{len(contacts)}] {result} | {c['specialty']:<22} | {c['email']}"
        print(line)
        log_lines.append(f"{line} | {c['full_name']}")

        # Token refresh every 10 emails
        if i % 10 == 0:
            try:
                token = refresh_token()
                print(f"   ↻ Token refreshed at #{i}")
            except Exception as e:
                print(f"   ✗ Token refresh failed: {e}")

        # 5-second delay between sends (vs 0.3s before — prevents rate-limiting)
        if i < len(contacts):
            time.sleep(5)

    # Write log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Bhopal Outreach RETRY Log\n")
        f.write(f"Total contacts retried: {len(contacts)}\n")
        f.write(f"Sent: {sent}  |  Failed: {failed}\n")
        f.write("=" * 80 + "\n\n")
        f.write("\n".join(log_lines))

    print(f"\n{'='*50}")
    print(f"DONE — Sent: {sent} | Failed: {failed}")
    print(f"Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
