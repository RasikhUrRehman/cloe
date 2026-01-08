"""
Xano API Client
Handles all interactions with Xano backend APIs
"""
from typing import Any, Dict, List, Optional
import os
import requests
from chatbot.utils.utils import setup_logging
from dotenv import load_dotenv

load_dotenv()

logger = setup_logging()

# Xano API Base URLs
XANO_AUTH_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:LNn6-rP8"
XANO_JOB_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb"
XANO_CHAT_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:wnnakKFu"
XANO_SESSION_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:mYiFh-E2"
XANO_CANDIDATE_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:6skoiMBa"
XANO_COMPANY_API_URL = "https://xoho-w3ng-km30.n7e.xano.io/api:JpRLUNqy"

# Default credentials
DEFAULT_EMAIL = "user@example.com"
DEFAULT_PASSWORD = "string123"


class XanoClient:
    """Client for interacting with Xano APIs"""

    def __init__(self, timeout: int = 10, email: str = DEFAULT_EMAIL, password: str = DEFAULT_PASSWORD):
        """
        Initialize Xano API client and authenticate
        
        Args:
            timeout: Request timeout in seconds
            email: Email for authentication
            password: Password for authentication
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {"Content-Type": "application/json"}
        
        # # Login to get auth token
        # self._login(email, password)

    def _login(self, email: str, password: str) -> bool:
        """
        Login to Xano and store the auth token
        
        Args:
            email: User email
            password: User password
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            url = f"{XANO_AUTH_API_URL}/auth/login"
            payload = {"email": email, "password": password}
            logger.info(f"Logging in to Xano with email: {email}")
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            self.auth_token = result.get("authToken")
            if self.auth_token:
                self.headers = {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                }
                logger.info("Successfully authenticated with Xano")
                return True
            else:
                logger.error("Login response did not contain authToken")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error logging in to Xano: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return False

    # ==================== SESSION APIs ====================
    
    def get_sessions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all sessions from Xano
        
        Returns:
            List of sessions if successful, None otherwise
        """
        try:
            url = f"{XANO_SESSION_API_URL}/session"
            logger.info("Fetching all sessions from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            sessions = response.json()
            logger.info(f"Successfully fetched {len(sessions)} sessions")
            return sessions
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sessions from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching sessions: {e}")
            return None

    def create_session(
        self, initial_status: str = "Started", candidate_id: Optional[int] = None, job_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new session in Xano
        
        Args:
            initial_status: Initial session status (default: "Started")
            candidate_id: Optional candidate ID to link
            job_id: Optional job ID for the position being applied to
            
        Returns:
            Session data if successful, None otherwise
        """
        try:
            url = f"{XANO_SESSION_API_URL}/session"
            payload = {"Status": initial_status}
            if candidate_id:
                payload["candidate_id"] = candidate_id
            if job_id:
                payload["job_id"] = job_id
            logger.info(f"Creating new Xano session with status {initial_status}, job_id: {job_id}")
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created Xano session: {result.get('id', 'unknown')} for job_id: {job_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Xano session: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating session: {e}")
            return None

    def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific session by ID
        
        Args:
            session_id: The session ID
            
        Returns:
            Session data if found, None otherwise
        """
        try:
            url = f"{XANO_SESSION_API_URL}/session/{session_id}"
            logger.info(f"Fetching session {session_id} from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            session_data = response.json()
            logger.info(f"Successfully fetched session {session_id}")
            return session_data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Session not found with ID: {session_id}")
            else:
                logger.error(f"HTTP error fetching session {session_id}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching session {session_id} from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching session {session_id}: {e}")
            return None

    def patch_session_status(
        self, session_id: int, status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update session status in Xano
        
        Args:
            session_id: The session ID
            status: New status ("Started", "Continue", "Pending", "Completed")
            
        Returns:
            Response from API if successful, None otherwise
        """
        valid_statuses = ["Started", "Continue", "Pending", "Completed"]
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}. Must be one of {valid_statuses}")
            return None
        try:
            url = f"{XANO_SESSION_API_URL}/session/{session_id}"
            payload = {"session_id": session_id, "Status": status}
            logger.info(f"Updating Xano session {session_id} status to {status}")
            response = self.session.patch(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated session {session_id} status to {status}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating Xano session {session_id} status: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating session status: {e}")
            return None

    def update_session(
        self, session_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update session with arbitrary data
        
        Args:
            session_id: The session ID
            data: Data to update
            
        Returns:
            Updated session data if successful, None otherwise
        """
        try:
            url = f"{XANO_SESSION_API_URL}/session/{session_id}"
            # Include session_id in payload as required by Xano API
            payload = {"session_id": session_id, **data}
            logger.info(f"Updating Xano session {session_id}")
            response = self.session.patch(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated session {session_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating Xano session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating session: {e}")
            return None

    def delete_session(self, session_id: int) -> bool:
        """
        Delete a session from Xano
        
        Args:
            session_id: The session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{XANO_SESSION_API_URL}/session/{session_id}"
            logger.info(f"Deleting Xano session {session_id}")
            response = self.session.delete(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully deleted session {session_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting Xano session {session_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting session: {e}")
            return False

    # ==================== JOB APIs ====================
    def get_jobs(self):
        url = f"{XANO_JOB_API_URL}/job"

        try:
            logger.info("Fetching all jobs from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            jobs = response.json()
            logger.info(f"Successfully fetched {len(jobs)} jobs")
            return jobs

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching jobs from Xano: {e}")
            logger.error(f"Response content: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching jobs from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_jobs(): {e}")
            return None

    def create_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new job in Xano
        
        Args:
            job_data: Job data to create
            
        Returns:
            Created job data if successful, None otherwise
        """
        try:
            url = f"{XANO_JOB_API_URL}/job"
            logger.info("Creating new job in Xano")
            response = self.session.post(url, json=job_data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created job: {result.get('id', 'unknown')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating job in Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating job: {e}")
            return None

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific job by its ID from Xano
        
        Args:
            job_id: The unique identifier for the job
            
        Returns:
            Job dictionary if found, None otherwise
        """
        try:
            url = f"{XANO_JOB_API_URL}/job/{job_id}"
            logger.info(f"Fetching job from Xano: {job_id}")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            job = response.json()
            logger.info(f"Successfully fetched job: {job.get('job_title', 'Unknown')} (ID: {job_id})")
            return job
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Job not found with ID: {job_id}")
            else:
                logger.error(f"HTTP error fetching job {job_id}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching job {job_id} from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching job {job_id}: {e}")
            return None

    def update_job(self, job_id: str, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a job in Xano
        
        Args:
            job_id: The job ID
            job_data: Data to update
            
        Returns:
            Updated job data if successful, None otherwise
        """
        try:
            url = f"{XANO_JOB_API_URL}/job/{job_id}"
            logger.info(f"Updating job {job_id} in Xano")
            response = self.session.patch(url, json=job_data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated job {job_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating job {job_id} in Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating job: {e}")
            return None

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from Xano
        
        Args:
            job_id: The job ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{XANO_JOB_API_URL}/job/{job_id}"
            logger.info(f"Deleting job {job_id} from Xano")
            response = self.session.delete(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully deleted job {job_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting job {job_id} from Xano: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting job: {e}")
            return False

    # ==================== AI CHAT MESSAGES APIs ====================
    
    def get_messages(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all AI chat messages from Xano
        
        Returns:
            List of messages if successful, None otherwise
        """
        try:
            url = f"{XANO_CHAT_API_URL}/aichatmessages"
            logger.info("Fetching all messages from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            messages = response.json()
            logger.info(f"Successfully fetched {len(messages)} messages")
            return messages
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching messages from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching messages: {e}")
            return None

    def get_message_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific message by ID
        
        Args:
            message_id: The message ID
            
        Returns:
            Message data if found, None otherwise
        """
        try:
            url = f"{XANO_CHAT_API_URL}/aichatmessages/{message_id}"
            logger.info(f"Fetching message {message_id} from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            message = response.json()
            logger.info(f"Successfully fetched message {message_id}")
            return message
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Message not found with ID: {message_id}")
            else:
                logger.error(f"HTTP error fetching message {message_id}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching message {message_id} from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching message {message_id}: {e}")
            return None

    def post_message(
        self, session_id: int, msg_content: str, msg_creator: str
    ) -> Optional[Dict[str, Any]]:
        """
        Post a message against a session in Xano
        
        Args:
            session_id: The session ID
            msg_content: The message content
            msg_creator: Message creator ("AI" or "User")
            
        Returns:
            Response from API if successful, None otherwise
        """
        if msg_creator not in ["AI", "User"]:
            logger.error(f"Invalid msg_creator: {msg_creator}. Must be 'AI' or 'User'")
            return None
        try:
            url = f"{XANO_CHAT_API_URL}/aichatmessages"
            payload = {
                "session_id": session_id,
                "MsgContent": msg_content,
                "MsgCreator": msg_creator,
            }
            logger.info(f"Posting message to Xano session {session_id} from {msg_creator}")
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully posted message to session {session_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting message to Xano session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting message: {e}")
            return None

    def update_message(
        self, message_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a message in Xano
        
        Args:
            message_id: The message ID
            data: Data to update
            
        Returns:
            Updated message data if successful, None otherwise
        """
        try:
            url = f"{XANO_CHAT_API_URL}/aichatmessages/{message_id}"
            logger.info(f"Updating message {message_id} in Xano")
            response = self.session.patch(url, headers=self.headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated message {message_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating message {message_id} in Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating message: {e}")
            return None

    def delete_message(self, message_id: int) -> bool:
        """
        Delete a message from Xano
        
        Args:
            message_id: The message ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{XANO_CHAT_API_URL}/aichatmessages/{message_id}"
            logger.info(f"Deleting message {message_id} from Xano")
            response = self.session.delete(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully deleted message {message_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting message {message_id} from Xano: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting message: {e}")
            return False

    def get_messages_by_session_id(
        self, session_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get all messages for a specific session
        
        Args:
            session_id: The session ID
            
        Returns:
            List of messages if successful, None otherwise
        """
        try:
            url = f"{XANO_CHAT_API_URL}/aichatmessages_by_Session_Id"
            params = {"session_id": session_id}
            logger.info(f"Fetching messages for session {session_id} from Xano")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            messages = response.json()
            logger.info(f"Successfully fetched {len(messages)} messages for session {session_id}")
            return messages
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching messages for session {session_id} from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching session messages: {e}")
            return None

    # ==================== CANDIDATE APIs ====================
    
    def get_candidates(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all candidates from Xano
        
        Returns:
            List of candidates if successful, None otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/candidate"
            logger.info("Fetching all candidates from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            candidates = response.json()
            logger.info(f"Successfully fetched {len(candidates)} candidates")
            return candidates
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching candidates from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching candidates: {e}")
            return None

    def create_candidate(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        score: Optional[float] = 0,
        file_path: Optional[str] = None,
        job_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: str = "Short Listed",
        session_id: Optional[int] = None,
        profilesummary: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new candidate in Xano using multipart/form-data API
        
        Args:
            name: Candidate name (required)
            email: Candidate email
            phone: Candidate phone number (as string)
            score: Fit score
            file_path: Path to file (e.g., resume PDF) to upload
            job_id: Associated job ID
            company_id: Associated company ID
            status: Application status
            session_id: Session ID
            profilesummary: Profile summary text
            
        Returns:
            Created candidate data if successful, None otherwise
        """
        files = None  # Initialize files to avoid UnboundLocalError in finally
        try:
            # Handle case where a single dict is passed as the first parameter
            # (legacy usage or convenience). Normalize keys to expected params.
            if isinstance(name, dict):
                payload = name
                name = payload.get("name") or payload.get("Name")
                email = payload.get("email") or payload.get("Email")
                phone = payload.get("phone") or payload.get("Phone")
                score = payload.get("score") or payload.get("Score")
                file_path = payload.get("file_path") or payload.get("filePath") or payload.get("FilePath")
                job_id = payload.get("job_id") or payload.get("jobId") or payload.get("jobID")
                company_id = payload.get("company_id") or payload.get("companyId")
                status = payload.get("status") or payload.get("Status") or status
                session_id = payload.get("session_id") or payload.get("sessionId") or payload.get("session") or session_id
                profilesummary = payload.get("profilesummary") or payload.get("ProfileSummary") or profilesummary

            # Ensure phone is a string if provided
            if phone is not None and not isinstance(phone, str):
                phone = str(phone)

            # Validate required param
            if not name or not isinstance(name, (str,)):
                logger.error("create_candidate: 'name' is required and must be a string")
                return None
            url = f"{XANO_CANDIDATE_API_URL}/candidate_new_api"
            
            # Build form data
            form_data = {
                'Name': (None, name),
                'Status': (None, status),
                'session_id': (None, str(session_id) if session_id else '0'),
                'my_session_id' : (None, "00000000-0000-0000-0000-000000000029")
            }
            
            # Add optional fields if provided
            if email:
                form_data['Email'] = (None, email)
            if phone is not None:
                # Ensure phone number starts with '+' for international format
                if not phone.startswith('+'):
                    phone = '+' + phone
                form_data['Phone'] = (None, phone)
            if score is not None:
                form_data['Score'] = (None, str(int(score)))
            if job_id:
                form_data['job_id'] = (None, job_id)
            if company_id:
                form_data['company_id'] = (None, company_id)
            if profilesummary:
                form_data['ProfileSummary'] = (None, profilesummary)
            
            # Handle file upload if provided
            if file_path:
                import mimetypes
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    mime_type, _ = mimetypes.guess_type(file_path)
                    mime_type = mime_type or 'application/octet-stream'
                    files = {'File': (file_name, open(file_path, 'rb'), mime_type)}
                else:
                    logger.warning(f"File not found: {file_path}")
                    files = None
            else:
                # If no file_path provided, don't include File field at all
                files = None

            # Prepare headers with API key authorization for candidate creation
            x_api_key = 'sk_test_51QxA9F7C2E8B4D1A6F9C3E7B2A' #os.getenv('X_API_KEY', '')
            logger.info(f"Using X_API_KEY: {'set' if x_api_key else 'not set'} for candidate creation")
            headers = {
                'x-api-key': x_api_key,
            }
                
            logger.info(f"Creating new candidate in Xano: {name}")
            logger.info("===================================")
            logger.info(f"Candidate form data: {form_data}")
            logger.info(f"Files to upload: {files}")
            logger.info("===================================")
            # Only merge files if they exist, otherwise just send form_data
            if files:
                response = self.session.post(
                    url, 
                    files={**form_data, **files},
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                response = self.session.post(
                    url, 
                    files=form_data,
                    headers=headers,
                    timeout=self.timeout
                )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Response from Xano: {result}")
            logger.info(f"Successfully created candidate: {result.get('id', 'unknown')}")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating candidate in Xano: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating candidate: {e}")
            return None
        finally:
            # Close file handle if opened
            if files and 'File' in files:
                try:
                    files['File'][1].close()
                except:
                    pass

    def patch_candidate_complete(
        self,
        candidate_id: int,
        name: Optional[str] = None,
        score: Optional[float] = None,
        phone: Optional[str] = None,
        report_pdf: Optional[str] = None,
        status: Optional[str] = None,
        session_id: Optional[int] = None,
        profile_summary: Optional[str] = None,
        my_session_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Patch/update candidate with complete information (CompletePatch endpoint)
        Automatically uploads PDF report if provided via upload_candidate_report_pdf()
        
        Args:
            candidate_id: Candidate ID to update
            name: Candidate name
            score: Fit score
            phone: Phone number
            report_pdf: Path to report PDF file to upload (uploaded separately)
            status: Status
            session_id: Session ID
            profile_summary: Profile summary
            my_session_id: Session UUID
            
        Returns:
            Updated candidate data if successful, None otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/CompletePatch"
            
            # Use JSON payload (no file upload in patch)
            payload = {
                "candidate_id": candidate_id
            }
            
            # Add optional fields if provided
            if name is not None:
                payload["Name"] = name
            if score is not None:
                payload["Score"] = score
            if phone is not None:
                payload["Phone"] = phone
            if status is not None:
                payload["Status"] = status
            if session_id is not None:
                payload["session_id"] = session_id
            if profile_summary is not None:
                payload["ProfileSummary"] = profile_summary
            if my_session_id is not None:
                payload["my_session_id"] = my_session_id
            
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Patching candidate {candidate_id}")
            logger.info(f"URL: {url}")
            logger.info(f"Payload: {payload}")
            
            # Send PATCH request with JSON payload
            response = requests.patch(
                url, 
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully patched candidate {candidate_id}")
            
            # Upload PDF report separately if provided
            if report_pdf and os.path.exists(report_pdf):
                logger.info(f"Uploading PDF report for candidate {candidate_id}")
                upload_result = self.upload_candidate_report_pdf(
                    candidate_id=candidate_id,
                    report_pdf_path=report_pdf
                )
                if upload_result:
                    logger.info(f"Successfully uploaded PDF report for candidate {candidate_id}")
                else:
                    logger.warning(f"Failed to upload PDF report for candidate {candidate_id}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error patching candidate {candidate_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error patching candidate: {e}")
            return None

    def upload_candidate_report_pdf(
        self,
        candidate_id: int,
        report_pdf_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Upload PDF report for a candidate using the update_file endpoint
        
        Args:
            candidate_id: Candidate ID to upload report for
            report_pdf_path: Path to the PDF file to upload
            
        Returns:
            Response data if successful, None otherwise
        """
        file_handle = None
        try:
            if not os.path.exists(report_pdf_path):
                logger.error(f"PDF file not found: {report_pdf_path}")
                return None
            
            url = f"{XANO_CANDIDATE_API_URL}/update_file"
            
            # Prepare the file for upload
            import mimetypes
            file_name = os.path.basename(report_pdf_path)
            mime_type, _ = mimetypes.guess_type(report_pdf_path)
            mime_type = mime_type or 'application/pdf'
            
            file_handle = open(report_pdf_path, 'rb')
            
            # Prepare multipart form data
            files = {
                'File': (file_name, file_handle, mime_type)
            }
            
            data = {
                'candidate_id': str(candidate_id)
            }
            
            logger.info(f"Uploading PDF report for candidate {candidate_id}")
            logger.info(f"URL: {url}")
            logger.info(f"File: {file_name}")
            
            # Use PATCH method for update_file endpoint
            response = requests.patch(
                url,
                files=files,
                data=data,
                headers={'Accept': 'application/json'},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully uploaded PDF report for candidate {candidate_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error uploading PDF for candidate {candidate_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading PDF: {e}")
            return None
        finally:
            # Close file handle if opened
            if file_handle:
                try:
                    file_handle.close()
                except:
                    pass

    def patch_candidate_email(
        self,
        candidate_id: int,
        email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Patch/update candidate email address only
        
        Args:
            candidate_id: Candidate ID to update
            email: New email address
            
        Returns:
            Updated candidate data if successful, None otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/patch_candidate_email"
            
            payload = {
                "candidate_id": candidate_id,
                "Email": email
            }
            
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Patching candidate {candidate_id} email to: {email}")
            logger.info(f"URL: {url}")
            logger.info(f"Payload: {payload}")
            
            response = requests.patch(
                url, 
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully patched candidate {candidate_id} email")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error patching candidate {candidate_id} email: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error patching candidate email: {e}")
            return None

    def get_candidate_by_id(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific candidate by ID
        
        Args:
            candidate_id: The candidate ID
            
        Returns:
            Candidate data if found, None otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/candidate/{candidate_id}"
            logger.info(f"Fetching candidate {candidate_id} from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            candidate = response.json()
            logger.info(f"Successfully fetched candidate {candidate_id}")
            return candidate
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Candidate not found with ID: {candidate_id}")
            else:
                logger.error(f"HTTP error fetching candidate {candidate_id}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching candidate {candidate_id} from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching candidate {candidate_id}: {e}")
            return None

    def update_candidate(
        self, candidate_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a candidate in Xano
        
        Args:
            candidate_id: The candidate ID
            data: Data to update (can include Name, Email, Phone, Score, Status, etc.)
            
        Returns:
            Updated candidate data if successful, None otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/candidate/{candidate_id}"
            logger.info(f"Updating candidate {candidate_id} in Xano")
            response = self.session.patch(url, headers=self.headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated candidate {candidate_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating candidate {candidate_id} in Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating candidate: {e}")
            return None

    def delete_candidate(self, candidate_id: int) -> bool:
        """
        Delete a candidate from Xano
        
        Args:
            candidate_id: The candidate ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/candidate/{candidate_id}"
            logger.info(f"Deleting candidate {candidate_id} from Xano")
            response = self.session.delete(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully deleted candidate {candidate_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting candidate {candidate_id} from Xano: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting candidate: {e}")
            return False

    # ==================== COMPANY APIs ====================
    
    def get_companies(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all companies from Xano
        
        Returns:
            List of companies if successful, None otherwise
        """
        try:
            url = f"{XANO_COMPANY_API_URL}/company"
            logger.info("Fetching all companies from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            companies = response.json()
            logger.info(f"Successfully fetched {len(companies)} companies")
            return companies
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching companies from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching companies: {e}")
            return None

    def create_company(
        self,
        company_name: str,
        description: Optional[str] = None,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        logo: Optional[str] = None,
        related_user: Optional[int] = None,
        verified: bool = False,
        company_docs: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new company in Xano
        
        Args:
            company_name: Company name (required)
            description: Company description
            website: Company website URL
            industry: Industry type
            logo: Logo URL
            related_user: Related user ID
            verified: Whether company is verified
            company_docs: List of document URLs
            
        Returns:
            Created company data if successful, None otherwise
        """
        try:
            url = f"{XANO_COMPANY_API_URL}/company"
            payload = {
                "company_name": company_name,
                "Verified": verified,
            }
            
            # Add optional fields if provided
            if description:
                payload["description"] = description
            if website:
                payload["website"] = website
            if industry:
                payload["industry"] = industry
            if logo:
                payload["logo"] = logo
            if related_user:
                payload["related_user"] = related_user
            if company_docs:
                payload["Company_Docs"] = company_docs
                
            logger.info(f"Creating new company in Xano: {company_name}")
            response = self.session.post(url, headers=self.headers,json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created company: {result.get('id', 'unknown')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating company in Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating company: {e}")
            return None

    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific company by ID
        
        Args:
            company_id: The company ID
            
        Returns:
            Company data if found, None otherwise
        """
        try:
            url = f"{XANO_COMPANY_API_URL}/company/{company_id}"
            logger.info(f"Fetching company {company_id} from Xano")
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            company = response.json()
            logger.info(f"Successfully fetched company {company_id}")
            return company
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Company not found with ID: {company_id}")
            else:
                logger.error(f"HTTP error fetching company {company_id}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching company {company_id} from Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching company {company_id}: {e}")
            return None

    def update_company(
        self, company_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a company in Xano
        
        Args:
            company_id: The company ID
            data: Data to update
            
        Returns:
            Updated company data if successful, None otherwise
        """
        try:
            url = f"{XANO_COMPANY_API_URL}/company/{company_id}"
            logger.info(f"Updating company {company_id} in Xano")
            response = self.session.patch(url, headers=self.headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated company {company_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating company {company_id} in Xano: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating company: {e}")
            return None

    def delete_company(self, company_id: str) -> bool:
        """
        Delete a company from Xano
        
        Args:
            company_id: The company ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{XANO_COMPANY_API_URL}/company/{company_id}"
            logger.info(f"Deleting company {company_id} from Xano")
            response = self.session.delete(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Successfully deleted company {company_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting company {company_id} from Xano: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting company: {e}")
            return False

    def close(self):
        """Close the session"""
        self.session.close()


class XanoClientSingleton:
    """Singleton holder for XanoClient instance to avoid global variables."""
    _instance: XanoClient = None
    
    @classmethod
    def get_instance(cls) -> XanoClient:
        """Get or create the XanoClient singleton instance."""
        if cls._instance is None:
            cls._instance = XanoClient()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None


def get_xano_client() -> XanoClient:
    """
    Get or create Xano client instance using singleton pattern.
    
    Returns:
        XanoClient instance
    """
    return XanoClientSingleton.get_instance()

