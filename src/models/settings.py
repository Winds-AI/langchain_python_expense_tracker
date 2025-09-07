"""
Pydantic models for application settings and AI provider configurations.
Provides type-safe structures with validation for settings management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator

from src.config.settings import settings


ProviderName = Literal["openai", "gemini"]
ModelName = str  # Flexible model name type


class AIProviderSettings(BaseModel):
    """Settings for AI providers and their models."""
    provider: ProviderName
    model: ModelName
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=4096)
    api_key_configured: bool = Field(default=False)

    @field_validator('model')
    @classmethod
    def validate_model_name(cls, v, info):
        """Validate model name based on provider."""
        provider = info.data.get('provider')
        if provider:
            if provider == "openai":
                valid_models = settings.openai_models
                if v not in valid_models:
                    raise ValueError(f"Invalid OpenAI model. Must be one of: {', '.join(valid_models)}")
            elif provider == "gemini":
                valid_models = settings.gemini_models
                if v not in valid_models:
                    raise ValueError(f"Invalid Gemini model. Must be one of: {', '.join(valid_models)}")
        return v


class AppSettingsModel(BaseModel):
    """Complete application settings model."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = Field(None)  # For future multi-user support

    # AI Settings
    ai_provider: ProviderName = Field(default="openai")
    ai_model: ModelName = Field(default="gpt-5-mini")
    ai_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    ai_max_tokens: Optional[int] = Field(None, gt=0, le=4096)

    # UI Settings
    theme: Literal["light", "dark", "auto"] = Field(default="auto")
    currency: str = Field(default="INR", pattern=r'^[A-Z]{3}$')
    date_format: str = Field(default="DD/MM/YYYY")
    items_per_page: int = Field(default=10, gt=0, le=100)

    # Notification Settings
    enable_notifications: bool = Field(default=True)
    enable_sound: bool = Field(default=False)

    # Privacy Settings
    enable_analytics: bool = Field(default=False)
    enable_error_reporting: bool = Field(default=True)

    # System Settings
    debug_mode: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code format."""
        if len(v) != 3 or not v.isalpha() or not v.isupper():
            raise ValueError("Currency must be a 3-letter uppercase code (e.g., USD, EUR, INR)")
        return v

    @field_validator('date_format')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format string."""
        valid_formats = ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD", "DD-MM-YYYY"]
        if v not in valid_formats:
            raise ValueError(f"Invalid date format. Must be one of: {', '.join(valid_formats)}")
        return v

    def dict_for_db(self) -> Dict[str, Any]:
        """Convert to dict format suitable for MongoDB storage."""
        data = self.model_dump(by_alias=True, exclude_unset=True)
        if 'id' in data and data['id'] is None:
            del data['id']  # Remove None _id for new documents
        return data

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "validate_by_name": True
    }


class SettingsCreate(BaseModel):
    """Model for creating new settings."""
    ai_provider: ProviderName = "openai"
    ai_model: ModelName = "gpt-5-mini"
    ai_temperature: float = 0.0
    ai_max_tokens: Optional[int] = None
    theme: Literal["light", "dark", "auto"] = "auto"
    currency: str = "INR"
    date_format: str = "DD/MM/YYYY"
    items_per_page: int = 10
    enable_notifications: bool = True
    enable_sound: bool = False
    enable_analytics: bool = False
    enable_error_reporting: bool = True
    debug_mode: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class SettingsUpdate(BaseModel):
    """Model for updating existing settings."""
    ai_provider: Optional[ProviderName] = None
    ai_model: Optional[ModelName] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None
    theme: Optional[Literal["light", "dark", "auto"]] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    items_per_page: Optional[int] = None
    enable_notifications: Optional[bool] = None
    enable_sound: Optional[bool] = None
    enable_analytics: Optional[bool] = None
    enable_error_reporting: Optional[bool] = None
    debug_mode: Optional[bool] = None
    log_level: Optional[Literal["DEBUG", "INFO", "WARNING", "ERROR"]] = None


class ProviderModels(BaseModel):
    """Available models for each provider."""
    openai: List[str] = Field(default_factory=lambda: settings.openai_models)
    gemini: List[str] = Field(default_factory=lambda: settings.gemini_models)
