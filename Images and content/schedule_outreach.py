import json
import random
import os
import subprocess
import time

def schedule_outreach():
    with open('batch_doctors.json', 'r', encoding='utf-8') as f:
        doctors = json.load(f)
    
    # Batch 1: Doctors 2-31 (indices 1 to 30)
    batch = doctors[1:31]
    
    if not os.path.exists('email_bodies'):
        os.makedirs('email_bodies')
    
    subject = "Introduction to Fnomo.com - Stock Analysis for Professionals"
    current_delay_ms = 0
    
    for i, doc in enumerate(batch):
        body_path = os.path.abspath(f"email_bodies/body_{i+1}.txt")
        with open(body_path, 'w', encoding='utf-8') as f:
            f.write(doc['body'])
        
        # Staggered delay: 2-5 min
        delay_s = random.randint(120, 300)
        current_delay_ms += delay_s * 1000
        
        # Command to send email and update state
        command = f'python "{os.path.abspath("send_one_outreach.py")}" "{doc["email"]}" "{doc["name"]}" "{subject}" "{body_path}"'
        
        # Schedule via cron
        job_name = f"Outreach_{i+1}"
        cron_payload = {
            "action": "add",
            "name": job_name,
            "schedule": {"kind": "in", "inMs": current_delay_ms},
            "payload": {"kind": "command", "command": command}
        }
        
        # Call cron tool via accio-mcp-cli (or just print for now and I'll call it)
        # Actually, I'll use subprocess to call it directly from here to be faster
        cron_json = json.dumps(cron_payload)
        # Using the tool's interface is better, but since I'm in a script...
        # Wait, I'll just make the script output the tool calls and I'll execute them.
        print(json.dumps(cron_payload))

if __name__ == "__main__":
    schedule_outreach()
