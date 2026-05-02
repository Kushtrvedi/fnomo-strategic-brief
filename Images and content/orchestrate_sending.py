import re
import json
import os
import time
import random
import subprocess

OUTREACH_FILE = 'Bhopal_Doctors_Personalized_Outreach.md'
STATE_FILE = 'sending_state.json'
USER_EMAIL = 'kush@fnomo.com' # Placeholder, will need to be confirmed or extracted if possible
SUBJECT = 'Improving Investment Decisions for Doctors - Introduction to Fnomo'

def parse_outreach_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by the separator ---
    sections = re.split(r'\n---\n', content)
    leads = []
    
    for section in sections:
        if '### To:' not in section:
            continue
            
        # Extract Name/Header
        header_match = re.search(r'### To: (.*?)\n', section)
        email_match = re.search(r'\*\*Email:\*\* (.*?)\n', section)
        
        if header_match and email_match:
            header = header_match.group(1)
            email = email_match.group(1).strip()
            
            # Extract name from header (before the first |)
            name = header.split('|')[0].strip()
            
            # Extract body (everything after the Email line)
            body_parts = section.split(f'**Email:** {email}')
            if len(body_parts) > 1:
                body = body_parts[1].strip()
                leads.append({
                    'name': name,
                    'email': email,
                    'body': body
                })
                
    return leads

def initialize_state(leads):
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    
    state = {
        'total_leads': len(leads),
        'sent_count': 0,
        'leads': []
    }
    
    for lead in leads:
        state['leads'].append({
            'email': lead['email'],
            'name': lead['name'],
            'status': 'pending',
            'timestamp': None,
            'message_id': None,
            'body': lead['body'] # Store body to avoid re-parsing
        })
        
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    return state

def save_state(state):
    state['sent_count'] = sum(1 for l in state['leads'] if l['status'] == 'sent')
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def send_email(lead, user_email):
    print(f"Sending email to {lead['name']} ({lead['email']})...")
    
    # Using accio-mcp-cli call send_gmail_message
    # Note: In a real script, we'd use subprocess or a library
    cmd = [
        'accio-mcp-cli', 'call', 'send_gmail_message',
        '--json', json.dumps({
            'to': lead['email'],
            'subject': SUBJECT,
            'body': lead['body'],
            'user_google_email': user_email,
            'body_format': 'plain'
        })
    ]
    
    try:
        # In this simulation, we'll just print the command or use a mock
        # result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # response = json.loads(result.stdout)
        
        # Mock success for now
        print(f"Success: Sent to {lead['email']}")
        return {"status": "sent", "message_id": "mock_id_" + str(random.randint(1000, 9999))}
    except Exception as e:
        print(f"Error sending to {lead['email']}: {e}")
        return {"status": "failed", "error": str(e)}

def orchestrate(batch_size=30):
    leads = parse_outreach_file(OUTREACH_FILE)
    state = initialize_state(leads)
    
    pending_leads = [l for l in state['leads'] if l['status'] == 'pending']
    to_send = pending_leads[:batch_size]
    
    print(f"Starting batch of {len(to_send)} emails.")
    
    for i, lead in enumerate(to_send):
        # Determine the user email - ideally this is passed in or configured
        # For now we use the placeholder
        res = send_email(lead, USER_EMAIL)
        
        # Update lead in state
        for s_lead in state['leads']:
            if s_lead['email'] == lead['email']:
                s_lead['status'] = res.get('status')
                s_lead['message_id'] = res.get('message_id')
                s_lead['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                if 'error' in res:
                    s_lead['error'] = res['error']
                break
        
        save_state(state)
        
        if i < len(to_send) - 1:
            delay = random.randint(120, 300)
            print(f"Waiting for {delay} seconds before next send...")
            # time.sleep(delay) # Commented out for the orchestration logic definition phase

if __name__ == '__main__':
    # orchestrate(30)
    pass
