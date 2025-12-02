"""
Configuration management for Cleo RAG Agent
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_CHAT_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    # Vector Embedding Settings (Removed - using Xano API)
    # MILVUS_HOST: str = "localhost"
    # MILVUS_PORT: int = 19530
    # MILVUS_COLLECTION_NAME: str = "cleo_knowledge_base"
    # Vector Embedding Settings (Removed - using Xano API)
    # EMBEDDING_DIMENSION: int = 3072
    # CHUNK_SIZE: int = 512
    # CHUNK_OVERLAP: int = 102
    # Application Settings
    APP_NAME: str = "Cleo RAG Agent"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_SESSION_INACTIVE_MINUTES: int = 30
    # Supported Languages
    SUPPORTED_LANGUAGES: str = "en,es"
    DEFAULT_LANGUAGE: str = "en"
    # Fit Score Weights (Verification removed - out of scope, Personality added)
    QUALIFICATION_WEIGHT: float = 0.30
    EXPERIENCE_WEIGHT: float = 0.50
    PERSONALITY_WEIGHT: float = 0.20  # Analyzes conversation for personality traits
    # File Storage Paths
    DATA_DIR: str = "./data"
    UPLOADS_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    CSV_STORAGE_DIR: str = "./storage"
    # Report Configuration
    REPORT_FORMAT: str = "pdf"
    INCLUDE_FIT_SCORE_IN_REPORT: bool = False
    # Retrieval Configuration (Removed - using Xano API)
    # DEFAULT_RETRIEVAL_METHOD: str = "hybrid"
    # TOP_K_RESULTS: int = 5
    # SIMILARITY_THRESHOLD: float = 0.7
    # Verification API (Mock)
    VERIFICATION_API_ENABLED: bool = False
    VERIFICATION_API_URL: str = "https://api.example.com/verify"
    VERIFICATION_API_KEY: str = "mock_key"
    # Dashboard Configuration
    DASHBOARD_URL: str = "https://dashboard.example.com"
    DASHBOARD_API_KEY: str = "mock_dashboard_key"
    # Redis (optional - used for session management if enabled)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    # LangFuse Configuration
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = False
    # Pydantic v2 configuration for BaseSettings
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        # Allow extra env vars (so non-declared env vars won't raise ValidationError)
        "extra": "allow",
    }
# Global settings instance
settings = Settings()
def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        settings.DATA_DIR,
        os.path.join(settings.DATA_DIR, "raw"),
        os.path.join(settings.DATA_DIR, "processed"),
        settings.UPLOADS_DIR,
        settings.REPORTS_DIR,
        settings.CSV_STORAGE_DIR,
        "logs",
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    # Create .gitkeep files
    for directory in directories:
        gitkeep_path = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "a", encoding="utf-8"):
                pass

