"""
Agent Tools Module
Contains tool factory for creating tools bound to an agent instance.
Uses LangChain's StructuredTool with closure to avoid global state.
"""
import os
import re
import uuid
import requests
from typing import TYPE_CHECKING, List, Optional
from langchain.tools import StructuredTool

from chatbot.utils.utils import setup_logging
from chatbot.utils.config import settings
from langchain_openai import ChatOpenAI
from chatbot.utils.xano_client import get_xano_client
from chatbot.utils.fit_score import FitScoreCalculator, FitScoreComponents
from chatbot.utils.report_generator import ReportGenerator

if TYPE_CHECKING:
    from chatbot.state.states import SessionState
    # Import agent type only for typing to avoid circular import at runtime
    from chatbot.core.agent import CleoRAGAgent

logger = setup_logging()


class AgentToolkit:
    """
    Toolkit that creates tools bound to a specific agent's session state.
    This avoids using global variables by encapsulating state within the toolkit instance.
    """
    
    def __init__(self, session_state: "SessionState", job_id: Optional[str] = None, agent: Optional["CleoRAGAgent"] = None):
        """
        Initialize the toolkit with agent's session state and job_id.
        
        Args:
            session_state: The agent's SessionState object
            job_id: The job ID for the position being applied to
        """
        self.session_state = session_state
        self.job_id = job_id
        # Optional reference to the running agent (used to access its memory & trigger prompts)
        self.agent = agent
        self.xano_client = get_xano_client()
        self._session_concluded = False  # Track if session has been concluded
        self._candidate_created = False  # Track if candidate has been created
        self._fit_score_calculator = FitScoreCalculator()
        self._report_generator = ReportGenerator(xano_client=self.xano_client)
        logger.info(f"AgentToolkit initialized for session {session_state.session_id}, job_id: {job_id}")
        # Ensure Application state exists so candidate contact details can be stored reliably
        try:
            from chatbot.state.states import ApplicationState
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
        except Exception:
            # If import fails for any reason, don't block toolkit initialization
            logger.debug("Could not auto-initialize ApplicationState in toolkit init")
    
    def _is_valid_uuid(self, value: str) -> bool:
        """
        Check if a string is a valid UUID.
        
        Args:
            value: String to validate
            
        Returns:
            True if valid UUID, False otherwise
        """
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, AttributeError):
            return False
    
    def save_state(self, milestone: str) -> str:
        """
        Save the current conversation state to persistent storage.
        
        Args:
            milestone: Description of the milestone being saved
        """
        logger.info(f"State milestone saved: {milestone} for session {self.session_state.session_id}")
        return f"State tracked in memory for session {self.session_state.session_id}: {milestone}"
    
    def _calculate_fit_score(self) -> FitScoreComponents:
        """
        Calculate the fit score for the current candidate based on session state.
        
        Returns:
            FitScoreComponents with all score details
        """
        try:
            # Get qualification and application states
            qualification = self.session_state.qualification
            application = self.session_state.application
            
            # Calculate fit score using the shared calculator
            fit_score_result = self._fit_score_calculator.calculate_fit_score(
                qualification=qualification,
                application=application,
                chat_history=None  # Chat history would require access to conversation
            )
            
            logger.info(f"Calculated fit score: {fit_score_result.total_score:.2f}")
            return fit_score_result
        except Exception as e:
            logger.error(f"Error calculating fit score: {e}")
            # Return default score components on error
            return FitScoreComponents(
                qualification_score=0.0,
                experience_score=0.0,
                personality_score=0.0,
                total_score=0.0,
                breakdown={}
            )
    
    def _generate_pdf_report(self, fit_score: FitScoreComponents) -> Optional[str]:
        """
        Generate PDF summary report for the session.
        
        Args:
            fit_score: Pre-calculated fit score components
            
        Returns:
            Path to generated PDF file, or None on error
        """
        try:
            session_id = self.session_state.session_id
            
            # Build application data from session state for report generator
            app_data = {
                'engagement': {},
                'qualification': {},
                'application': {},
                'verification': {},
                'fit_score': {
                    'total_score': fit_score.total_score,
                    'qualification_score': fit_score.qualification_score,
                    'experience_score': fit_score.experience_score,
                    'personality_score': fit_score.personality_score,
                    'breakdown': fit_score.breakdown
                }
            }
            
            # Populate from session state if available
            if self.session_state.engagement:
                app_data['engagement'] = self.session_state.engagement.model_dump()
            if self.session_state.qualification:
                app_data['qualification'] = self.session_state.qualification.model_dump()
            if self.session_state.application:
                app_data['application'] = self.session_state.application.model_dump()
            if self.session_state.verification:
                app_data['verification'] = self.session_state.verification.model_dump()
            
            # Generate report
            result = self._report_generator.generate_report(
                session_id=session_id,
                include_fit_score=True,
                app_data=app_data
            )
            
            pdf_path = result.get('pdf_report')
            logger.info(f"Generated PDF report for session {session_id}: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return None
    
    def _create_candidate_on_conclude(self, fit_score: FitScoreComponents, pdf_path: Optional[str]) -> Optional[int]:
        """
        Create candidate record when session concludes.
        This is called only once when the session ends.
        
        Args:
            fit_score: Pre-calculated fit score components
            pdf_path: Path to generated PDF report
            
        Returns:
            Candidate ID if created, None otherwise
        """
        try:
            # Check if candidate already exists
            if self._candidate_created:
                logger.info("Candidate already created for this session")
                if self.session_state.engagement and self.session_state.engagement.candidate_id:
                    return self.session_state.engagement.candidate_id
                return None
            
            # Get candidate name from application state
            name = None
            email = None
            phone = None
            
            if self.session_state.application:
                name = self.session_state.application.full_name
                email = self.session_state.application.email
                phone = self.session_state.application.phone_number

            # Validate and sanitize email
            email_clean = None
            if email:
                # Validate email format using regex
                email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
                if re.match(email_pattern, email.strip()):
                    email_clean = email.strip().lower()
                else:
                    logger.warning(f"Invalid email format: {email}. Skipping email field.")

            # Sanitize phone: only include digits. If digits-only, pass as integer; otherwise skip.
            phone_clean = None
            if phone:
                try:
                    # Extract digits only (strip +, -, spaces, parentheses, etc.)
                    digits = ''.join(filter(str.isdigit, str(phone)))
                    if digits:
                        # Convert to int for Xano's integer field
                        phone_clean = int(digits)
                except Exception:
                    phone_clean = None
            
            # Verify required candidate contact information is present
            if not name:
                logger.warning("Cannot create candidate: no name available")
                return None
            if not email:
                logger.warning("Cannot create candidate: no email available")
                return None
            if not phone:
                logger.warning("Cannot create candidate: no phone available")
                return None
            
            # Get job_id and company_id
            job_id = self.job_id
            company_id = None
            xano_session_id = None
            
            if self.session_state.engagement:
                if not job_id:
                    job_id = self.session_state.engagement.job_id
                company_id = self.session_state.engagement.company_id
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # Validate job_id is a UUID, if not try to fetch from Xano
            if job_id:
                if not self._is_valid_uuid(job_id):
                    logger.warning(f"job_id '{job_id}' is not a valid UUID. Attempting to fetch job from Xano...")
                    job_data = self.xano_client.get_job_by_id(job_id)
                    if job_data and 'id' in job_data:
                        job_id = str(job_data['id'])
                        logger.info(f"Retrieved UUID job_id from Xano: {job_id}")
                    else:
                        logger.error(f"Failed to retrieve job with ID '{job_id}' from Xano. Cannot create candidate without valid UUID.")
                        return None
            else:
                logger.warning("No job_id available for candidate creation")
            
            logger.info(f"Creating candidate {name} with score {fit_score.total_score:.2f}")
            
            # Create candidate in Xano with fit score and PDF
            candidate = self.xano_client.create_candidate(
                name=name or "unable to fetch",
                email=email_clean,
                phone=phone_clean,
                score=fit_score.total_score,
                file_path=pdf_path,
                job_id=job_id,
                company_id=company_id,
                session_id=xano_session_id,
                status="Short Listed"
            )
            
            if candidate:
                candidate_id = candidate.get('id')
                self._candidate_created = True
                
                # Store candidate_id in engagement state
                if self.session_state.engagement:
                    self.session_state.engagement.candidate_id = candidate_id
                    # Update session with candidate_id in Xano
                    if xano_session_id:
                        self.xano_client.update_session(xano_session_id, {"candidate_id": candidate_id})
                
                logger.info(f"Created candidate {candidate_id} for session {self.session_state.session_id} with score {fit_score.total_score:.2f}")
                
                # Delete the local PDF report after successful candidate creation
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        logger.info(f"Deleted local PDF report: {pdf_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete local PDF report {pdf_path}: {e}")
                
                return candidate_id
            else:
                logger.warning("Failed to create candidate in Xano")
                return None
        except Exception as e:
            logger.error(f"Error creating candidate: {e}")
            return None

    def _fetch_contact_info_from_memory(self) -> bool:
        """
        Scan the agent's conversation memory for contact information and populate
        the session_state.application fields when found.

        Returns:
            True if any field was populated, False otherwise
        """
        try:
            # Build transcript from agent memory (if available) or Xano messages
            transcript = []
            if self.agent and hasattr(self.agent, 'memory') and hasattr(self.agent.memory, 'chat_memory'):
                mem = self.agent.memory.chat_memory
                for m in mem.messages:
                    # messages have type and content
                    role = getattr(m, 'type', 'human')
                    content = getattr(m, 'content', '') or ''
                    transcript.append(f"{role}: {content}")
            elif self.session_state.engagement and self.session_state.engagement.xano_session_id:
                try:
                    messages = self.xano_client.get_messages_by_session_id(self.session_state.engagement.xano_session_id) or []
                    for msg in messages:
                        role = 'human' if msg.get('MsgCreator', '').lower() == 'user' else 'assistant'
                        transcript.append(f"{role}: {msg.get('MsgContent', '')}")
                except Exception:
                    transcript = []

            if not transcript:
                return False

            # Use LLM to extract contact info - prefer agent.llm if available
            llm = None
            if self.agent and hasattr(self.agent, 'llm') and self.agent.llm:
                llm = self.agent.llm
            else:
                llm = ChatOpenAI(
                    model=settings.OPENAI_CHAT_MODEL,
                    temperature=0.0,
                    openai_api_key=settings.OPENAI_API_KEY,
                )

            transcript_text = transcript
            prompt = ( 
                "You are a strict JSON extractor. Given the following conversation transcript between an agent and a user, extract the candidate's full name, email address, and phone number. \n"
                "IMPORTANT INSTRUCTIONS:\n"
                "- full_name: Extract BOTH first name AND last name. If only one name is mentioned, then ask to give full name. And judge with NER that it is a name and then store.\n"
                "- email: Extract the complete email address with proper format (username@domain.extension). Skip if format is invalid.\n"
                "- phone: Extract the phone number with all digits.\n"
                "Return ONLY valid JSON with the exact keys: full_name, email, phone. Use null for missing fields and don't output any other text. If multiple values are present, use the most recent values.\n"
                "Examples:\n"
                "- Good full_name: \"John Smith\", \"Sarah Johnson\"\n"
                "- Incomplete full_name: \"John\" (only first name)\n"
                "- Good email: \"john.smith@gmail.com\", \"sarah@company.co.uk\"\n"
                "- Invalid email: \"john@test\" (missing extension), \"test@test\" (incomplete domain)\n\n"
                f"TRANSCRIPT:\n{transcript_text}\n\n"
            )

            logger.debug("Calling LLM to extract contact info from transcript")
            response = llm.invoke(prompt)
            response_text = response.content

            # Extract JSON payload from response
            import json, re
            json_text = response_text.strip()
            # If response contains code block, extract it
            if "```json" in json_text:
                start = json_text.find('```json') + 7
                end = json_text.find('```', start)
                json_text = json_text[start:end].strip()
            elif "```" in json_text:
                start = json_text.find('```') + 3
                end = json_text.find('```', start)
                json_text = json_text[start:end].strip()

            extracted = None
            try:
                extracted = json.loads(json_text)
            except Exception:
                # Last resort: try to find email and phone using regex as fallback
                extracted = {"full_name": None, "email": None, "phone": None}
                email_m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", response_text)
                phone_m = re.search(r"(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})", response_text)
                name_m = re.search(r"\"?full_name\"?\s*[:=]\s*\"([A-Za-z\s]+)\"", response_text)
                if email_m:
                    extracted['email'] = email_m.group()
                if phone_m:
                    extracted['phone'] = phone_m.group()
                if name_m:
                    extracted['full_name'] = name_m.group(1).strip().title()

            # Ensure app state
            from chatbot.state.states import ApplicationState
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
            app = self.session_state.application
            updated = False
            if isinstance(extracted, dict):
                f = extracted.get('full_name')
                e = extracted.get('email')
                p = extracted.get('phone')
                
                # Validate and save full name
                if f and not app.full_name:
                    name_cleaned = f.strip().title()
                    # Check if name has at least 2 parts (first and last)
                    name_parts = name_cleaned.split()
                    if len(name_parts) < 2:
                        logger.warning(f"Extracted name appears incomplete: '{name_cleaned}' (only {len(name_parts)} part(s))")
                    app.full_name = name_cleaned
                    updated = True
                
                # Validate and save email
                if e and not app.email:
                    email_cleaned = e.strip().lower()
                    # Validate email format
                    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
                    if re.match(email_pattern, email_cleaned):
                        app.email = email_cleaned
                        updated = True
                    else:
                        logger.warning(f"Extracted email has invalid format: '{email_cleaned}'")
                
                # Save phone
                if p and not app.phone_number:
                    app.phone_number = p.strip()
                    updated = True

            return updated
        except Exception as e:
            logger.error(f"Error while extracting contact info using LLM: {e}")
            return False

    def conclude_session(self, reason: str) -> str:
        """
        Conclude the current session when the user indicates they want to end the conversation
        or when the session times out.
        
        This method:
        1. Calculates the fit score
        2. Generates a PDF summary report
        3. Creates the candidate record with score and PDF
        4. Updates the session status in Xano
        
        Args:
            reason: The reason for concluding the session (e.g., "User said goodbye", "Session timed out")
        """
        try:
            if self._session_concluded:
                return "Session has already been concluded."
            
            self._session_concluded = True
            xano_session_id = None
            
            if self.session_state.engagement:
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # Determine final status based on what was collected
            final_status = "Ended"
            if self.session_state.application and self.session_state.application.stage_completed:
                final_status = "Completed"
            elif self.session_state.qualification and self.session_state.qualification.stage_completed:
                final_status = "Qualified - Pending"
            elif self.session_state.engagement and self.session_state.engagement.consent_given:
                final_status = "In Progress - Paused"
            else:
                final_status = "Ended - Early Exit"
            
            # Step 1: Calculate fit score (only once)
            fit_score = self._calculate_fit_score()
            logger.info(f"Session conclude - Fit score calculated: {fit_score.total_score:.2f}")
            
            # Step 2: Generate PDF report (uses pre-calculated fit score)
            pdf_path = self._generate_pdf_report(fit_score)
            if pdf_path:
                logger.info(f"Session conclude - PDF report generated: {pdf_path}")
            
            # Step 3: Create candidate if we have contact info (uses pre-calculated fit score and PDF)
            candidate_id = None

            # Identify missing fields
            missing = []
            if not self.session_state.application or not self.session_state.application.full_name:
                missing.append("full_name")
            if not self.session_state.application or not self.session_state.application.email:
                missing.append("email")
            if not self.session_state.application or not self.session_state.application.phone_number:
                missing.append("phone")

            # If some contact fields are missing, attempt to fetch them from conversation memory
            if missing:
                logger.info(f"Missing contact fields at conclude: {missing}")
                fetched = False
                try:
                    fetched = self._fetch_contact_info_from_memory()
                    if fetched:
                        logger.info("Fetched missing contact info from conversation memory")
                except Exception as e:
                    logger.debug(f"Error scanning conversation memory: {e}")

                # If still missing and we have an agent instance, prompt it to re-check history / ask user
                if not fetched and self.agent:
                    try:
                        prompt = (
                            "Please re-check the conversation history and extract any candidate contact information "
                            "(full name, email, phone). If found, respond with them explicitly in the reply so we can capture and save them. "
                            "If any details are missing, ask a clear question requesting ONLY the missing details."
                        )
                        # Trigger the agent to process the prompt; this may generate an assistant message or a follow-up question
                        self.agent.process_message(prompt)
                        # Re-scan after agent had a chance to inspect and respond
                        fetched = self._fetch_contact_info_from_memory()
                        if fetched:
                            logger.info("Fetched missing contact info after prompting agent")
                    except Exception as e:
                        logger.debug(f"Failed to prompt agent for contact info: {e}")

            # Finally, attempt to create candidate if all required fields are present
            if (
                self.session_state.application
                and self.session_state.application.full_name
                and self.session_state.application.email
                and self.session_state.application.phone_number
            ):
                # Additional validation before creating candidate
                name = self.session_state.application.full_name
                email = self.session_state.application.email
                
                # Validate name completeness (should have at least first and last name)
                name_parts = name.split() if name else []
                if len(name_parts) < 2:
                    logger.warning(f"Name appears incomplete: '{name}' (only {len(name_parts)} part(s)). Agent should collect full name.")
                
                # Validate email format
                email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
                if not re.match(email_pattern, email):
                    logger.warning(f"Email format invalid: '{email}'. Agent should validate email during conversation.")
                
                candidate_id = self._create_candidate_on_conclude(fit_score, pdf_path)
            else:
                logger.warning("Candidate will not be created on conclude: missing name, email, or phone")
                if candidate_id:
                    logger.info(f"Session conclude - Candidate created: {candidate_id}")
            
            # Step 4: Update session in Xano
            if xano_session_id:
                update_data = {
                    "Status": final_status,
                    "conversation_stage": "concluded",
                    "conclusion_reason": reason,
                }
                
                if candidate_id:
                    update_data["candidate_id"] = candidate_id
                
                self.xano_client.update_session(xano_session_id, update_data)
                logger.info(f"Session {xano_session_id} concluded with status: {final_status}, reason: {reason}")
            
            return f"Session concluded successfully. Status: {final_status}. Reason: {reason}"
            
        except Exception as e:
            logger.error(f"Error concluding session: {e}")
            return f"Session ended with note: {reason}"
    
    def _ensure_candidate_created(self) -> Optional[int]:
        """
        Ensure candidate is created for this session before verification.
        If candidate doesn't exist yet, create it now.
        
        Returns:
            Candidate ID if created or already exists, None if creation failed
        """
        # Check if candidate already exists for this session
        if self.session_state.engagement and self.session_state.engagement.candidate_id:
            logger.info(f"Candidate already exists: {self.session_state.engagement.candidate_id}")
            return self.session_state.engagement.candidate_id
        
        # Candidate doesn't exist, so create it now
        logger.info("Candidate not yet created. Creating candidate now before verification...")
        
        try:
            # Calculate fit score
            fit_score = self._calculate_fit_score()
            
            # Generate PDF report
            pdf_path = self._generate_pdf_report(fit_score)
            
            # Create candidate
            candidate_id = self._create_candidate_on_conclude(fit_score, pdf_path)
            
            if candidate_id:
                logger.info(f"Candidate created successfully: {candidate_id}")
                return candidate_id
            else:
                logger.warning("Failed to create candidate")
                return None
                
        except Exception as e:
            logger.error(f"Error ensuring candidate creation: {e}")
            return None
    
    def send_email_verification_code(self, email: str) -> str:
        """
        Send email verification code to the candidate.
        First ensures candidate is created, then sends verification code.
        
        Args:
            email: Email address to send verification code to
            
        Returns:
            Message indicating success or failure, and stores user_id and code for later validation
        """
        try:
            # Ensure candidate is created before verification
            candidate_id = self._ensure_candidate_created()
            if not candidate_id:
                logger.warning("Cannot send email verification code: candidate could not be created")
                return "✗ Unable to prepare verification. Please complete your application first."
            
            # Call Xano API to send email code
            url = "https://xoho-w3ng-km3o.n7e.xano.io/api:QMW9Va2W/Send_Code_to_Email"
            payload = {"email": email}
            
            response = requests.post(url, json=payload, timeout=self.xano_client.timeout)
            response.raise_for_status()
            
            result = response.json()
            user_id = result.get('id')
            email_code = result.get('EmailCode')
            
            # Store verification state for this session
            if not self.session_state.verification:
                from chatbot.state.states import VerificationState
                self.session_state.verification = VerificationState(session_id=self.session_state.session_id)
            
            self.session_state.verification.email_verification_user_id = user_id
            self.session_state.verification.email_verification_code = email_code
            self.session_state.verification.email_for_verification = email
            
            logger.info(f"Email verification code sent to {email}, user_id: {user_id}, candidate_id: {candidate_id}")
            return f"✓ Verification code sent to {email}. Please check your email and enter the code when ready."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending email verification code: {e}")
            return f"✗ Failed to send verification code to {email}. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error sending email verification code: {e}")
            return f"✗ An error occurred while sending verification code. Please try again."

    def validate_email_verification(self, user_id: int, code: str) -> str:
        """
        Validate email verification code provided by user.
        First ensures candidate is created, then validates the code.
        
        Args:
            user_id: User ID from previous email send
            code: Verification code entered by user
            
        Returns:
            Message indicating if verification was successful
        """
        try:
            # Ensure candidate is created before validation
            candidate_id = self._ensure_candidate_created()
            if not candidate_id:
                logger.warning("Cannot validate email verification code: candidate could not be created")
                return "✗ Unable to complete verification. Please complete your application first."
            
            # Call Xano API to validate email code
            url = "https://xoho-w3ng-km3o.n7e.xano.io/api:QMW9Va2W/ValidateEmail"
            payload = {"user_id": user_id, "Code": code}
            
            response = requests.post(url, json=payload, timeout=self.xano_client.timeout)
            response.raise_for_status()
            
            result = response.json()
            email_verified = result.get('EmailVerification', False)
            
            if email_verified:
                # Update verification state
                if not self.session_state.verification:
                    from chatbot.state.states import VerificationState
                    self.session_state.verification = VerificationState(session_id=self.session_state.session_id)
                
                self.session_state.verification.email_verified = True
                logger.info(f"Email verified successfully for user_id: {user_id}, candidate_id: {candidate_id}")
                return "✓ Email verified successfully!"
            else:
                logger.warning(f"Email verification failed for user_id: {user_id}")
                return "✗ Email verification failed. Please check the code and try again."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating email verification code: {e}")
            return f"✗ Verification failed. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error validating email verification: {e}")
            return f"✗ An error occurred during verification. Please try again."

    def send_phone_verification_code(self, phone: str) -> str:
        """
        Send phone verification code to the candidate.
        First ensures candidate is created, then sends verification code.
        
        Args:
            phone: Phone number to send verification code to
            
        Returns:
            Message indicating success or failure, and stores user_id and code for later validation
        """
        try:
            # Ensure candidate is created before verification
            candidate_id = self._ensure_candidate_created()
            if not candidate_id:
                logger.warning("Cannot send phone verification code: candidate could not be created")
                return "✗ Unable to prepare verification. Please complete your application first."
            
            # Call Xano API to send phone code (using email as identifier)
            url = "https://xoho-w3ng-km3o.n7e.xano.io/api:QMW9Va2W/Send_Code_to_Phone"
            # The API expects email parameter based on the notebook example
            if self.session_state.application and self.session_state.application.email:
                email = self.session_state.application.email
            else:
                return "✗ Email not found in session. Please provide email first."
            
            payload = {"email": email}
            
            response = requests.post(url, json=payload, timeout=self.xano_client.timeout)
            response.raise_for_status()
            
            result = response.json()
            user_id = result.get('id')
            phone_code = result.get('PhoneCode')
            
            # Store verification state for this session
            if not self.session_state.verification:
                from chatbot.state.states import VerificationState
                self.session_state.verification = VerificationState(session_id=self.session_state.session_id)
            
            self.session_state.verification.phone_verification_user_id = user_id
            self.session_state.verification.phone_verification_code = phone_code
            self.session_state.verification.phone_for_verification = phone
            
            logger.info(f"Phone verification code sent, user_id: {user_id}, candidate_id: {candidate_id}")
            return f"✓ Verification code sent to {phone}. Please enter the code when ready."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending phone verification code: {e}")
            return f"✗ Failed to send verification code to {phone}. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error sending phone verification code: {e}")
            return f"✗ An error occurred while sending verification code. Please try again."

    def validate_phone_verification(self, user_id: int, code: str) -> str:
        """
        Validate phone verification code provided by user.
        First ensures candidate is created, then validates the code.
        
        Args:
            user_id: User ID from previous phone send
            code: Verification code entered by user
            
        Returns:
            Message indicating if verification was successful
        """
        try:
            # Ensure candidate is created before validation
            candidate_id = self._ensure_candidate_created()
            if not candidate_id:
                logger.warning("Cannot validate phone verification code: candidate could not be created")
                return "✗ Unable to complete verification. Please complete your application first."
            
            # Call Xano API to validate phone code
            url = "https://xoho-w3ng-km3o.n7e.xano.io/api:QMW9Va2W/ValidatePhoneVerification"
            payload = {"user_id": user_id, "Code": code}
            
            response = requests.post(url, json=payload, timeout=self.xano_client.timeout)
            response.raise_for_status()
            
            result = response.json()
            phone_verified = result.get('Phone_Verification', False)
            
            if phone_verified:
                # Update verification state
                if not self.session_state.verification:
                    from chatbot.state.states import VerificationState
                    self.session_state.verification = VerificationState(session_id=self.session_state.session_id)
                
                self.session_state.verification.phone_verified = True
                logger.info(f"Phone verified successfully for user_id: {user_id}, candidate_id: {candidate_id}")
                return "✓ Phone verified successfully!"
            else:
                logger.warning(f"Phone verification failed for user_id: {user_id}")
                return "✗ Phone verification failed. Please check the code and try again."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating phone verification code: {e}")
            return f"✗ Verification failed. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error validating phone verification: {e}")
            return f"✗ An error occurred during verification. Please try again."

    def get_tools(self) -> List[StructuredTool]:
        """
        Get all tools bound to this toolkit's session state.
        
        Returns:
            List of StructuredTool instances bound to this toolkit
        """
        tools = [
            StructuredTool.from_function(
                func=self.save_state,
                name="save_state",
                description="Save the current conversation state to persistent storage. Use this to save key conversation milestones like when user starts application, shares resume, or agrees to proceed.",
            ),
            StructuredTool.from_function(
                func=self.send_email_verification_code,
                name="send_email_verification_code",
                description=(
                    "Send email verification code to candidate. Call this after asking if user is available for email verification. "
                    "The system will send a verification code to their email and store it for later validation. "
                    "Input: candidate's email address."
                ),
            ),
            StructuredTool.from_function(
                func=self.validate_email_verification,
                name="validate_email_verification",
                description=(
                    "Validate the email verification code provided by the user. Call this after user enters the code they received. "
                    "If code is valid, email is marked as verified. "
                    "Input: user_id (from email send response) and the 6-digit code user provided."
                ),
            ),
            StructuredTool.from_function(
                func=self.send_phone_verification_code,
                name="send_phone_verification_code",
                description=(
                    "Send phone verification code to candidate. Call this after asking if user is available for phone verification. "
                    "The system will send a verification code to their phone and store it for later validation. "
                    "Input: candidate's phone number."
                ),
            ),
            StructuredTool.from_function(
                func=self.validate_phone_verification,
                name="validate_phone_verification",
                description=(
                    "Validate the phone verification code provided by the user. Call this after user enters the code they received. "
                    "If code is valid, phone is marked as verified. "
                    "Input: user_id (from phone send response) and the 6-digit code user provided."
                ),
            ),
            StructuredTool.from_function(
                func=self.conclude_session,
                name="conclude_session",
                description=(
                    "Use this tool when the user indicates they want to end the conversation (e.g., says goodbye, thanks and leaves, needs to go, will think about it). "
                    "IMPORTANT: Before calling this, you MUST have collected the candidate's NAME, PHONE NUMBER, and EMAIL ADDRESS. "
                    "This tool calculates fit score, generates a report, and creates the candidate record. "
                    "Input should be the reason for ending (e.g., 'User said goodbye', 'User needs time to decide', 'User completed application')."
                ),
            ),
        ]
        return tools


def create_agent_tools(session_state: "SessionState", job_id: Optional[str] = None, agent: Optional["CleoRAGAgent"] = None) -> List[StructuredTool]:
    """
    Factory function to create tools bound to a specific session state.
    
    Args:
        session_state: The agent's SessionState object
        job_id: The job ID for the position being applied to
        
    Returns:
        List of tools bound to the provided session state
    """
    toolkit = AgentToolkit(session_state, job_id, agent=agent)
    return toolkit.get_tools()
