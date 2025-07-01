#!/usr/bin/env python3
import requests
import json

# Test data for murder investigation
test_responses = [
    "CASE-2024-TEST",
    "2024-01-15", 
    "10:30 PM",
    "Downtown apartment building",
    "John Smith",
    "35",
    "Male",
    "Gunshot wound to chest",
    "9mm pistol",
    "Michael Johnson",
    "Tall, dark hair, wearing black jacket",
    "Neighbor heard argument and gunshots",
    "Shell casings, fingerprints on door handle, blood evidence"
]

def test_murder_investigation():
    base_url = "http://localhost:5001/api/murder"
    
    # Start new session
    response = requests.post(base_url, json={
        "question": "",
        "force_new_session": True
    })
    
    if response.status_code != 200:
        print(f"Failed to start session: {response.status_code}")
        return
    
    data = response.json()
    session_id = data["session_id"]
    print(f"Started session: {session_id}")
    print(f"First message: {data['data']['analysis']}")
    
    # Go through all the questions
    for i, answer in enumerate(test_responses):
        print(f"\nStep {i+1}: Sending '{answer}'")
        
        response = requests.post(base_url, json={
            "question": answer,
            "session_id": session_id
        })
        
        if response.status_code != 200:
            print(f"Failed at step {i+1}: {response.status_code}")
            break
            
        data = response.json()
        print(f"Response: {data['data']['analysis'][:100]}...")
        
        if not data['data']['is_collecting_info']:
            print("\n=== ANALYSIS COMPLETE ===")
            print(data['data']['analysis'])
            break
    
    return session_id

if __name__ == "__main__":
    test_murder_investigation()
