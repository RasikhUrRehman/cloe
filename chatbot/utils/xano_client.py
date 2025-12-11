"""
Xano API Client
Handles all interactions with Xano backend APIs
"""
from typing import Any, Dict, List, Optional
import requests
from chatbot.utils.utils import setup_logging

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
        
        # Login to get auth token
        self._login(email, password)

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
        phone: Optional[int] = None,
        score: Optional[float] = None,
        report_pdf: Optional[str] = None,
        job_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: str = "Short Listed",
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
        application: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new candidate in Xano
        
        Args:
            name: Candidate name (required)
            email: Candidate email
            phone: Candidate phone number
            score: Fit score
            report_pdf: PDF report path
            job_id: Associated job ID
            company_id: Associated company ID
            status: Application status
            user_id: User ID
            session_id: Session ID
            application: Application file data
            
        Returns:
            Created candidate data if successful, None otherwise
        """
        try:
            url = f"{XANO_CANDIDATE_API_URL}/candidate"
            payload = {
                "Name": name,
                "Status": status,
            }
            
            # Add optional fields if provided
            if email:
                payload["Email"] = email
            if phone:
                payload["Phone"] = phone
            if score is not None:
                payload["Score"] = score
            if report_pdf:
                payload["Report_pdf"] = report_pdf
            if job_id:
                payload["job_id"] = job_id
            if company_id:
                payload["company_id"] = company_id
            if user_id:
                payload["user_id"] = user_id
            if session_id:
                payload["session_id"] = session_id
            if application:
                payload["Application"] = application
                
            logger.info(f"Creating new candidate in Xano: {name}")
            logger.debug(f"Candidate payload: {payload}")
            response = self.session.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
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

