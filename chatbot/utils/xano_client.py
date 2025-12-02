"""
Xano API Client
Handles all interactions with Xano backend APIs
"""
from typing import Any, Dict, Optional
import requests
from chatbot.utils.utils import setup_logging
logger = setup_logging()
# Xano API Base URLs
XANO_JOB_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb"
XANO_CHAT_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:wnnakKFu"
XANO_SESSION_API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:mYiFh-E2"
class XanoClient:
    """Client for interacting with Xano APIs"""
    def __init__(self, timeout: int = 10):
        """
        Initialize Xano API client
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
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
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            job = response.json()
            logger.info(
                f"Successfully fetched job: {job.get('job_title', 'Unknown')} (ID: {job_id})"
            )
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
            logger.info(
                f"Posting message to Xano session {session_id} from {msg_creator}"
            )
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
            logger.error(
                f"Invalid status: {status}. Must be one of {valid_statuses}"
            )
            return None
        try:
            url = f"{XANO_SESSION_API_URL}/session/{session_id}"
            payload = {"session_id": session_id, "Status": status}
            logger.info(f"Updating Xano session {session_id} status to {status}")
            response = self.session.patch(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated session {session_id} status to {status}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error updating Xano session {session_id} status: {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating session status: {e}")
            return None
    def create_session(self, initial_status: str = "Started") -> Optional[Dict[str, Any]]:
        """
        Create a new session in Xano
        Args:
            initial_status: Initial session status (default: "Started")
        Returns:
            Session data if successful, None otherwise
        """
        try:
            url = f"{XANO_SESSION_API_URL}/session"
            payload = {"Status": initial_status}
            logger.info(f"Creating new Xano session with status {initial_status}")
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created Xano session: {result.get('id', 'unknown')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Xano session: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating session: {e}")
            return None
    def close(self):
        """Close the session"""
        self.session.close()
# Global client instance
_xano_client = None
def get_xano_client() -> XanoClient:
    """
    Get or create global Xano client instance
    Returns:
        XanoClient instance
    """
    global _xano_client
    if _xano_client is None:
        _xano_client = XanoClient()
    return _xano_client

