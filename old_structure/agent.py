"""
Agentic RAG System
LangChain-based agent that reasons, uses tools, and queries knowledge base
"""
from typing import Dict, Any, List, Optional, Callable
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from retrievers import KnowledgeBaseRetriever, RetrievalMethod
from states import (
    SessionState, EngagementState, QualificationState,
    ApplicationState, VerificationState, ConversationStage, StateManager
)
from config import settings
from utils import setup_logging, get_current_timestamp

logger = setup_logging()


class CleoRAGAgent:
    """Agentic RAG system for conversational job application"""
    
    def __init__(
        self,
        session_state: SessionState = None,
        retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID
    ):
        """
        Initialize Cleo RAG Agent
        
        Args:
            session_state: Current session state (creates new if None)
            retrieval_method: Method for knowledge base retrieval
        """
        self.session_state = session_state or SessionState()
        self.retrieval_method = retrieval_method
        self.state_manager = StateManager()
        
        # Initialize retriever
        try:
            self.retriever = KnowledgeBaseRetriever()
        except Exception as e:
            logger.warning(f"Could not initialize retriever: {e}. Agent will work without KB.")
            self.retriever = None
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create tools and agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        tools = []
        
        # Knowledge Base Query Tool
        if self.retriever:
            def query_knowledge_base(query: str) -> str:
                """
                Query the knowledge base for relevant information about jobs,
                company policies, requirements, benefits, etc.
                Use this when you need specific information to answer user questions.
                """
                try:
                    results = self.retriever.retrieve(
                        query=query,
                        method=self.retrieval_method,
                        top_k=3
                    )
                    context = self.retriever.format_context(results)
                    return context
                except Exception as e:
                    logger.error(f"Error querying knowledge base: {e}")
                    return "Unable to retrieve information from knowledge base."
            
            tools.append(Tool(
                name="query_knowledge_base",
                func=query_knowledge_base,
                description="Query the knowledge base for information about jobs, requirements, benefits, company policies, etc."
            ))
        
        # Save State Tool
        def save_current_state(state_info: str) -> str:
            """Save the current conversation state"""
            try:
                self.state_manager.save_session(self.session_state)
                return f"State saved successfully for session {self.session_state.session_id}"
            except Exception as e:
                logger.error(f"Error saving state: {e}")
                return f"Error saving state: {str(e)}"
        
        tools.append(Tool(
            name="save_state",
            func=save_current_state,
            description="Save the current conversation state to persistent storage"
        ))
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent"""
        # Get system prompt based on current stage
        system_prompt = self._get_system_prompt()
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def _get_system_prompt(self) -> str:
        """Get system prompt based on current conversation stage"""
        base_prompt = """You are Cleo, an AI assistant helping job applicants through the application process.
You are friendly, professional, and conversational - NOT a rigid form-based chatbot.

Your capabilities:
- You can query a knowledge base for information about jobs, company policies, requirements, and benefits
- You guide applicants through a structured conversation flow
- You collect information naturally through conversation
- You are patient and supportive

Current Session Info:
- Session ID: {session_id}
- Current Stage: {current_stage}
- Language: {language}

IMPORTANT Guidelines:
1. ALWAYS decide if you need to query the knowledge base before answering
2. Use the query_knowledge_base tool when you need specific information about:
   - Job requirements and qualifications
   - Company policies and procedures
   - Benefits and compensation
   - Work schedules and shifts
   - Application process details
3. For general conversation or when you already have the information, respond directly
4. Keep responses natural and conversational
5. Ask one question at a time
6. Be encouraging and positive
"""
        
        # Stage-specific prompts
        stage_prompts = {
            ConversationStage.ENGAGEMENT: """
You are in the ENGAGEMENT stage. Your goals:
1. Greet the applicant warmly
2. Explain who you are and what you'll help them with
3. Get their consent to proceed
4. Capture company_id and job_id if mentioned
5. Once consent is obtained, move to qualification

Be welcoming and build trust. Use the knowledge base to answer questions about the company or position.
""",
            ConversationStage.QUALIFICATION: """
You are in the QUALIFICATION stage. Your goals:
1. Confirm age eligibility (18+)
2. Verify work authorization
3. Ask about shift preferences
4. Ask about availability start date
5. Confirm transportation availability
6. Ask about hours preference (full-time/part-time)

Be conversational - don't make it feel like a form. If someone doesn't meet requirements, let them down gently.
Use the knowledge base to provide information about shifts, schedules, and requirements.
""",
            ConversationStage.APPLICATION: """
You are in the APPLICATION stage. Your goals:
1. Collect full name
2. Get phone number
3. Get email address
4. Get address
5. Ask about previous employment
6. Ask about job title and experience
7. Ask about relevant skills
8. Ask about references
9. Ask communication preference

