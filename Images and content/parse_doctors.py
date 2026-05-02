import re
import json
import os

def parse_outreach_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by separator ---
    sections = re.split(r'\n---', content)
    doctors = []
    
    for section in sections:
        # Extract name
        name_match = re.search(r'### To: (.*)', section)
        if not name_match:
            continue
        name = name_match.group(1).split('|')[0].strip()
        
        # Extract email
        email_match = re.search(r'\*\*Email:\*\* (.*)', section)
        if not email_match:
            continue
        email = email_match.group(1).strip()
        
        # Extract body (everything after Email until the end or Warm regards)
        # body starts after the line with Email
        body_parts = section.split('\n')
        body_lines = []
        found_email = False
        for line in body_parts:
            if '**Email:**' in line:
                found_email = True
                continue
            if found_email:
                body_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        
        doctors.append({
            'name': name,
            'email': email,
            'body': body
        })
    
    return doctors

if __name__ == "__main__":
    doctors = parse_outreach_file('Bhopal_Doctors_Personalized_Outreach.md')
    # Save first 50 doctors to a temporary json for processing
    with open('batch_doctors.json', 'w', encoding='utf-8') as f:
        json.dump(doctors[:50], f, indent=2)
    print(f"Extracted {len(doctors)} doctors. Saved first 50 to batch_doctors.json")
