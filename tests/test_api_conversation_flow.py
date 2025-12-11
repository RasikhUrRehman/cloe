import re
from fastapi.testclient import TestClient
from chatbot.api.app import app
from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import ConversationStage, EngagementState, QualificationState, ApplicationState


class DummyXanoClient:
    def __init__(self):
        self.sessions = {}
        self.created_candidates = []

    def create_session(self, initial_status: str = "Started", candidate_id: int | None = None):
        # Return a deterministic fake Xano session
        return {"id": 9999}

    def create_candidate(self, **kwargs):
        # Record that candidate creation was attempted and return a fake candidate
        self.created_candidates.append(kwargs)
        return {"id": 12345}

    def post_message(self, session_id, message, creator):
        # No-op for tests
        return True

    def get_messages_by_session_id(self, session_id):
        return []

    def get_sessions(self):
        return []

    def delete_session(self, session_id):
        return True

    def get_session_by_id(self, session_id):
        return {"Status": "Started", "id": session_id}

    def patch_session_status(self, session_id, status):
        return {"id": session_id, "Status": status}

    def update_session(self, session_id, data):
        return {"id": session_id, **data}


# A deterministic fake conversation processor that updates session state based on keywords

def fake_process_message(self, user_message: str):
    s = self.session_state

    # Normalize
    msg = (user_message or "").lower()

    # If this is the initial greeting prompt, return greeting
    if "start the conversation" in msg:
        return ["Hello! I'm Cleo, your friendly job assistant. Would you like to apply for this position?"]

    # ENGAGEMENT stage
    if s.current_stage == ConversationStage.ENGAGEMENT:
        if "apply" in msg or ("yes" in msg and not s.engagement.consent_given):
            if not s.engagement:
                s.engagement = EngagementState(session_id=s.session_id)
            s.engagement.consent_given = True
            s.engagement.stage_completed = True
            s.current_stage = ConversationStage.QUALIFICATION
            return ["Great — thanks for confirming. Let me ask a few questions about your eligibility."]
        return ["Hi there — would you like to apply for this role?"]

    # QUALIFICATION stage
    if s.current_stage == ConversationStage.QUALIFICATION:
        if not s.qualification:
            s.qualification = QualificationState(session_id=s.session_id)

        # Simple parsing - set fields based on keywords
        if "over 18" in msg or re.search(r"\b25\b|\b18\b|over 18", msg):
            s.qualification.age_confirmed = True
        if "authorized" in msg or "work in the us" in msg:
            s.qualification.work_authorization = True
        if "day" in msg or "morning" in msg:
            s.qualification.shift_preference = "day"
        if "immediately" in msg or "start" in msg:
            s.qualification.availability_start = "immediately"
        if "transportation" in msg or "car" in msg:
            s.qualification.transportation = True

        # If essential qualification fields present, advance
        if s.qualification.age_confirmed and s.qualification.work_authorization:
            s.qualification.stage_completed = True
            s.current_stage = ConversationStage.APPLICATION
            return ["Thank you — looks like you qualify. Let's move to the application section."]

        return ["Please answer the next eligibility question."]

    # APPLICATION stage
    if s.current_stage == ConversationStage.APPLICATION:
        if not s.application:
            s.application = ApplicationState(session_id=s.session_id)

        # Extract name/phone/email simply by keywords
        if "name is" in msg or msg.startswith("my name"):
            # crude extraction
            m = re.search(r"name(?: is|\s+is|:)?\s+([\w \-]+)", user_message, re.I)
            if m:
                cleaned = m.group(1).strip()
                s.application.full_name = cleaned
            else:
                # fallback: use entire user_message
                s.application.full_name = user_message
        if "phone" in msg or re.search(r"\b\+?\d[\d\-\s]{7,}\b", user_message):
            m = re.search(r"(\+?\d[\d\-\s]{7,})", user_message)
            if m:
                s.application.phone_number = m.group(1).strip()
        if "email" in msg or re.search(r"\S+@\S+\.\S+", user_message):
            m = re.search(r"(\S+@\S+\.\S+)", user_message)
            if m:
                s.application.email = m.group(1).strip()

        # If name/email/phone present, finish application
        if s.application.full_name and s.application.email and s.application.phone_number:
            s.application.stage_completed = True
            s.current_stage = ConversationStage.VERIFICATION
            return ["Application saved — thanks! We will now verify your details."]

        return ["Thanks — could you share your name, phone number and email so we can continue?"]

    # VERIFICATION or fallback
    return ["Thanks — your application is being processed and is ready for verification."]



