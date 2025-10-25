"""
Complete Example: Job-Specific Session Workflow

This script demonstrates the complete workflow:
1. Fetch available jobs
2. Select a job
3. Create a session for that job
4. Have a conversation with the agent
5. See how the agent uses job information
"""
import requests
import json
from typing import Optional, Dict, Any

# Configuration
XANO_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_"
CHATBOT_API_URL = "http://localhost:8000"


def fetch_jobs() -> list:
    """Fetch all jobs from Xano API"""
    try:
        response = requests.get(XANO_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        return []


def display_jobs(jobs: list):
    """Display available jobs"""
    print("\n" + "=" * 100)
    print("AVAILABLE JOBS")
    print("=" * 100)
    
    for i, job in enumerate(jobs, start=1):
        print(f"\n{i}. {job.get('job_title', 'N/A')}")
        print(f"   Company: {job.get('company_name', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        print(f"   Type: {job.get('job_type', 'N/A')}")
        print(f"   ID: {job.get('id', 'N/A')}")


def create_session(job_id: str) -> Optional[str]:
    """Create a new session for a specific job"""
    url = f"{CHATBOT_API_URL}/api/v1/session/create"
    
    payload = {
        "job_id": job_id,
        "retrieval_method": "hybrid",
        "language": "en"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        session_data = response.json()
        
        print(f"\n✅ Session created: {session_data['session_id']}")
        print(f"   Stage: {session_data['current_stage']}")
        
        return session_data['session_id']
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None


def send_message(session_id: str, message: str) -> Optional[Dict[str, Any]]:
    """Send a message to the chatbot"""
    url = f"{CHATBOT_API_URL}/api/v1/chat"
    
    payload = {
        "session_id": session_id,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None


def get_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """Get current session status"""
    url = f"{CHATBOT_API_URL}/api/v1/session/{session_id}/status"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return None


def automated_conversation_demo(session_id: str):
    """
    Demonstrate an automated conversation showing how the agent
    uses job information
    """
    print("\n" + "=" * 100)
    print("AUTOMATED CONVERSATION DEMO")
    print("=" * 100)
    
    # Conversation sequence
    messages = [
        "Hi",
        "Yes, I'm interested",
        "What will I be doing in this role?",
        "I'm 28 years old",
        "Yes, I'm authorized to work in the US",
        "I prefer morning shifts",
        "I can start next week",
        "Yes, I have a car",
        "I'm looking for full-time work"
    ]
    
    for msg in messages:
        print(f"\n👤 You: {msg}")
        response = send_message(session_id, msg)
        
        if response:
            print(f"🤖 Cleo: {response['response'][:500]}...")  # Truncate long responses
            print(f"   [Stage: {response['current_stage']}]")
        
        # Brief pause for readability
        import time
        time.sleep(1)


def interactive_conversation(session_id: str):
    """Interactive conversation mode"""
    print("\n" + "=" * 100)
    print("INTERACTIVE CHAT MODE")
    print("Type 'quit' to exit, 'status' to see session status")
    print("=" * 100)
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if user_input.lower() == 'status':
            status = get_session_status(session_id)
            if status:
                print("\n📊 Session Status:")
                print(json.dumps(status, indent=2))
            continue
        
        if not user_input:
            continue
        
        response = send_message(session_id, user_input)
        
        if response:
            print(f"\n🤖 Cleo: {response['response']}")
            print(f"   [Stage: {response['current_stage']}]")


def main():
    """Main function"""
    print("=" * 100)
    print("JOB-SPECIFIC SESSION WORKFLOW DEMO")
    print("=" * 100)
    
    # Step 1: Fetch jobs
    print("\n📋 Step 1: Fetching available jobs...")
    jobs = fetch_jobs()
    
    if not jobs:
        print("No jobs available. Check if the Xano API is accessible.")
        return
    
    # Step 2: Display jobs
    display_jobs(jobs)
    
    # Step 3: Select a job
    print("\n" + "=" * 100)
    
    choice = input("\nSelect a job number (or press Enter for job #1): ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(jobs):
        selected_job = jobs[int(choice) - 1]
    else:
        selected_job = jobs[0]  # Default to first job
    
    job_id = selected_job.get('id')
    job_title = selected_job.get('job_title', 'N/A')
    
    print(f"\n✅ Selected: {job_title}")
    print(f"   Job ID: {job_id}")
    
    # Step 4: Create session
    print("\n📋 Step 2: Creating session with job context...")
    session_id = create_session(job_id)
    
    if not session_id:
        print("Failed to create session. Make sure the chatbot API is running.")
        print("Start it with: docker-compose up --build -d")
        return
    
    # Step 5: Choose conversation mode
    print("\n" + "=" * 100)
    print("Choose conversation mode:")
    print("1. Automated demo (watch a sample conversation)")
    print("2. Interactive mode (chat yourself)")
    
    mode = input("\nYour choice (1 or 2): ").strip()
    
    if mode == "1":
        automated_conversation_demo(session_id)
    else:
        interactive_conversation(session_id)
    
    # Final status
    print("\n" + "=" * 100)
    print("FINAL SESSION STATUS")
    print("=" * 100)
    
    status = get_session_status(session_id)
    if status:
        print(json.dumps(status, indent=2))
    
    print("\n✅ Demo completed!")
    print(f"   Session ID: {session_id}")


if __name__ == "__main__":
    main()
