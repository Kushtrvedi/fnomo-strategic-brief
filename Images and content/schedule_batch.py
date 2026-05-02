import json
import random
import os
import subprocess

def schedule_batch():
    with open('batch_doctors.json', 'r', encoding='utf-8') as f:
        doctors = json.load(f)
    
    # Batch 1: Doctors 2-31 (indices 1 to 30)
    # The prompt says "extract recipients 2-30" which is 29 people.
    # But then says "Once 30 emails are sent".
    # I will take 30 doctors starting from index 1.
    batch = doctors[1:31]
    
    if not os.path.exists('email_bodies'):
        os.makedirs('email_bodies')
    
    subject = "Introduction to Fnomo.com - Stock Analysis for Professionals"
    current_delay_ms = 0
    
    scheduled_count = 0
    for i, doc in enumerate(batch):
        # Create body file
        body_path = f"email_bodies/body_{i+1}.txt"
        with open(body_path, 'w', encoding='utf-8') as f:
            f.write(doc['body'])
        
        # Staggered delay: 2-5 min (120-300s)
        # First email can go almost immediately or after 2 min.
        # Let's start with a small delay for the first one.
        delay_s = random.randint(120, 300)
        current_delay_ms += delay_s * 1000
        
        # Prepare cron job
        job_name = f"Outreach_{i+1}_{doc['email']}"
        command = f'python send_one_outreach.py "{doc["email"]}" "{doc["name"]}" "{subject}" "{body_path}"'
        
        payload = {
            "kind": "command",
            "command": command
        }
        
        schedule = {
            "kind": "in",
            "inMs": current_delay_ms
        }
        
        # Use accio-mcp-cli to call cron tool if available, or I'll just use the cron tool directly if I can
        # But I am the agent, I should use the cron tool.
        # Wait, I can't call tools inside a loop easily if I want to be efficient.
        # I'll just print the commands and run them via bash in one go? 
        # No, I should call the cron tool 30 times.
        
        scheduled_count += 1
        print(f"Scheduling {job_name} in {current_delay_ms/1000}s")
        
        # I will return the list of cron add calls to the agent
    
    return batch, current_delay_ms

if __name__ == "__main__":
    batch, total_time = schedule_batch()
    print(f"Prepared {len(batch)} emails. Total duration: {total_time/1000/60:.2f} minutes.")
