"""
Agentic RAG System
LangChain-based agent that reasons, uses tools, and queries knowledge base
"""
from typing import Any, Dict, List
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
# LangFuse imports
try:
    from langfuse.langchain import CallbackHandler as LangFuseCallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
# from chatbot.core.retrievers import RetrievalMethod
from chatbot.core.tools import create_agent_tools, AgentToolkit
from chatbot.prompts.prompts import get_system_prompt
from chatbot.state.states import (
    ApplicationState,
    ConversationStage,
    EngagementState,
    QualificationState,
    SessionState,
    VerificationState,
)
from chatbot.utils.config import settings
from chatbot.utils.job_fetcher import format_job_details
from chatbot.utils.utils import get_current_timestamp, setup_logging
from chatbot.utils.xano_client import get_xano_client
logger = setup_logging()
class CleoRAGAgent:
    """Agentic RAG system for conversational job application"""
    def __init__(
        self,
        session_state: SessionState = None,
        job_id: str = None,
    ):
        """
        Initialize Cleo RAG Agent
        Args:
            session_state: Current session state (creates new if None)
            job_id: Job ID for the position being applied to
        """
        self.session_state = session_state or SessionState()
        self.job_id = job_id  # Store job_id for candidate creation
        self.xano_client = get_xano_client()
        
        # Create toolkit for this agent (bound to session state, no globals)
        # Pass a reference to the agent so the toolkit can access conversation memory
        self.toolkit = AgentToolkit(self.session_state, self.job_id, agent=self)
        
        # Create Xano session and store session ID
        if not self.session_state.engagement:
            self.session_state.engagement = EngagementState(session_id=self.session_state.session_id)
        
        if not self.session_state.engagement.xano_session_id:
            xano_session = self.xano_client.create_session(initial_status="Started", job_id=self.job_id)
            if xano_session:
                self.session_state.engagement.xano_session_id = xano_session.get('id')
                # Also store job_id in engagement state for consistency
                if self.job_id:
                    self.session_state.engagement.job_id = self.job_id
                logger.info(f"Created Xano session {self.session_state.engagement.xano_session_id} for session {self.session_state.session_id} with job_id: {self.job_id}")
            else:
                logger.warning(f"Failed to create Xano session for {self.session_state.session_id}")
        
        # Initialize LangFuse if enabled
        self.langfuse_handler = None
        self.langfuse_enabled = settings.LANGFUSE_ENABLED
        if self.langfuse_enabled and LANGFUSE_AVAILABLE:
            try:
                # Test basic connection first
                from langfuse import Langfuse
                test_client = Langfuse(
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    host=settings.LANGFUSE_HOST,
                )
                # Try a minimal trace to validate connection
                test_client.trace(name="agent_init_test")
                logger.info("✅ LangFuse connection validated")
                # Initialize callback handler (reads from environment variables)
                self.langfuse_handler = LangFuseCallbackHandler()
                self.langfuse_enabled = True
                logger.info("✅ LangFuse callback handler initialized")
            except Exception as e:
                logger.warning(f"⚠️  LangFuse initialization failed: {e}")
                logger.info("🔄 Agent will continue without observability tracking")
                self.langfuse_handler = None
                self.langfuse_enabled = False
        # Initialize LLM
        callbacks = [self.langfuse_handler] if self.langfuse_handler else []
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
            callbacks=callbacks,
        )
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        
        # Add job_id to memory context if provided
        if self.job_id:
            from langchain.schema import SystemMessage
            self.memory.chat_memory.add_message(
                SystemMessage(content=f"IMPORTANT CONTEXT: This session is for job_id: {self.job_id}. When creating a candidate, this job_id MUST be associated with the candidate record.")
            )
            logger.info(f"Added job_id {self.job_id} to agent memory")
        
        # Get tools from the toolkit (bound to this agent's session state)
        self.tools = self.toolkit.get_tools()
        self.agent = self._create_agent()
        
        # Track the last stage added to context to avoid repetition
        self.last_context_stage = None

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent"""
        # Get system prompt based on current stage using CleoPrompts
        system_prompt = self._get_system_prompt()
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm, tools=self.tools, prompt=prompt
        )
        # Create agent executor with callbacks
        callbacks = [self.langfuse_handler] if self.langfuse_handler else []
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,  # Prevent tool execution details from being exposed
            max_iterations=15,  # Increased to allow multiple tool calls per turn
            handle_parsing_errors=True,
            callbacks=callbacks,
        )
        return agent_executor
    def _get_system_prompt(self) -> str:
        """Get system prompt based on current conversation stage"""
        # Get language from engagement state
        language = "en"
        if self.session_state.engagement:
            language = getattr(self.session_state.engagement, "language", "en")
        # Get job details if available
        job_context = ""
        if self.session_state.engagement and self.session_state.engagement.job_details:
            job_context = format_job_details(self.session_state.engagement.job_details)
        # Get generated questions if available
        generated_questions = None
        if self.session_state.engagement and self.session_state.engagement.generated_questions:
            generated_questions = self.session_state.engagement.generated_questions
        # Use CleoPrompts to get the complete system prompt
        return get_system_prompt(
            session_id=self.session_state.session_id,
            current_stage=self.session_state.current_stage,
            language=language,
            job_context=job_context,
            generated_questions=generated_questions,
        )
    def _refresh_agent_with_job_context(self):
        """Refresh the agent with updated job context"""
        self.agent = self._create_agent()
        logger.info("Agent refreshed with job context")
    
    def _update_xano_status(self, stage: ConversationStage):
        """Update Xano session status based on conversation stage"""
        if not self.session_state.engagement or not self.session_state.engagement.xano_session_id:
            logger.warning("Cannot update Xano status: No Xano session ID found")
            return
        
        xano_session_id = self.session_state.engagement.xano_session_id
        
        # Map conversation stages to Xano status values
        stage_to_status = {
            ConversationStage.ENGAGEMENT: "Started",
            ConversationStage.QUALIFICATION: "Continue",
            ConversationStage.APPLICATION: "Continue",
            ConversationStage.VERIFICATION: "Pending",
            ConversationStage.COMPLETED: "Completed",
        }
        
        status = stage_to_status.get(stage, "Continue")
        
        result = self.xano_client.patch_session_status(xano_session_id, status)
        if result:
            logger.info(f"Updated Xano session {xano_session_id} to status: {status}")
        else:
            logger.warning(f"Failed to update Xano session {xano_session_id} status")
    
    def sync_session_state_to_xano(self):
        """
        Synchronize the current session state to Xano.
        This ensures Xano always has the most up-to-date status.
        Call this after any state changes to keep Xano in sync.
        """
        if not self.session_state.engagement or not self.session_state.engagement.xano_session_id:
            logger.warning("Cannot sync to Xano: No Xano session ID found")
            return False
        
        xano_session_id = self.session_state.engagement.xano_session_id
        current_stage = self.session_state.current_stage
        
        # Map conversation stages to Xano status values
        stage_to_status = {
            ConversationStage.ENGAGEMENT: "Started",
            ConversationStage.QUALIFICATION: "Continue",
            ConversationStage.APPLICATION: "Continue",
            ConversationStage.VERIFICATION: "Pending",
            ConversationStage.COMPLETED: "Completed",
        }
        
        status = stage_to_status.get(current_stage, "Continue")
        
        # Prepare update data with both status and stage information
        update_data = {
            "Status": status,
            "conversation_stage": current_stage.value,  # Store the actual stage name
        }
        
        # Add candidate_id if available
        if self.session_state.engagement.candidate_id:
            update_data["candidate_id"] = self.session_state.engagement.candidate_id
        
        result = self.xano_client.update_session(xano_session_id, update_data)
        if result:
            logger.info(f"Synced session state to Xano: session={xano_session_id}, status={status}, stage={current_stage.value}")
            return True
        else:
            logger.warning(f"Failed to sync session state to Xano for session {xano_session_id}")
            return False
    
    def get_xano_session_status(self) -> dict:
        """
        Get the current session status from Xano.
        Returns a dict with status, stage, and other session info.
        """
        if not self.session_state.engagement or not self.session_state.engagement.xano_session_id:
            return {
                "status": "Unknown",
                "conversation_stage": self.session_state.current_stage.value,
                "synced": False,
                "error": "No Xano session ID"
            }
        
        xano_session_id = self.session_state.engagement.xano_session_id
        xano_session = self.xano_client.get_session_by_id(xano_session_id)
        
        if xano_session:
            return {
                "xano_session_id": xano_session_id,
                "status": xano_session.get("Status", "Unknown"),
                "conversation_stage": xano_session.get("conversation_stage", self.session_state.current_stage.value),
                "candidate_id": xano_session.get("candidate_id"),
                "synced": True,
                "local_stage": self.session_state.current_stage.value,
            }
        else:
            return {
                "status": "Unknown",
                "conversation_stage": self.session_state.current_stage.value,
                "synced": False,
                "error": "Failed to fetch from Xano"
            }
    def process_message(self, user_message: str) -> List[str]:
        """
        Process user message and generate response(s) with retry logic
        Args:
            user_message: User's input message
        Returns:
            List of agent's response messages (can be single or multiple)
        """
        logger.info(f"Processing message: {user_message}")
        # Add LangFuse trace metadata
        trace_metadata = {
            "session_id": self.session_state.session_id,
            "current_stage": self.session_state.current_stage.value,
            "user_message": user_message,
        }
        return self._process_message_with_retry(user_message, trace_metadata)
    def _process_message_with_retry(self, user_message: str, trace_metadata: dict, max_retries: int = 3) -> List[str]:
        """
        Process message with retry logic and fallback
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Processing attempt {attempt + 1}/{max_retries} for message: {user_message[:50]}...")
                # Update state before processing to maintain context
                self._pre_process_state_update(user_message)
                # Add extra instruction to encourage multi-message responses and provide context
                enhanced_input = self._enhance_input_with_context(user_message)
                # Prepare callbacks with metadata - only if LangFuse is working
                callbacks = []
                if self.langfuse_enabled and self.langfuse_handler:
                    try:
                        # Use the existing handler for this conversation
                        callbacks.append(self.langfuse_handler)
                    except Exception as e:
                        logger.warning(f"Failed to add LangFuse handler: {e}")
                        # Continue without callbacks rather than failing
                # Invoke agent with callbacks
                response = self.agent.invoke(
                    {"input": enhanced_input},
                    config={"callbacks": callbacks} if callbacks else {},
                )
                logger.info("Agent invocation successful")
                logger.info(f"Agent enhance input: {enhanced_input}")
                
                agent_response = response.get(
                    "output", "I'm sorry, I didn't understand that."
                )
                # Validate response quality before returning
                if self._is_valid_response(agent_response):
                    # Split response into multiple messages if needed
                    messages = self._split_multi_messages(agent_response)
                    # Update conversation state based on response
                    self._update_state_from_conversation(user_message, agent_response)
                    logger.info(f"Successfully processed message on attempt {attempt + 1}")
                    return messages
                else:
                    logger.warning(f"Invalid response on attempt {attempt + 1}: {agent_response[:100]}...")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # Final attempt failed, use fallback
                        break
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                import traceback
                logger.error(f"Traceback on attempt {attempt + 1}: {traceback.format_exc()}")
                if attempt < max_retries - 1:
                    continue
                else:
                    # All attempts failed
                    break
        # All retries failed - return fallback message
        logger.error(f"All {max_retries} attempts failed for message processing")
        # Better error handling - don't show generic error for simple inputs
        if self._is_simple_acknowledgment(user_message):
            return ["Thank you for that information. An agent will connect with you soon to continue."]
        else:
            return [
                "I'm experiencing technical difficulties at the moment. "
                "An agent will connect with you soon to assist you further. "
                "Thank you for your patience."
            ]
    def _is_valid_response(self, response: str) -> bool:
        """
        Check if the response is valid and not malformed
        """
        if not response or not isinstance(response, str):
            return False
        response_lower = response.lower().strip()
        # Check if response is too short (likely malformed)
        if len(response_lower) < 5:
            return False
        # Check for specific malformed response patterns (exact matches)
        malformed_patterns = [
            "I'm having trouble processing that. Could you try rephrasing your response?",
            "I'm sorry, I didn't understand that.",
            "",  # Empty response
        ]
        # Check for exact malformed patterns
        for pattern in malformed_patterns:
            if pattern.lower() == response_lower:
                return False
        # If response is longer than 15 characters and doesn't match malformed patterns,
        # it's likely a valid response
        if len(response_lower) > 15:
            return True
        # For shorter responses, check if they contain conversational elements
        conversational_indicators = [
            "hello", "hi", "thank", "please", "can", "would", "let",
            "tell", "need", "help", "information", "question", "answer",
            "application", "job", "position", "experience", "qualification",
            "welcome", "great", "sure", "yes", "no", "okay", "name", "email"
        ]
        has_conversational_content = any(
            indicator in response_lower for indicator in conversational_indicators
        )
        return has_conversational_content
    def _is_simple_acknowledgment(self, user_message: str) -> bool:
        """Check if user message is a simple acknowledgment"""
        simple_responses = ["ok", "okay", "yes", "sure", "alright", "fine", "good"]
        return user_message.lower().strip() in simple_responses
    def _pre_process_state_update(self, user_message: str):
        """Update state before processing to maintain better context"""
        # This helps with immediate state updates for simple acknowledgments
        user_lower = user_message.lower().strip()
        # Handle simple consent acknowledgments
        if (
            self.session_state.current_stage == ConversationStage.ENGAGEMENT
            and user_lower in ["ok", "okay", "yes", "sure"]
            and self.session_state.engagement
            and not self.session_state.engagement.consent_given
        ):
            self.session_state.engagement.consent_given = True
            self.session_state.engagement.stage_completed = True
            self.session_state.current_stage = ConversationStage.QUALIFICATION
            self._update_xano_status(ConversationStage.QUALIFICATION)
            # Sync the full state to Xano for real-time alignment
            self.sync_session_state_to_xano()
            logger.info("Quick transition to QUALIFICATION based on consent")
    def _enhance_input_with_context(self, user_message: str) -> str:
        """
        Enhance user input with context about what information has already been collected
        Args:
            user_message: Original user message
        Returns:
            Enhanced input with context and multi-message encouragement
        """
        # Get current context summary
        context_summary = self._get_current_context_summary()
        # Detect patterns that should trigger multi-message responses
        user_lower = user_message.lower()
        # Patterns that typically warrant acknowledgment + follow-up
        acknowledgment_triggers = [
            "yes",
            "sure",
            "okay",
            "ok",
            "definitely",
            "absolutely",
            "i am",
            "i have",
            "i can",
            "i do",
            "my",
            "full-time",
            "part-time",
        ]
        question_triggers = ["hi", "hello", "hey", "good morning", "good afternoon"]
        should_encourage = any(
            trigger in user_lower
            for trigger in acknowledgment_triggers + question_triggers
        )
        enhanced_input = f"{user_message}\n\n{context_summary}"
        if should_encourage:
            enhanced_input += "\n\n[SYSTEM REMINDER: This is a perfect opportunity to use [NEXT_MESSAGE] to acknowledge their response and ask the next question. Break your response into natural conversation parts.]"
        return enhanced_input
    def _get_stage_specific_subprompt(self) -> str:
        """Get stage-specific subprompt with tool guidance and collection requirements"""
        stage = self.session_state.current_stage
        
        if stage == ConversationStage.ENGAGEMENT:
            return """[ENGAGEMENT STAGE INSTRUCTIONS]:
- PRIMARY GOAL: Build rapport and obtain consent to proceed
- REQUIRED INFORMATION: User consent to continue with application
- AVAILABLE TOOLS: fetch_job_details (use if job context needed)
- CONVERSATION STYLE: Warm, welcoming, conversational
- NEXT STEP: Once consent obtained, move to QUALIFICATION stage
"""
        
        elif stage == ConversationStage.QUALIFICATION:
            subprompt = """[QUALIFICATION STAGE INSTRUCTIONS]:
- PRIMARY GOAL: Collect essential qualification criteria
- REQUIRED INFORMATION TO COLLECT:
"""
            # Add dynamic checklist based on what's already collected
            qual = self.session_state.qualification
            if qual:
                
                if not qual.work_authorization:
                    subprompt += "  ☐ Work authorization\n"
                else:
                    subprompt += "  ✓ Work authorization\n"
                    
                if not qual.shift_preference:
                    subprompt += "  ☐ Shift preference (morning/afternoon/evening/overnight)\n"
                else:
                    subprompt += f"  ✓ Shift preference: {qual.shift_preference}\n"
                    
                if not qual.availability_start:
                    subprompt += "  ☐ Availability start date\n"
                else:
                    subprompt += "  ✓ Availability start date\n"
                    
                if not qual.transportation:
                    subprompt += "  ☐ Transportation confirmation\n"
                else:
                    subprompt += "  ✓ Transportation\n"
                    
                if not qual.age_confirmed:
                    subprompt += "  ☐ Age confirmation (18+)\n"
                else:
                    subprompt += "  ✓ Age confirmed\n"
                    
                if not qual.hours_preference:
                    subprompt += "  ☐ Hours preference (full-time/part-time)\n"
                else:
                    subprompt += f"  ✓ Hours preference: {qual.hours_preference}\n"
            else:
                
                subprompt += "  ☐ Work authorization\n"
                subprompt += "  ☐ Shift preference\n"
                subprompt += "  ☐ Availability start date\n"
                subprompt += "  ☐ Transportation\n"
                subprompt += "  ☐ Age confirmation (18+)\n"
                subprompt += "  ☐ Hours preference\n"
            
            subprompt += """
- CONVERSATION STYLE: Friendly but efficient, ask one question at a time
- IMPORTANT: Do NOT ask for name, email, or phone during QUALIFICATION. These will be collected in APPLICATION stage.
- NEXT STEP: Once all qualification info collected, move to APPLICATION stage
"""
            return subprompt
        
        elif stage == ConversationStage.APPLICATION:
            subprompt = """[APPLICATION STAGE INSTRUCTIONS]:
- PRIMARY GOAL: Collect applicant contact and experience information
- You Must ask candidate about their experience and education after collecting contact info.
- If candidate has no experience, ask about relevant skills.
- If candidate provides insufficient detail, politely probe for some more information.

- REQUIRED INFORMATION TO COLLECT:
"""
            # Add dynamic checklist
            app = self.session_state.application
            if app:
                subprompt += "\n Education: \n"
        
                if app.years_experience is None:
                    subprompt += "  ☐ Years of experience\n"
                else:
                    subprompt += f"  ✓ Years of experience: {app.years_experience}\n"

                if not app.full_name:
                    subprompt += "  ☐ Full name (USE save_name TOOL)\n"
                else:
                    subprompt += f"  ✓ Full name: {app.full_name}\n"
                    
                if not app.email:
                    subprompt += "  ☐ Email address (USE save_email TOOL)\n"
                else:
                    subprompt += f"  ✓ Email: {app.email}\n"
                    
                if not app.phone_number:
                    subprompt += "  ☐ Phone number (USE save_phone_number TOOL)\n"
                else:
                    subprompt += f"  ✓ Phone: {app.phone_number}\n"
                    
            else:
                subprompt += "  ☐ Years of experience\n"
                subprompt += "  ☐ Education\n"
                subprompt += "  ☐ Full name (USE save_name TOOL)\n"
                subprompt += "  ☐ Email address (USE save_email TOOL)\n"
                subprompt += "  ☐ Phone number (USE save_phone_number TOOL)\n"
                
            
            subprompt += """
            
            - REQUIRED TOOLS: 
  * save_name: MUST be called when user provides their name
  * save_email: MUST be called when user provides their email
  * save_phone_number: MUST be called when user provides their phone
- CONVERSATION STYLE: Professional yet friendly, acknowledge each piece of information
- NEXT STEP: After experience questions are completed, call send_email_verification_code tool to start verification process
"""
            return subprompt
        
        elif stage == ConversationStage.VERIFICATION:
            self.toolkit.send_email_verification_code(email=self.session_state.application.email)
            return """[VERIFICATION STAGE INSTRUCTIONS]:
- PRIMARY GOAL: Verify contact information and confirm submission
- REQUIRED ACTIONS:
  * Verify email address and phone number by sending confirmation code using tools
  * Prompt user to provide received code
  * Validate code using tool verify_code
  * IF USER SAYS THEY DIDN'T RECEIVE CODE: IMMEDIATELY call send_email_verification_code or send_phone_verification_code tool again (don't just apologize - actually resend by calling the tool)
  
- AVAILABLE TOOLS: send_email_verification_code, send_phone_verification_code, validate_phone_verification, validate_email_verification
- RESENDING CODES: If user says "didn't receive", "no code", "haven't gotten it", etc., call the send tool again immediately
- CONVERSATION STYLE: Clear, confirmatory, reassuring
- NEXT STEP: Once verified, move to COMPLETED stage
"""
        
        elif stage == ConversationStage.COMPLETED:
            return """[COMPLETED STAGE INSTRUCTIONS]:
- PRIMARY GOAL: Provide closure and next steps
- ACTIONS:
  * Thank the candidate for their application
  * Provide timeline for response
  * Offer to answer any final questions
- AVAILABLE TOOLS: patch_candidate_patch_candidate_with_report, conclude_session
- CONVERSATION STYLE: Warm, appreciative, encouraging
"""
        
        return ""
    
    def _get_current_context_summary(self) -> str:
        """Get a summary of what information has already been collected, filtered by current stage"""
        context = "[CONTEXT - INFORMATION ALREADY COLLECTED]:\n"
        
        current_stage = self.session_state.current_stage
        
        # ENGAGEMENT STAGE: Only show engagement info
        if current_stage == ConversationStage.ENGAGEMENT:
            if self.session_state.engagement:
                if self.session_state.engagement.consent_given:
                    context += "- User has given consent to proceed\n"
        
        # QUALIFICATION STAGE: Show engagement + qualification info
        elif current_stage == ConversationStage.QUALIFICATION:
            # Previous stage info (minimal)
            if self.session_state.engagement and self.session_state.engagement.consent_given:
                context += "- User has given consent to proceed\n"
            
            # Current stage info
            if self.session_state.qualification:
                qual = self.session_state.qualification
                if qual.age_confirmed:
                    context += "- Age confirmed (18+)\n"
                if qual.work_authorization:
                    context += "- Work authorization confirmed\n"
                if qual.shift_preference:
                    context += f"- Shift preference: {qual.shift_preference}\n"
                if qual.availability_start:
                    context += f"- Availability start: {qual.availability_start}\n"
                if qual.transportation:
                    context += "- Transportation confirmed\n"
                if qual.hours_preference:
                    context += f"- Hours preference: {qual.hours_preference}\n"
        
        # APPLICATION STAGE: Show only application info (and minimal previous context)
        elif current_stage == ConversationStage.APPLICATION:
            # Only include key qualifiers, not full details
            if self.session_state.engagement and self.session_state.engagement.consent_given:
                context += "- Qualified for application\n"
            
            # Current stage info (application)
            if self.session_state.application:
                app = self.session_state.application
                if app.full_name:
                    context += f"- Name: {app.full_name}\n"
                if app.email:
                    context += f"- Email: {app.email}\n"
                if app.phone_number:
                    context += f"- Phone: {app.phone_number}\n"
                if app.years_experience is not None:
                    context += f"- Experience: {app.years_experience} years\n"
        
        # VERIFICATION STAGE: Show application info only
        elif current_stage == ConversationStage.VERIFICATION:
            if self.session_state.application:
                app = self.session_state.application
                if app.full_name:
                    context += f"- Name: {app.full_name}\n"
                if app.email:
                    context += f"- Email: {app.email}\n"
                if app.phone_number:
                    context += f"- Phone: {app.phone_number}\n"
                if app.years_experience is not None:
                    context += f"- Experience: {app.years_experience} years\n"
        
        # COMPLETION STAGE: Show minimal context
        elif current_stage == ConversationStage.COMPLETED:
            if self.session_state.application and self.session_state.application.full_name:
                context += f"- Candidate: {self.session_state.application.full_name}\n"
        
        # Only add stage information if the stage has changed
        if self.session_state.current_stage != self.last_context_stage:
            context += f"\n[CURRENT STAGE]: {self.session_state.current_stage.value}\n"
            
            # Add stage-specific subprompt with tool guidance
            context += "\n" + self._get_stage_specific_subprompt()
            
            # Update the tracked stage
            self.last_context_stage = self.session_state.current_stage
        
        return context
    def _split_multi_messages(self, response: str) -> List[str]:
        """
        Split agent response into multiple messages if separator is present,
        or intelligently detect natural conversation breaks
        Args:
            response: Agent's response text
        Returns:
            List of message strings
        """
        # First, clean the response of any tool-related text or thinking
        response = self._filter_tool_artifacts(response)
        
        # Check if response contains the multi-message separator
        separator = "[NEXT_MESSAGE]"
        if separator in response:
            # Split by separator and clean up whitespace
            messages = [msg.strip() for msg in response.split(separator) if msg.strip()]
            # Filter each message for tool artifacts
            messages = [self._filter_tool_artifacts(msg) for msg in messages]
            logger.info(f"Split response into {len(messages)} messages using separator")
            return messages
        else:
            # Intelligent post-processing: detect natural conversation breaks
            messages = self._detect_natural_breaks(response)
            if len(messages) > 1:
                logger.info(
                    f"Intelligently split response into {len(messages)} messages"
                )
                return messages
            else:
                # Return single message as a list
                return [response]
    def _filter_tool_artifacts(self, response: str) -> str:
        """
        Remove any tool-related text, thinking, or system artifacts from the response
        Args:
            response: Agent's response text
        Returns:
            Cleaned response text
        """
        import re
        
        # Remove common tool-related artifacts
        patterns_to_remove = [
            r"\[RESULT AFTER TOOL CALL\]",
            r"\[RESULT[^\]]+\]",
            r"\[SILENT[^\]]+\]",
            r"\[CALLING [^\]]+\]",
            r"\[TOOL_[^\]]+\]",
            r"\[THINKING[^\]]*\]",
            r"\[INTERNAL[^\]]*\]",
            r"\[DEBUG[^\]]*\]",
            r"\[SILENT[^\]]*\]",
            r"I'm calling.*?tool",
            r"Let me call.*?tool",
            r"I'll use.*?tool",
            r"I will call.*?tool",
            r"Calling tool:.*?\n",
            r"Tool result:.*?\n",
        ]
        
        cleaned_response = response
        for pattern in patterns_to_remove:
            cleaned_response = re.sub(pattern, "", cleaned_response, flags=re.IGNORECASE)
        
        # Remove any bracketed system messages that might have leaked
        cleaned_response = re.sub(r"\[SYSTEM[^\]]*\].*?(?=\n|$)", "", cleaned_response, flags=re.IGNORECASE)
        
        # Clean up any multiple spaces or newlines created by removal
        cleaned_response = re.sub(r"\s+", " ", cleaned_response)
        cleaned_response = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned_response)
        
        return cleaned_response.strip()
    
    def _detect_natural_breaks(self, response: str) -> List[str]:
        """
        Intelligently detect natural conversation breaks in a response
        Args:
            response: Agent's response text
        Returns:
            List of message strings (may be just one if no breaks detected)
        """
        import re
        # Patterns that suggest natural conversation breaks
        break_patterns = [
            # Acknowledgment + Question pattern: "Great! Now, let me ask..."
            r"([^.!?]*[.!?])\s+(Now,?\s*let me ask|Now,?\s*tell me|Let\'s move on|Moving on|Next,?\s*I\'d like)",
            # Excitement + Follow-up: "That's fantastic! What about..."
            r"([^.!?]*[.!?])\s+(What about|How about|Tell me about|Could you|Would you|Do you)",
            # Confirmation + Next step: "Perfect! Here's what we'll do..."
            r"([^.!?]*[.!?])\s+(Here\'s what|Now here\'s|Let\'s start|Let\'s begin|First,?\s*I need)",
            # Transition phrases: "Awesome! So, ..."
            r"([^.!?]*[.!?])\s+(So,?\s*|Alright,?\s*|OK,?\s*|Okay,?\s*|Well,?\s*)",
        ]
        # Check for acknowledgment + question patterns
        for pattern in break_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                first_part = match.group(1).strip()
                rest = response[match.end(1) :].strip()
                if (
                    first_part and rest and len(first_part) < 150
                ):  # Don't split very long first parts
                    return [first_part, rest]
        # Check for multiple sentences that could be naturally split
        sentences = re.split(r"(?<=[.!?])\s+", response.strip())
        if len(sentences) >= 3:  # Only split if we have enough content
            # Look for a good split point (around 1/3 to 1/2 way through)
            total_chars = len(response)
            current_chars = 0
            for i, sentence in enumerate(
                sentences[:-1]
            ):  # Don't split at the last sentence
                current_chars += len(sentence)
                # If we're in the sweet spot (30-70% through) and have a good acknowledgment
                if 0.3 <= current_chars / total_chars <= 0.7:
                    # Check if this sentence ends with acknowledgment words
                    ack_words = [
                        "great",
                        "perfect",
                        "excellent",
                        "fantastic",
                        "wonderful",
                        "awesome",
                        "good",
                    ]
                    if any(word in sentence.lower() for word in ack_words):
                        first_part = " ".join(sentences[: i + 1]).strip()
                        second_part = " ".join(sentences[i + 1 :]).strip()
                        if first_part and second_part:
                            return [first_part, second_part]
        # No natural breaks found
        return [response]
    def _update_state_from_conversation(self, user_message: str, agent_response: str):
        """
        Update session state based on conversation context
        Enhanced with better state tracking and automatic fit score calculation
        """
        user_lower = user_message.lower()
        agent_lower = agent_response.lower()
        state_changed = False
        # Extract information from user message regardless of stage (proactive extraction)
        self._extract_information_proactively(user_message)
        # Engagement stage updates
        if self.session_state.current_stage == ConversationStage.ENGAGEMENT:
            if not self.session_state.engagement:
                self.session_state.engagement = EngagementState(
                    session_id=self.session_state.session_id
                )
            # Check for consent keywords
            if any(
                word in user_lower
                for word in [
                    "yes",
                    "sure",
                    "okay",
                    "ok",
                    "proceed",
                    "continue",
                    "agree",
                ]
            ):
                if not self.session_state.engagement.consent_given:
                    self.session_state.engagement.consent_given = True
                    self.session_state.engagement.stage_completed = True
                    self.session_state.current_stage = ConversationStage.QUALIFICATION
                    self._update_xano_status(ConversationStage.QUALIFICATION)
                    state_changed = True
                    logger.info("Moving to QUALIFICATION stage")
        # Qualification stage updates
        elif self.session_state.current_stage == ConversationStage.QUALIFICATION:
            if not self.session_state.qualification:
                self.session_state.qualification = QualificationState(
                    session_id=self.session_state.session_id
                )
            qual = self.session_state.qualification
            # Age confirmation
            if any(
                phrase in user_lower
                for phrase in [
                    "yes",
                    "i am 18",
                    "i'm 18",
                    "18 or older",
                    "over 18",
                    "above 18",
                ]
            ):
                if not qual.age_confirmed and (
                    "age" in agent_lower or "18" in agent_lower
                ):
                    qual.age_confirmed = True
                    state_changed = True
                    logger.info("Age confirmed")
            # Work authorization
            if any(
                phrase in user_lower
                for phrase in [
                    "authorized",
                    "citizen",
                    "yes",
                    "legally authorized",
                    "work permit",
                ]
            ):
                if not qual.work_authorization and (
                    "work" in agent_lower
                    and ("authorized" in agent_lower or "authorization" in agent_lower)
                ):
                    qual.work_authorization = True
                    state_changed = True
                    logger.info("Work authorization confirmed")
            # Shift preference detection
            shift_keywords = [
                "morning",
                "day",
                "afternoon",
                "evening",
                "night",
                "overnight",
            ]
            for shift in shift_keywords:
                if shift in user_lower and not qual.shift_preference:
                    qual.shift_preference = shift
                    state_changed = True
                    logger.info(f"Shift preference set to: {shift}")
                    break
            # Availability start date
            import re
            date_patterns = [
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # MM/DD/YYYY or MM-DD-YYYY
                r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",  # YYYY/MM/DD or YYYY-MM-DD
                r"\basap\b",
                r"\bimmediately\b",
                r"\bright away\b",
                r"\btomorrow\b",
            ]
            if not qual.availability_start:
                for pattern in date_patterns:
                    if re.search(pattern, user_lower):
                        qual.availability_start = (
                            user_message  # Store the full response for now
                        )
                        state_changed = True
                        logger.info("Availability start date captured")
                        break
            # Transportation
            if any(
                phrase in user_lower
                for phrase in [
                    "yes",
                    "have transportation",
                    "can get there",
                    "own car",
                    "reliable transportation",
                ]
            ):
                if not qual.transportation and "transportation" in agent_lower:
                    qual.transportation = True
                    state_changed = True
                    logger.info("Transportation confirmed")
            # Hours preference
            hours_keywords = ["full-time", "full time", "part-time", "part time"]
            for hours in hours_keywords:
                if hours in user_lower and not qual.hours_preference:
                    qual.hours_preference = hours.replace("-", "-")  # Normalize
                    state_changed = True
                    logger.info(f"Hours preference set to: {hours}")
                    break
            # Check if qualification is complete and transition to application
            if self._is_qualification_complete(qual):
                if not qual.stage_completed:
                    qual.qualification_status = "qualified"
                    qual.stage_completed = True
                    self.session_state.current_stage = ConversationStage.APPLICATION
                    self._update_xano_status(ConversationStage.APPLICATION)
                    state_changed = True
                    logger.info("Qualification completed - Moving to APPLICATION stage")
        # Application stage updates
        # elif self.session_state.current_stage == ConversationStage.APPLICATION:
        #     if not self.session_state.application:
        #         self.session_state.application = ApplicationState(
        #             session_id=self.session_state.session_id
        #         )
        #     app = self.session_state.application
            # Extract application information using simple patterns
            # if self._extract_application_info(user_message, app):
            #     state_changed = True
            # Check if application is complete and transition appropriately
            # if self._is_application_complete(app):
            #     if not app.stage_completed:
            #         app.application_status = "submitted"
            #         app.stage_completed = True
            #         # Create candidate immediately upon application completion
            #         self._create_candidate_immediately()
            #         # Transition to verification stage only if candidate has experience
            #         if app.years_experience > 0:
            #             self.session_state.current_stage = ConversationStage.VERIFICATION
            #             self._update_xano_status(ConversationStage.VERIFICATION)
            #             state_changed = True
            #             logger.info(
            #                 "Application completed with experience - Moving to VERIFICATION stage for contact verification"
            #             )
            #         else:
            #             logger.info(
            #                 "Application completed with no experience - Staying in APPLICATION stage to continue asking questions"
            #             )
        # Verification stage updates
        elif self.session_state.current_stage == ConversationStage.VERIFICATION:
            if not self.session_state.verification:
                self.session_state.verification = VerificationState(
                    session_id=self.session_state.session_id
                )
            # Handle verification completion
            # This would be triggered by actual verification processes
        # Log state changes and sync to Xano
        if state_changed:
            logger.info(
                f"State updated for session {self.session_state.session_id}"
            )
            # Sync the updated state to Xano to keep it in real-time alignment
            self.sync_session_state_to_xano()
    def _is_qualification_complete(self, qual: QualificationState) -> bool:
        """Check if qualification stage is complete"""
        return all(
            [
                qual.age_confirmed,
                qual.work_authorization,
                qual.shift_preference,
                qual.availability_start,
                qual.transportation,
                qual.hours_preference,
            ]
        )
    def _extract_application_info(self, user_message: str, app: ApplicationState) -> bool:
        """Extract application information from user message
        Returns:
            bool: True if any information was extracted and state changed
        """
        import re
        state_changed = False
        
        # Note: Email, phone, and name are now collected via agent tools (save_email, save_phone_number, save_name)
        # The agent will call these tools when the user provides this information
        
        # Experience patterns (more flexible)
        exp_patterns = [
            r"(\d+(?:\.\d+)?)\s*years?",  # e.g. 5 years, 2.5 years
            r"worked\s*(?:for\s*)?(\d+(?:\.\d+)?)\s*years?",
            r"experience\s*(?:of|:)\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*yrs?",
        ]
        if app.years_experience is None:
            for pattern in exp_patterns:
                exp_match = re.search(pattern, user_message.lower())
                if exp_match:
                    app.years_experience = float(exp_match.group(1))
                    logger.info(f"Years of experience captured: {app.years_experience}")
                    state_changed = True
                    break
            
            # Check for "no experience" patterns
            if not state_changed:
                no_exp_patterns = [
                    r"no\s+experience",
                    r"no\s+work\s+experience",
                    r"zero\s+experience",
                    r"none",
                    r"no\s+prior\s+experience",
                    r"fresh\s+graduate",
                    r"new\s+graduate",
                    r"entry\s+level",
                    r"first\s+job",
                    r"never\s+worked",
                ]
                if any(re.search(pattern, user_message.lower()) for pattern in no_exp_patterns):
                    app.years_experience = 0.0
                    logger.info("No experience detected, setting years_experience to 0")
                    state_changed = True
        return state_changed
    def _is_application_complete(self, app: ApplicationState) -> bool:
        """Check if application stage is complete"""
        return all(
            [
                app.full_name,
                app.phone_number,
                app.email,
                app.years_experience is not None,
            ]
        )
    def _extract_information_proactively(self, user_message: str) -> bool:
        """
        Proactively extract information from user message regardless of current stage
        This helps capture information provided voluntarily by users
        Returns:
            bool: True if any information was extracted and state was saved
        """
        import re
        state_changed = False
        # Initialize states if needed
        if not self.session_state.qualification:
            self.session_state.qualification = QualificationState(
                session_id=self.session_state.session_id
            )
        if not self.session_state.application:
            self.session_state.application = ApplicationState(
                session_id=self.session_state.session_id
            )
        user_lower = user_message.lower()
        # Extract qualification information
        qual = self.session_state.qualification
        # Age confirmation patterns
        age_patterns = [
            "18",
            "nineteen",
            "twenty",
            "over 18",
            "older than 18",
            "above 18",
        ]
        if not qual.age_confirmed and any(
            pattern in user_lower for pattern in age_patterns
        ):
            qual.age_confirmed = True
            state_changed = True
            logger.info("Proactively captured age confirmation")
        # Work authorization patterns
        work_auth_patterns = [
            "authorized to work",
            "citizen",
            "work permit",
            "legally work",
            "work visa",
        ]
        if not qual.work_authorization and any(
            pattern in user_lower for pattern in work_auth_patterns
        ):
            qual.work_authorization = True
            state_changed = True
            logger.info("Proactively captured work authorization")
        # Shift preferences
        shift_keywords = {
            "morning": ["morning", "am", "early", "day shift"],
            "afternoon": ["afternoon", "day", "daytime"],
            "evening": ["evening", "night", "pm"],
            "overnight": ["overnight", "late night", "midnight", "graveyard"],
        }
        if not qual.shift_preference:
            for shift, keywords in shift_keywords.items():
                if any(keyword in user_lower for keyword in keywords):
                    qual.shift_preference = shift
                    state_changed = True
                    logger.info(f"Proactively captured shift preference: {shift}")
                    break
        # Hours preference
        if not qual.hours_preference:
            if any(
                phrase in user_lower
                for phrase in ["full-time", "full time", "fulltime"]
            ):
                qual.hours_preference = "full-time"
                state_changed = True
                logger.info("Proactively captured hours preference: full-time")
            elif any(
                phrase in user_lower
                for phrase in ["part-time", "part time", "parttime"]
            ):
                qual.hours_preference = "part-time"
                state_changed = True
                logger.info("Proactively captured hours preference: part-time")
        # Transportation
        if not qual.transportation and any(
            phrase in user_lower
            for phrase in [
                "have transportation",
                "own car",
                "reliable transport",
                "can get there",
            ]
        ):
            qual.transportation = True
            state_changed = True
            logger.info("Proactively captured transportation")
        # Extract application information
        app = self.session_state.application
        
        # Note: Email, phone, and name are now collected via agent tools (save_email, save_phone_number, save_name)
        # The agent will call these tools when the user provides this information
        
        # Experience patterns (more flexible)
        exp_patterns = [
            r"(\d+(?:\.\d+)?)\s*years?",  # e.g. 5 years, 2.5 years
            r"worked\s*(?:for\s*)?(\d+(?:\.\d+)?)\s*years?",
            r"experience\s*(?:of|:)\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*yrs?",
        ]
        if app.years_experience is None:
            for pattern in exp_patterns:
                exp_match = re.search(pattern, user_message.lower())
                if exp_match:
                    app.years_experience = float(exp_match.group(1))
                    logger.info(f"Years of experience captured: {app.years_experience}")
                    state_changed = True
                    break
            
            # Check for "no experience" patterns
            if not state_changed:
                no_exp_patterns = [
                    r"no\s+experience",
                    r"no\s+work\s+experience",
                    r"zero\s+experience",
                    r"none",
                    r"no\s+prior\s+experience",
                    r"fresh\s+graduate",
                    r"new\s+graduate",
                    r"entry\s+level",
                    r"first\s+job",
                    r"never\s+worked",
                ]
                if any(re.search(pattern, user_message.lower()) for pattern in no_exp_patterns):
                    app.years_experience = 0.0
                    logger.info("No experience detected, setting years_experience to 0")
                    state_changed = True
        # Log state changes
        if state_changed:
            logger.info("Proactive information extraction completed")
        return state_changed
    
    # Removed _calculate_and_save_fit_score - fit score is now calculated during report generation

    def _create_candidate_immediately(self):
        """
        Create the candidate record immediately when application is complete.
        This is triggered automatically, not by user saying goodbye.
        """
        try:
            logger.info("Creating candidate immediately upon application completion...")
            
            # Ensure candidate is created using the toolkit's method
            candidate_id = self.toolkit._ensure_candidate_created()
            
            if candidate_id:
                logger.info(f"Candidate created successfully: {candidate_id}")
                return candidate_id
            else:
                logger.warning("Failed to create candidate during application completion")
                return None
                
        except Exception as e:
            logger.error(f"Error creating candidate immediately: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation state"""
        app_complete = (
            self.session_state.application.stage_completed
            if self.session_state.application
            else False
        )
        return {
            "session_id": self.session_state.session_id,
            "current_stage": self.session_state.current_stage.value,
            "engagement_complete": (
                self.session_state.engagement.stage_completed
                if self.session_state.engagement
                else False
            ),
            "qualification_complete": (
                self.session_state.qualification.stage_completed
                if self.session_state.qualification
                else False
            ),
            "application_complete": app_complete,
            "ready_for_verification": app_complete,
        }
    def reset_conversation(self):
        """Reset the conversation memory and agent"""
        self.memory.clear()
        self.agent = self._create_agent()
        logger.info("Conversation reset")
def main():
    """Example usage of Cleo RAG Agent"""
    from chatbot.utils.config import ensure_directories
    ensure_directories()
    # Create agent
    agent = CleoRAGAgent()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        _responses = agent.process_message(user_input)

if __name__ == "__main__":
    main()

