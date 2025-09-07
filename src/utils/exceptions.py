"""
Custom exceptions for the expense tracker application.
Provides structured error handling with specific exception types for different scenarios.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class ExpenseTrackerError(Exception):
    """Base exception class for all expense tracker errors."""

    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Database Exceptions
class DatabaseError(ExpenseTrackerError):
    """Base class for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed", details: Dict[str, Any] = None):
        super().__init__(message, "DB_CONNECTION_ERROR", details)


class DuplicateKeyError(DatabaseError):
    """Raised when attempting to insert a document with duplicate key."""

    def __init__(self, field: str, value: Any, collection: str, details: Dict[str, Any] = None):
        message = f"Duplicate {field} '{value}' in collection '{collection}'"
        error_details = {"field": field, "value": value, "collection": collection}
        if details:
            error_details.update(details)
        super().__init__(message, "DUPLICATE_KEY_ERROR", error_details)


class DocumentNotFoundError(DatabaseError):
    """Raised when a requested document is not found."""

    def __init__(self, document_id: str, collection: str, details: Dict[str, Any] = None):
        message = f"Document with ID '{document_id}' not found in collection '{collection}'"
        error_details = {"document_id": document_id, "collection": collection}
        if details:
            error_details.update(details)
        super().__init__(message, "DOCUMENT_NOT_FOUND", error_details)


# Validation Exceptions
class ValidationError(ExpenseTrackerError):
    """Base class for validation-related errors."""
    pass


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(self, field: str, value: Any, reason: str, details: Dict[str, Any] = None):
        message = f"Invalid input for field '{field}': {reason}"
        error_details = {"field": field, "value": value, "reason": reason}
        if details:
            error_details.update(details)
        super().__init__(message, "INVALID_INPUT", error_details)


class MissingRequiredFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field: str, details: Dict[str, Any] = None):
        message = f"Required field '{field}' is missing"
        error_details = {"field": field}
        if details:
            error_details.update(details)
        super().__init__(message, "MISSING_REQUIRED_FIELD", error_details)


# Business Logic Exceptions
class BusinessLogicError(ExpenseTrackerError):
    """Base class for business logic errors."""
    pass


class CategoryNotFoundError(BusinessLogicError):
    """Raised when a category is not found."""

    def __init__(self, category_id: str, details: Dict[str, Any] = None):
        message = f"Category with ID '{category_id}' not found"
        error_details = {"category_id": category_id}
        if details:
            error_details.update(details)
        super().__init__(message, "CATEGORY_NOT_FOUND", error_details)


class CategoryAlreadyExistsError(BusinessLogicError):
    """Raised when attempting to create a category that already exists."""

    def __init__(self, name: str, details: Dict[str, Any] = None):
        message = f"Category with name '{name}' already exists"
        error_details = {"category_name": name}
        if details:
            error_details.update(details)
        super().__init__(message, "CATEGORY_ALREADY_EXISTS", error_details)


class SubcategoryNotFoundError(BusinessLogicError):
    """Raised when a subcategory is not found."""

    def __init__(self, category_id: str, subcategory_name: str, details: Dict[str, Any] = None):
        message = f"Subcategory '{subcategory_name}' not found in category '{category_id}'"
        error_details = {"category_id": category_id, "subcategory_name": subcategory_name}
        if details:
            error_details.update(details)
        super().__init__(message, "SUBCATEGORY_NOT_FOUND", error_details)


class SubcategoryAlreadyExistsError(BusinessLogicError):
    """Raised when attempting to create a subcategory that already exists."""

    def __init__(self, category_id: str, subcategory_name: str, details: Dict[str, Any] = None):
        message = f"Subcategory '{subcategory_name}' already exists in category '{category_id}'"
        error_details = {"category_id": category_id, "subcategory_name": subcategory_name}
        if details:
            error_details.update(details)
        super().__init__(message, "SUBCATEGORY_ALREADY_EXISTS", error_details)


# AI/Model Exceptions
class AIError(ExpenseTrackerError):
    """Base class for AI-related errors."""
    pass


class APIKeyNotConfiguredError(AIError):
    """Raised when API key is not configured."""

    def __init__(self, provider: str, details: Dict[str, Any] = None):
        message = f"API key not configured for provider '{provider}'"
        error_details = {"provider": provider}
        if details:
            error_details.update(details)
        super().__init__(message, "API_KEY_NOT_CONFIGURED", error_details)


class ModelNotAvailableError(AIError):
    """Raised when requested AI model is not available."""

    def __init__(self, provider: str, model: str, details: Dict[str, Any] = None):
        message = f"Model '{model}' not available for provider '{provider}'"
        error_details = {"provider": provider, "model": model}
        if details:
            error_details.update(details)
        super().__init__(message, "MODEL_NOT_AVAILABLE", error_details)


class AIProcessingError(AIError):
    """Raised when AI processing fails."""

    def __init__(self, provider: str, model: str, original_error: str, details: Dict[str, Any] = None):
        message = f"AI processing failed for {provider}/{model}: {original_error}"
        error_details = {"provider": provider, "model": model, "original_error": original_error}
        if details:
            error_details.update(details)
        super().__init__(message, "AI_PROCESSING_ERROR", error_details)


# Configuration Exceptions
class ConfigurationError(ExpenseTrackerError):
    """Base class for configuration-related errors."""
    pass


class SettingsNotFoundError(ConfigurationError):
    """Raised when application settings are not found."""

    def __init__(self, user_id: Optional[str] = None, details: Dict[str, Any] = None):
        message = "Application settings not found"
        if user_id:
            message += f" for user '{user_id}'"
        error_details = {"user_id": user_id}
        if details:
            error_details.update(details)
        super().__init__(message, "SETTINGS_NOT_FOUND", error_details)


# Utility functions for error handling
def handle_database_error(error: Exception, operation: str, collection: str) -> ExpenseTrackerError:
    """
    Convert database exceptions to application-specific errors.

    Args:
        error: The original database exception
        operation: The operation being performed (e.g., "insert", "find", "update")
        collection: The collection name

    Returns:
        ExpenseTrackerError: Application-specific error
    """
    error_str = str(error).lower()

    if "duplicate key" in error_str or "e11000" in error_str:
        # Extract field information from MongoDB duplicate key error
        if "name" in error_str:
            return DuplicateKeyError("name", "unknown", collection)
        else:
            return DuplicateKeyError("unknown", "unknown", collection)

    elif "not found" in error_str or "does not exist" in error_str:
        return DocumentNotFoundError("unknown", collection)

    else:
        return DatabaseError(f"Database operation '{operation}' failed on collection '{collection}': {str(error)}",
                           "DB_OPERATION_FAILED",
                           {"operation": operation, "collection": collection, "original_error": str(error)})


def safe_operation(operation_name: str):
    """
    Decorator for safe database operations with error handling.

    Args:
        operation_name: Name of the operation for logging

    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Re-raise application-specific errors as-is
                if isinstance(e, ExpenseTrackerError):
                    raise
                # Convert other exceptions to application errors
                raise ExpenseTrackerError(f"Operation '{operation_name}' failed: {str(e)}",
                                        "OPERATION_FAILED",
                                        {"operation": operation_name, "original_error": str(e)})
        return wrapper
    return decorator
