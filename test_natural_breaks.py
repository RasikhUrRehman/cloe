"""
Test intelligent natural break detection
"""
from chatbot.core.agent import CleoRAGAgent
import os

def test_natural_breaks():
    """Test the natural break detection"""    
    os.environ['OPENAI_API_KEY'] = 'test-key'  # Set dummy key for testing
    
    agent = CleoRAGAgent()
    
    # Test cases for natural break detection
    test_responses = [
        "Great! Now, let me ask you about your experience.",
        "That's fantastic! What type of job are you looking for?",
        "Perfect! Here's what we'll do next.",
        "Excellent! Tell me about your availability.",
        "Wonderful! So, are you interested in full-time work?",
        "That's perfect! Moving on to the next question.",
        "Great choice! Full-time roles offer stability. Do you have transportation?",
        "Perfect! Now let's discuss your experience. What skills do you have?",
    ]
    
    print("=" * 60)
    print("TESTING INTELLIGENT NATURAL BREAK DETECTION")
    print("=" * 60)
    
    for i, response in enumerate(test_responses, 1):
        print(f"\nTest {i}: {response}")
        print("-" * 50)
        
        # Test natural break detection directly
        messages = agent._detect_natural_breaks(response)
        
        print(f"Detected {len(messages)} messages:")
        for j, msg in enumerate(messages, 1):
            print(f"  {j}. {msg}")
        
        if len(messages) > 1:
            print("✓ NATURAL BREAK DETECTED!")
        else:
            print("• No natural break found")

if __name__ == "__main__":
    test_natural_breaks()