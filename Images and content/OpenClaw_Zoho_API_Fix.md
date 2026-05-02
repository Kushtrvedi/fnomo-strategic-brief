# OpenClaw — Zoho Mail API Access Guide
**Status: CONFIRMED WORKING** | Tested: 25 April 2026 | From: FNOMO Team

---

## What Was Wrong (Root Cause)

OpenClaw's agent drew the wrong conclusion. The Zoho Mail API is **NOT disabled** and does **NOT require admin reconfiguration**. The failures were caused by three code-level mistakes:

| Error Seen | Actual Cause | Fix |
|---|---|---|
| `EXTRA_KEY_FOUND_IN_JSON` | Wrong payload field names | Use `toAddress`, `content`, `fromAddress` |
| `URL_RULE_NOT_CONFIGURED` | Wrong endpoint (`/sendMail` doesn't exist) | Use `/messages` endpoint |
| Connection failures | Wrong base URL (`.com` instead of `.eu`) | Use `mail.zoho.eu` |

---

## Working Configuration (Verified)

### Credentials (.env)
```
ZOHO_CLIENT_ID=1000.SP0SD2VJL9TD4KTSOZZUR1Y4DC1BIF
ZOHO_CLIENT_SECRET=a24b610c3247d33650fcc64d098475572266a3f5cf
ZOHO_REFRESH_TOKEN=1000.ccac70a5de34427c4b7d69c5cfb74748.38fe2067305b4b98970efe47e6288f33
ZOHO_ACCOUNT_ID=8585832000000002002
SENDER_EMAIL=kush@mail.fnomo.com
```

### Token Refresh Endpoint
```
POST https://accounts.zoho.eu/oauth/v2/token
```
Parameters:
```
grant_type=refresh_token
client_id=<ZOHO_CLIENT_ID>
client_secret=<ZOHO_CLIENT_SECRET>
refresh_token=<ZOHO_REFRESH_TOKEN>
```
Returns `access_token` valid for 3600 seconds.

### Send Email Endpoint
```
POST https://mail.zoho.eu/api/accounts/8585832000000002002/messages
```

**Critical notes:**
- Domain is `zoho.eu` NOT `zoho.com`
- Path is `/api/accounts/` NOT `/api/v1/accounts/`
- Endpoint is `/messages` NOT `/sendMail`

### Request Headers
```
Authorization: Zoho-oauthtoken <access_token>
Content-Type: application/json
```

### Correct Payload Shape
```json
{
  "fromAddress": "kush@mail.fnomo.com",
  "toAddress":   "recipient@example.com",
  "subject":     "Your subject here",
  "content":     "Email body text here",
  "mailFormat":  "plaintext"
}
```

**Field names that will cause `EXTRA_KEY_FOUND_IN_JSON` if used (DO NOT USE):**
- `to` → use `toAddress` instead
- `body` → use `content` instead
- `from` → use `fromAddress` instead
- `text` → use `content` instead
- `html` → use `content` with `"mailFormat": "html"` instead

### Optional: Schedule for Future Send
Add `scheduleTime` as epoch milliseconds:
```json
{
  "fromAddress":  "kush@mail.fnomo.com",
  "toAddress":    "recipient@example.com",
  "subject":      "Your subject",
  "content":      "Email body",
  "mailFormat":   "plaintext",
  "scheduleTime": 1745827200000
}
```

---

## Verified Test Result

```
HTTP 200
{
  "status": { "code": 200, "description": "success" },
  "data": {
    "subject": "Zoho API Test",
    "messageId": "1777080126855001200",
    "fromAddress": "kush@mail.fnomo.com",
    "toAddress": "info@busybulls.com",
    "mailFormat": "plaintext"
  }
}
```

---

## Working Python Implementation

```python
import requests
import time

# Credentials
CLIENT_ID     = "1000.SP0SD2VJL9TD4KTSOZZUR1Y4DC1BIF"
CLIENT_SECRET = "a24b610c3247d33650fcc64d098475572266a3f5cf"
REFRESH_TOKEN = "1000.ccac70a5de34427c4b7d69c5cfb74748.38fe2067305b4b98970efe47e6288f33"
ACCOUNT_ID    = "8585832000000002002"
SENDER_EMAIL  = "kush@mail.fnomo.com"

TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
MAIL_URL  = f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}/messages"


def get_access_token():
    resp = requests.post(TOKEN_URL, params={
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_email(to_address, subject, body):
    token = get_access_token()
    payload = {
        "fromAddress": SENDER_EMAIL,
        "toAddress":   to_address,
        "subject":     subject,
        "content":     body,
        "mailFormat":  "plaintext",
    }
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type":  "application/json",
    }
    resp = requests.post(MAIL_URL, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


# Example usage
result = send_email(
    to_address="recipient@example.com",
    subject="Hello from OpenClaw",
    body="This is a test email."
)
print(result)
```

---

## What NOT To Do (OpenClaw Agent's Mistakes)

```python
# WRONG — all of these will fail

# Wrong domain
url = "https://mail.zoho.com/api/v1/accounts/{id}/messages"  # .com and /v1/ both wrong

# Wrong endpoint
url = "https://mail.zoho.eu/api/v1/accounts/{id}/sendMail"   # /v1/ and sendMail both wrong

# Wrong payload fields
payload = {
    "to":      ["recipient@example.com"],   # wrong — array not allowed, wrong key
    "from":    "sender@example.com",        # wrong key
    "body":    "Email text",                # wrong key
    "subject": "Subject",
}
```

---

## Summary

The API was working the entire time. No Zoho admin changes were needed.
Use `mail.zoho.eu`, `/api/accounts/{id}/messages`, and the exact field names above.
The refresh token does not expire unless manually revoked — no re-authentication needed.
