#!/usr/bin/env python3
"""
Test script for the Murder Agent API
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:5001"
API_ENDPOINT = f"{API_BASE_URL}/api/murder"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Health Check Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_murder_agent_conversation():
    """Test the complete murder agent conversation flow"""

    # Test data matching the example conversation
    conversation_data = [
        {"question": "", "expected_field": "case_id"},  # Initial greeting
        {"question": "002", "expected_field": "date_of_crime"},
        {"question": "2000-05-12", "expected_field": "time_of_crime"},
        {"question": "12:30 am", "expected_field": "location"},
        {"question": "italy", "expected_field": "victim_name"},
        {"question": "itaniey", "expected_field": "victim_age"},
        {"question": "34", "expected_field": "victim_gender"},
        {"question": "male", "expected_field": "cause_of_death"},
        {"question": "test", "expected_field": "weapon_used"},
        {"question": "test", "expected_field": "crime_scene_description"},
        {"question": "test", "expected_field": "witnesses"},
        {"question": "test", "expected_field": "evidence_found"},
        {"question": "test", "expected_field": "suspects"},
        {"question": "test", "expected_field": "additional_notes"},
        {"question": "test", "expected_field": "analysis"}
    ]

    session_id = None

    print("Starting Murder Agent Conversation Test...")
    print("=" * 50)

    for i, data in enumerate(conversation_data):
        print(f"\nStep {i + 1}: {data['expected_field']}")
        print("-" * 30)

        payload = {
            "question": data["question"]
        }

        if session_id:
            payload["session_id"] = session_id

        try:
            response = requests.post(API_ENDPOINT, json=payload)

            if response.status_code == 200:
                result = response.json()

                if result["success"]:
                    session_id = result["session_id"]
                    analysis = result["data"]["analysis"]
                    current_step = result["data"]["current_step"]
                    is_collecting_info = result["data"]["is_collecting_info"]

                    print(f"Session ID: {session_id}")
                    print(f"Current Step: {current_step}")
                    print(f"Is Collecting Info: {is_collecting_info}")
                    print(f"Response: {analysis[:200]}...")

                    if current_step == "completed":
                        print("\n" + "=" * 50)
                        print("FINAL ANALYSIS RECEIVED!")
                        print("=" * 50)
                        print(analysis)

                        # Test PDF download
                        print("\n" + "=" * 50)
                        print("TESTING PDF DOWNLOAD...")
                        print("=" * 50)
                        test_pdf_download(session_id)
                        break

                else:
                    print(f"API Error: {result.get('error', 'Unknown error')}")
                    break

            else:
                print(f"HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                break

        except Exception as e:
            print(f"Request failed: {e}")
            break

        # Small delay between requests
        time.sleep(0.5)

def test_pdf_download(session_id):
    """Test PDF download functionality"""
    try:
        pdf_endpoint = f"{API_BASE_URL}/api/murder/download-pdf"
        payload = {"session_id": session_id}

        response = requests.post(pdf_endpoint, json=payload)

        if response.status_code == 200:
            # Save the PDF to test file
            filename = f"test_murder_report_{int(time.time())}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)

            print(f"✓ PDF downloaded successfully: {filename}")
            print(f"✓ PDF size: {len(response.content)} bytes")

            # Check if it's a valid PDF (starts with %PDF)
            if response.content.startswith(b'%PDF'):
                print("✓ PDF file appears to be valid")
                return True
            else:
                print("✗ Downloaded file may not be a valid PDF")
                return False
        else:
            print(f"✗ PDF download failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ PDF download test failed: {e}")
        return False

def test_ping():
    """Test the ping functionality"""
    payload = {"question": "ping"}

    try:
        response = requests.post(API_ENDPOINT, json=payload)
        print(f"Ping Test Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Ping test failed: {e}")
        return False

if __name__ == "__main__":
    print("Murder Agent API Test Suite")
    print("=" * 40)

    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    if test_health_check():
        print("✓ Health check passed")
    else:
        print("✗ Health check failed")
        exit(1)

    # Test 2: Ping Test
    print("\n2. Testing Ping...")
    if test_ping():
        print("✓ Ping test passed")
    else:
        print("✗ Ping test failed")

    # Test 3: Full Conversation
    print("\n3. Testing Full Conversation...")
    test_murder_agent_conversation()

    print("\n" + "=" * 40)
    print("Test suite completed!")
