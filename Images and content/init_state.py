import json
import os

def initialize_state():
    with open('batch_doctors.json', 'r', encoding='utf-8') as f:
        doctors = json.load(f)
    
    # Batch 1: Doctors 2-31 (indices 1 to 30)
    batch = doctors[1:31]
    
    state = {
        "total_leads": 246,
        "sent_count": 0,
        "leads": []
    }
    
    for doc in batch:
        state['leads'].append({
            "email": doc['email'],
            "name": doc['name'],
            "status": "pending",
            "timestamp": None,
            "message_id": None
        })
    
    with open('sending_state.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

if __name__ == "__main__":
    initialize_state()
    print("Initialized sending_state.json with 30 pending leads.")
