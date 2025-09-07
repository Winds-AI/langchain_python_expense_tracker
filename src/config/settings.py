"""
Pydantic settings and configuration helpers.

Loads secrets from Streamlit's st.secrets when available, otherwise
falls back to environment variables.
"""

from __future__ import annotations

from typing import Optional, List

import os

try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover - streamlit not always present in non-app contexts
    st = None  # type: ignore

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    openai_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    mongodb_uri: Optional[str] = Field(default=None)
    langsmith_api_key: Optional[str] = Field(default=None)

    default_ai_provider: str = Field(default="openai")
    default_ai_model: str = Field(default="gpt-5-mini")

    # Configurable model lists
    openai_models: List[str] = Field(default_factory=lambda: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-5-mini"])
    gemini_models: List[str] = Field(default_factory=lambda: ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash", "gemini-1.5-pro"])

    app_title: str = Field(default="Expense Tracker")
    app_icon: str = Field(default="💰")
    log_level: str = Field(default="INFO")
    debug_mode: bool = Field(default=False)

    @staticmethod
    def _read_secret(name: str) -> Optional[str]:
        # Prefer Streamlit secrets if available
        if st is not None:
            try:
                # Try case-insensitive match with st.secrets
                if name.lower() in st.secrets:
                    value = st.secrets[name.lower()]
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                elif name in st.secrets:  # Fallback to exact match
                    value = st.secrets[name]
                    if isinstance(value, str) and value.strip():
                        return value.strip()
            except Exception as e:
                print(f"Error accessing st.secrets[{name}]: {e}")
        # Fallback to environment variables
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _read_secret_list(name: str) -> Optional[List[str]]:
        # Prefer Streamlit secrets if available
        if st is not None:
            try:
                # Try case-insensitive match with st.secrets
                if name.lower() in st.secrets:
                    value = st.secrets[name.lower()]
                    if isinstance(value, list):
                        return value
                elif name in st.secrets:  # Fallback to exact match
                    value = st.secrets[name]
                    if isinstance(value, list):
                        return value
            except Exception as e:
                print(f"Error accessing st.secrets[{name}]: {e}")
        # Fallback to environment variables (as comma-separated string)
        value = os.getenv(name)
        if value is not None and value.strip():
            return [item.strip() for item in value.split(",") if item.strip()]
        return None

    @classmethod
    def load(cls) -> "AppSettings":
        return cls(
            openai_api_key=cls._read_secret("OPENAI_API_KEY"),
            google_api_key=cls._read_secret("GOOGLE_API_KEY"),
            mongodb_uri=cls._read_secret("MONGODB_URI"),
            langsmith_api_key=cls._read_secret("LANGSMITH_API_KEY"),
            default_ai_provider=cls._read_secret("DEFAULT_AI_PROVIDER") or "openai",
            default_ai_model=cls._read_secret("DEFAULT_AI_MODEL") or "gpt-5-mini",
            openai_models=cls._read_secret_list("OPENAI_MODELS") or ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-5-mini"],
            gemini_models=cls._read_secret_list("GEMINI_MODELS") or ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash", "gemini-1.5-pro"],
            app_title=cls._read_secret("APP_TITLE") or "Expense Tracker",
            app_icon=cls._read_secret("APP_ICON") or "💰",
            log_level=cls._read_secret("LOG_LEVEL") or "INFO",
            debug_mode=cls._read_secret("DEBUG_MODE") == "true",
        )


settings = AppSettings.load()

# Pydantic settings (secrets/env)
