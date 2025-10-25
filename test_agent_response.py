"""
Test Agent Response - Check if agent is generating multi-messages
"""
from chatbot.core.agent import CleoRAGAgent
from chatbot.core.retrievers import RetrievalMethod
from chatbot.utils.config import ensure_directories
from chatbot.utils.utils import setup_logging

logger = setup_logging()

def test_agent_responses():
    """Test if agent generates multi-message responses"""
    ensure_directories()
    
    # Create agent
    agent = CleoRAGAgent(retrieval_method=RetrievalMethod.HYBRID)
    
    # Test messages that should trigger multi-message responses
    test_messages = [
        "Hi there!",
        "Yes, I'd like to apply for a position",
        "Sure, I consent to proceed",
        "I'm looking for full-time work",
        "Yes, I'm over 18 and authorized to work"
    ]
    
    print("=" * 60)
    print("TESTING AGENT MULTI-MESSAGE RESPONSES")
    print("=" * 60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. USER: {message}")
        print("-" * 40)
        
        # Process message
        responses = agent.process_message(message)
        
        print(f"RAW RESPONSE COUNT: {len(responses)}")
        
        if len(responses) > 1:
            print("✓ MULTI-MESSAGE DETECTED!")
            for j, response in enumerate(responses, 1):
                print(f"   Message {j}: {response}")
        else:
            print("• Single message response:")
            print(f"   {responses[0]}")
            
            # Check if raw response contained separator
            if "[NEXT_MESSAGE]" in responses[0]:
                print("⚠️  WARNING: Raw response contains [NEXT_MESSAGE] but wasn't split!")
        
        print()

if __name__ == "__main__":
    test_agent_responses()