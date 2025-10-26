#!/usr/bin/env python3
"""
Test specific conversation scenarios to verify fixes
"""
from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import SessionState

def test_simple_responses():
    """Test that simple responses like 'ok' don't trigger errors"""
    print("=" * 50)
    print("TESTING SIMPLE RESPONSES - NO ERRORS")
    print("=" * 50)
    
    agent = CleoRAGAgent()
    
    test_cases = [
        "ok",
        "okay", 
        "yes",
        "sure",
        "alright"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}. USER: {message}")
        print("-" * 30)
        
        try:
            responses = agent.process_message(message)
            print(f"✓ SUCCESS - {len(responses)} message(s)")
            for j, response in enumerate(responses, 1):
                print(f"   Response {j}: {response[:80]}{'...' if len(response) > 80 else ''}")
        except Exception as e:
            print(f"✗ ERROR: {e}")

def test_context_awareness():
    """Test that agent remembers what info was already provided"""
    print("\n" + "=" * 50)
    print("TESTING CONTEXT AWARENESS")
    print("=" * 50)
    
    agent = CleoRAGAgent()
    
    conversation = [
        "Hi, I'm looking for full-time work and I'm over 18",
        "Yes, I consent to proceed",
        "I have transportation and can start immediately"
    ]
    
    for i, message in enumerate(conversation, 1):
        print(f"\n{i}. USER: {message}")
        print("-" * 40)
        
        responses = agent.process_message(message)
        
        for j, response in enumerate(responses, 1):
            print(f"   Response {j}: {response}")
        
        # Show captured state after each message
        print(f"   [STATE] Stage: {agent.session_state.current_stage.value}")
        if agent.session_state.qualification:
            qual = agent.session_state.qualification
            print(f"   [STATE] Age: {qual.age_confirmed}, Work Auth: {qual.work_authorization}, Hours: {qual.hours_preference}")

if __name__ == "__main__":
    test_simple_responses()
    test_context_awareness()