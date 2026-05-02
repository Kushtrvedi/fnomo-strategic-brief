"""
Fnomo — Bhopal Doctors Specialty-Targeted Outreach Sender
Contacts are hard-coded (extracted from Bhopal_Doctors_Personalized_Outreach.md).
Deduplication, specialty-matched templates, sends via Zoho Mail EU API.
"""

import time
import requests

# ── Zoho credentials ────────────────────────────────────────────────────────
CLIENT_ID     = "1000.NMT7FVPCB4JSSUFI1WSA99RWCQ8LBD"
CLIENT_SECRET = "6d1c4808abcac57ede83724738e5f568ae40771fc4"
REFRESH_TOKEN = "1000.26bcc31d7a1ddc141689c7a11044d34e.73afd2939c5f5ce4940ac697e1ed49d3"
ACCOUNT_ID    = "8585832000000002002"
FROM_ADDRESS  = "kush@mail.fnomo.com"

LOG_FILE = r"C:\Users\kush_\Antigravity\eigent\Downloads\fnomo\bhopal_send_log.txt"

# ── Template routing ─────────────────────────────────────────────────────────
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

SIGNATURE = "\n\nWarm regards,\nKush Trivedi\nBusiness Head, Fnomo.com\n+91 93403 92140"

# ── All 77 unique Bhopal doctor contacts ────────────────────────────────────
RAW_CONTACTS = [
    ("Dr. Ajay Goenka",          "Medicine",          "Chirayu Medical College",     "info@cmchbhopal.com"),
    ("Dr. Skand Kumar Trivedi",  "Cardiology",        "Bansal Hospital",             "skand.trivedi@bansalhospital.com"),
    ("Dr. Gopal Batni",          "Internal Med",      "Apollo Sage Hospital",        "gopal.batni@apollosage.in"),
    ("Dr. Shyam Agrawal",        "Oncology",          "Navodaya Oncology",           "contact@navodaya.com"),
    ("Dr. Kavita Singh",         "Gynaecology",       "GMC / Private Clinic",        "kavita.singh@gmc.edu.in"),
    ("Dr. Aaditya Sirohi",       "CTVS Surgery",      "AIIMS Bhopal",                "aaditya.ctvs@aiimsbhopal.edu.in"),
    ("Dr. Rohit Joshi",          "Child Neuro",       "Bansal Hospital",             "rohit.joshi@bansalhospital.com"),
    ("Dr. Deepti Gupta",         "Gynaecology",       "Bansal Hospital",             "deepti.gupta@bansalhospital.com"),
    ("Dr. Sunil Malik",          "Cardiology",        "Arera Heart Clinic",          "sunil.malik@gmail.com"),
    ("Dr. Amitabh Sonakiya",     "Orthopaedics",      "MP Nagar Clinic",             "amitabh.ortho@yahoo.com"),
    ("Dr. Shiv Shanker",         "Medicine",          "Chirayu Medical College",     "dean@cmchbhopal.com"),
    ("Dr. Nitesh Arora",         "Cardiology",        "Chirayu Hospital",            "nitesh.cardio@cmchbhopal.com"),
    ("Dr. Rajesh Singh",         "Psychiatry",        "AIIMS Bhopal",                "rajesh.psych@aiimsbhopal.edu.in"),
    ("Dr. Rahul Varma",          "ENT Surgery",       "Sagar Multispeciality",       "rahul.varma@smhbhopal.com"),
    ("Dr. Palak Paliwal",        "Gastroenterology",  "Paliwal Hospital",            "palak.paliwal@gmail.com"),
    ("Dr. JP Sharma",            "Anesthesiology",    "AIIMS Bhopal",                "jp.sharma@aiimsbhopal.edu.in"),
    ("Dr. Seetha Lekshmi B",     "Neurology",         "Apollo Sage Hospital",        "seetha.lekshmi@apollosage.in"),
    ("Dr. Onkar Patel",          "Gastroenterology",  "Bansal Hospital",             "onkar.patel@bansalhospital.com"),
    ("Dr. Santosh Agrawal",      "Urology",           "Bansal Hospital",             "santosh.agrawal@bansalhospital.com"),
    ("Dr. Akhil Kumar Tiwari",   "Oncology",          "Apollo Sage Hospital",        "akhil.tiwari@apollosage.in"),
    ("Dr. Ashish Jain",          "Gastroenterology",  "Bansal Hospital",             "ashish.jain@bansalhospital.com"),
    ("Dr. Sanjay Pandey",        "Urology",           "Bansal Hospital",             "sanjay.pandey@bansalhospital.com"),
    ("Dr. Alok Jaiswal",         "Neurosurgery",      "Bansal Hospital",             "alok.jaiswal@bansalhospital.com"),
    ("Dr. Naveen Pundir",        "Oncology",          "Bansal Hospital",             "naveen.pundir@bansalhospital.com"),
    ("Dr. Manish Jain",          "Nephrology",        "Apollo Sage Hospital",        "manish.jain@apollosage.in"),
    ("Dr. Shweta Singh",         "Gynaecology",       "Apollo Sage Hospital",        "shweta.singh@apollosage.in"),
    ("Dr. Ankur Gupta",          "Orthopaedics",      "Apollo Sage Hospital",        "ankur.gupta@apollosage.in"),
    ("Dr. Varun Mittal",         "Gastroenterology",  "Apollo Sage Hospital",        "varun.mittal@apollosage.in"),
    ("Dr. Ritesh Kansal",        "Neurosurgery",      "Apollo Sage Hospital",        "ritesh.kansal@apollosage.in"),
    ("Dr. Preeti Jain",          "Pediatrics",        "Apollo Sage Hospital",        "preeti.jain@apollosage.in"),
    ("Dr. Pankaj Sharma",        "Pulmonology",       "Apollo Sage Hospital",        "pankaj.sharma@apollosage.in"),
    ("Dr. Swati Gupta",          "ENT Surgery",       "Apollo Sage Hospital",        "swati.gupta@apollosage.in"),
    ("Dr. Manoj Kesarwani",      "Urology",           "Apollo Sage Hospital",        "manoj.kesarwani@apollosage.in"),
    ("Dr. Deepthi S",            "Dermatology",       "Apollo Sage Hospital",        "deepthi.s@apollosage.in"),
    ("Dr. Swapnil",              "Neurosurgery",      "Peoples Hospital",            "swapnil.neuro@peoples.org"),
    ("Dr. S.N. Singh",           "Orthopaedics",      "Peoples Hospital",            "sn.singh@peopleshospital.org"),
    ("Dr. Neeraj Shrivastava",   "Internal Med",      "Peoples Hospital",            "neeraj.s@peoples.org"),
    ("Dr. Anjali Gupta",         "Gynaecology",       "Peoples Hospital",            "anjali.g@peoples.org"),
    ("Dr. Gaurav Gupta",         "ENT Surgery",       "Peoples Hospital",            "gaurav.g@peoples.org"),
    ("Dr. Hemant Verma",         "Ophthalmology",     "Peoples Hospital",            "hemant.v@peoples.org"),
    ("Dr. Rajiv Singh",          "Psychiatry",        "Peoples Hospital",            "rajiv.s@peoples.org"),
    ("Dr. S.K. Sharma",          "Dermatology",       "Peoples Hospital",            "sk.sharma@peoples.org"),
    ("Dr. Manish Sahu",          "Dentistry",         "Peoples Hospital",            "manish.s@peoples.org"),
    ("Dr. P.K. Rai",             "Cardiology",        "Peoples Hospital",            "pk.rai@peoples.org"),
    ("Dr. Sunita Jain",          "Paediatrics",       "Peoples Hospital",            "sunita.j@peoples.org"),
    ("Dr. Anil Gupta",           "Orthopaedics",      "Noble Multispeciality",       "anil.gupta@noblebhopal.com"),
    ("Dr. Rekha Jain",           "Gynaecology",       "Noble Multispeciality",       "rekha.jain@noblebhopal.com"),
    ("Dr. Vikas Shrivastava",    "Internal Med",      "Noble Multispeciality",       "vikas.s@noblebhopal.com"),
    ("Dr. Rahul Saini",          "Paediatrics",       "Noble Multispeciality",       "rahul.s@noblebhopal.com"),
    ("Dr. Neeraj Kumar",         "Surgery",           "Noble Multispeciality",       "neeraj.k@noblebhopal.com"),
    ("Dr. Pooja Sharma",         "Pathology",         "Noble Multispeciality",       "pooja.s@noblebhopal.com"),
    ("Dr. Sameer Gupta",         "Radiology",         "Noble Multispeciality",       "sameer.g@noblebhopal.com"),
    ("Dr. Arun Kumar",           "Orthopaedics",      "Sahara Fracture Hosp",        "arun.k@saharaortho.com"),
    ("Dr. K.K. Shrivastava",     "Orthopaedics",      "Sahara Fracture Hosp",        "kk.s@saharaortho.com"),
    ("Dr. Santosh Choudhary",    "Ophthalmology",     "Sagar Multispeciality",       "contact@smhbhopal.com"),
    ("Dr. Jai Prakash Paliwal",  "Surgery",           "Paliwal Hospital",            "paliwal.hospital@gmail.com"),
    ("Dr. Shashi Gandhi",        "Microbiology",      "GMC Bhopal",                  "shashi.gandhi@gmc.edu.in"),
    ("Dr. Roopesh Jain",         "Medicine",          "JK Hospital",                 "roopesh.jain@jkhospital.org"),
    ("Dr. Ram Kumar Agrawal",    "Orthopaedics",      "Kasturba BHEL",               "rk.agrawal@bhel.in"),
    ("Dr. Sheela Malani",        "Internal Med",      "Kasturba BHEL",               "sheela.malani@bhel.in"),
    ("Dr. Atulya Saurabh",       "Medicine",          "Kasturba BHEL",               "atulya.saurabh@bhel.in"),
    ("Dr. Sunil Rathore",        "Plastic Surgery",   "Bansal Hospital",             "sunil.rathore@bansalhospital.com"),
    ("Dr. Mayur Agarwal",        "Endocrinology",     "Gulmohar Clinic",             "mayur.endo@gmail.com"),
    ("Dr. Pankaj Kumar Mishra",  "Nephrology",        "Bansal Hospital",             "pankaj.mishra@bansalhospital.com"),
    ("Dr. Alok Gupta",           "Oncology",          "Navodaya Oncology",           "alokguptaonco@gmail.com"),
    ("Dr. Nitya Bisarya",        "Anaesthesia",       "Apollo Sage Hospital",        "nitya.bisarya@apollosage.in"),
    ("Dr. Manoj Paliwal",        "Microbiology",      "GMC Bhopal",                  "manoj.paliwal@gmc.edu.in"),
    ("Dr. Richa Sharma",         "Medicine",          "Mansarovar Medical Col",      "richa.sharma@mansarovarmc.com"),
    ("Dr. Ashutosh Badwik",      "Medicine",          "Mansarovar Medical Col",      "admin@mansarovarmc.com"),
    ("Dr. Nirendra Kumar Rai",   "Neurology",         "Apollo Sage Hospital",        "nirendra.rai@apollosage.in"),
    ("Dr. Sandeep Choudhary",    "Psychiatry",        "Chirayu Hospital",            "sandeep.c@cmchbhopal.com"),
    ("Dr. Alpa Prabhu",          "Gynaecology",       "Sagar Multispeciality",       "spsgn@spsbhopal.ac.in"),
    ("Dr. Shraddha Kanungo",     "Gynaecology",       "Sagar Multispeciality",       "shraddhakanungo@spsbhopal.ac.in"),
    ("Dr. Prachi Varma",         "Gynaecology",       "Sagar Multispeciality",       "prachi.v@smhbhopal.com"),
    ("Dr. Ashish Saraogi",       "Surgery",           "LBS Hospital",                "ashish.saraogi@lbshospital.com"),
    ("Dr. Avadhesh N Khare",     "Cardiology",        "LBS Hospital",                "avadhesh.khare@lbshospital.com"),
    ("Dr. A D Suri",             "Nephrology",        "LBS Hospital",                "ad.suri@lbshospital.com"),
]


