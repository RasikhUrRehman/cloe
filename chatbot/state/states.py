"""
Conversation State Management
Defines state models for conversation tracking
"""
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from chatbot.utils.utils import (
    generate_session_id,
    get_current_timestamp,
    setup_logging,
)
logger = setup_logging()
class ConversationStage(Enum):
    """Enumeration of conversation stages"""
    ENGAGEMENT = "engagement"
    QUALIFICATION = "qualification"
    APPLICATION = "application"
    VERIFICATION = "verification"
    COMPLETED = "completed"
class EngagementState(BaseModel):
    """Engagement stage data model"""
    session_id: str = Field(default_factory=generate_session_id)
    start_time: str = Field(default_factory=get_current_timestamp)
    consent_given: bool = False
    company_id: Optional[str] = None
    job_id: Optional[str] = None
    job_details: Optional[Dict[str, Any]] = None  # Full job details from API
    language: str = "en"
    stage_completed: bool = False
    xano_session_id: Optional[int] = None  # Xano backend session ID
    candidate_id: Optional[int] = None  # Xano candidate ID
    
    class Config:
        use_enum_values = True
class QualificationState(BaseModel):
    """Qualification stage data model"""
    session_id: str
    age_confirmed: Optional[bool] = None
    work_authorization: Optional[bool] = None
    shift_preference: Optional[str] = None
    availability_start: Optional[str] = None
    transportation: Optional[bool] = None
    hours_preference: Optional[str] = None
    qualification_status: str = "pending"  # pending, qualified, disqualified
    stage_completed: bool = False
    class Config:
        use_enum_values = True
class ApplicationState(BaseModel):
    """Application stage data model"""
    session_id: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    previous_employer: Optional[str] = None
    job_title: Optional[str] = None
    years_experience: Optional[float] = None
    skills: Optional[str] = None  # Comma-separated
    references: Optional[str] = None
    communication_preference: Optional[str] = None
    application_status: str = "in_progress"  # in_progress, submitted
    stage_completed: bool = False
    class Config:
        use_enum_values = True
class VerificationState(BaseModel):
    """Verification stage data model"""
    session_id: str
    id_uploaded: bool = False
    id_type: Optional[str] = None
    verification_source: Optional[str] = None
    verification_status: str = "pending"  # pending, verified, failed
    timestamp_verified: Optional[str] = None
    data_signature: Optional[str] = None
    stage_completed: bool = False
    class Config:
        use_enum_values = True
class SessionState(BaseModel):
    """Complete session state"""
    session_id: str = Field(default_factory=generate_session_id)
    current_stage: ConversationStage = ConversationStage.ENGAGEMENT
    engagement: Optional[EngagementState] = None
    qualification: Optional[QualificationState] = None
    application: Optional[ApplicationState] = None
    verification: Optional[VerificationState] = None
    created_at: str = Field(default_factory=get_current_timestamp)
    updated_at: str = Field(default_factory=get_current_timestamp)
    class Config:
        use_enum_values = True
class StateManager:
    """Manages conversation state in memory"""
    def __init__(self, storage_dir: str = None):
        """Initialize StateManager - storage_dir parameter kept for backward compatibility"""
        pass

    def save_engagement(self, state: EngagementState):
        """No-op: State managed via Xano"""
        logger.debug(f"Engagement state for session {state.session_id} (managed via Xano)")

    def save_qualification(self, state: QualificationState):
        """No-op: State managed via Xano"""
        logger.debug(f"Qualification state for session {state.session_id} (managed via Xano)")

    def save_application(self, state: ApplicationState):
        """No-op: State managed via Xano"""
        logger.debug(f"Application state for session {state.session_id} (managed via Xano)")

    def save_verification(self, state: VerificationState):
        """No-op: State managed via Xano"""
        logger.debug(f"Verification state for session {state.session_id} (managed via Xano)")

    def save_session(self, state: SessionState):
        """No-op: Session state managed via Xano"""
        state.updated_at = get_current_timestamp()
        logger.debug(f"Session {state.session_id} at stage {state.current_stage} (managed via Xano)")

    def load_engagement(self, session_id: str) -> Optional[EngagementState]:
        """Load engagement state - returns None as state is managed via Xano"""
        return None

    def load_qualification(self, session_id: str) -> Optional[QualificationState]:
        """Load qualification state - returns None as state is managed via Xano"""
        return None

    def load_application(self, session_id: str) -> Optional[ApplicationState]:
        """Load application state - returns None as state is managed via Xano"""
        return None

    def load_verification(self, session_id: str) -> Optional[VerificationState]:
        """Load verification state - returns None as state is managed via Xano"""
        return None

    def get_all_sessions(self) -> list:
        """Get all sessions - returns empty list as sessions managed via Xano"""
        return []


def main():
    """Example usage of state management"""
    session = SessionState()
    engagement = EngagementState(
        session_id=session.session_id,
        consent_given=True,
        company_id="COMPANY123",
        job_id="JOB456",
        language="en",
        stage_completed=True,
    )
    session.engagement = engagement
    session.current_stage = ConversationStage.QUALIFICATION
    logger.info(f"Created session {session.session_id} at stage {session.current_stage}")

if __name__ == "__main__":
    main()


