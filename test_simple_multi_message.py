"""
Simple test for multi-message splitting logic
Tests the message splitting without requiring full agent setup
"""

def split_multi_messages(response: str) -> list:
    """
    Split agent response into multiple messages if separator is present
    
    Args:
        response: Agent's response text
    
    Returns:
        List of message strings
    """
    # Check if response contains the multi-message separator
    separator = "[NEXT_MESSAGE]"
    
    if separator in response:
        # Split by separator and clean up whitespace
        messages = [msg.strip() for msg in response.split(separator) if msg.strip()]
        print(f"Split response into {len(messages)} messages")
        return messages
    else:
        # Return single message as a list
        return [response]


def test_multi_message_split():
    """Test that messages are split correctly"""
    
    print("=== Testing Multi-Message Functionality ===\n")
    
    # Test 1: Single message (no separator)
    print("Test 1: Single message response")
    print("-" * 50)
    test_response = "This is a single message without any separator."
    messages = split_multi_messages(test_response)
    print(f"Input: {test_response}")
    print(f"Output: {messages}")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 1, "Should have 1 message"
    print("✓ Test 1 passed\n")
    
    # Test 2: Multiple messages with separator
    print("Test 2: Multiple messages with separator")
    print("-" * 50)
    test_response = "First message here.[NEXT_MESSAGE]Second message here.[NEXT_MESSAGE]Third message here."
    messages = split_multi_messages(test_response)
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
    messages = split_multi_messages(test_response)
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
    messages = split_multi_messages(test_response)
    print(f"Input: {test_response}")
    print(f"Output messages:")
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. {msg}")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 2, "Should have 2 messages (empty parts removed)"
    print("✓ Test 4 passed\n")
    
    # Test 5: Whitespace around separator
    print("Test 5: Whitespace around separator")
    print("-" * 50)
    test_response = "Message one.   [NEXT_MESSAGE]   Message two."
    messages = split_multi_messages(test_response)
    print(f"Input: '{test_response}'")
    print(f"Output messages:")
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. '{msg}'")
    print(f"Number of messages: {len(messages)}")
    assert len(messages) == 2, "Should have 2 messages"
    assert messages[0] == "Message one.", "First message should be trimmed"
    assert messages[1] == "Message two.", "Second message should be trimmed"
    print("✓ Test 5 passed\n")
    
    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)
    print("\nThe message splitting logic works correctly!")
    print("Multi-message feature is ready to use.")

if __name__ == "__main__":
    test_multi_message_split()