def build_contacts():
    seen = set()
    contacts = []
    for full_name, specialty, hospital, email in RAW_CONTACTS:
        email = email.strip()
        if not email or email in seen:
            continue
        seen.add(email)
        name_parts = full_name.replace("Dr. ", "").strip().split()
        greeting = f"Hi Dr. {name_parts[-1]}" if name_parts else f"Hi {full_name}"
        contacts.append({
            "full_name": full_name,
            "specialty": specialty,
            "hospital":  hospital,
            "email":     email,
            "greeting":  greeting,
        })
    return contacts


def get_template(greeting, specialty, hospital):
    s = specialty.lower()
    h = hospital.lower()

    # Priority 1: Academic / Government hospital
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
            "Would a 15-minute walkthrough be useful? Happy to set one up at your "
            "convenience.\n\n"
            "You can explore it here: https://fnomo.com (free sign-up)"
        )
        return subject, body + SIGNATURE

    # Priority 2: Surgeons (in OT, time-starved)
    if any(sp in s for sp in SURGEON_SPECIALTIES):
        subject = "For doctors who don't have time to watch the market"
        body = (
            f"{greeting},\n\n"
            "Between back-to-back procedures, tracking your investments is nearly "
            "impossible — and most of us end up just trusting whatever our broker "
            "or CA says.\n\n"
            "Fnomo is a stock analysis platform that helps you do a two-minute sanity "
            "check on any stock before you put money in, or before you act on "
            "someone's tip.\n\n"
            "Color-coded, plain language. Not trading — flat subscription, so we earn "
            "on that, not when you invest.\n\n"
            "If a short demo would be useful, I'm happy to set one up at your "
            "convenience.\n\n"
            "Explore here: https://fnomo.com (free sign-up)"
        )
        return subject, body + SIGNATURE

    # Priority 3: Physicians / analytical specialists
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

    # Default: Private clinic / general
    subject = "A tool built for busy professionals — like you"
    body = (
        f"{greeting},\n\n"
        "Managing patient care and your own finances at the same time is genuinely "
        "hard — most of us end up delegating investments to someone else and hoping "
        "for the best.\n\n"
        "Fnomo is a stock analysis platform (not trading) that lets you do a quick, "
        "clear check on any investment before you commit. Color-coded, no finance "
        "background needed.\n\n"
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
    print(f"Total unique contacts: {len(contacts)}\n")

    print("Refreshing Zoho token...")
    token = refresh_token()
    print("Token OK. Starting sends...\n")

    sent = 0
    failed = 0
    log_lines = []

    for i, c in enumerate(contacts, 1):
        subject, body = get_template(c["greeting"], c["specialty"], c["hospital"])
        status, resp_data = send_email(token, c["email"], subject, body)

        if status == 200:
            sent += 1
            result = "SENT"
        else:
            failed += 1
            result = f"FAIL({status}) {resp_data}"

        line = f"[{i:02d}/{len(contacts)}] {result} | {c['specialty']:<22} | {c['email']}"
        print(line)
        log_lines.append(f"{line} | {c['full_name']}")

        time.sleep(0.3)

        # Refresh token every 50 emails
        if i % 50 == 0:
            try:
                token = refresh_token()
                print(f"   ↻ Token refreshed at #{i}")
            except Exception as e:
                print(f"   ✗ Token refresh failed: {e}")

    # Write log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Bhopal Outreach Send Log\n")
        f.write(f"Total unique contacts: {len(contacts)}\n")
        f.write(f"Sent: {sent}  |  Failed: {failed}\n")
        f.write("=" * 80 + "\n\n")
        f.write("\n".join(log_lines))

    print(f"\n{'='*50}")
    print(f"DONE — Sent: {sent} | Failed: {failed}")
    print(f"Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
