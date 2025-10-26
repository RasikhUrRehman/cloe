"""
Test API Multi-Message Functionality
"""
import requests
import json
import time

def test_api_multi_messages():
    """Test multi-message functionality via API"""
    base_url = "http://localhost:8000"
    
    # Test health check
    print("Testing API health...")
    health_response = requests.get(f"{base_url}/health")
    if health_response.status_code == 200:
        print("✓ API is healthy")
    else:
        print("✗ API health check failed")
        return
    
    # Create session
    print("\nCreating session...")
    session_response = requests.post(f"{base_url}/api/v1/session/create", json={
        "retrieval_method": "hybrid",
        "language": "en"
    })
    
    if session_response.status_code != 200:
        print(f"✗ Failed to create session: {session_response.text}")
        return
    
    session_data = session_response.json()
    session_id = session_data["session_id"]
    print(f"✓ Session created: {session_id}")
    
    # Print initial message
    initial_message = session_data.get("message", "")
    print(f"Initial message: {initial_message}")
    
    # Test messages that should trigger multi-message responses
    test_messages = [
        "Hi there!",
        "Yes, I'd like to apply for a position",
        "Sure, I consent to proceed",
        "I'm looking for full-time work",
        "Yes, I'm over 18"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING MULTI-MESSAGE API RESPONSES")
    print("=" * 60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. USER: {message}")
        print("-" * 50)
        
        # Send message
        chat_response = requests.post(f"{base_url}/api/v1/chat", json={
            "session_id": session_id,
            "message": message
        })
        
        if chat_response.status_code != 200:
            print(f"✗ Failed to send message: {chat_response.text}")
            continue
        
        chat_data = chat_response.json()
        responses = chat_data.get("responses", [])
        
        print(f"API returned {len(responses)} messages:")
        
        if len(responses) > 1:
            print("✓ MULTI-MESSAGE SUCCESS!")
            for j, response in enumerate(responses, 1):
                print(f"   Message {j}: {response}")
        elif len(responses) == 1:
            print(f"• Single message: {responses[0]}")
        else:
            print("✗ No messages returned")
        
        # Brief delay between messages
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("MULTI-MESSAGE API TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_api_multi_messages()