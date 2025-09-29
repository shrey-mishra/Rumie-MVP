"""
Mock Sentry service for error tracking and monitoring
Provides structured logging fallback when Sentry DSN is not available
"""

import structlog
from typing import Dict, Any, Optional
import time
import json
from datetime import datetime

logger = structlog.get_logger("mock_sentry")

class MockSentryService:
    """Mock Sentry service for error tracking and monitoring"""
    
    def __init__(self):
        self.error_count = 0
        self.performance_metrics = []
        self.error_log = []
    
    def capture_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Capture and log exceptions with context"""
        self.error_count += 1
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "context": context or {},
            "error_id": f"mock_error_{self.error_count}"
        }
        
        self.error_log.append(error_data)
        
        logger.error("Exception captured by mock Sentry",
                   error_type=error_data["error_type"],
                   error_message=error_data["error_message"],
                   error_id=error_data["error_id"],
                   context=error_data["context"])
        
        return error_data["error_id"]
    
    def capture_message(self, message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
        """Capture and log messages with context"""
        message_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "level": level,
            "context": context or {},
            "message_id": f"mock_msg_{int(time.time())}"
        }
        
        logger.info("Message captured by mock Sentry",
                  message=message,
                  level=level,
                  message_id=message_data["message_id"],
                  context=context)
        
        return message_data["message_id"]
    
    def add_breadcrumb(self, message: str, category: str = "default", level: str = "info"):
        """Add breadcrumb for debugging context"""
        breadcrumb = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "category": category,
            "level": level
        }
        
        logger.debug("Breadcrumb added",
                    message=message,
                    category=category,
                    level=level)
    
    def set_user_context(self, user_id: str, email: str = None, **kwargs):
        """Set user context for error tracking"""
        user_context = {
            "user_id": user_id,
            "email": email,
            **kwargs
        }
        
        logger.info("User context set",
                   user_id=user_id,
                   email=email,
                   additional_context=kwargs)
    
    def set_tag(self, key: str, value: str):
        """Set tag for error categorization"""
        logger.debug("Tag set", key=key, value=value)
    
    def set_extra(self, key: str, value: Any):
        """Set extra data for error context"""
        logger.debug("Extra data set", key=key, value=str(value))
    
    def start_transaction(self, name: str, op: str = "http.server"):
        """Start a performance transaction"""
        transaction_id = f"mock_transaction_{int(time.time())}"
        transaction = {
            "transaction_id": transaction_id,
            "name": name,
            "operation": op,
            "start_time": time.time(),
            "status": "started"
        }
        
        self.performance_metrics.append(transaction)
        
        logger.info("Transaction started",
                   transaction_id=transaction_id,
                   name=name,
                   operation=op)
        
        return MockTransaction(transaction_id, self)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of captured errors"""
        error_types = {}
        for error in self.error_log:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": self.error_count,
            "error_types": error_types,
            "recent_errors": self.error_log[-10:] if self.error_log else [],
            "performance_transactions": len(self.performance_metrics)
        }
    
    def clear_logs(self):
        """Clear error and performance logs"""
        self.error_count = 0
        self.performance_metrics.clear()
        self.error_log.clear()
        logger.info("Mock Sentry logs cleared")

class MockTransaction:
    """Mock transaction for performance monitoring"""
    
    def __init__(self, transaction_id: str, sentry_service: MockSentryService):
        self.transaction_id = transaction_id
        self.sentry_service = sentry_service
        self.start_time = time.time()
        self.status = "started"
    
    def set_status(self, status: str):
        """Set transaction status"""
        self.status = status
        logger.debug("Transaction status updated",
                    transaction_id=self.transaction_id,
                    status=status)
    
    def set_tag(self, key: str, value: str):
        """Set transaction tag"""
        logger.debug("Transaction tag set",
                    transaction_id=self.transaction_id,
                    key=key,
                    value=value)
    
    def finish(self, status: str = "ok"):
        """Finish transaction"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Update transaction in performance metrics
        for transaction in self.sentry_service.performance_metrics:
            if transaction["transaction_id"] == self.transaction_id:
                transaction["end_time"] = end_time
                transaction["duration"] = duration
                transaction["status"] = status
                break
        
        logger.info("Transaction finished",
                   transaction_id=self.transaction_id,
                   duration=duration,
                   status=status)

# Global mock Sentry instance
mock_sentry = MockSentryService()

def capture_exception(exception: Exception, context: Optional[Dict[str, Any]] = None):
    """Global function to capture exceptions"""
    return mock_sentry.capture_exception(exception, context)

def capture_message(message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
    """Global function to capture messages"""
    return mock_sentry.capture_message(message, level, context)

def add_breadcrumb(message: str, category: str = "default", level: str = "info"):
    """Global function to add breadcrumbs"""
    mock_sentry.add_breadcrumb(message, category, level)

def set_user_context(user_id: str, email: str = None, **kwargs):
    """Global function to set user context"""
    mock_sentry.set_user_context(user_id, email, **kwargs)

def start_transaction(name: str, op: str = "http.server"):
    """Global function to start transactions"""
    return mock_sentry.start_transaction(name, op)
