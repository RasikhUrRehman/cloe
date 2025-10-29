"""
Test Conversation Flow
Tests complete application flow through all stages and verifies stage transitions
"""

import json
import time
from datetime import datetime

from chatbot.core.agent import CleoRAGAgent
from chatbot.core.retrievers import RetrievalMethod
from chatbot.state.states import ConversationStage
from chatbot.utils.config import ensure_directories
from chatbot.utils.fit_score import FitScoreCalculator
from chatbot.utils.utils import setup_logging

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
    
    # Create agent with job context
    print("Initializing agent with job context...")
    agent = CleoRAGAgent(retrieval_method=RetrievalMethod.HYBRID)
    
    # Set a job for testing (simulate warehouse job)
    from chatbot.state.states import EngagementState
    
    agent.session_state.engagement = EngagementState(
        session_id=agent.session_state.session_id,
        job_id="WAREHOUSE-001",
        job_details={
            "title": "Warehouse Associate",
            "company": "ABC Logistics",
            "location": "Los Angeles, CA",
            "type": "Full-time",
            "shift": "Day shift (8am-5pm)",
            "requirements": [
                "Must be 18 years or older",
                "Valid work authorization in the US",
                "Ability to lift 50 lbs",
                "Forklift certification preferred"
            ],
            "salary": "$18-22/hour",
            "benefits": ["Health insurance", "401k", "Paid time off"]
        }
    )
    
    print(f"Session ID: {agent.session_state.session_id}")
    print(f"Job: {agent.session_state.engagement.job_details['title']}")
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
    assert agent.session_state.current_stage == ConversationStage.VERIFICATION, "❌ Should be in VERIFICATION stage"
    
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
