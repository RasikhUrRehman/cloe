"""
Test script to verify early candidate creation flow
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import SessionState
from chatbot.utils.utils import setup_logging

logger = setup_logging()

def test_early_candidate_flow():
    """Test the new early candidate creation flow"""
    
    print("\n" + "="*60)
    print("TESTING EARLY CANDIDATE CREATION FLOW")
    print("="*60 + "\n")
    
    # Initialize agent with a test job_id
    job_id = "2b951289-6c7e-403c-baf8-9c0d5e803df5"
    session_state = SessionState()
    agent = CleoRAGAgent(session_state=session_state, job_id=job_id)
    
    print("\n📝 Step 1: User provides name")
    print("-" * 60)
    response = agent.process_message("My name is John Smith")
    print(f"Agent: {response}")
    
    print("\n📝 Step 2: User provides email")
    print("-" * 60)
    response = agent.process_message("My email is john.smith@example.com")
    print(f"Agent: {response}")
    
    print("\n📝 Step 3: User provides phone")
    print("-" * 60)
    response = agent.process_message("My phone number is 555-123-4567")
    print(f"Agent: {response}")
    
    print("\n📝 Step 4: User provides age")
    print("-" * 60)
    response = agent.process_message("I'm 28 years old")
    print(f"Agent: {response}")
    
    print("\n" + "="*60)
    print("📊 CHECKING SESSION STATE")
    print("="*60)
    
    if session_state.application:
        print(f"✓ Full Name: {session_state.application.full_name}")
        print(f"✓ Email: {session_state.application.email}")
        print(f"✓ Phone: {session_state.application.phone_number}")
        print(f"✓ Age: {session_state.application.age}")
    
    if session_state.engagement and session_state.engagement.candidate_id:
        print(f"✓ Candidate ID: {session_state.engagement.candidate_id}")
        print(f"✓ User ID: {session_state.engagement.user_id}")
        print("\n✅ CANDIDATE WAS CREATED SUCCESSFULLY!")
    else:
        print("\n❌ CANDIDATE WAS NOT CREATED - Check tool calls in logs above")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_early_candidate_flow()
