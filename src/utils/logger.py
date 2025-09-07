"""
Logging utility for the expense tracker application.
Provides structured logging with different levels and contexts.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from src.config.settings import settings


class ExpenseTrackerLogger:
    """Custom logger for expense tracker with structured logging."""

    def __init__(self, name: str = "expense_tracker"):
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Setup logger with appropriate handlers and formatters."""
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Set log level from settings
        log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional - only if debug mode)
        if settings.debug_mode:
            log_file = Path("logs/expense_tracker.log")
            log_file.parent.mkdir(exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _log_with_context(self, level: int, message: str, context: Optional[Dict[str, Any]] = None, exc_info=None):
        """Log message with context information."""
        if context:
            # Format context as key=value pairs
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} | {context_str}"

        self.logger.log(level, message, exc_info=exc_info)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log_with_context(logging.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info=None):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, context, exc_info)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info=None):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, context, exc_info)

    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation."""
        context = {"operation": operation, "status": "started", **kwargs}
        self.info(f"Operation started: {operation}", context)

    def log_operation_success(self, operation: str, duration_ms: Optional[float] = None, **kwargs):
        """Log successful completion of an operation."""
        context = {"operation": operation, "status": "success", **kwargs}
        if duration_ms is not None:
            context["duration_ms"] = duration_ms
        self.info(f"Operation completed: {operation}", context)

    def log_operation_error(self, operation: str, error: Exception, **kwargs):
        """Log operation error."""
        context = {
            "operation": operation,
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
        self.error(f"Operation failed: {operation}", context, exc_info=error)

    def log_database_operation(self, operation: str, collection: str, document_id: Optional[str] = None, **kwargs):
        """Log database operations."""
        context = {"operation": operation, "collection": collection, **kwargs}
        if document_id:
            context["document_id"] = document_id
        self.debug(f"Database operation: {operation}", context)

    def log_ai_operation(self, provider: str, model: str, operation: str, **kwargs):
        """Log AI operations."""
        context = {
            "operation": operation,
            "provider": provider,
            "model": model,
            **kwargs
        }
        self.info(f"AI operation: {operation}", context)


# Global logger instance
logger = ExpenseTrackerLogger()


def get_logger(name: str) -> ExpenseTrackerLogger:
    """Get a logger instance with specific name."""
    return ExpenseTrackerLogger(name)


def log_execution_time(func):
    """Decorator to log function execution time."""
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        operation_name = f"{func.__module__}.{func.__name__}"

        logger.log_operation_start(operation_name)

        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000
            logger.log_operation_success(operation_name, duration_ms=duration)
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000
            logger.log_operation_error(operation_name, e, duration_ms=duration)
            raise
    return wrapper


def log_database_operation(collection: str, operation: str):
    """Decorator to log database operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()

            try:
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000

                # Extract document_id if available
                document_id = None
                if args and len(args) > 1:
                    # Assume first arg after self is document_id or data with id
                    first_arg = args[1]
                    if isinstance(first_arg, str):
                        document_id = first_arg
                    elif hasattr(first_arg, 'id') and first_arg.id:
                        document_id = first_arg.id

                logger.log_database_operation(
                    operation, collection, document_id,
                    duration_ms=duration, success=True
                )
                return result
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds() * 1000
                logger.log_database_operation(
                    operation, collection,
                    duration_ms=duration, success=False, error=str(e)
                )
                raise
        return wrapper
    return decorator
