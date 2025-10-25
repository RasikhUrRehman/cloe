"""
Test Multi-Message Functionality
Tests that the agent can send multiple messages in a single response
"""
import sys
import os

# Add chatbot package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.core.agent import CleoRAGAgent
from chatbot.utils.config import ensure_directories

def test_multi_message_split():
    """Test that messages are split correctly"""
    ensure_directories()
    
    # Create agent
    agent = CleoRAGAgent()
    
    print("=== Testing Multi-Message Functionality ===\n")
    
    # Test 1: Single message (no separator)
    print("Test 1: Single message response")
    print("-" * 50)
    test_response = "This is a single message without any separator."
    messages = agent._split_multi_messages(test_response)
    print(f"Input: {test_response}")
    print(f"Output: {messages}")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 1, "Should have 1 message"
    print("✓ Test 1 passed\n")
    
    # Test 2: Multiple messages with separator
    print("Test 2: Multiple messages with separator")
    print("-" * 50)
    test_response = "First message here.[NEXT_MESSAGE]Second message here.[NEXT_MESSAGE]Third message here."
    messages = agent._split_multi_messages(test_response)
    print(f"Input: {test_response}")
    print(f"Output messages:")
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. {msg}")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 3, "Should have 3 messages"
    assert messages[0] == "First message here.", "First message should match"
    assert messages[1] == "Second message here.", "Second message should match"
    assert messages[2] == "Third message here.", "Third message should match"
    print("✓ Test 2 passed\n")
    
    # Test 3: Realistic conversation example
    print("Test 3: Realistic conversation scenario")
    print("-" * 50)
    test_response = "Fantastic, thank you! Let's start with something straightforward: Do you have any preference for the type of job you're looking for, like part-time or full-time roles?[NEXT_MESSAGE]Perfect, part-time works well for many people's schedules. It's great to have that flexibility. Next question: Are morning shifts something you'd be comfortable with?"
    messages = agent._split_multi_messages(test_response)
    print(f"Output messages:")
    for i, msg in enumerate(messages, 1):
        print(f"  Message {i}:")
        print(f"    {msg}\n")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 2, "Should have 2 messages"
    print("✓ Test 3 passed\n")
    
    # Test 4: Empty separator handling
    print("Test 4: Whitespace and empty parts handling")
    print("-" * 50)
    test_response = "Message one.[NEXT_MESSAGE]  [NEXT_MESSAGE]Message two."
    messages = agent._split_multi_messages(test_response)
    print(f"Input: {test_response}")
    print(f"Output messages:")
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. {msg}")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 2, "Should have 2 messages (empty parts removed)"
    print("✓ Test 4 passed\n")
    
    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)

if __name__ == "__main__":
    test_multi_message_split()
