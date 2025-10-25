"""
Conversation State Management
Defines state models and CSV-based persistence
"""
import os
import csv
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from chatbot.utils.config import settings
from chatbot.utils.utils import setup_logging, generate_session_id, get_current_timestamp

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
    language: str = "en"
    stage_completed: bool = False
    
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
    """Manages conversation state persistence using CSV files"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or settings.CSV_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # CSV file paths
        self.engagement_file = os.path.join(self.storage_dir, "engagement_states.csv")
        self.qualification_file = os.path.join(self.storage_dir, "qualification_states.csv")
        self.application_file = os.path.join(self.storage_dir, "application_states.csv")
        self.verification_file = os.path.join(self.storage_dir, "verification_states.csv")
        self.session_file = os.path.join(self.storage_dir, "sessions.csv")
        
        self._initialize_csv_files()
    
    def _initialize_csv_files(self):
        """Create CSV files with headers if they don't exist"""
        # Engagement CSV
        if not os.path.exists(self.engagement_file):
            with open(self.engagement_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(EngagementState.model_fields.keys()))
                writer.writeheader()
        
        # Qualification CSV
        if not os.path.exists(self.qualification_file):
            with open(self.qualification_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(QualificationState.model_fields.keys()))
                writer.writeheader()
        
        # Application CSV
        if not os.path.exists(self.application_file):
            with open(self.application_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(ApplicationState.model_fields.keys()))
                writer.writeheader()
        
        # Verification CSV
        if not os.path.exists(self.verification_file):
            with open(self.verification_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(VerificationState.model_fields.keys()))
                writer.writeheader()
        
        # Session CSV
        if not os.path.exists(self.session_file):
            with open(self.session_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(SessionState.model_fields.keys()))
                writer.writeheader()
    
    def save_engagement(self, state: EngagementState):
        """Save engagement state to CSV"""
        with open(self.engagement_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(EngagementState.model_fields.keys()))
            writer.writerow(state.model_dump())
        logger.info(f"Saved engagement state for session {state.session_id}")
    
    def save_qualification(self, state: QualificationState):
        """Save qualification state to CSV"""
        with open(self.qualification_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(QualificationState.model_fields.keys()))
            writer.writerow(state.model_dump())
        logger.info(f"Saved qualification state for session {state.session_id}")
    
    def save_application(self, state: ApplicationState):
        """Save application state to CSV"""
        with open(self.application_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(ApplicationState.model_fields.keys()))
            writer.writerow(state.model_dump())
        logger.info(f"Saved application state for session {state.session_id}")
    
    def save_verification(self, state: VerificationState):
        """Save verification state to CSV"""
        with open(self.verification_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(VerificationState.model_fields.keys()))
            writer.writerow(state.model_dump())
        logger.info(f"Saved verification state for session {state.session_id}")
    
    def save_session(self, state: SessionState):
        """Save complete session state"""
        state.updated_at = get_current_timestamp()
        
        # Save individual states
        if state.engagement:
            self.save_engagement(state.engagement)
        if state.qualification:
            self.save_qualification(state.qualification)
        if state.application:
            self.save_application(state.application)
        if state.verification:
            self.save_verification(state.verification)
        
        # Save session metadata
        with open(self.session_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(SessionState.model_fields.keys()))
            # Convert state to dict and handle nested objects
            session_dict = {
                'session_id': state.session_id,
                'current_stage': state.current_stage.value if isinstance(state.current_stage, ConversationStage) else state.current_stage,
                'engagement': str(state.engagement is not None),
                'qualification': str(state.qualification is not None),
                'application': str(state.application is not None),
                'verification': str(state.verification is not None),
                'created_at': state.created_at,
                'updated_at': state.updated_at
            }
            writer.writerow(session_dict)
        
        logger.info(f"Saved session {state.session_id} at stage {state.current_stage}")
    
    def load_engagement(self, session_id: str) -> Optional[EngagementState]:
        """Load engagement state from CSV"""
        if not os.path.exists(self.engagement_file):
            return None
        
        with open(self.engagement_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    return EngagementState(**row)
        return None
    
    def load_qualification(self, session_id: str) -> Optional[QualificationState]:
        """Load qualification state from CSV"""
        if not os.path.exists(self.qualification_file):
            return None
        
        with open(self.qualification_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    return QualificationState(**row)
        return None
    
    def load_application(self, session_id: str) -> Optional[ApplicationState]:
        """Load application state from CSV"""
        if not os.path.exists(self.application_file):
            return None
        
        with open(self.application_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    return ApplicationState(**row)
        return None
    
    def load_verification(self, session_id: str) -> Optional[VerificationState]:
        """Load verification state from CSV"""
        if not os.path.exists(self.verification_file):
            return None
        
        with open(self.verification_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    return VerificationState(**row)
        return None
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all session records"""
        sessions = []
        if not os.path.exists(self.session_file):
            return sessions
        
        with open(self.session_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sessions = list(reader)
        
        return sessions


def main():
    """Example usage of state management"""
    from chatbot.utils.config import ensure_directories
    ensure_directories()
    
    manager = StateManager()
    
    # Create a new session
    session = SessionState()
    
    # Engagement stage
    engagement = EngagementState(
        session_id=session.session_id,
        consent_given=True,
        company_id="COMPANY123",
        job_id="JOB456",
        language="en",
        stage_completed=True
    )
    session.engagement = engagement
    session.current_stage = ConversationStage.QUALIFICATION
    
    manager.save_session(session)
    print(f"Created session: {session.session_id}")


if __name__ == "__main__":
    main()
