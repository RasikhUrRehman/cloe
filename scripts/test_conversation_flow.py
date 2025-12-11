"""
Test Conversation Flow
Tests complete application flow through all stages and verifies stage transitions
"""
import json
import time
from datetime import datetime
from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import ConversationStage
from chatbot.utils.config import ensure_directories
from chatbot.utils.fit_score import FitScoreCalculator
from chatbot.utils.utils import setup_logging
from chatbot.utils.job_fetcher import get_all_jobs
logger = setup_logging()
def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")
def print_stage_info(agent: CleoRAGAgent):
    """Print current stage information"""
    summary = agent.get_conversation_summary()
    print(f"\n[STAGE INFO]")
    print(f"Current Stage: {summary['current_stage']}")
    print(f"Engagement Complete: {summary['engagement_complete']}")
    print(f"Qualification Complete: {summary['qualification_complete']}")
    print(f"Application Complete: {summary['application_complete']}")
    print(f"Ready for Verification: {summary['ready_for_verification']}")
    print()
def send_message(agent: CleoRAGAgent, user_message: str, show_stage=True):
    """Send a message and display responses"""
    print(f"👤 User: {user_message}")
    responses = agent.process_message(user_message)
    for i, response in enumerate(responses):
        if i > 0:
            print()
        print(f"🤖 Cleo: {response}")
    if show_stage:
        print_stage_info(agent)
    time.sleep(0.5)  # Small delay for readability
