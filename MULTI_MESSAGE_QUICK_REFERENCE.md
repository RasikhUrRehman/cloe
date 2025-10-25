# Multi-Message Quick Reference

## 🚀 Quick Start

To send multiple messages from Cleo, use the separator `[NEXT_MESSAGE]` in your response.

## ✨ Syntax

```
"First message[NEXT_MESSAGE]Second message[NEXT_MESSAGE]Third message"
```

## 📖 Examples

### Example 1: Simple Acknowledgment + Question
```
"Thanks for that![NEXT_MESSAGE]What's your availability?"
```
**Result:**
- Message 1: "Thanks for that!"
- Message 2: "What's your availability?"

### Example 2: Conversational Flow
```
"Fantastic, thank you! Let's start with something straightforward: Do you have any preference for the type of job you're looking for, like part-time or full-time roles?[NEXT_MESSAGE]Perfect, part-time works well for many people's schedules. It's great to have that flexibility. Next question: Are morning shifts something you'd be comfortable with?"
```
**Result:**
- Message 1: "Fantastic, thank you! Let's start with something straightforward: Do you have any preference for the type of job you're looking for, like part-time or full-time roles?"
- Message 2: "Perfect, part-time works well for many people's schedules. It's great to have that flexibility. Next question: Are morning shifts something you'd be comfortable with?"

### Example 3: Multiple Transitions
```
"Great![NEXT_MESSAGE]Let's move to the next section.[NEXT_MESSAGE]Tell me about your experience."
```
**Result:**
- Message 1: "Great!"
- Message 2: "Let's move to the next section."
- Message 3: "Tell me about your experience."

## ⚡ Best Practices

| ✅ DO | ❌ DON'T |
|-------|----------|
| Use for acknowledgment + question | Use for every response |
| Keep messages focused (1 idea each) | Create 10+ micro messages |
| Use to reduce overwhelm | Use just to show off |
| Create natural conversation flow | Split mid-sentence randomly |

## 💡 Common Patterns

### Pattern 1: Acknowledge → Ask
```
"Perfect![NEXT_MESSAGE]What's your preferred shift?"
```

### Pattern 2: Explain → Request
```
"This role needs flexibility.[NEXT_MESSAGE]Can you work weekends?"
```

### Pattern 3: Transition → New Topic
```
"Got it![NEXT_MESSAGE]Now about your experience...[NEXT_MESSAGE]How many years in retail?"
```

## 🎯 When to Use

Use multi-message when you want to:
- ✅ Make conversation feel more natural
- ✅ Acknowledge before asking
- ✅ Break complex info into chunks
- ✅ Create comfortable pacing

Don't use when:
- ❌ Single message is already clear
- ❌ Messages are very short
- ❌ You're overusing it (every response)

## 🔍 Technical Details

| Aspect | Details |
|--------|---------|
| **Separator** | `[NEXT_MESSAGE]` (case-sensitive) |
| **Timing** | 800ms between messages (with typing indicator) |
| **Whitespace** | Automatically trimmed |
| **Empty messages** | Automatically removed |
| **Max messages** | No limit (but 2-3 recommended) |

## 🧪 Testing Your Message

```python
# Test string splitting
test = "Message one[NEXT_MESSAGE]Message two"
messages = test.split("[NEXT_MESSAGE]")
# Result: ["Message one", "Message two"]
```

## 📱 How It Looks to Users

**Agent sends:**
```
"Great choice![NEXT_MESSAGE]Are you available on weekends?"
```

**User sees:**
1. "Great choice!" ✓
2. [Cleo is typing...]  
3. "Are you available on weekends?" ✓

**Timing:**
- Message 1 appears immediately
- 400ms pause
- Typing indicator shows
- 800ms delay
- Message 2 appears

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Messages not splitting | Check spelling: `[NEXT_MESSAGE]` |
| Extra whitespace | Whitespace is auto-trimmed (don't worry!) |
| Too many messages | Use 2-3 max per response |
| Timing feels off | Adjust in `web/app.js` (800ms/400ms) |

## 📊 Impact

### Before (Single Message)
```
"Great choice! Are you available on weekends?"
```
Single message, immediate delivery

### After (Multi-Message)
```
"Great choice![NEXT_MESSAGE]Are you available on weekends?"
```
Two messages with natural pacing and typing indicators

**Result:** More human, less robotic, better user experience! 🎉

---

**Remember:** Use sparingly for maximum impact! Quality over quantity.
