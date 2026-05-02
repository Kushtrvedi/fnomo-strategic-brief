import sys
import json
import subprocess
import datetime
import os

def send_email(to, subject, body, user_email):
    # Use the full path to accio-mcp-cli.cmd on Windows
    accio_path = r"C:\Users\kush_\AppData\Roaming\Accio\pre-install\906b605a3eb4\accio-mcp-cli.cmd"
    cmd = [
        accio_path, "call", "send_gmail_message",
        "--json", json.dumps({
            "to": to,
            "subject": subject,
            "body": body,
            "user_google_email": user_email,
            "body_format": "plain"
        })
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result

def update_state(email, status, message_id=None):
    state_file = 'sending_state.json'
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
    else:
        state = {"total_leads": 0, "sent_count": 0, "leads": []}
    
    found = False
    for lead in state['leads']:
        if lead['email'] == email:
            lead['status'] = status
            lead['timestamp'] = datetime.datetime.now().isoformat()
            lead['message_id'] = message_id
            found = True
            break
    
    if not found:
        state['leads'].append({
            "email": email,
            "status": status,
            "timestamp": datetime.datetime.now().isoformat(),
            "message_id": message_id
        })
    
    if status == 'sent':
        state['sent_count'] = sum(1 for l in state['leads'] if l['status'] == 'sent')
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

if __name__ == "__main__":
    # Usage: python send_one_outreach.py <email> <name> <subject> <body_file>
    email = sys.argv[1]
    name = sys.argv[2]
    subject = sys.argv[3]
    body_file = sys.argv[4]
    user_email = "kushtrivedi88@gmail.com"
    
    with open(body_file, 'r', encoding='utf-8') as f:
        body = f.read()
    
    print(f"Sending email to {name} ({email})...")
    res = send_email(email, subject, body, user_email)
    
    if res.returncode == 0:
        if "Email sent!" in res.stdout:
            # Extract message ID from string like "Email sent! Message ID: 19ddef65e486496e"
            try:
                message_id = res.stdout.split("Message ID: ")[1].strip()
                update_state(email, 'sent', message_id)
                print(f"Successfully sent to {email}. Message ID: {message_id}")
            except:
                update_state(email, 'sent', "unknown")
                print(f"Successfully sent to {email} (id parsing failed).")
        else:
            try:
                output = json.loads(res.stdout)
                message_id = output.get('id') or output.get('message_id') or "unknown"
                update_state(email, 'sent', message_id)
                print(f"Successfully sent to {email}. Message ID: {message_id}")
            except Exception as e:
                update_state(email, 'sent', "unknown")
                print(f"Successfully sent to {email} (json parsing failed).")
    else:
        update_state(email, 'failed')
        print(f"Error sending to {email}: {res.stderr}")
