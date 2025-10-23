"""
Utilities for logging and common functions
"""
import sys
from loguru import logger
from config import settings


def setup_logging():
    """Configure logging for the application"""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL
    )
    
    # Add file handler
    logger.add(
        "logs/cleo_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    return logger


def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    from datetime import datetime
    return datetime.utcnow().isoformat()


def detect_language(text: str) -> str:
    """
    Detect language from text (simple heuristic)
    In production, use a proper language detection library
    """
    # Simple heuristic: check for Spanish keywords
    spanish_keywords = [
        'hola', 'gracias', 'por favor', 'sí', 'no', 'trabajo',
        'empleo', 'aplicación', 'información', 'nombre'
    ]
    
    text_lower = text.lower()
    spanish_count = sum(1 for word in spanish_keywords if word in text_lower)
    
    if spanish_count >= 2:
        return 'es'
    return 'en'
