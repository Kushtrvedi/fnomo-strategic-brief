import re

def extract_data(line):
    # Skip header and empty lines
    if not line.strip() or '|' not in line or 'Full Name' in line or ':---' in line:
        return None
    
    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 6:
        return None
    
    # Name is in parts[1], e.g., "**Dr. Ajay Goenka**"
    full_name_raw = parts[1].strip()
    full_name = full_name_raw.replace('**', '').replace('Dr.', '').strip()
    
    # Specialty is in parts[2]
    specialty = parts[2].strip()
    
    # Hospital is in parts[4]
    hospital = parts[4].strip()
    
    # Email is in parts[5], e.g., "`info@cmchbhopal.com`" or "`info@cmchbhopal.com\""
    email_raw = parts[5].strip()
    # Remove any backticks, quotes, or trailing spaces
    email = email_raw.replace('`', '').replace('"', '').replace('\'', '').strip()
    
    if not email or '@' not in email:
        return None
    
    return {
        'full_name': full_name,
        'specialty': specialty,
        'hospital': hospital,
        'email': email
    }

def get_salutation(full_name):
    name_parts = full_name.split()
    if len(name_parts) == 2:
        return f"Hi Dr. {name_parts[1]},"
    else:
        return f"Hi Dr. {full_name},"

template = """{salutation}
Happy to introduce Fnomo.com.
We are a new start-up and we’ve recently launched a software designed for professionals like you — who often have limited time to manage investments and sometimes rely on others for decisions.
Fnomo is a stock analysis platform (not trading).
We don’t earn when you trade — it works on a simple subscription model, so there’s no conflict of interest.
Think of it like Google for your investments.
Before you put your money or act on someone’s advice, you can use Fnomo to check and validate your decision clearly.
You can explore it here:
https://fnomo.com and do free sign-up 
Everything is simple and color-coded, so even non-finance users can understand it easily.
If helpful, I can arrange a quick demo to walk you through it.

Warm regards,
Kush Trivedi, Business Head ,9340392140 ."""

input_file = 'Bhopal_Doctors_Database_Ultra.md'
output_file = 'Bhopal_Doctors_Personalized_Outreach.md'

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except Exception as e:
    # Try alternative path if needed, but here it should be in current dir
    import os
    abs_path = os.path.join(os.getcwd(), input_file)
    with open(abs_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

personalized_messages = []
seen_doctors = set() # To avoid duplicates if the list repeats

for line in lines:
    data = extract_data(line)
    if data:
        # print(f"DEBUG: Found {data['full_name']}")
        # Create a unique key to avoid exact duplicates
        key = (data['full_name'], data['email'])
        # if key in seen_doctors:
        #    continue
        seen_doctors.add(key)
        
        salutation = get_salutation(data['full_name'])
        message = template.format(salutation=salutation)
        
        # Add metadata header for each message
        header = f"### To: Dr. {data['full_name']} | {data['specialty']} | {data['hospital']}\n**Email:** {data['email']}\n\n"
        personalized_messages.append(header + message + "\n\n---\n\n")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Bhopal Doctors Personalized Outreach Messages\n\n")
    f.write(f"Total Personalized Messages: {len(personalized_messages)}\n\n")
    f.writelines(personalized_messages)

print(f"Generated {len(personalized_messages)} messages in {output_file}")
print(f"Unique doctors: {len(seen_doctors)}")
