"""
Pydantic settings and configuration helpers.

Loads secrets from Streamlit's st.secrets when available, otherwise
falls back to environment variables.
"""

from __future__ import annotations

from typing import Optional, List, Any, Mapping, Sequence, Tuple

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
    langsmith_endpoint: Optional[str] = Field(default=None)
    langsmith_project: Optional[str] = Field(default=None)
    langsmith_tracing: bool = Field(default=False)

    default_ai_provider: str = Field(default="openai")
    default_ai_model: str = Field(default="gpt-5-mini")

    # Configurable model lists
    openai_models: List[str] = Field(default_factory=lambda: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-5-mini"])
    gemini_models: List[str] = Field(default_factory=lambda: ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash", "gemini-1.5-pro"])

    app_title: str = Field(default="Expense Tracker")
    app_icon: str = Field(default="💰")
    log_level: str = Field(default="INFO")
    debug_mode: bool = Field(default=False)

    # Admin auth (PBKDF2-SHA256 hex-encoded values)
    admin_password_hash: Optional[str] = Field(default=None)
    admin_password_salt: Optional[str] = Field(default=None)
    # Optional plaintext fallback (only used if hash+salt are absent)
    admin_password_plain: Optional[str] = Field(default=None)

    @staticmethod
    def _get_from_secrets(path: Sequence[str]) -> Optional[Any]:
        """Traverse st.secrets with a path of keys (case-insensitive at each level)."""
        if st is None:
            return None
        try:
            node: Any = st.secrets  # type: ignore
            for key in path:
                if not isinstance(node, Mapping):
                    return None
                # Try exact, lower, upper
                if key in node:  # type: ignore[index]
                    node = node[key]  # type: ignore[index]
                elif key.lower() in node:  # type: ignore[operator]
                    node = node[key.lower()]  # type: ignore[index]
                elif key.upper() in node:  # type: ignore[operator]
                    node = node[key.upper()]  # type: ignore[index]
                else:
                    return None
            return node
        except Exception as e:  # pragma: no cover
            print(f"Error traversing st.secrets path {path}: {e}")
            return None

    @classmethod
    def _read_secret_variants(cls, names: Sequence[str], nested_paths: Sequence[Sequence[str]] | None = None) -> Optional[str]:
        """Try multiple names and nested paths in st.secrets, then fall back to env vars."""
        nested_paths = nested_paths or []
        # Try nested paths first
        for p in nested_paths:
            val = cls._get_from_secrets(p)
            if isinstance(val, str) and val.strip():
                return val.strip()
        # Try top-level keys in secrets (case-insensitive)
        if st is not None:
            try:
                for n in names:
                    # lower first
                    if n.lower() in st.secrets:  # type: ignore[operator]
                        v = st.secrets[n.lower()]  # type: ignore[index]
                        if isinstance(v, str) and v.strip():
                            return v.strip()
                    if n in st.secrets:  # type: ignore[operator]
                        v = st.secrets[n]  # type: ignore[index]
                        if isinstance(v, str) and v.strip():
                            return v.strip()
            except Exception as e:  # pragma: no cover
                print(f"Error accessing st.secrets for names {names}: {e}")
        # Finally environment variables
        for n in names:
            v = os.getenv(n)
            if v is not None and v.strip():
                return v.strip()
        return None

    @classmethod
    def _read_secret_list_variants(cls, names: Sequence[str], nested_paths: Sequence[Sequence[str]] | None = None) -> Optional[List[str]]:
        nested_paths = nested_paths or []
        for p in nested_paths:
            val = cls._get_from_secrets(p)
            if isinstance(val, list):
                return [str(x).strip() for x in val if str(x).strip()]
        if st is not None:
            try:
                for n in names:
                    if n.lower() in st.secrets:  # type: ignore[operator]
                        v = st.secrets[n.lower()]  # type: ignore[index]
                        if isinstance(v, list):
                            return [str(x).strip() for x in v if str(x).strip()]
                    if n in st.secrets:  # type: ignore[operator]
                        v = st.secrets[n]  # type: ignore[index]
                        if isinstance(v, list):
                            return [str(x).strip() for x in v if str(x).strip()]
            except Exception as e:  # pragma: no cover
                print(f"Error accessing st.secrets list for names {names}: {e}")
        # Comma-separated env var
        for n in names:
            v = os.getenv(n)
            if v is not None and v.strip():
                return [item.strip() for item in v.split(",") if item.strip()]
        return None

    @classmethod
    def _read_bool_variants(cls, names: Sequence[str], nested_paths: Sequence[Sequence[str]] | None = None, default: bool = False) -> bool:
        val = cls._read_secret_variants(names, nested_paths)
        if val is None:
            return default
        normalized = val.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

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
        settings = cls(
            openai_api_key=cls._read_secret_variants(
                ["OPENAI_API_KEY", "openai_api_key"],
                [("LLM", "OPENAI_API_KEY"), ("llm", "openai_api_key"), ("OPENAI", "API_KEY"), ("openai", "api_key")],
            ),
            google_api_key=cls._read_secret_variants(
                ["GOOGLE_API_KEY", "google_api_key"],
                [("LLM", "GOOGLE_API_KEY"), ("llm", "google_api_key"), ("GEMINI", "API_KEY"), ("gemini", "api_key"), ("GOOGLE", "API_KEY"), ("google", "api_key")],
            ),
            mongodb_uri=cls._read_secret_variants(
                ["MONGODB_URI", "mongodb_uri"],
                [("MONGODB", "URI"), ("mongodb", "uri"), ("DATABASE", "URI"), ("database", "uri")],
            ),
            langsmith_api_key=cls._read_secret_variants(
                ["LANGSMITH_API_KEY", "LANGCHAIN_API_KEY", "langsmith_api_key"],
                [("LANGSMITH", "API_KEY"), ("langsmith", "api_key"), ("LANGCHAIN", "API_KEY"), ("langchain", "api_key")],
            ),
            langsmith_endpoint=cls._read_secret_variants(
                ["LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT", "langsmith_endpoint"],
                [("LANGSMITH", "ENDPOINT"), ("langsmith", "endpoint"), ("LANGCHAIN", "ENDPOINT"), ("langchain", "endpoint")],
            ),
            langsmith_project=cls._read_secret_variants(
                ["LANGSMITH_PROJECT", "LANGCHAIN_PROJECT", "langsmith_project"],
                [("LANGSMITH", "PROJECT"), ("langsmith", "project"), ("LANGCHAIN", "PROJECT"), ("langchain", "project")],
            ),
            langsmith_tracing=cls._read_bool_variants(
                ["LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "langsmith_tracing"],
                [("LANGSMITH", "TRACING"), ("langsmith", "tracing")],
                default=False,
            ),
            default_ai_provider=cls._read_secret_variants(
                ["DEFAULT_AI_PROVIDER", "default_ai_provider"],
                [("LLM", "PROVIDER"), ("llm", "provider")],
            )
            or "openai",
            default_ai_model=cls._read_secret_variants(
                ["DEFAULT_AI_MODEL", "default_ai_model"],
                [("LLM", "MODEL"), ("llm", "model")],
            )
            or "gpt-5-mini",
            openai_models=cls._read_secret_list_variants(
                ["OPENAI_MODELS", "openai_models"],
                [("LLM", "OPENAI_MODELS"), ("llm", "openai_models")],
            )
            or ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-5-mini"],
            gemini_models=cls._read_secret_list_variants(
                ["GEMINI_MODELS", "gemini_models"],
                [("LLM", "GEMINI_MODELS"), ("llm", "gemini_models")],
            )
            or ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash", "gemini-1.5-pro"],
            app_title=cls._read_secret_variants(["APP_TITLE", "app_title"], [("APP", "TITLE"), ("app", "title")])
            or "Expense Tracker",
            app_icon=cls._read_secret_variants(["APP_ICON", "app_icon"], [("APP", "ICON"), ("app", "icon")])
            or "💰",
            log_level=cls._read_secret_variants(["LOG_LEVEL", "log_level"]) or "INFO",
            debug_mode=cls._read_bool_variants(["DEBUG_MODE", "debug_mode"], [("APP", "DEBUG"), ("app", "debug")], default=False),
            admin_password_hash=cls._read_secret_variants(
                ["ADMIN_PASSWORD_HASH", "admin_password_hash"],
                [("ADMIN", "PASSWORD_HASH"), ("admin", "password_hash")],
            ),
            admin_password_salt=cls._read_secret_variants(
                ["ADMIN_PASSWORD_SALT", "admin_password_salt"],
                [("ADMIN", "PASSWORD_SALT"), ("admin", "password_salt")],
            ),
            admin_password_plain=cls._read_secret_variants(
                ["ADMIN_PASSWORD", "admin_password"],
                [("ADMIN", "PASSWORD"), ("admin", "password")],
            ),
        )

        # Export commonly used secrets to environment variables for library compatibility
        def _export_env(key: str, value: Optional[str]):
            if value and not os.getenv(key):
                os.environ[key] = value

        _export_env("OPENAI_API_KEY", settings.openai_api_key)
        _export_env("GOOGLE_API_KEY", settings.google_api_key)
        _export_env("MONGODB_URI", settings.mongodb_uri)
        # LangSmith / LangChain tracing vars
        if settings.langsmith_tracing or settings.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        _export_env("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        _export_env("LANGCHAIN_ENDPOINT", settings.langsmith_endpoint)
        if settings.langsmith_project:
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

        return settings


settings = AppSettings.load()

# Pydantic settings (secrets/env)
