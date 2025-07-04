#!/usr/bin/env python3
"""
Simple test script for the Interactive Agent API
"""

import requests
import json

def test_interactive_agent():
    """Test the interactive agent endpoint"""
    
    base_url = "http://localhost:5001"
    endpoint = f"{base_url}/api/interactive"
    
    print("Testing Interactive Agent API...")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.post(endpoint, json={
            "question": "ping"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['message']}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    # Test 2: Start new conversation
    print("\n2. Testing new conversation...")
    try:
        response = requests.post(endpoint, json={
            "question": "",
            "force_new_session": True
        })
        
        if response.status_code == 200:
            data = response.json()
            session_id = data['session_id']
            print(f"✓ New conversation started")
            print(f"  Session ID: {session_id}")
            print(f"  Response: {data['data']['analysis'][:100]}...")
        else:
            print(f"✗ New conversation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ New conversation error: {e}")
        return False
    
    # Test 3: Send a message
    print("\n3. Testing message sending...")
    try:
        response = requests.post(endpoint, json={
            "question": "Hello! Can you help me with a simple question?",
            "session_id": session_id
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Message sent successfully")
            print(f"  Response: {data['data']['analysis'][:200]}...")
        else:
            print(f"✗ Message sending failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Message sending error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! Interactive Agent is working correctly.")
    return True

def test_server_connection():
    """Test if the server is running"""
    try:
        response = requests.get("http://localhost:5001/health")
        if response.status_code == 200:
            print("✓ Server is running")
            return True
        else:
            print(f"✗ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("Make sure the backend server is running on port 5001")
        return False

if __name__ == "__main__":
    print("Interactive Agent Test Suite")
    print("=" * 50)
    
    # First check if server is running
    if not test_server_connection():
        print("\nPlease start the backend server first:")
        print("cd AiJusticeGridPrototype/AiJusticegrid/backend")
        print("python app.py")
        exit(1)
    
    # Run the tests
    if test_interactive_agent():
        print("\n🎉 Interactive Agent is ready to use!")
    else:
        print("\n❌ Some tests failed. Please check the server logs.")
