"""
Agentic RAG System
LangChain-based agent that reasons, uses tools, and queries knowledge base
"""

from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

# LangFuse imports
try:
    from langfuse.langchain import CallbackHandler as LangFuseCallbackHandler

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

from chatbot.core.retrievers import KnowledgeBaseRetriever, RetrievalMethod
from chatbot.prompts.prompts import CleoPrompts
from chatbot.state.states import (
    ApplicationState,
    ConversationStage,
    EngagementState,
    QualificationState,
    SessionState,
    StateManager,
    VerificationState,
)
from chatbot.utils.config import settings
from chatbot.utils.job_fetcher import format_job_details
from chatbot.utils.utils import setup_logging

logger = setup_logging()


class CleoRAGAgent:
    """Agentic RAG system for conversational job application"""

    def __init__(
        self,
        session_state: SessionState = None,
        retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID,
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
            logger.warning(
                f"Could not initialize retriever: {e}. Agent will work without KB."
            )
            self.retriever = None

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
                test_trace = test_client.trace(name="agent_init_test")
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
                Query the company's knowledge base for relevant information.

                IMPORTANT: This knowledge base contains COMPANY DOCUMENTS from the hiring company, including:
                - Company policies and procedures
                - Job descriptions and detailed requirements
                - Benefits, compensation, and HR policies
                - Company culture, values, and work environment details
                - Training materials and onboarding procedures
                - Any other company-specific information

                Use this tool whenever users have questions or ambiguities about:
                - Job requirements, responsibilities, or expectations
                - Company policies, procedures, or culture
                - Benefits, salary, compensation, or work conditions
                - Training, development, or career opportunities
                - Any company-specific processes or information
                """
                try:
                    results = self.retriever.retrieve(
                        query=query, method=self.retrieval_method, top_k=3
                    )
                    context = self.retriever.format_context(results)
                    return context
                except Exception as e:
                    logger.error(f"Error querying knowledge base: {e}")
                    return "Unable to retrieve information from knowledge base."

            tools.append(
                Tool(
                    name="query_knowledge_base",
                    func=query_knowledge_base,
                    description="Query the company's knowledge base containing company documents for information about jobs, requirements, benefits, policies, culture, and any company-specific details. Use this when users need clarification about company-related topics.",
                )
            )

        # Save State Tool
        def save_current_state(state_info: str) -> str:
            """Save the current conversation state"""
            try:
                self.state_manager.save_session(self.session_state)
                return f"State saved successfully for session {self.session_state.session_id}"
            except Exception as e:
                logger.error(f"Error saving state: {e}")
                return f"Error saving state: {str(e)}"

        tools.append(
            Tool(
                name="save_state",
                func=save_current_state,
                description="Save the current conversation state to persistent storage",
            )
        )

        return tools

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
            verbose=True,
            max_iterations=5,
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

        # Use CleoPrompts to get the complete system prompt
        return CleoPrompts.get_system_prompt(
            session_id=self.session_state.session_id,
            current_stage=self.session_state.current_stage,
            language=language,
            job_context=job_context,
        )

    def _refresh_agent_with_job_context(self):
        """Refresh the agent with updated job context"""
        self.agent = self._create_agent()
        logger.info("Agent refreshed with job context")

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
            self.state_manager.save_session(self.session_state)
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

    def _get_current_context_summary(self) -> str:
        """Get a summary of what information has already been collected"""
        context = "[CONTEXT - INFORMATION ALREADY COLLECTED]:\n"

        # Engagement info
        if self.session_state.engagement:
            if self.session_state.engagement.consent_given:
                context += "- User has given consent to proceed\n"

        # Qualification info
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

        # Application info
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

        context += f"\n[CURRENT STAGE]: {self.session_state.current_stage.value}\n"
        context += "[INSTRUCTION]: DO NOT ask for information that has already been collected. Move to the next needed information or proceed to the next stage if current stage is complete.\n"

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
        # Check if response contains the multi-message separator
        separator = "[NEXT_MESSAGE]"

        if separator in response:
            # Split by separator and clean up whitespace
            messages = [msg.strip() for msg in response.split(separator) if msg.strip()]
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
                    state_changed = True
                    logger.info("Qualification completed - Moving to APPLICATION stage")

        # Application stage updates
        elif self.session_state.current_stage == ConversationStage.APPLICATION:
            if not self.session_state.application:
                self.session_state.application = ApplicationState(
                    session_id=self.session_state.session_id
                )

            app = self.session_state.application

            # Extract application information using simple patterns
            self._extract_application_info(user_message, app)

            # Check if application is complete and trigger fit score calculation
            if self._is_application_complete(app):
                if not app.stage_completed:
                    app.application_status = "submitted"
                    app.stage_completed = True

                    # Calculate fit score and transition to verification
                    self._calculate_and_save_fit_score()

                    self.session_state.current_stage = ConversationStage.VERIFICATION
                    state_changed = True
                    logger.info(
                        "Application completed - Fit score calculated - Moving to VERIFICATION stage"
                    )

        # Verification stage updates
        elif self.session_state.current_stage == ConversationStage.VERIFICATION:
            if not self.session_state.verification:
                self.session_state.verification = VerificationState(
                    session_id=self.session_state.session_id
                )

            # Handle verification completion
            # This would be triggered by actual verification processes

        # Save state if changes were made
        if state_changed:
            self.state_manager.save_session(self.session_state)
            logger.info(
                f"State updated and saved for session {self.session_state.session_id}"
            )

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

    def _extract_application_info(self, user_message: str, app: ApplicationState):
        """Extract application information from user message"""
        import re

        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if not app.email:
            email_match = re.search(email_pattern, user_message)
            if email_match:
                app.email = email_match.group()
                logger.info("Email captured")

        # Phone pattern
        phone_pattern = (
            r"(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})"
        )
        if not app.phone_number:
            phone_match = re.search(phone_pattern, user_message)
            if phone_match:
                app.phone_number = phone_match.group()
                logger.info("Phone number captured")

        # Name pattern (simple approach - look for "My name is" or similar)
        name_patterns = [
            r"my name is ([A-Za-z\s]{2,})",
            r"i'm ([A-Za-z\s]{2,})",
            r"i am ([A-Za-z\s]{2,})",
        ]
        if not app.full_name:
            for pattern in name_patterns:
                name_match = re.search(pattern, user_message.lower())
                if name_match:
                    app.full_name = name_match.group(1).strip().title()
                    logger.info(f"Name captured: {app.full_name}")
                    break

        # Years of experience
        exp_pattern = r"(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:experience|exp)"
        if not app.years_experience:
            exp_match = re.search(exp_pattern, user_message.lower())
            if exp_match:
                app.years_experience = float(exp_match.group(1))
                logger.info(f"Years of experience captured: {app.years_experience}")

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

    def _extract_information_proactively(self, user_message: str):
        """
        Proactively extract information from user message regardless of current stage
        This helps capture information provided voluntarily by users
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

        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if not app.email:
            email_match = re.search(email_pattern, user_message)
            if email_match:
                app.email = email_match.group()
                state_changed = True
                logger.info("Proactively captured email")

        # Phone pattern
        phone_pattern = (
            r"(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})"
        )
        if not app.phone_number:
            phone_match = re.search(phone_pattern, user_message)
            if phone_match:
                app.phone_number = phone_match.group()
                state_changed = True
                logger.info("Proactively captured phone number")

        # Name pattern
        name_patterns = [
            r"my name is ([A-Za-z\s]+)",
            r"i'm ([A-Za-z\s]+)",
            r"i am ([A-Za-z\s]+)",
            r"call me ([A-Za-z\s]+)",
        ]
        if not app.full_name:
            for pattern in name_patterns:
                name_match = re.search(pattern, user_lower)
                if name_match:
                    name = name_match.group(1).strip().title()
                    # Avoid capturing common words as names
                    false_positives = [
                        "interested",
                        "looking",
                        "good",
                        "ready",
                        "over",
                        "older",
                        "above",
                        "under",
                        "authorized",
                        "eighteen",
                    ]
                    if (
                        len(name) > 1
                        and not any(word in name.lower() for word in false_positives)
                        and len(name.split()) >= 2
                    ):  # Require at least first and last name
                        app.full_name = name
                        state_changed = True
                        logger.info(f"Proactively captured name: {name}")
                        break

        # Years of experience
        exp_patterns = [
            r"(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:experience|exp)",
            r"(\d+)\s*(?:year|yr)s?\s*experience",
            r"worked?\s*(?:for\s*)?(\d+)\s*years?",
        ]
        if app.years_experience is None:
            for pattern in exp_patterns:
                exp_match = re.search(pattern, user_lower)
                if exp_match:
                    years = float(exp_match.group(1))
                    if 0 <= years <= 50:  # Reasonable range
                        app.years_experience = years
                        state_changed = True
                        logger.info(f"Proactively captured experience: {years} years")
                        break

        # Save state if any changes were made
        if state_changed:
            self.state_manager.save_session(self.session_state)
            logger.info("Proactive information extraction completed - state saved")

    def _calculate_and_save_fit_score(self):
        """Calculate fit score when application is complete"""
        try:
            from chatbot.utils.fit_score import FitScoreCalculator
            from chatbot.utils.report_generator import ReportGenerator

            calculator = FitScoreCalculator()

            # Calculate fit score
            fit_score = calculator.calculate_fit_score(
                qualification=self.session_state.qualification,
                application=self.session_state.application,
                verification=self.session_state.verification,
            )

            logger.info(f"Fit score calculated: {fit_score.total_score:.2f}/100")

            # Generate report
            report_gen = ReportGenerator()
            reports = report_gen.generate_report(
                session_id=self.session_state.session_id, include_fit_score=True
            )

            logger.info(f"Reports generated: {reports}")

            # The fit score and reports are now available and will be posted to web interface
            # via the existing API endpoints

        except Exception as e:
            logger.error(f"Error calculating fit score: {e}")
            # Don't let fit score calculation failure prevent state progression

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation state"""
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
            "application_complete": (
                self.session_state.application.stage_completed
                if self.session_state.application
                else False
            ),
            "verification_complete": (
                self.session_state.verification.stage_completed
                if self.session_state.verification
                else False
            ),
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

    print("=== Cleo RAG Agent Demo ===")
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nThank you for using Cleo!")
            break

        responses = agent.process_message(user_input)

        # Handle multiple messages
        for i, response in enumerate(responses):
            if i > 0:
                print()  # Add newline between multiple messages
            print(f"Cleo: {response}")
        print()  # Add newline after all messages

        # Show stage info
        summary = agent.get_conversation_summary()
        print(f"[Stage: {summary['current_stage']}]\n")


if __name__ == "__main__":
    main()
