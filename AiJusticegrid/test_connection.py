#!/usr/bin/env python3
import requests
import json

def test_murder_agent():
    url = "http://localhost:5001/api/murder"
    data = {
        "question": "ping"
    }
    
    try:
        print("Testing Murder Agent connection...")
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_cybercrime_agent():
    url = "http://localhost:5001/api/cyber"
    data = {
        "question": "ping"
    }
    
    try:
        print("Testing Cybercrime Agent connection...")
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_health():
    url = "http://localhost:5001/health"
    
    try:
        print("Testing Health endpoint...")
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Backend Connections ===")
    
    health_ok = test_health()
    murder_ok = test_murder_agent()
    cyber_ok = test_cybercrime_agent()
    
    print(f"\n=== Results ===")
    print(f"Health endpoint: {'✓' if health_ok else '✗'}")
    print(f"Murder agent: {'✓' if murder_ok else '✗'}")
    print(f"Cybercrime agent: {'✓' if cyber_ok else '✗'}")
    
    if all([health_ok, murder_ok, cyber_ok]):
        print("\n🎉 All endpoints working!")
    else:
        print("\n❌ Some endpoints have issues")
