"""
Test script to demonstrate LangFuse integration with Cleo RAG Agent
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import SessionState, ConversationStage
from chatbot.utils.config import settings

def test_langfuse_integration():
    """Test the agent with LangFuse tracing enabled"""
    
    print("🚀 Testing Cleo RAG Agent with LangFuse Integration")
    print("=" * 60)
    
    # Check if LangFuse is configured
    if not settings.LANGFUSE_ENABLED:
        print("⚠️  LangFuse is disabled. Set LANGFUSE_ENABLED=true in .env to enable tracing.")
        print("   You can still test the agent functionality without observability.\n")
    else:
        print("✅ LangFuse is enabled!")
        print(f"   Host: {settings.LANGFUSE_HOST}")
        print(f"   Public Key: {settings.LANGFUSE_PUBLIC_KEY[:10]}..." if settings.LANGFUSE_PUBLIC_KEY else "   Public Key: Not configured")
        print()
    
    # Create a test session
    session = SessionState()
    print(f"📋 Created test session: {session.session_id}")
    
    # Initialize agent
    print("🤖 Initializing Cleo RAG Agent...")
    try:
        agent = CleoRAGAgent(session_state=session)
        print("✅ Agent initialized successfully!")
        
        if agent.langfuse_handler:
            print("✅ LangFuse callback handler active")
        else:
            print("ℹ️  Running without LangFuse (check configuration)")
            
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return
    
    print()
    
    # Test conversation scenarios
    test_scenarios = [
        {
            "name": "Greeting and Job Interest",
            "message": "Hi, I'm interested in applying for a job position"
        },
        {
            "name": "Company Policy Question",
            "message": "What are the work hours and benefits for this position?"
        },
        {
            "name": "Job Requirements Question", 
            "message": "What qualifications do I need for this role?"
        },
        {
            "name": "Application Process Question",
            "message": "How does the application process work?"
        }
    ]
    
    print("🎭 Testing conversation scenarios:")
    print("-" * 40)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   User: {scenario['message']}")
        
        try:
            # Process message through agent
            responses = agent.process_message(scenario['message'])
            
            print(f"   Cleo: ", end="")
            for j, response in enumerate(responses):
                if j > 0:
                    print("         ", end="")
                # Truncate long responses for cleaner output
                display_response = response[:100] + "..." if len(response) > 100 else response
                print(display_response)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Observability Information:")
    
    if settings.LANGFUSE_ENABLED and agent.langfuse_handler:
        print(f"✅ Traces are being sent to: {settings.LANGFUSE_HOST}")
        print(f"📊 Session ID for filtering: {session.session_id}")
        print("🌐 View traces in your LangFuse dashboard:")
        print(f"   {settings.LANGFUSE_HOST}/project/traces")
        print("\n💡 What you'll see in LangFuse:")
        print("   • Complete conversation flow")
        print("   • Knowledge base query results") 
        print("   • Token usage and costs")
        print("   • Agent tool usage")
        print("   • Response times")
    else:
        print("ℹ️  To enable observability:")
        print("   1. Get LangFuse API keys from https://cloud.langfuse.com")
        print("   2. Update .env file with your keys")
        print("   3. Set LANGFUSE_ENABLED=true")
        print("   4. Re-run this test")
    
    print(f"\n🎯 Agent Configuration:")
    print(f"   Model: {settings.OPENAI_CHAT_MODEL}")
    print(f"   Temperature: {settings.OPENAI_TEMPERATURE}")
    print(f"   Session Stage: {session.current_stage.value}")
    print(f"   Knowledge Base: {'✅ Available' if agent.retriever else '❌ Not configured'}")

if __name__ == "__main__":
    test_langfuse_integration()