"""
Example: Create a session with a specific job
Demonstrates how to use the job_id parameter when creating a session
"""
import requests
import json

# API endpoint
API_BASE_URL = "http://localhost:8000"

def create_session_with_job(job_id: str):
    """
    Create a new session for a specific job
    
    Args:
        job_id: The job ID to apply for
    """
    url = f"{API_BASE_URL}/api/v1/session/create"
    
    payload = {
        "job_id": job_id,
        "retrieval_method": "hybrid",
        "language": "en"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        session_data = response.json()
        
        print("✅ Session Created Successfully!")
        print(f"Session ID: {session_data['session_id']}")
        print(f"Message: {session_data['message']}")
        print(f"Current Stage: {session_data['current_stage']}")
        
        return session_data['session_id']
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating session: {e}")
        return None


def send_message(session_id: str, message: str):
    """
    Send a message to the chatbot
    
    Args:
        session_id: The session ID
        message: The message to send
    """
    url = f"{API_BASE_URL}/api/v1/chat"
    
    payload = {
        "session_id": session_id,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        chat_data = response.json()
        
        print(f"\n🤖 Cleo: {chat_data['response']}")
        print(f"[Stage: {chat_data['current_stage']}]")
        
        return chat_data
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending message: {e}")
        return None


def main():
    """
    Main function to demonstrate the job-specific session
    """
    print("=" * 80)
    print("Job-Specific Session Demo")
    print("=" * 80)
    
    # Example job ID (replace with an actual job ID from your API)
    # You can get this by running test.py first to see available job IDs
    job_id = input("\nEnter Job ID (or press Enter for demo): ").strip()
    
    if not job_id:
        # Use a demo job ID - replace with actual from your API
        job_id = "93626fb0-a859-4d0e-afa7-9f4854380e77"
        print(f"Using demo job ID: {job_id}")
    
    # Create session with job
    session_id = create_session_with_job(job_id)
    
    if not session_id:
        print("Failed to create session. Make sure the API is running.")
        return
    
    print("\n" + "=" * 80)
    print("Chat Session Started")
    print("Type 'quit' to exit")
    print("=" * 80)
    
    # Interactive chat loop
    while True:
        user_message = input("\n👤 You: ").strip()
        
        if user_message.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using Cleo!")
            break
        
        if not user_message:
            continue
        
        send_message(session_id, user_message)


if __name__ == "__main__":
    main()
