"""
Demo Conversation Script
Demonstrates end-to-end Cleo RAG Agent interaction
"""
from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import ConversationStage
from chatbot.utils.report_generator import ReportGenerator
from chatbot.utils.config import ensure_directories
from chatbot.utils.utils import setup_logging
import time

logger = setup_logging()


def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'=' * 20} {title} {'=' * 20}\n")
    else:
        print("\n" + "=" * 60 + "\n")


def simulate_conversation():
    """Simulate a complete conversation flow"""
    ensure_directories()
    
    print_separator("Cleo RAG Agent Demo - Complete Conversation Flow")
    
    # Create agent
    print("Initializing Cleo RAG Agent...")
    agent = CleoRAGAgent()
    print(f"Session ID: {agent.session_state.session_id}\n")
    
    # Conversation scenarios
    conversations = [
        # ENGAGEMENT STAGE
        {
            "stage": "ENGAGEMENT",
            "messages": [
                ("User", "Hi there!"),
                ("User", "Yes, I'd like to apply for a position"),
                ("User", "Sure, I consent to proceed"),
            ]
        },
        # QUALIFICATION STAGE
        {
            "stage": "QUALIFICATION",
            "messages": [
                ("User", "Yes, I'm over 18 years old"),
                ("User", "Yes, I'm authorized to work in the United States"),
                ("User", "I prefer day shifts"),
                ("User", "I can start on February 1st, 2024"),
                ("User", "Yes, I have my own transportation"),
                ("User", "I'm looking for full-time work"),
            ]
        },
        # APPLICATION STAGE
        {
            "stage": "APPLICATION",
            "messages": [
                ("User", "My name is Sarah Johnson"),
                ("User", "My phone number is 555-0199"),
                ("User", "My email is sarah.johnson@email.com"),
                ("User", "I live at 456 Oak Avenue, Springfield, IL 62701"),
                ("User", "I previously worked at MegaMart"),
                ("User", "I was a Warehouse Associate"),
                ("User", "I have about 4 years of experience"),
                ("User", "My skills include forklift operation, inventory management, order picking, packing, and shipping"),
                ("User", "Yes, I can provide references from my previous supervisors"),
                ("User", "I prefer email communication"),
            ]
        },
        # VERIFICATION STAGE
        {
            "stage": "VERIFICATION",
            "messages": [
                ("User", "Yes, I can upload my ID"),
                ("User", "I'll upload my driver's license"),
            ]
        }
    ]
    
    # Run conversation
    for conv_stage in conversations:
        print_separator(f"Stage: {conv_stage['stage']}")
        
        for speaker, message in conv_stage['messages']:
            print(f"{speaker}: {message}")
            
            if speaker == "User":
                responses = agent.process_message(message)
                # Handle multiple messages
                for i, response in enumerate(responses):
                    if i > 0:
                        print()  # Add newline between multiple messages
                    print(f"Cleo: {response}")
                print()  # Add newline after all messages
                time.sleep(0.5)  # Simulate thinking time
        
        # Show stage summary
        summary = agent.get_conversation_summary()
        print(f"\n[Current Stage: {summary['current_stage']}]")
        print(f"[Engagement Complete: {summary['engagement_complete']}]")
        print(f"[Qualification Complete: {summary['qualification_complete']}]")
        print(f"[Application Complete: {summary['application_complete']}]")
        
        time.sleep(1)
    
    # Manually complete verification for demo purposes
    print_separator("Completing Verification (Simulated)")
    from chatbot.state.states import VerificationState
    from chatbot.utils.utils import get_current_timestamp
    
    verification = VerificationState(
        session_id=agent.session_state.session_id,
        id_uploaded=True,
        id_type="driver_license",
        verification_status="verified",
        timestamp_verified=get_current_timestamp(),
        stage_completed=True
    )
    agent.session_state.verification = verification
    agent.session_state.current_stage = ConversationStage.COMPLETED
    
    # Save final state
    agent.state_manager.save_session(agent.session_state)
    print("Verification completed and session saved!")
    
    # Generate report
    print_separator("Generating Eligibility Report")
    report_gen = ReportGenerator()
    
    try:
        result = report_gen.generate_report(
            session_id=agent.session_state.session_id,
            include_fit_score=True
        )
        
        print("Report generated successfully!")
        print(f"\nJSON Report: {result['json_report']}")
        print(f"PDF Report: {result['pdf_report']}")
        
        # Show fit score
        import json
        with open(result['json_report'], 'r') as f:
            report_data = json.load(f)
        
        if 'fit_score' in report_data:
            print_separator("Fit Score Analysis")
            fit = report_data['fit_score']
            print(f"Total Score: {fit['total_score']}/100")
            print(f"Rating: {fit['rating']}")
            print(f"\nComponent Scores:")
            print(f"  Qualification: {fit['qualification_score']}/100")
            print(f"  Experience: {fit['experience_score']}/100")
            print(f"  Verification: {fit['verification_score']}/100")
        
        print_separator("Eligibility Summary")
        summary = report_data['eligibility_summary']
        print(f"Qualified: {summary['qualified']}")
        print(f"Verified: {summary['verified']}")
        print(f"Application Complete: {summary['application_complete']}")
        print(f"Recommendation: {summary['recommendation']}")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        print(f"Error generating report: {e}")
    
    print_separator("Demo Complete")
    print(f"Session ID: {agent.session_state.session_id}")
    print("\nThis session can be resumed later using the session ID.")
    print("All data has been saved to CSV files in the storage directory.")


def demo_retrieval():
    """Demo the retrieval methods (requires knowledge base to be populated)"""
    print_separator("Knowledge Base Retrieval Demo")
    
    try:
        from chatbot.core.retrievers import KnowledgeBaseRetriever, RetrievalMethod
        
        retriever = KnowledgeBaseRetriever()
        
        queries = [
            "What are the shift requirements?",
            "What benefits are available?",
            "What skills are needed for warehouse positions?",
        ]
        
        for query in queries:
            print(f"\nQuery: {query}")
            print("-" * 60)
            
            results = retriever.retrieve(
                query=query,
                method=RetrievalMethod.HYBRID,
                top_k=2
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"  Document: {result['document_name']}")
                    print(f"  Section: {result['section']}")
                    print(f"  Score: {result.get('score', 0):.3f}")
                    print(f"  Text: {result['text'][:150]}...")
            else:
                print("  No results found (knowledge base may be empty)")
        
        print_separator()
        
    except Exception as e:
        logger.warning(f"Retrieval demo skipped: {e}")
        print(f"Retrieval demo skipped (Milvus may not be running): {e}")
        print("To use retrieval features, make sure Milvus is running:")
        print("  docker-compose up -d")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("CLEO RAG AGENT - COMPLETE DEMONSTRATION")
    print("=" * 60)
    
    # Demo 1: Complete conversation flow
    simulate_conversation()
    
    # Demo 2: Retrieval methods (optional)
    print("\n\nWould you like to demo the knowledge base retrieval? (Requires Milvus)")
    response = input("Enter 'yes' to continue: ").strip().lower()
    
    if response == 'yes':
        demo_retrieval()
    
    print("\n" + "=" * 60)
    print("Thank you for exploring Cleo RAG Agent!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