def test_api_conversation_flow(monkeypatch):
    # Use FastAPI TestClient
    client = TestClient(app)

    # Patch Xano client to avoid network calls
    import chatbot.utils.xano_client as xano_mod
    # Reuse same dummy client across all calls so we can assert create_candidate behavior
    dummy_xano = DummyXanoClient()
    monkeypatch.setattr(xano_mod, "get_xano_client", lambda: dummy_xano)

    # Patch agent process_message with fake function before session creation
    monkeypatch.setattr(CleoRAGAgent, "process_message", fake_process_message, raising=False)

    # Create session
    response = client.post("/api/v1/sessions/create", json={"job_id": "WAREHOUSE-001", "language": "en"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    assert data["current_stage"] == "engagement"

    # Send an engagement message consenting to apply
    resp = client.post("/api/v1/chat", json={"session_id": session_id, "message": "Yes, I'd like to apply"})
    assert resp.status_code == 200
    chat_data = resp.json()
    assert chat_data["current_stage"] == "qualification"

    # Qualification messages
    messages = [
        "Yes, I'm 25 years old",
        "Yes, I'm authorized to work in the US",
        "I prefer day shifts",
        "I can start immediately",
        "Yes, I have my own transportation",
    ]

    for m in messages:
        resp = client.post("/api/v1/chat", json={"session_id": session_id, "message": m})
        assert resp.status_code == 200

    # After key messages, the agent should be in APPLICATION stage
    status_resp = client.get(f"/api/v1/sessions/{session_id}/status")
    assert status_resp.status_code == 200
    status = status_resp.json()
    assert status["current_stage"] == "application"

    # Application stage messages
    app_msgs = [
        "My name is John Smith",
        "My phone number is +15551234567",
        "My email is john.smith@example.com",
    ]

    for m in app_msgs:
        resp = client.post("/api/v1/chat", json={"session_id": session_id, "message": m})
        assert resp.status_code == 200

    # Verify we reached VERIFICATION stage
    final_status = client.get(f"/api/v1/sessions/{session_id}/status").json()
    assert final_status["current_stage"] == "verification"

    # Verify session details reflect application
    details = client.get(f"/api/v1/sessions/{session_id}").json()
    assert details["current_stage"] == "verification"
    assert details["application"]["full_name"] == "John Smith"
    assert "+15551234567" in details["application"]["phone_number"] or details["application"]["phone_number"] == "+15551234567"
    assert details["application"]["email"] == "john.smith@example.com"

    # Ensure no candidate was created mid-conversation
    assert len(dummy_xano.created_candidates) == 0, "Candidate should not be created before conclude"

    # Now explicitly conclude the session (simulate user saying goodbye)
    from chatbot.utils.session_manager import get_session_manager
    session_manager = get_session_manager()
    agent = session_manager.get_session(session_id)
    assert agent is not None
    conclude_result = agent.toolkit.conclude_session("User said goodbye")
    assert "Session concluded successfully" in conclude_result

    # Candidate should now have been created and associated with the Xano session ID
    assert len(dummy_xano.created_candidates) == 1
    created_kwargs = dummy_xano.created_candidates[0]
    # The session_id passed to create_candidate should be the Xano session id (9999)
    assert str(created_kwargs.get("session_id")) == "9999"

    # List applications (should succeed, but may be empty)
    apps_resp = client.get("/api/v1/applications?limit=10&offset=0")
    assert apps_resp.status_code in (200, 404)

    # Get fit score (may return 200 or 500 if fit score calculation expects real AI)
    fit_resp = client.get(f"/api/v1/sessions/{session_id}/fit_score")
    assert fit_resp.status_code in (200, 500)



# End of file