Collect information naturally through conversation. You can ask clarifying questions.
Use the knowledge base to answer questions about the role or what skills are valued.
""",
            ConversationStage.VERIFICATION: """
You are in the VERIFICATION stage. Your goals:
1. Request ID upload/verification
2. Explain verification process
3. Confirm verification status
4. Complete the application process

Be clear about requirements and next steps.
Use the knowledge base to explain verification procedures and requirements.
"""
        }
        
        current_stage_prompt = stage_prompts.get(
            self.session_state.current_stage,
            "Continue the conversation naturally."
        )
        
        return base_prompt.format(
            session_id=self.session_state.session_id,
            current_stage=self.session_state.current_stage.value,
            language=getattr(self.session_state.engagement, 'language', 'en') if self.session_state.engagement else 'en'
        ) + "\n\n" + current_stage_prompt
    
    def process_message(self, user_message: str) -> str:
        """
        Process user message and generate response
        
        Args:
            user_message: User's input message
        
        Returns:
            Agent's response
        """
        logger.info(f"Processing message: {user_message}")
        
        try:
            # Invoke agent
            response = self.agent.invoke({"input": user_message})
            agent_response = response.get("output", "I'm sorry, I didn't understand that.")
            
            # Update conversation state based on response
            self._update_state_from_conversation(user_message, agent_response)
            
            return agent_response
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error. Could you please rephrase that?"
    
    def _update_state_from_conversation(self, user_message: str, agent_response: str):
        """
        Update session state based on conversation context
        This is a simplified version - in production, use more sophisticated NLU
        """
        user_lower = user_message.lower()
        
        # Engagement stage updates
        if self.session_state.current_stage == ConversationStage.ENGAGEMENT:
            if not self.session_state.engagement:
                self.session_state.engagement = EngagementState(
                    session_id=self.session_state.session_id
                )
            
            # Check for consent keywords
            if any(word in user_lower for word in ['yes', 'sure', 'okay', 'ok', 'proceed', 'continue']):
                self.session_state.engagement.consent_given = True
                self.session_state.engagement.stage_completed = True
                self.session_state.current_stage = ConversationStage.QUALIFICATION
                logger.info("Moving to QUALIFICATION stage")
        
        # Qualification stage updates
        elif self.session_state.current_stage == ConversationStage.QUALIFICATION:
            if not self.session_state.qualification:
                self.session_state.qualification = QualificationState(
                    session_id=self.session_state.session_id
                )
            
            # Simple keyword detection (in production, use better NLU)
            if 'yes' in user_lower or '18' in user_message or 'older' in user_lower:
                if not self.session_state.qualification.age_confirmed:
                    self.session_state.qualification.age_confirmed = True
            
            if 'authorized' in user_lower or 'citizen' in user_lower:
                self.session_state.qualification.work_authorization = True
            
            # Check if qualification is complete
            qual = self.session_state.qualification
            if all([qual.age_confirmed, qual.work_authorization]):
                qual.qualification_status = "qualified"
                if not qual.stage_completed and qual.shift_preference and qual.availability_start:
                    qual.stage_completed = True
                    self.session_state.current_stage = ConversationStage.APPLICATION
                    logger.info("Moving to APPLICATION stage")
        
        # Application stage updates
        elif self.session_state.current_stage == ConversationStage.APPLICATION:
            if not self.session_state.application:
                self.session_state.application = ApplicationState(
                    session_id=self.session_state.session_id
                )
            
            # In production, use NER to extract name, phone, email, etc.
            # This is simplified placeholder logic
            
        # Auto-save state periodically
        if self.session_state.engagement and self.session_state.engagement.stage_completed:
            self.state_manager.save_session(self.session_state)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation state"""
        return {
            'session_id': self.session_state.session_id,
            'current_stage': self.session_state.current_stage.value,
            'engagement_complete': self.session_state.engagement.stage_completed if self.session_state.engagement else False,
            'qualification_complete': self.session_state.qualification.stage_completed if self.session_state.qualification else False,
            'application_complete': self.session_state.application.stage_completed if self.session_state.application else False,
            'verification_complete': self.session_state.verification.stage_completed if self.session_state.verification else False,
        }


def main():
    """Example usage of Cleo RAG Agent"""
    from config import ensure_directories
    ensure_directories()
    
    # Create agent
    agent = CleoRAGAgent()
    
    print("=== Cleo RAG Agent Demo ===")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using Cleo!")
            break
        
        response = agent.process_message(user_input)
        print(f"\nCleo: {response}\n")
        
        # Show stage info
        summary = agent.get_conversation_summary()
        print(f"[Stage: {summary['current_stage']}]\n")


if __name__ == "__main__":
    main()
