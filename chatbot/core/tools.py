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
    
    def _generate_report_and_extract_data(self) -> tuple[Optional[str], float, str]:
        """
        Generate PDF report and extract fit_score and profile_summary.
        
        Returns:
            Tuple of (pdf_path, fit_score, profile_summary)
        """
        try:
            session_id = self.session_state.session_id
            xano_session_id = None
            
            # Get xano_session_id from engagement state
            if self.session_state.engagement:
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # If we have a Xano session ID, use it to generate the report
            if xano_session_id:
                logger.info(f"Generating report for Xano session {xano_session_id}")
                
                result = self._report_generator.generate_report(
                    session_id=str(xano_session_id)
                )
                
                pdf_path = result.get('pdf_report')
                fit_score = result.get('fit_score', 0)
                profile_summary = result.get('profile_summary', '')
                
                logger.info(f"Generated PDF report for Xano session {xano_session_id}: {pdf_path}")
                logger.info(f"Extracted fit_score: {fit_score}, profile_summary length: {len(profile_summary)}")
                return pdf_path, fit_score, profile_summary
            else:
                logger.warning(f"No Xano session ID available for session {session_id}, cannot generate report")
                return None, 0, ''
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            import traceback
            traceback.print_exc()
            return None, 0, ''
    
    def _create_candidate_on_conclude(self, fit_score: float, profile_summary: str, pdf_path: Optional[str]) -> Optional[int]:
        """
        Create candidate record when session concludes.
        This is called only once when the session ends.
        
        Args:
            fit_score: Fit score value from report generation
            profile_summary: Profile summary/explanation from report generation
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

            # Sanitize phone: preserve + sign if present, extract digits
            phone_clean = None
            if phone:
                try:
                    stripped = str(phone).strip()
                    # Check if phone starts with +
                    has_plus = stripped.startswith('+')
                    # Extract digits only (strip -, spaces, parentheses, etc.)
                    digits = ''.join(filter(str.isdigit, stripped))
                    if digits:
                        # Add + sign back if it was present
                        phone_clean = f"+{digits}" if has_plus else digits
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
                        # Also extract company_id if not already set
                        if not company_id and 'company_id' in job_data:
                            company_id = job_data['company_id']
                            logger.info(f"Retrieved company_id from job data: {company_id}")
                    else:
                        logger.error(f"Failed to retrieve job with ID '{job_id}' from Xano. Cannot create candidate without valid UUID.")
                        return None
            else:
                logger.warning("No job_id available for candidate creation")
            
            # If company_id is still None, fetch job details to get company_id
            if not company_id and job_id:
                logger.info(f"company_id not set, fetching job details for job_id: {job_id}")
                job_data = self.xano_client.get_job_by_id(job_id)
                if job_data and '_related_company' in job_data:
                    company_id = job_data['_related_company']['id']
                    logger.info(f"Retrieved company_id from job data: {company_id}")
                else:
                    logger.warning(f"Failed to retrieve company_id from job {job_id}")
            
            logger.info(f"Creating candidate {name} with score {fit_score}")
            
            # Create candidate in Xano with fit score and PDF
            # Ensure profile_summary is a string (should already be JSON string from report generator)
            profile_summary_str = profile_summary if isinstance(profile_summary, str) else str(profile_summary)
            
            candidate = self.xano_client.create_candidate(
                name=name or "unable to fetch",
                email=email_clean,
                phone=phone_clean,
                score=fit_score,
                file_path=pdf_path,
                job_id=job_id,
                company_id=company_id,
                session_id=xano_session_id,
                status="Short Listed",
                profilesummary=profile_summary_str
            )

            logger.info("========================================")
            logger.info(f"Candidate creation response: {candidate}")
            logger.info("========================================")
            
            if candidate:
                candidate_id = candidate.get('id')
                user_id = candidate.get('user_id')  # Extract user_id from candidate response
                self._candidate_created = True

                
                # Store candidate_id and user_id in engagement state
                if self.session_state.engagement:
                    self.session_state.engagement.candidate_id = candidate_id
                    if user_id:
                        self.session_state.engagement.user_id = user_id
                        logger.info(f"Saved user_id {user_id} for candidate {candidate_id}")
                    # Update session with candidate_id in Xano
                    if xano_session_id:
                        self.xano_client.update_session(xano_session_id, {"candidate_id": candidate_id})
                
                logger.info(f"Created candidate {candidate_id} for session {self.session_state.session_id} with score {fit_score:.2f}")
                
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
        Check if contact information exists in the application state.
        
        Note: Contact information is now collected via agent tools (save_name, save_email, save_phone_number)
        rather than extracted via regex or LLM parsing. This method only validates presence of required fields.

        Returns:
            True if all contact fields are present, False otherwise
        """
        try:
            from chatbot.state.states import ApplicationState
            
            # Ensure application state exists
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
            
            app = self.session_state.application
            
            # Check if all required contact fields are present
            has_all_info = (
                app.full_name is not None and
                app.email is not None and
                app.phone_number is not None
            )
            
            if has_all_info:
                logger.info("All contact information is present in application state")
            else:
                missing = []
                if not app.full_name:
                    missing.append("full_name")
                if not app.email:
                    missing.append("email")
                if not app.phone_number:
                    missing.append("phone_number")
                logger.warning(f"Missing contact information: {', '.join(missing)}")
            
            return has_all_info
            
        except Exception as e:
            logger.error(f"Error checking contact info: {e}")
            return False

    def _sync_application_data_to_xano(self) -> bool:
        """
        Sync application state data (name, email, phone) to Xano session.
        This ensures contact information is persisted and available even after session timeout.
        
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            if not self.session_state.engagement or not self.session_state.engagement.xano_session_id:
                logger.warning("Cannot sync application data to Xano: No Xano session ID found")
                return False
            
            if not self.session_state.application:
                logger.warning("Cannot sync application data to Xano: No application state found")
                return False
            
            xano_session_id = self.session_state.engagement.xano_session_id
            app = self.session_state.application
            
            # Prepare update data with application fields
            update_data = {}
            
            if app.full_name:
                update_data["candidate_name"] = app.full_name
            if app.email:
                update_data["candidate_email"] = app.email
            if app.phone_number:
                update_data["candidate_phone"] = app.phone_number
            if app.age:
                update_data["candidate_age"] = app.age
            
            # Only update if we have data to sync
            if update_data:
                result = self.xano_client.update_session(xano_session_id, update_data)
                if result:
                    logger.info(f"Synced application data to Xano session {xano_session_id}: {list(update_data.keys())}")
                    return True
                else:
                    logger.warning(f"Failed to sync application data to Xano session {xano_session_id}")
                    return False
            else:
                logger.debug("No application data to sync to Xano")
                return True
                
        except Exception as e:
            logger.error(f"Error syncing application data to Xano: {e}")
            return False

    def conclude_session(self, reason: str) -> str:
        """
        Conclude the current session when the user indicates they want to end the conversation
        or when the session times out.
        
        This method:
        1. Generates a PDF report and extracts fit score and profile summary
        2. Creates the candidate record with score, profile summary, and PDF
        3. Updates the session status in Xano
        
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
            
            # Step 1: Generate PDF report and extract fit score and profile summary
            pdf_path, fit_score, profile_summary = self._generate_report_and_extract_data()
            if pdf_path:
                logger.info(f"Session conclude - PDF report generated: {pdf_path}")
            logger.info(f"Session conclude - Fit score extracted: {fit_score:.2f}")
            
            # Step 2: Check if candidate already exists, then patch or create
            candidate_id = None
            
            # Check if candidate was already created earlier (e.g., during verification)
            if self.session_state.engagement and self.session_state.engagement.candidate_id:
                candidate_id = self.session_state.engagement.candidate_id
                logger.info(f"Candidate already exists (ID: {candidate_id}), will patch with report data")
                
                # Patch existing candidate with report data
                try:
                    # Ensure profile_summary is a string (should already be JSON string from report generator)
                    profile_summary_str = profile_summary if isinstance(profile_summary, str) else str(profile_summary)
                    
                    result = self.xano_client.patch_candidate_complete(
                        candidate_id=candidate_id,
                        score=fit_score,
                        profile_summary=profile_summary_str,
                        status="Short Listed",
                        session_id=self.session_state.engagement.xano_session_id if self.session_state.engagement else None
                    )
                    
                    if result:
                        logger.info(f"Successfully patched candidate {candidate_id} with report data (score: {fit_score:.2f})")
                        
                        # Upload PDF if available
                        if pdf_path and os.path.exists(pdf_path):
                            upload_result = self.xano_client.upload_candidate_report_pdf(candidate_id, pdf_path)
                            if upload_result:
                                logger.info(f"Successfully uploaded PDF report for candidate {candidate_id}")
                                # Delete local PDF after successful upload
                                try:
                                    os.remove(pdf_path)
                                    logger.info(f"Deleted local PDF report: {pdf_path}")
                                except Exception as e:
                                    logger.warning(f"Failed to delete local PDF report {pdf_path}: {e}")
                            else:
                                logger.warning(f"Failed to upload PDF report for candidate {candidate_id}")
                    else:
                        logger.warning(f"Failed to patch candidate {candidate_id} with report data")
                except Exception as e:
                    logger.error(f"Error patching candidate {candidate_id}: {e}")
            else:
                # No existing candidate, need to create one
                logger.info("No existing candidate found, will create new candidate if contact info available")

            # First, try to load contact info from Xano session data (in case it was synced earlier)
            if self.session_state.engagement and self.session_state.engagement.xano_session_id:
                xano_session_id = self.session_state.engagement.xano_session_id
                try:
                    xano_session = self.xano_client.get_session_by_id(xano_session_id)
                    if xano_session:
                        # Load contact info from Xano into application state if not already present
                        from chatbot.state.states import ApplicationState
                        if not self.session_state.application:
                            self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
                        
                        app = self.session_state.application
                        
                        # Restore from Xano if local state is missing
                        if not app.full_name and xano_session.get("candidate_name"):
                            app.full_name = xano_session["candidate_name"]
                            logger.info(f"Restored name from Xano: {app.full_name}")
                        if not app.email and xano_session.get("candidate_email"):
                            app.email = xano_session["candidate_email"]
                            logger.info(f"Restored email from Xano: {app.email}")
                        if not app.phone_number and xano_session.get("candidate_phone"):
                            app.phone_number = xano_session["candidate_phone"]
                            logger.info(f"Restored phone from Xano: {app.phone_number}")
                        if not app.age and xano_session.get("candidate_age"):
                            app.age = xano_session["candidate_age"]
                            logger.info(f"Restored age from Xano: {app.age}")
                except Exception as e:
                    logger.debug(f"Could not load session data from Xano: {e}")

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

            # Only create candidate if one doesn't already exist
            if not candidate_id:
                # Finally, attempt to create candidate if all required fields are present
                if (
                    self.session_state.application
                    and not self._candidate_created
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
                    
                    candidate_id = self._create_candidate_on_conclude(fit_score, profile_summary, pdf_path)
                    if candidate_id:
                        logger.info(f"Session conclude - Candidate created: {candidate_id}")
                else:
                    logger.warning("Candidate will not be created on conclude: missing name, email, or phone")
            
            # Step 3: Update session in Xano
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
            if (
                self.session_state.application
                and not self._candidate_created
                and self.session_state.application.full_name
                and self.session_state.application.email
                and self.session_state.application.phone_number
            ):
                # Generate report and extract fit score and profile summary
                pdf_path, fit_score, profile_summary = self._generate_report_and_extract_data()
                
                # Create candidate
                candidate_id = self._create_candidate_on_conclude(fit_score, profile_summary, pdf_path)
                
                if candidate_id:
                    logger.info(f"Candidate created successfully: {candidate_id}")
                    return candidate_id
                else:
                    logger.warning("Failed to create candidate")
                    return None
            else:
                logger.warning("Cannot create candidate: missing name, email, or phone")
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
            
            # Check if we already have user_id from candidate creation
            user_id = None
            if self.session_state.engagement and self.session_state.engagement.user_id:
                user_id = self.session_state.engagement.user_id
                logger.info(f"Using stored user_id {user_id} from candidate creation")
            
            # Call Xano API to send email code
            url = "https://xoho-w3ng-km3o.n7e.xano.io/api:QMW9Va2W/Send_Code_to_Email"
            payload = {"email": email}
            
            response = requests.post(url, json=payload, timeout=self.xano_client.timeout)
            response.raise_for_status()
            
            result = response.json()
            # Use user_id from API response if we don't have one yet
            if not user_id:
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
            
            user_id = self.session_state.engagement.user_id
            logger.info(f"Validating email verification for user_id: {user_id}, candidate_id: {candidate_id}")
            # Call Xano API to validate email code
            url = "https://xoho-w3ng-km3o.n7e.xano.io/api:QMW9Va2W/ValidateEmail"
            payload = {"user_id": user_id, "Code": code}
            
            response = requests.post(url, json=payload, timeout=self.xano_client.timeout)
            response.raise_for_status()
            
            result = response.json()
            logger.info("========================================")
            logger.info(f"Email verification response: {result}")

            logger.info("========================================")
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
            
            # Check if we already have user_id from candidate creation
            user_id = None
            if self.session_state.engagement and self.session_state.engagement.user_id:
                user_id = self.session_state.engagement.user_id
                logger.info(f"Using stored user_id {user_id} from candidate creation")
            
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
            # Use user_id from API response if we don't have one yet
            if not user_id:
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
            
            user_id = self.session_state.engagement.user_id
            
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

    def save_phone_number(self, phone_number: str) -> str:
        """
        Save the candidate's phone number to application state.
        
        Args:
            phone_number: The phone number provided by the candidate
            
        Returns:
            Success message confirming the phone number was saved
        """
        try:
            from chatbot.state.states import ApplicationState
            
            # Ensure application state exists
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
            
            # Save phone number
            self.session_state.application.phone_number = phone_number.strip()
            logger.info(f"Phone number saved: {phone_number}")
            
            # Persist to Xano immediately
            self._sync_application_data_to_xano()
            
            return f"✓ Phone number saved: {phone_number}"
            
        except Exception as e:
            logger.error(f"Error saving phone number: {e}")
            return f"✗ Failed to save phone number. Please try again."

    def save_email(self, email: str) -> str:
        """
        Save the candidate's email address to application state.
        
        Args:
            email: The email address provided by the candidate
            
        Returns:
            Success message confirming the email was saved
        """
        try:
            from chatbot.state.states import ApplicationState
            
            # Ensure application state exists
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
            
            # Save email (lowercase for consistency)
            self.session_state.application.email = email.strip().lower()
            logger.info(f"Email saved: {email}")
            
            # Persist to Xano immediately
            self._sync_application_data_to_xano()
            
            return f"✓ Email saved: {email}"
            
        except Exception as e:
            logger.error(f"Error saving email: {e}")
            return f"✗ Failed to save email. Please try again."

    def save_name(self, full_name: str) -> str:
        """
        Save the candidate's full name to application state.
        
        Args:
            full_name: The full name (first and last) provided by the candidate
            
        Returns:
            Success message confirming the name was saved
        """
        try:
            from chatbot.state.states import ApplicationState
            
            # Ensure application state exists
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
            
            # Save name with proper capitalization
            self.session_state.application.full_name = full_name.strip().title()
            logger.info(f"Name saved: {full_name}")
            
            # Persist to Xano immediately
            self._sync_application_data_to_xano()
            
            return f"✓ Name saved: {full_name}"
            
        except Exception as e:
            logger.error(f"Error saving name: {e}")
            return f"✗ Failed to save name. Please try again."

    def save_age(self, age: int) -> str:
        """
        Save the candidate's age to application state.
        
        Args:
            age: The age provided by the candidate
            
        Returns:
            Success message confirming the age was saved
        """
        try:
            from chatbot.state.states import ApplicationState
            
            # Ensure application state exists
            if not self.session_state.application:
                self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
            
            # Save age
            self.session_state.application.age = age
            logger.info(f"Age saved: {age}")
            
            return f"✓ Age saved: {age}"
            
        except Exception as e:
            logger.error(f"Error saving age: {e}")
            return f"✗ Failed to save age. Please try again."

    def create_candidate_early(self) -> str:
        """
        Create candidate record immediately with basic information (name, email, phone, age).
        This is called early in the conversation, without generating a report.
        The report will be generated and patched later when the session concludes.
        
        Returns:
            Success message with candidate ID, or error message
        """
        try:
            # Check if candidate already exists
            if self._candidate_created:
                logger.info("Candidate already created for this session")
                if self.session_state.engagement and self.session_state.engagement.candidate_id:
                    return f"✓ Candidate already created with ID: {self.session_state.engagement.candidate_id}"
                return "✓ Candidate already exists for this session"
            
            # Validate required fields are present
            if not self.session_state.application:
                return "✗ Cannot create candidate: No application data available"
            
            app = self.session_state.application
            if not app.full_name or not app.email or not app.phone_number:
                missing = []
                if not app.full_name:
                    missing.append("name")
                if not app.email:
                    missing.append("email")
                if not app.phone_number:
                    missing.append("phone")
                return f"✗ Cannot create candidate: Missing {', '.join(missing)}"
            
            # Validate email format
            email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
            if not re.match(email_pattern, app.email.strip()):
                return f"✗ Invalid email format: {app.email}"
            
            # Get job_id and company_id
            job_id = self.job_id
            company_id = None
            xano_session_id = None
            
            if self.session_state.engagement:
                if not job_id:
                    job_id = self.session_state.engagement.job_id
                company_id = self.session_state.engagement.company_id
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # Validate and fetch job_id if needed
            if job_id and not self._is_valid_uuid(job_id):
                logger.warning(f"job_id '{job_id}' is not a valid UUID. Attempting to fetch from Xano...")
                job_data = self.xano_client.get_job_by_id(job_id)
                if job_data and 'id' in job_data:
                    job_id = str(job_data['id'])
                    logger.info(f"Retrieved UUID job_id from Xano: {job_id}")
                    if not company_id and 'company_id' in job_data:
                        company_id = job_data['company_id']
                else:
                    logger.error(f"Failed to retrieve valid job_id")
                    job_id = None
            
            # Fetch company_id if missing
            if not company_id and job_id:
                job_data = self.xano_client.get_job_by_id(job_id)
                if job_data and '_related_company' in job_data:
                    company_id = job_data['_related_company']['id']
                    logger.info(f"Retrieved company_id from job data: {company_id}")
            
            # Sanitize phone number (preserve + sign if present)
            phone_clean = None
            if app.phone_number:
                try:
                    stripped = str(app.phone_number).strip()
                    # Check if phone starts with +
                    has_plus = stripped.startswith('+')
                    # Extract only digits
                    digits = ''.join(filter(str.isdigit, stripped))
                    if digits:
                        # Add + sign back if it was present
                        phone_clean = f"+{digits}" if has_plus else digits
                except Exception:
                    phone_clean = None
            
            logger.info(f"Creating candidate early: {app.full_name}")
            
            # Create candidate WITHOUT report (score=0, no file_path)
            candidate = self.xano_client.create_candidate(
                name=app.full_name,
                email=app.email.strip().lower(),
                phone=phone_clean,
                score=0,  # No score yet
                file_path=None,  # No report yet
                job_id=job_id,
                company_id=company_id,
                session_id=xano_session_id,
                status="Short Listed",  # Status indicates candidate is in progress
                profilesummary=None  # No profile summary yet
            )
            
            if candidate:
                candidate_id = candidate.get('id')
                user_id = candidate.get('user_id')
                self._candidate_created = True
                
                # Store in engagement state
                if self.session_state.engagement:
                    self.session_state.engagement.candidate_id = candidate_id
                    if user_id:
                        self.session_state.engagement.user_id = user_id
                        logger.info(f"Saved user_id {user_id} for candidate {candidate_id}")
                    
                    # Update session with candidate_id
                    if xano_session_id:
                        self.xano_client.update_session(xano_session_id, {"candidate_id": candidate_id})
                
                logger.info(f"Created candidate {candidate_id} early without report")
                return f"✓ Candidate created successfully with ID: {candidate_id}"
            else:
                return "✗ Failed to create candidate in system"
                
        except Exception as e:
            logger.error(f"Error creating candidate early: {e}")
            import traceback
            traceback.print_exc()
            return f"✗ Error creating candidate: {str(e)}"

    def patch_candidate_with_report(self) -> str:
        """
        Generate report and patch the existing candidate with complete information.
        This is called at the end of the conversation to update the candidate with their report.
        
        Returns:
            Success message or error message
        """
        try:
            # Check if candidate exists
            if not self.session_state.engagement or not self.session_state.engagement.candidate_id:
                return "✗ Cannot patch candidate: No candidate ID found. Create candidate first."
            
            candidate_id = self.session_state.engagement.candidate_id
            
            # Generate report
            pdf_path, fit_score, profile_summary = self._generate_report_and_extract_data()
            
            if not pdf_path:
                logger.warning("No PDF report generated, patching with score and summary only")
            
            # Get session info
            xano_session_id = None
            if self.session_state.engagement:
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # Ensure profile_summary is a string (should already be JSON string from report generator)
            profile_summary_str = profile_summary if isinstance(profile_summary, str) else str(profile_summary)
            
            # Patch candidate with complete data (PDF upload handled internally)
            result = self.xano_client.patch_candidate_complete(
                candidate_id=candidate_id,
                score=fit_score,
                report_pdf=pdf_path,
                status="Short Listed",
                profile_summary=profile_summary_str,
                session_id=xano_session_id
            )
            
            if result:
                logger.info(f"Successfully patched candidate {candidate_id} with report (score: {fit_score})")
                
                # Delete local PDF after successful patch and upload
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        logger.info(f"Deleted local PDF report: {pdf_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete local PDF: {e}")
                
                return f"✓ Candidate report generated and updated (Fit Score: {fit_score:.0f}%)"
            else:
                return "✗ Failed to update candidate with report"
                
        except Exception as e:
            logger.error(f"Error patching candidate with report: {e}")
            import traceback
            traceback.print_exc()
            return f"✗ Error updating candidate: {str(e)}"

    def update_candidate_email(self, new_email: str) -> str:
        """
        Update the candidate's email address.
        Use this when the user provides a corrected email address.
        
        Args:
            new_email: The new email address
            
        Returns:
            Success message or error message
        """
        try:
            # Validate email format
            email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
            if not re.match(email_pattern, new_email.strip()):
                return f"✗ Invalid email format: {new_email}"
            
            # Update in application state
            if self.session_state.application:
                self.session_state.application.email = new_email.strip().lower()
                logger.info(f"Updated email in application state: {new_email}")
            
            # If candidate already created, patch in Xano
            if self.session_state.engagement and self.session_state.engagement.candidate_id:
                candidate_id = self.session_state.engagement.candidate_id
                
                result = self.xano_client.patch_candidate_email(
                    candidate_id=candidate_id,
                    email=new_email.strip().lower()
                )
                
                if result:
                    logger.info(f"Updated candidate {candidate_id} email to: {new_email}")
                    # Reset email verification since email changed
                    if self.session_state.verification:
                        self.session_state.verification.email_verified = False
                        self.session_state.verification.email_for_verification = None
                    return f"✓ Email updated to: {new_email}. Please verify the new email."
                else:
                    return "✗ Failed to update email in system"
            else:
                # Candidate not created yet, just update state
                return f"✓ Email updated to: {new_email}"
                
        except Exception as e:
            logger.error(f"Error updating candidate email: {e}")
            return f"✗ Error updating email: {str(e)}"

    def update_candidate_phone(self, new_phone: str) -> str:
        """
        Update the candidate's phone number.
        Use this when the user provides a corrected phone number.
        
        Args:
            new_phone: The new phone number
            
        Returns:
            Success message or error message
        """
        try:
            # Clean phone number (preserve + sign if present, extract digits)
            phone_clean = None
            try:
                stripped = new_phone.strip()
                # Check if phone starts with +
                has_plus = stripped.startswith('+')
                # Extract only digits
                digits = ''.join(filter(str.isdigit, str(stripped)))
                if digits:
                    # Add + sign back if it was present
                    phone_clean = f"+{digits}" if has_plus else digits
                else:
                    return f"✗ Invalid phone number format: {new_phone}"
            except Exception:
                return f"✗ Invalid phone number format: {new_phone}"
            
            # Update in application state
            if self.session_state.application:
                self.session_state.application.phone_number = phone_clean
                logger.info(f"Updated phone in application state: {phone_clean}")
            
            # If candidate already created, patch in Xano
            if self.session_state.engagement and self.session_state.engagement.candidate_id:
                candidate_id = self.session_state.engagement.candidate_id
                
                result = self.xano_client.patch_candidate_complete(
                    candidate_id=candidate_id,
                    phone=phone_clean
                )
                
                if result:
                    logger.info(f"Updated candidate {candidate_id} phone to: {new_phone}")
                    # Reset phone verification since phone changed
                    if self.session_state.verification:
                        self.session_state.verification.phone_verified = False
                        self.session_state.verification.phone_for_verification = None
                    return f"✓ Phone number updated to: {new_phone}. Please verify the new phone number."
                else:
                    return "✗ Failed to update phone number in system"
            else:
                # Candidate not created yet, just update state
                return f"✓ Phone number updated to: {new_phone}"
                
        except Exception as e:
            logger.error(f"Error updating candidate phone: {e}")
            return f"✗ Error updating phone: {str(e)}"

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
                func=self.save_name,
                name="save_name",
                description=(
                    "Save the candidate's full name (first and last name). Call this IMMEDIATELY when the user provides their name. "
                    "Extract the full name from the user's message and call this tool. "
                    "IMPORTANT: Only call this when you have BOTH first name AND last name. If user only provides first name, ask for the last name. "
                    "Input: full_name (e.g., 'John Smith', 'Sarah Johnson')"
                ),
            ),
            StructuredTool.from_function(
                func=self.save_email,
                name="save_email",
                description=(
                    "Save the candidate's email address. Call this IMMEDIATELY when the user provides their email. "
                    "Extract the email from the user's message and call this tool with the email address. "
                    "Input: email (e.g., 'john.doe@example.com')"
                ),
            ),
            StructuredTool.from_function(
                func=self.save_phone_number,
                name="save_phone_number",
                description=(
                    "Save the candidate's phone number. Call this IMMEDIATELY when the user provides their phone number. "
                    "Extract the phone number from the user's message and call this tool with the cleaned phone number. "
                    "Input: phone_number (e.g., '555-123-4567', '+1-555-123-4567')"
                ),
            ),
            StructuredTool.from_function(
                func=self.save_age,
                name="save_age",
                description=(
                    "Save the candidate's age. Call this IMMEDIATELY when the user provides their age. "
                    "Extract the age from the user's message and call this tool. "
                    "Input: age (integer, e.g., 25, 30)"
                ),
            ),
            StructuredTool.from_function(
                func=self.create_candidate_early,
                name="create_candidate_early",
                description=(
                    "Create candidate record in the system with basic information (name, email, phone, age). "
                    "Call this AFTER you have collected and validated ALL of: name, email, phone, and age. "
                    "This creates the candidate WITHOUT generating a report - the report will be added later. "
                    "The candidate record is needed before sending verification codes. "
                    "Do NOT call this multiple times - check if candidate is already created first."
                ),
            ),
            StructuredTool.from_function(
                func=self.update_candidate_email,
                name="update_candidate_email",
                description=(
                    "Update the candidate's email address if they provide a correction. "
                    "Use this when the user says their email was wrong or provides a different email. "
                    "This updates both the application state and the candidate record in the system. "
                    "Input: new_email (the corrected email address)"
                ),
            ),
            StructuredTool.from_function(
                func=self.update_candidate_phone,
                name="update_candidate_phone",
                description=(
                    "Update the candidate's phone number if they provide a correction. "
                    "Use this when the user says their phone was wrong or provides a different phone number. "
                    "This updates both the application state and the candidate record in the system. "
                    "Input: new_phone (the corrected phone number)"
                ),
            ),
            StructuredTool.from_function(
                func=self.send_email_verification_code,
                name="send_email_verification_code",
                description=(
                    "Send email verification code to candidate. CRITICAL: Execute this tool COMPLETELY SILENTLY WITHOUT ANY ANNOUNCEMENT OR INDICATION TO THE USER. "
                    "DO NOT say 'I'm sending the code', 'Let me send you a code', or '[RESULT AFTER TOOL CALL]' - NOTHING. "
                    "DO NOT show [CALLING SEND_EMAIL_VERIFICATION_CODE] or any bracket text to the user. "
                    "WHEN TO CALL THIS TOOL - Call IMMEDIATELY when user says ANY of these: "
                    "'yes', 'sure', 'ok', 'okay', 'ready', 'go ahead', 'verify', 'send it', 'verify email', 'send code', 'send the code', or ANY phrase indicating readiness. "
                    "EXECUTION PATTERN: "
                    "1. User indicates readiness (yes/ok/sure/ready/verify email/etc.) "
                    "2. YOU IMMEDIATELY CALL THIS TOOL SILENTLY (absolutely no message to user during execution) "
                    "3. Tool executes and returns result "
                    "4. ONLY AFTER the tool returns success, tell user the code was sent. "
                    "The tool will send a verification code to their email and return a success/failure message. "
                    "Input: candidate's email address."
                ),
            ),
            StructuredTool.from_function(
                func=self.validate_email_verification,
                name="validate_email_verification",
                description=(
                    "Validate the email verification code provided by the user. "
                    "CRITICAL: Call this tool COMPLETELY SILENTLY - DO NOT say '[CALLING VALIDATE EMAIL]', '[RESULT AFTER TOOL CALL]', or announce you're calling it. "
                    "DO NOT show any bracket text or thinking to the user. "
                    "When user provides the code (typically a 6-digit number), immediately call this tool with the user_id and code SILENTLY. "
                    "After tool returns, respond to the user naturally about whether verification succeeded or failed. "
                    "Input: user_id (from email send response) and the 6-digit code user provided."
                ),
            ),
            StructuredTool.from_function(
                func=self.send_phone_verification_code,
                name="send_phone_verification_code",
                description=(
                    "Send phone verification code to candidate. CRITICAL: Execute this tool COMPLETELY SILENTLY WITHOUT ANY ANNOUNCEMENT OR INDICATION TO THE USER. "
                    "DO NOT say 'I'm sending the code', 'The code has been sent', '[RESULT AFTER TOOL CALL]', or show any bracket text BEFORE calling this tool. "
                    "WHEN TO CALL THIS TOOL - Call IMMEDIATELY when user says ANY of these: "
                    "'yes', 'sure', 'ok', 'okay', 'ready', 'go ahead', 'verify', 'send it', 'sudre', "
                    "'verify phone', 'verify my phone', 'verify phone number', 'phone verification', "
                    "'send code', 'send the code', 'verify again', 'resend', 'send again', 'verify phone number again', "
                    "or ANY phrase indicating readiness or requesting phone verification. "
                    "EXECUTION PATTERN: "
                    "1. User indicates readiness or requests verification (any of the above phrases) "
                    "2. YOU IMMEDIATELY CALL THIS TOOL SILENTLY (absolutely no message to user during execution) "
                    "3. Tool executes and returns result "
                    "4. ONLY AFTER the tool returns success, tell user the code was sent. "
                    "The tool will send a verification code to their phone and return a success/failure message. "
                    "Input: candidate's phone number."
                ),
            ),
            StructuredTool.from_function(
                func=self.validate_phone_verification,
                name="validate_phone_verification",
                description=(
                    "Validate the phone verification code provided by the user. "
                    "CRITICAL: Call this tool COMPLETELY SILENTLY - DO NOT say '[CALLING VALIDATE PHONE VERIFICATION]', '[RESULT AFTER TOOL CALL]', or announce you're calling it. "
                    "DO NOT show any bracket text, thinking, or internal reasoning to the user. "
                    "When user provides the code (typically a 6-digit number like '176053'), immediately call this tool with the user_id and code SILENTLY. "
                    "After tool returns, respond naturally to tell user if verification succeeded or failed. "
                    "EXAMPLE: User says '176053' → You call this tool silently (user sees nothing) → Tool returns result → You say 'Perfect! Your phone is verified!' "
                    "Input: user_id (from phone send response) and the 6-digit code user provided."
                ),
            ),
            StructuredTool.from_function(
                func=self.patch_candidate_with_report,
                name="patch_candidate_with_report",
                description=(
                    "Generate the final report and update the candidate with their fit score and profile summary. "
                    "Call this AFTER the conversation is complete and you have gathered all necessary information. "
                    "This generates the PDF report, calculates fit score, and updates the candidate record. "
                    "Typically called just before concluding the session."
                ),
            ),
            StructuredTool.from_function(
                func=self.conclude_session,
                name="conclude_session",
                description=(
                    "End the conversation session. Call this when the user indicates they want to leave (goodbye, thanks, need to go). "
                    "IMPORTANT: Before calling this, ensure the candidate report has been generated (call patch_candidate_with_report if needed). "
                    "Input: reason for ending (e.g., 'User said goodbye', 'User completed application')."
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