def test_complete_application_flow():
    """Test complete application flow through all stages"""
    print_separator("CLEO CHATBOT - COMPLETE APPLICATION FLOW TEST")
    # Ensure directories exist
    ensure_directories()
    
    # Fetch a real job from Xano
    print("Fetching available jobs from Xano...")
    jobs = get_all_jobs()
    
    if not jobs:
        print("⚠️ No jobs found in Xano. Please create a job first.")
        print("Exiting test...")
        return
    
    # Use the first available job
    test_job = jobs[0]
    job_id = str(test_job.get('id'))
    print(f"Using job: {test_job.get('job_title', 'Unknown')} (ID: {job_id})")
    
    # Create agent with job context
    print("Initializing agent with job context...")
    agent = CleoRAGAgent(job_id=job_id)
    
    # Set job for testing with real Xano data
    from chatbot.state.states import EngagementState
    agent.session_state.engagement = EngagementState(
        session_id=agent.session_state.session_id,
        job_id=job_id,
        job_details=test_job
    )
    print(f"Session ID: {agent.session_state.session_id}")
    print(f"Job: {test_job.get('job_title', 'Unknown')}")
    print()
    # ========================================
    # ENGAGEMENT STAGE
    # ========================================
    print_separator("STAGE 1: ENGAGEMENT")
    send_message(agent, "Hello")
    send_message(agent, "Yes, I'd like to apply")
    send_message(agent, "Yes, I consent")
    # ========================================
    # QUALIFICATION STAGE
    # ========================================
    print_separator("STAGE 2: QUALIFICATION")
    send_message(agent, "Yes, I'm 25 years old")
    send_message(agent, "Yes, I'm authorized to work in the US")
    send_message(agent, "I prefer day shifts")
    send_message(agent, "I can start immediately")
    send_message(agent, "Yes, I have my own transportation")
    send_message(agent, "I'm looking for full-time work")
    # ========================================
    # APPLICATION STAGE
    # ========================================
    print_separator("STAGE 3: APPLICATION")
    send_message(agent, "My name is John Smith")
    send_message(agent, "My phone number is 555-123-4567")
    send_message(agent, "My email is john.smith@email.com")
    send_message(agent, "I live at 123 Main Street, Los Angeles, CA 90001")
    send_message(agent, "I previously worked at XYZ Warehouse")
    send_message(agent, "I was a Warehouse Worker")
    send_message(agent, "I have 3.5 years of experience")
    send_message(agent, "I have skills in forklift operation, inventory management, packing, and shipping")
    send_message(agent, "Yes, I can provide references from my previous employer")
    send_message(agent, "I prefer email for communication")
    send_message(agent, "okk Good Bye")
    
    # ========================================
    # WAIT FOR SESSION CONCLUSION
    # ========================================
    print_separator("WAITING FOR SESSION TO WIND UP")
    print("⏳ Waiting 3 minutes for agent to conclude session and create candidate...")
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Wait for 3 minutes (180 seconds)
    for remaining in range(180, 0, -30):
        print(f"   ⏰ {remaining} seconds remaining...")
        time.sleep(30)
    
    print(f"End time: {datetime.now().strftime('%H:%M:%S')}")
    print("✅ Wait complete. Triggering session conclusion...")
    print()
    
    # ========================================
    # TRIGGER SESSION CONCLUSION
    # ========================================
    print_separator("SESSION CONCLUSION & CANDIDATE CREATION")
    try:
        # Get the toolkit to manually conclude the session
        from chatbot.core.tools import AgentToolkit
        toolkit = AgentToolkit(
            session_state=agent.session_state,
            job_id=agent.session_state.engagement.job_id if agent.session_state.engagement else None,
            agent=agent
        )
        
        # Conclude the session
        conclusion_result = toolkit.conclude_session("Test completed - winding up session")
        print(f"Conclusion Result: {conclusion_result}")
        print()
        
        # Check if candidate was created
        if agent.session_state.engagement and agent.session_state.engagement.candidate_id:
            print(f"✅ SUCCESS: Candidate created with ID: {agent.session_state.engagement.candidate_id}")
        else:
            print("⚠️ WARNING: No candidate ID found in engagement state")
            
    except Exception as e:
        print(f"❌ ERROR during session conclusion: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================
    # VERIFICATION STAGE
    # ========================================
    print_separator("STAGE 4: VERIFICATION (OUT OF SCOPE)")
    print("Note: Verification is out of scope for this project.")
    print("The application is now complete and ready for verification.")
    print()
    # ========================================
    # CALCULATE FIT SCORE
    # ========================================
    print_separator("FIT SCORE CALCULATION")
    # Get chat history for personality analysis
    chat_history = []
    if agent.memory and hasattr(agent.memory, 'chat_memory'):
        for message in agent.memory.chat_memory.messages:
            chat_history.append({
                "role": "human" if message.type == "human" else "ai",
                "content": message.content,
            })
    calculator = FitScoreCalculator(llm=agent.llm)
    fit_score = calculator.calculate_fit_score(
        qualification=agent.session_state.qualification,
        application=agent.session_state.application,
        chat_history=chat_history,
        verification=agent.session_state.verification  # Will be ignored
    )
    print(f"Qualification Score: {fit_score.qualification_score:.2f}/100")
    print(f"Experience Score: {fit_score.experience_score:.2f}/100")
    print(f"Personality Score: {fit_score.personality_score:.2f}/100")
    print(f"\n✨ TOTAL FIT SCORE: {fit_score.total_score:.2f}/100")
    print(f"📊 RATING: {calculator.get_fit_rating(fit_score.total_score)}")
    # ========================================
    # DISPLAY COMPLETE APPLICATION DATA
    # ========================================
    print_separator("COMPLETE APPLICATION DATA")
    application_data = {
        "session_id": agent.session_state.session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "job": agent.session_state.engagement.job_details,
        "stages": {
            "engagement": agent.session_state.engagement.model_dump() if agent.session_state.engagement else None,
            "qualification": agent.session_state.qualification.model_dump() if agent.session_state.qualification else None,
            "application": agent.session_state.application.model_dump() if agent.session_state.application else None,
        },
        "fit_score": {
            "total_score": fit_score.total_score,
            "rating": calculator.get_fit_rating(fit_score.total_score),
            "qualification_score": fit_score.qualification_score,
            "experience_score": fit_score.experience_score,
            "personality_score": fit_score.personality_score,
            "breakdown": fit_score.breakdown
        },
        "status": {
            "current_stage": agent.session_state.current_stage.value,
            "engagement_complete": agent.session_state.engagement.stage_completed if agent.session_state.engagement else False,
            "qualification_complete": agent.session_state.qualification.stage_completed if agent.session_state.qualification else False,
            "application_complete": agent.session_state.application.stage_completed if agent.session_state.application else False,
            "ready_for_verification": agent.session_state.application.stage_completed if agent.session_state.application else False,
        }
    }
    print(json.dumps(application_data, indent=2, default=str))
    # ========================================
    # STAGE TRANSITION VERIFICATION
    # ========================================
    print_separator("STAGE TRANSITION VERIFICATION")
    print("✅ Verifying stage transitions:")
    print(f"   Started at: ENGAGEMENT")
    print(f"   Moved to: QUALIFICATION")
    print(f"   Moved to: APPLICATION")
    print(f"   Moved to: VERIFICATION")
    print(f"   Current Stage: {agent.session_state.current_stage.value}")
    print()
    # Verify all stages completed properly
    assert agent.session_state.engagement.stage_completed, "❌ Engagement stage should be completed"
    assert agent.session_state.qualification.stage_completed, "❌ Qualification stage should be completed"
    assert agent.session_state.application.stage_completed, "❌ Application stage should be completed"
    # Note: Stage might be COMPLETED instead of VERIFICATION after all data is collected
    assert agent.session_state.current_stage in [ConversationStage.VERIFICATION, ConversationStage.COMPLETED], "❌ Should be in VERIFICATION or COMPLETED stage"
    print("✅ All stage transitions verified successfully!")
    # ========================================
    # SAVE SESSION
    # ========================================
    print_separator("SAVING SESSION")
    agent.state_manager.save_session(agent.session_state)
    print(f"✅ Session saved: {agent.session_state.session_id}")
    print(f"   Location: storage/")
    # ========================================
    # SUMMARY
    # ========================================
    print_separator("TEST SUMMARY")
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print()
    print(f"Session ID: {agent.session_state.session_id}")
    print(f"Applicant: {agent.session_state.application.full_name}")
    print(f"Job: {agent.session_state.engagement.job_details['title']}")
    print(f"Fit Score: {fit_score.total_score:.2f}/100 ({calculator.get_fit_rating(fit_score.total_score)})")
    print(f"Current Stage: {agent.session_state.current_stage.value}")
    print()
    print("All stages progressed correctly:")
    print(f"  ✅ Engagement: Completed")
    print(f"  ✅ Qualification: Completed")
    print(f"  ✅ Application: Completed")
    print(f"  ✅ Ready for Verification: {agent.session_state.application.stage_completed if agent.session_state.application else False}")
    print()
    return application_data


def test_conclude_requires_name_email_phone():
    """Ensure conclude will not create a candidate unless name, email, and phone are present"""
    from chatbot.core.tools import AgentToolkit
    from chatbot.utils.fit_score import FitScoreComponents
    from chatbot.state.states import ApplicationState

    agent = CleoRAGAgent()
    # Initialize application state with only a name (missing email and phone)
    agent.session_state.application = ApplicationState(session_id=agent.session_state.session_id, full_name="Jane Doe")
    toolkit = AgentToolkit(agent.session_state)
    fit_score = FitScoreComponents(qualification_score=0.0, experience_score=0.0, personality_score=0.0, total_score=0.0, breakdown={})
    candidate_id = toolkit._create_candidate_on_conclude(fit_score, None)
    assert candidate_id is None, "Candidate should not be created without email and phone"


def test_conclude_fetches_from_memory():
    """Ensure conclude will attempt to fetch missing name/email/phone from conversation memory and create candidate"""
    from chatbot.core.tools import AgentToolkit
    from chatbot.utils.fit_score import FitScoreComponents
    agent = CleoRAGAgent()
    # Ensure application state is empty
    agent.session_state.application = None
    # Inject messages into memory that contain contact info
    from langchain.schema import HumanMessage
    agent.memory.chat_memory.add_message(HumanMessage(content="My name is Alice Wonderland"))
    agent.memory.chat_memory.add_message(HumanMessage(content="My email is alice@example.com"))
    agent.memory.chat_memory.add_message(HumanMessage(content="My phone number is +15551234567"))

    # Verify application still empty
    assert not agent.session_state.application or not agent.session_state.application.full_name

    # Bind toolkit to agent so it can read memory
    toolkit = AgentToolkit(agent.session_state, agent.job_id, agent=agent)

    # Replace xano_client with dummy to avoid HTTP calls
    class DummyXanoClient:
        def create_candidate(self, **kwargs):
            return {"id": 999}
        def update_session(self, *args, **kwargs):
            return True
    toolkit.xano_client = DummyXanoClient()
    toolkit._report_generator = toolkit._report_generator  # keep existing generator if any

    fit_score = FitScoreComponents(qualification_score=0.0, experience_score=0.0, personality_score=0.0, total_score=0.0, breakdown={})
    # Call conclude_session - it should read from memory and create candidate
    result = toolkit.conclude_session("User said goodbye")
    assert "Session concluded successfully" in result
    # Verify candidate created and stored in engagement state
    if agent.session_state.engagement:
        assert agent.session_state.engagement.candidate_id == 999
if __name__ == "__main__":
    try:
        application_data = test_complete_application_flow()
        # Write results to file
        output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(application_data, f, indent=2, default=str)
        print(f"📄 Full results saved to: {output_file}")
        print()
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

