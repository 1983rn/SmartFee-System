#!/usr/bin/env python3
"""
Test SMS functionality with provided credentials
"""
from sms_service import sms_service

def test_sms():
    """Test SMS sending to the provided phone number"""
    test_phone = "+265991332952"
    test_message = "Hello! This is a test message from SmartFee System. SMS integration is working correctly."
    
    print(f"Testing SMS to: {test_phone}")
    print(f"Message: {test_message}")
    print("-" * 50)
    
    result = sms_service.send_sms(test_phone, test_message)
    
    if result['success']:
        print("✅ SMS sent successfully!")
        print(f"Message ID: {result.get('message_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
    else:
        print("❌ SMS failed to send!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    test_sms()
