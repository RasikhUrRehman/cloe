"""
Test the enhanced conversation summary generation
"""
from chatbot.api.routes.applications import _generate_conversation_summary

# Test with sample conversation
test_messages = [
    {'MsgCreator': 'Agent', 'MsgContent': 'Hello! Welcome to our application process. Can you tell me about your previous work experience?'},
    {'MsgCreator': 'User', 'MsgContent': 'Hi! I worked as a warehouse associate at ABC Corp for 3 years. I have experience with forklift operation, inventory management, and shipping/receiving.'},
    {'MsgCreator': 'Agent', 'MsgContent': 'That sounds great! What are some of your key skills?'},
    {'MsgCreator': 'User', 'MsgContent': 'I am certified in forklift operation, I am very organized, good with computers, and I work well in a team. I also have experience training new employees.'},
    {'MsgCreator': 'Agent', 'MsgContent': 'Excellent! Why are you interested in this position?'},
    {'MsgCreator': 'User', 'MsgContent': 'I am looking for a position with growth opportunities. I heard your company offers good benefits and career advancement, which is important to me.'},
    {'MsgCreator': 'Agent', 'MsgContent': 'What is your availability?'},
    {'MsgCreator': 'User', 'MsgContent': 'I can start in 2 weeks, and I am available for any shift.'},
    {'MsgCreator': 'Agent', 'MsgContent': 'Do you have any questions for me?'},
    {'MsgCreator': 'User', 'MsgContent': 'Yes, what are the typical work hours and is there overtime available? Also, what kind of training do you provide?'},
]

job_details = {
    'job_title': 'Warehouse Associate',
    'company': 'XYZ Logistics',
    'location': 'Chicago, IL',
    'requirements': 'Forklift certification, 2+ years warehouse experience'
}

print('Testing enhanced conversation summary generation...')
print('=' * 80)
summary = _generate_conversation_summary(test_messages, job_details)
print()
print('DISCUSSION SUMMARY:')
print(summary['discussion_summary'])
print()
print('CANDIDATE STRENGTHS:')
for i, s in enumerate(summary['strengths'], 1):
    print(f'  {i}. {s}')
print()
print('AREAS FOR IMPROVEMENT:')
for i, w in enumerate(summary['weaknesses'], 1):
    print(f'  {i}. {w}')
print()
print('OVERALL IMPRESSION:')
print(summary['overall_impression'])
print()
print('=' * 80)
print('✅ Test complete!')
