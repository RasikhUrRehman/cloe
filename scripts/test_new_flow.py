"""
Test the new conversation flow with early candidate creation and patching
"""
from chatbot.utils.xano_client import XanoClient

xc = XanoClient()

# Example 1: Create candidate early (without report)
print("=" * 60)
print("Example 1: Creating candidate early (without report)")
print("=" * 60)

candidate_data = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "job_id": "2b951289-6c7e-403c-baf8-9c0d5e803df5",
    "company_id": "226e9e5b-6773-46e6-9b2d-caa5a14429ff",
    "status": "In Progress",  # Status indicates candidate is still in conversation
    "session_id": 30,
    "score": 0,  # No score yet
    "file_path": None,  # No report yet
    "profilesummary": None  # No summary yet
}

result = xc.create_candidate(**candidate_data)
if result:
    print(f"✓ Candidate created successfully!")
    print(f"  Candidate ID: {result.get('id')}")
    print(f"  User ID: {result.get('user_id')}")
    print(f"  Status: {result.get('Status')}")
    candidate_id = result.get('id')
else:
    print("✗ Failed to create candidate")
    candidate_id = None

# Example 2: Update candidate email if they made a mistake
if candidate_id:
    print("\n" + "=" * 60)
    print("Example 2: Updating candidate email (user corrected it)")
    print("=" * 60)
    
    new_email = "john.doe.correct@example.com"
    result = xc.patch_candidate_email(
        candidate_id=candidate_id,
        email=new_email
    )
    if result:
        print(f"✓ Email updated successfully to: {new_email}")
    else:
        print("✗ Failed to update email")

# Example 3: Patch candidate with complete information and report at the end
if candidate_id:
    print("\n" + "=" * 60)
    print("Example 3: Patching candidate with final report (session complete)")
    print("=" * 60)
    
    result = xc.patch_candidate_complete(
        candidate_id=candidate_id,
        score=85,  # Fit score calculated from conversation
        status="Short Listed",
        profile_summary="John is a strong candidate with relevant experience...",
        session_id=30,
        report_pdf="https://example.com/reports/candidate_123.pdf",  # URL to uploaded report
        my_session_id="00000000-0000-0000-0000-000000000030"
    )
    if result:
        print(f"✓ Candidate patched successfully with report!")
        print(f"  Status: {result.get('Status')}")
        print(f"  Score: {result.get('Score')}")
    else:
        print("✗ Failed to patch candidate with report")

print("\n" + "=" * 60)
print("NEW FLOW SUMMARY:")
print("=" * 60)
print("""
1. Collect: Name → Email → Phone → Age
2. Create candidate immediately (without report): create_candidate()
3. Verify email and phone
4. Continue conversation (questions, experience, etc.)
5. At end: Generate report and patch candidate: patch_candidate_complete()
6. Conclude session

The agent decides when to call each tool based on the conversation state!
""")
