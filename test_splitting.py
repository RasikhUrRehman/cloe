"""
Quick test for multi-message functionality
"""
from chatbot.core.agent import CleoRAGAgent
from chatbot.utils.config import ensure_directories
import os

def quick_test():
    """Quick test of multi-message functionality"""
    os.environ['OPENAI_API_KEY'] = 'test-key'  # Set dummy key for testing
    
    # Test the splitting logic directly
    agent = CleoRAGAgent()
    
    # Test cases
    test_responses = [
        "Great! What type of job are you looking for?",
        "That's fantastic![NEXT_MESSAGE]What type of job are you looking for?",
        "Perfect! I'm excited to help you today. What brings you here?",
        "Excellent! You meet the requirements. Now let's talk about your experience.",
    ]
    
    print("=" * 60)
    print("TESTING MULTI-MESSAGE SPLITTING")
    print("=" * 60)
    
    for i, response in enumerate(test_responses, 1):
        print(f"\nTest {i}: {response}")
        print("-" * 50)
        
        # Test the splitting directly
        messages = agent._split_multi_messages(response)
        
        print(f"Split into {len(messages)} messages:")
        for j, msg in enumerate(messages, 1):
            print(f"  {j}. {msg}")
        
        if len(messages) > 1:
            print("✓ MULTI-MESSAGE SUCCESS!")
        else:
            print("• Single message")

if __name__ == "__main__":
    quick_test()