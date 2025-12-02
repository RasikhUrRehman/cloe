"""
Conversation State Management
Defines state models and CSV-based persistence
"""
import csv
import os
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from chatbot.utils.config import settings
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
        self.qualification_file = os.path.join(
            self.storage_dir, "qualification_states.csv"
        )
        self.application_file = os.path.join(self.storage_dir, "application_states.csv")
        self.verification_file = os.path.join(
            self.storage_dir, "verification_states.csv"
        )
        self.session_file = os.path.join(self.storage_dir, "sessions.csv")
        self._initialize_csv_files()
    def _initialize_csv_files(self):
        """Create CSV files with headers if they don't exist"""
        # Engagement CSV
        if not os.path.exists(self.engagement_file):
            with open(self.engagement_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(EngagementState.model_fields.keys())
                )
                writer.writeheader()
        # Qualification CSV
        if not os.path.exists(self.qualification_file):
            with open(self.qualification_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(QualificationState.model_fields.keys())
                )
                writer.writeheader()
        # Application CSV
        if not os.path.exists(self.application_file):
            with open(self.application_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(ApplicationState.model_fields.keys())
                )
                writer.writeheader()
        # Verification CSV
        if not os.path.exists(self.verification_file):
            with open(self.verification_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(VerificationState.model_fields.keys())
                )
                writer.writeheader()
        # Session CSV
        if not os.path.exists(self.session_file):
            with open(self.session_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(SessionState.model_fields.keys())
                )
                writer.writeheader()
    def _update_csv_record(
        self,
        file_path: str,
        session_id: str,
        new_data: Dict[str, Any],
        fieldnames: List[str],
    ):
        """Update or insert a record in CSV file, avoiding duplicates"""
        import json
        import shutil
        import tempfile
        # Clean the data to match fieldnames and handle complex types
        cleaned_data = {}
        for field in fieldnames:
            if field in new_data:
                value = new_data[field]
                # Handle complex types (dict, list) by serializing to JSON
                if isinstance(value, (dict, list)):
                    cleaned_data[field] = json.dumps(value) if value is not None else ""
                # Handle None values
                elif value is None:
                    cleaned_data[field] = ""
                # Handle boolean values
                elif isinstance(value, bool):
                    cleaned_data[field] = str(value)
                else:
                    cleaned_data[field] = str(value)
            else:
                cleaned_data[field] = ""
        # Read existing records
        existing_records = []
        record_found = False
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["session_id"] == session_id:
                        # Update existing record
                        existing_records.append(cleaned_data)
                        record_found = True
                    else:
                        # Clean existing row to only include current fieldnames
                        cleaned_row = {}
                        for field in fieldnames:
                            cleaned_row[field] = row.get(field, "")
                        existing_records.append(cleaned_row)
        # If record not found, add it
        if not record_found:
            existing_records.append(cleaned_data)
        # Write all records back to file with extrasaction='ignore' to handle any extra fields
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8", delete=False
        ) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(existing_records)
            temp_file_path = temp_file.name
        # Replace original file with updated file
        shutil.move(temp_file_path, file_path)
    def save_engagement(self, state: EngagementState):
        """Save or update engagement state to CSV"""
        fieldnames = list(EngagementState.model_fields.keys())
        self._update_csv_record(
            self.engagement_file, state.session_id, state.model_dump(), fieldnames
        )
        logger.info(f"Saved engagement state for session {state.session_id}")
    def save_qualification(self, state: QualificationState):
        """Save or update qualification state to CSV"""
        fieldnames = list(QualificationState.model_fields.keys())
        self._update_csv_record(
            self.qualification_file, state.session_id, state.model_dump(), fieldnames
        )
        logger.info(f"Saved qualification state for session {state.session_id}")
    def save_application(self, state: ApplicationState):
        """Save or update application state to CSV"""
        fieldnames = list(ApplicationState.model_fields.keys())
        self._update_csv_record(
            self.application_file, state.session_id, state.model_dump(), fieldnames
        )
        logger.info(f"Saved application state for session {state.session_id}")
    def save_verification(self, state: VerificationState):
        """Save or update verification state to CSV"""
        fieldnames = list(VerificationState.model_fields.keys())
        self._update_csv_record(
            self.verification_file, state.session_id, state.model_dump(), fieldnames
        )
        logger.info(f"Saved verification state for session {state.session_id}")
    def save_session(self, state: SessionState):
        """Save complete session state"""
        state.updated_at = get_current_timestamp()
        # Save individual states (will update existing records)
        if state.engagement:
            self.save_engagement(state.engagement)
        if state.qualification:
            self.save_qualification(state.qualification)
        if state.application:
            self.save_application(state.application)
        if state.verification:
            self.save_verification(state.verification)
        # Save session metadata
        session_dict = {
            "session_id": state.session_id,
            "current_stage": (
                state.current_stage.value
                if isinstance(state.current_stage, ConversationStage)
                else state.current_stage
            ),
            "engagement_complete": (
                state.engagement.stage_completed if state.engagement else False
            ),
            "qualification_complete": (
                state.qualification.stage_completed if state.qualification else False
            ),
            "application_complete": (
                state.application.stage_completed if state.application else False
            ),
            "ready_for_verification": (
                state.application.stage_completed if state.application else False
            ),
            "created_at": state.created_at,
            "updated_at": state.updated_at,
        }
        # Update sessions CSV with new schema
        fieldnames = [
            "session_id",
            "current_stage",
            "engagement_complete",
            "qualification_complete",
            "application_complete",
            "ready_for_verification",
            "created_at",
            "updated_at",
        ]
        self._update_csv_record(
            self.session_file, state.session_id, session_dict, fieldnames
        )
        logger.info(f"Saved session {state.session_id} at stage {state.current_stage}")
    def load_engagement(self, session_id: str) -> Optional[EngagementState]:
        """Load engagement state from CSV"""
        if not os.path.exists(self.engagement_file):
            return None
        import json
        with open(self.engagement_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["session_id"] == session_id:
                    # Clean the row data
                    clean_row = {}
                    for key, value in row.items():
                        if key in EngagementState.model_fields:
                            # Handle empty strings as None
                            if value == "":
                                clean_row[key] = None
                            # Handle boolean fields
                            elif key in ["consent_given", "stage_completed"]:
                                clean_row[key] = value.lower() == "true"
                            # Handle job_details JSON field
                            elif key == "job_details" and value:
                                try:
                                    clean_row[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    clean_row[key] = None
                            else:
                                clean_row[key] = value
                    return EngagementState(**clean_row)
        return None
    def load_qualification(self, session_id: str) -> Optional[QualificationState]:
        """Load qualification state from CSV"""
        if not os.path.exists(self.qualification_file):
            return None
        with open(self.qualification_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["session_id"] == session_id:
                    # Clean the row data
                    clean_row = {}
                    for key, value in row.items():
                        if key in QualificationState.model_fields:
                            # Handle empty strings as None
                            if value == "":
                                clean_row[key] = None
                            # Handle boolean fields
                            elif key in [
                                "age_confirmed",
                                "work_authorization",
                                "transportation",
                                "stage_completed",
                            ]:
                                clean_row[key] = (
                                    value.lower() == "true" if value else None
                                )
                            else:
                                clean_row[key] = value
                    return QualificationState(**clean_row)
        return None
    def load_application(self, session_id: str) -> Optional[ApplicationState]:
        """Load application state from CSV"""
        if not os.path.exists(self.application_file):
            return None
        with open(self.application_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["session_id"] == session_id:
                    # Clean the row data
                    clean_row = {}
                    for key, value in row.items():
                        if key in ApplicationState.model_fields:
                            # Handle empty strings as None
                            if value == "":
                                clean_row[key] = None
                            # Handle boolean fields
                            elif key in ["stage_completed"]:
                                clean_row[key] = (
                                    value.lower() == "true" if value else False
                                )
                            # Handle numeric fields
                            elif key == "years_experience" and value:
                                try:
                                    clean_row[key] = float(value)
                                except ValueError:
                                    clean_row[key] = None
                            else:
                                clean_row[key] = value
                    return ApplicationState(**clean_row)
        return None
    def load_verification(self, session_id: str) -> Optional[VerificationState]:
        """Load verification state from CSV"""
        if not os.path.exists(self.verification_file):
            return None
        with open(self.verification_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["session_id"] == session_id:
                    # Clean the row data
                    clean_row = {}
                    for key, value in row.items():
                        if key in VerificationState.model_fields:
                            # Handle empty strings as None
                            if value == "":
                                clean_row[key] = None
                            # Handle boolean fields
                            elif key in ["id_uploaded", "stage_completed"]:
                                clean_row[key] = (
                                    value.lower() == "true" if value else False
                                )
                            else:
                                clean_row[key] = value
                    return VerificationState(**clean_row)
        return None
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all session records"""
        sessions = []
        if not os.path.exists(self.session_file):
            return sessions
        with open(self.session_file, "r", encoding="utf-8") as f:
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
        stage_completed=True,
    )
    session.engagement = engagement
    session.current_stage = ConversationStage.QUALIFICATION
    manager.save_session(session)

if __name__ == "__main__":
    main()

