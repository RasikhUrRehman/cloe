# Multi-Message Feature Implementation

## Overview

This feature allows Cleo to send multiple messages in a single response, creating a more natural and conversational flow. Instead of sending one long message, Cleo can now break her responses into multiple parts that appear sequentially, mimicking natural human conversation patterns.

## How It Works

### 1. Message Separator

Cleo uses a special separator `[NEXT_MESSAGE]` to indicate where responses should be split into separate messages.

**Example:**
```
"Fantastic, thank you![NEXT_MESSAGE]Let's start with the first question: Do you prefer part-time or full-time roles?"
```

This will be displayed to the user as two separate messages:
1. "Fantastic, thank you!"
2. "Let's start with the first question: Do you prefer part-time or full-time roles?"

### 2. Backend Changes

#### Agent (`chatbot/core/agent.py`)

- **`process_message()`**: Now returns a `List[str]` instead of a single `str`
- **`_split_multi_messages()`**: New method that splits responses by `[NEXT_MESSAGE]` separator
  - Strips whitespace from each message
  - Removes empty messages
  - Returns list of clean message strings

#### API (`chatbot/api/app.py`)

- **`ChatResponse` model**: Changed `response: str` to `responses: List[str]`
- **`/api/v1/chat` endpoint**: Now returns array of messages instead of single message
- All response handling updated to work with message arrays

#### Main Application (`main.py`)

- **`chat()` method**: Joins multiple responses with `\n\n` for CLI display
- Maintains backward compatibility for command-line usage

### 3. Frontend Changes

#### Web Interface (`web/app.js`)

The `handleSendMessage()` function now:

1. Accepts responses as an array: `response.responses`
2. Displays messages sequentially with timing:
   - 800ms delay between messages (shows typing indicator)
   - 400ms pause after displaying each message
3. Provides smooth, natural conversation flow
4. Falls back to single message if needed (backward compatibility)

**Timing Flow:**
```
User sends message
  ↓
Show typing indicator
  ↓
API responds with array: ["Message 1", "Message 2", "Message 3"]
  ↓
Hide typing indicator
  ↓
Display "Message 1"
  ↓
Wait 400ms
  ↓
Show typing indicator
  ↓
Wait 800ms
  ↓
Hide typing indicator
  ↓
Display "Message 2"
  ↓
(repeat for remaining messages)
```

### 4. Prompt Updates

The system prompt (`chatbot/prompts/prompts.py`) now includes instructions for multi-message usage:

```
📨 MULTIPLE MESSAGE SENDING

When you need to send multiple messages in a conversation (to make the flow more natural 
and conversational), you can separate them using the marker: [NEXT_MESSAGE]

WHEN TO USE MULTIPLE MESSAGES:
- When acknowledging user's response AND asking the next question
- When providing context/explanation AND then asking for information
- When transitioning between topics naturally
- When you want to create a more conversational, less overwhelming experience

IMPORTANT: Use this sparingly - only when it truly makes the conversation more natural.
```

## Usage Examples

### Example 1: Acknowledging + Asking
```python
response = "Great choice![NEXT_MESSAGE]Now, are you comfortable with morning shifts?"
# Displays as:
# Cleo: "Great choice!"
# [slight pause with typing indicator]
# Cleo: "Now, are you comfortable with morning shifts?"
```

### Example 2: Multiple Transitions
```python
response = "Perfect, that's exactly what we need![NEXT_MESSAGE]Let me ask you about your availability.[NEXT_MESSAGE]When would you be able to start?"
# Displays as 3 separate messages
```

### Example 3: Single Message (No Separator)
```python
response = "Thank you for that information. Could you tell me more about your experience?"
# Displays as single message (normal behavior)
```

## Testing

Run the test suite to verify multi-message functionality:

```bash
python test_multi_message.py
```

This tests:
- Single message handling
- Multiple message splitting
- Whitespace trimming
- Empty message removal
- Realistic conversation scenarios

## API Changes

### Before (Single Message)
```json
{
  "session_id": "abc-123",
  "response": "Hello! How can I help you?",
  "current_stage": "engagement",
  "timestamp": "2025-10-25T10:30:00"
}
```

### After (Multiple Messages)
```json
{
  "session_id": "abc-123",
  "responses": [
    "Hello! How can I help you?",
    "I'm Cleo, your application assistant."
  ],
  "current_stage": "engagement",
  "timestamp": "2025-10-25T10:30:00"
}
```

## Best Practices

### When to Use Multi-Message

✅ **DO use when:**
- Acknowledging user input before asking next question
- Breaking long explanations into digestible parts
- Creating natural conversation transitions
- Making the chat feel more human and less robotic

❌ **DON'T use when:**
- Every single response (overuse reduces impact)
- Messages are very short (combine them instead)
- The flow is already natural with one message
- You're just listing items (use formatting instead)

### Message Length Guidelines

- **First message**: Acknowledgment or reaction (1-2 sentences)
- **Subsequent messages**: Questions or information (2-3 sentences)
- **Total**: Aim for 2-3 messages maximum per response
- Keep each message focused on one idea

### Example Patterns

**Pattern 1: Acknowledge + Question**
```
"That's perfect![NEXT_MESSAGE]Are you available for weekend shifts?"
```

**Pattern 2: Explain + Ask**
```
"This position requires flexibility in scheduling.[NEXT_MESSAGE]Would you be comfortable with varying shift times?"
```

**Pattern 3: Transition**
```
"Great, I have all I need about your availability.[NEXT_MESSAGE]Now let's talk about your experience.[NEXT_MESSAGE]How many years have you worked in customer service?"
```

## Backward Compatibility

The implementation maintains backward compatibility:

1. **CLI/Console**: Multiple messages are joined with `\n\n`
2. **API**: Clients checking for `response.response` will still work (first message)
3. **Fallback**: If `responses` is not an array, system handles gracefully

## Performance Considerations

- **Network**: Minimal impact (same data, different structure)
- **UI**: 800ms + 400ms per additional message = slight delay but more natural
- **Processing**: Negligible overhead for string splitting

## Future Enhancements

Potential improvements:
- Dynamic timing based on message length
- Typing indicator speed variation
- User preference for message delays
- Analytics on multi-message effectiveness
- A/B testing different delay timings

## Troubleshooting

### Messages not splitting
- Check that `[NEXT_MESSAGE]` is spelled exactly right (case-sensitive)
- Verify no extra spaces within the separator
- Check browser console for errors

### Timing feels off
- Adjust delays in `web/app.js`:
  - `800` for typing indicator delay
  - `400` for pause after message

### API returns single string
- Verify API is updated and restarted
- Check that `responses` (plural) is used, not `response`
- Confirm FastAPI model updated

## Files Changed

1. `chatbot/prompts/prompts.py` - Added multi-message instructions
2. `chatbot/core/agent.py` - Added `_split_multi_messages()`, updated `process_message()`
3. `chatbot/api/app.py` - Updated API models and endpoints
4. `main.py` - Updated CLI to handle message arrays
5. `web/app.js` - Added sequential message display with timing
6. `scripts/demo_conversation.py` - Updated to handle message arrays
7. `test_multi_message.py` - New test file for functionality

## Migration Guide

If you have existing integrations:

1. Update API response handling:
   ```javascript
   // Old
   const message = response.response;
   
   // New
   const messages = response.responses;
   messages.forEach(msg => displayMessage(msg));
   ```

2. For single message fallback:
   ```javascript
   const messageText = response.responses 
     ? response.responses[0] 
     : response.response;
   ```

3. CLI applications work automatically (messages are joined)

---

**Implementation Date**: October 25, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
