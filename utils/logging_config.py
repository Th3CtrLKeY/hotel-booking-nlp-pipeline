"""
Structured Logging Configuration

GDPR-safe logging that never logs raw email content or PII.
Logs structured JSON for easy parsing and monitoring.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredLogger:
    """
    JSON-structured logger with PII protection.
    
    Principles:
    - Never log raw email content
    - Never log guest names, email addresses, phone numbers
    - Log processing metadata, errors, and performance metrics
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Args:
            name: Logger name (usually __name__)
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def log_processing_start(self, email_id: str):
        """Log start of email processing."""
        self.logger.info(json.dumps({
            "event": "processing_start",
            "email_id": email_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_processing_complete(
        self,
        email_id: str,
        processing_time_ms: float,
        intent: str
    ):
        """Log successful processing completion."""
        self.logger.info(json.dumps({
            "event": "processing_complete",
            "email_id": email_id,
            "processing_time_ms": processing_time_ms,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_error(
        self,
        email_id: str,
        error_type: str,
        error_message: str,
        stage: Optional[str] = None
    ):
        """
        Log processing error without PII.
        
        Args:
            email_id: Email identifier
            error_type: Type of error (e.g., "parsing_error")
            error_message: Generic error message (NO email content)
            stage: Pipeline stage where error occurred
        """
        self.logger.error(json.dumps({
            "event": "processing_error",
            "email_id": email_id,
            "error_type": error_type,
            "error_message": error_message,
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_warning(self, email_id: str, warning_type: str, message: str):
        """Log non-fatal warning."""
        self.logger.warning(json.dumps({
            "event": "warning",
            "email_id": email_id,
            "warning_type": warning_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_performance(self, stage: str, duration_ms: float):
        """Log stage-level performance metrics."""
        self.logger.debug(json.dumps({
            "event": "performance",
            "stage": stage,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }))


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat()
        }
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> StructuredLogger:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        StructuredLogger instance
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    level = level_map.get(log_level.upper(), logging.INFO)
    return StructuredLogger("hotel_email_parser", level=level)
