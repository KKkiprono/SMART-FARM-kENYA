#!/usr/bin/env python3
"""
Test script for Arduino Sensor Data Processor Flask API
This script demonstrates how to send sensor data to the Flask server
"""

import requests
import json
import time
from typing import Dict, Any

# Server configuration
SERVER_URL = "http://localhost:5000"
SUBMIT_ENDPOINT = f"{SERVER_URL}/submit-data"
HEALTH_ENDPOINT = f"{SERVER_URL}/health"

# Test data scenarios
TEST_SCENARIOS = {
    "normal_conditions": {
        "temperature": 22.5,
        "humidity": 45.0,
        "light_intensity": 400,
        "gas_level": 120,
        "description": "Normal environmental conditions"
    },
    "hot_conditions": {
        "temperature": 32.1,
        "humidity": 65.2,
        "light_intensity": 800,
        "gas_level": 180,
        "description": "Hot conditions - should trigger fan and red LED"
    },
    "cold_conditions": {
        "temperature": 12.3,
        "humidity": 80.5,
        "light_intensity": 150,
        "gas_level": 95,
        "description": "Cold conditions - should trigger blue LED"
    },
    "gas_alert": {
        "temperature": 25.0,
        "humidity": 55.0,
        "light_intensity": 600,
        "gas_level": 450,
        "description": "Gas alert conditions - should trigger gas alert"
    },
    "extreme_conditions": {
        "temperature": 35.8,
        "humidity": 85.0,
        "light_intensity": 950,
        "gas_level": 520,
        "description": "Extreme conditions - hot + gas alert"
    }
}

def test_health_check() -> bool:
    """Test the health check endpoint"""
    try:
        print("Testing health check endpoint...")
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed with error: {e}")
        return False

def send_sensor_data(scenario_name: str, data: Dict[str, Any]) -> bool:
    """Send sensor data to the Flask server"""
    try:
        print(f"\n--- Testing {scenario_name} ---")
        print(f"Description: {data['description']}")
        
        # Prepare payload (remove description)
        payload = {k: v for k, v in data.items() if k != 'description'}
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        
        # Send POST request
        response = requests.post(
            SUBMIT_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"AI Decision: {json.dumps(result['decision'], indent=2)}")
            
            # Display key decisions
            decision = result['decision']
            print(f"🔧 Action: {decision.get('action', 'N/A')}")
            print(f"💡 LED: {decision.get('led', 'N/A')}")
            print(f"🌀 Fan: {decision.get('fan', 'N/A')}")
            print(f"⚠️  Gas Alert: {decision.get('gas_alert', 'N/A')}")
            print(f"📊 Priority: {decision.get('priority', 'N/A')}")
            print(f"🧠 Reasoning: {decision.get('reasoning', 'N/A')}")
            
            return True
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error details: {json.dumps(error_info, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed with error: {e}")
        return False

def test_sms_endpoints():
    """Test SMS-related endpoints"""
    print("\n--- Testing SMS Endpoints ---")
    
    # Test SMS status
    try:
        print("\nTesting SMS status endpoint...")
        response = requests.get(f"{SERVER_URL}/sms/status", timeout=10)
        
        if response.status_code == 200:
            print("✅ SMS status endpoint working")
            status_data = response.json()
            print(f"SMS Service Status: {json.dumps(status_data['sms_service'], indent=2)}")
        else:
            print(f"❌ SMS status failed with status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ SMS status failed with error: {e}")
    
    # Test SMS test message (optional - uncomment if you want to send test SMS)
    # try:
    #     print("\nTesting test SMS endpoint...")
    #     response = requests.post(f"{SERVER_URL}/sms/test", timeout=30)
    #     
    #     if response.status_code == 200:
    #         print("✅ Test SMS sent successfully")
    #         result = response.json()
    #         print(f"SMS Result: {json.dumps(result, indent=2)}")
    #     else:
    #         print(f"⚠️ Test SMS failed with status: {response.status_code}")
    #         try:
    #             error_info = response.json()
    #             print(f"Error: {error_info.get('error', 'Unknown')}")
    #         except:
    #             print(f"Raw response: {response.text}")
    #             
    # except requests.exceptions.RequestException as e:
    #     print(f"❌ Test SMS failed with error: {e}")

def test_invalid_data():
    """Test with invalid data to verify error handling"""
    print("\n--- Testing Invalid Data Scenarios ---")
    
    invalid_scenarios = [
        {
            "name": "missing_temperature",
            "data": {"humidity": 50.0, "light_intensity": 400, "gas_level": 120},
            "expected": "Missing required fields"
        },
        {
            "name": "invalid_humidity",
            "data": {"temperature": 25.0, "humidity": 150.0, "light_intensity": 400, "gas_level": 120},
            "expected": "Humidity out of range"
        },
        {
            "name": "invalid_light",
            "data": {"temperature": 25.0, "humidity": 50.0, "light_intensity": 2000, "gas_level": 120},
            "expected": "Light intensity out of range"
        },
        {
            "name": "non_json",
            "data": "this is not json",
            "expected": "Content-Type error"
        }
    ]
    
    for scenario in invalid_scenarios:
        print(f"\nTesting {scenario['name']}...")
        try:
            if isinstance(scenario['data'], str):
                # Test non-JSON data
                response = requests.post(
                    SUBMIT_ENDPOINT,
                    data=scenario['data'],
                    headers={'Content-Type': 'text/plain'},
                    timeout=10
                )
            else:
                response = requests.post(
                    SUBMIT_ENDPOINT,
                    json=scenario['data'],
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            
            if response.status_code != 200:
                print(f"✅ Correctly rejected with status: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"Error message: {error_info.get('error', 'N/A')}")
                except:
                    print(f"Raw response: {response.text}")
            else:
                print(f"❌ Should have been rejected but got status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request error (expected): {e}")

def main():
    """Main test function"""
    print("🚀 Arduino Sensor Data Processor API Test Suite")
    print("=" * 60)
    
    # Test health check first
    if not test_health_check():
        print("\n❌ Server appears to be down. Please start the Flask server first.")
        print("Run: python app.py")
        return
    
    # Test all valid scenarios
    success_count = 0
    total_tests = len(TEST_SCENARIOS)
    
    for scenario_name, data in TEST_SCENARIOS.items():
        if send_sensor_data(scenario_name, data):
            success_count += 1
        time.sleep(1)  # Small delay between requests
    
    # Test SMS endpoints
    test_sms_endpoints()
    
    # Test invalid data scenarios
    test_invalid_data()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {success_count}/{total_tests} valid scenarios passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    print("\n📝 To test manually with curl:")
    print("\n# Submit sensor data:")
    print("curl -X POST http://localhost:5000/submit-data \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"temperature\": 25.0, \"humidity\": 50.0, \"light_intensity\": 400, \"gas_level\": 120}'")
    
    print("\n# Check SMS status:")
    print("curl -X GET http://localhost:5000/sms/status")
    
    print("\n# Send test SMS (uncomment in test_sms_endpoints() first):")
    print("curl -X POST http://localhost:5000/sms/test")

if __name__ == "__main__":
    main()