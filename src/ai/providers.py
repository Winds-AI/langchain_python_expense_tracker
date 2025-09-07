"""
Providers: OpenAI and Gemini client factories using LangChain with LangSmith tracing.
"""

from __future__ import annotations

import os
from typing import Literal, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import base64

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore

from src.config.settings import settings


def _setup_langsmith():
    """Configure LangSmith tracing environment variables."""
    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = "expense_tracker"
        return True
    return False


ProviderName = Literal["openai", "gemini"]


def get_llm(provider: ProviderName, model: str):
    # Setup LangSmith tracing if configured
    langsmith_enabled = _setup_langsmith()

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not configured.")
        llm = ChatOpenAI(api_key=settings.openai_api_key, model=model, temperature=0)
        if langsmith_enabled:
            # Enable tracing for this specific instance
            llm.callbacks = []  # LangSmith will automatically attach callbacks
        return llm

    if provider == "gemini":
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY not configured.")
        llm = ChatGoogleGenerativeAI(google_api_key=settings.google_api_key, model=model, temperature=0)
        if langsmith_enabled:
            # Enable tracing for this specific instance
            llm.callbacks = []  # LangSmith will automatically attach callbacks
        return llm

    raise ValueError(f"Unsupported provider: {provider}")


def get_available_providers() -> Dict[str, List[str]]:
    """Return available providers and supported models for UI selection."""
    return {
        "openai": settings.openai_models,
        "gemini": settings.gemini_models,
    }


def transcribe_with_gemini(audio_bytes: bytes,
                           mime_type: str,
                           model: Optional[str] = None,
                           prompt: Optional[str] = None) -> str:
    """Transcribe speech audio using Gemini. Optimized for low-cost STT and "Gujlish".

    Args:
        audio_bytes: Raw audio bytes from st.audio_input()
        mime_type: e.g., "audio/wav", "audio/webm"
        model: Gemini model to use; defaults to a cost-effective STT-capable model
        prompt: Optional system prompt for transcription behavior

    Returns:
        Transcript string.
    """
    if genai is None:
        raise RuntimeError("google-generativeai SDK not available. Please install/configure.")
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured.")

    genai.configure(api_key=settings.google_api_key)
    chosen_model = model or "gemini-1.5-flash"
    stt_prompt = prompt or (
        "You are a speech-to-text assistant. Transcribe the following audio to plain text. "
        "Preserve numerals and currency values. Support Gujarati-English mixed speech (Gujlish). "
        "Return only the transcription without any extra commentary."
    )

    gmodel = genai.GenerativeModel(chosen_model)

    # The SDK accepts audio parts as dicts with mime_type and raw bytes
    parts = [
        {"mime_type": mime_type, "data": audio_bytes},
        stt_prompt,
    ]
    resp = gmodel.generate_content(parts)
    # Handle response variations
    text = getattr(resp, "text", None)
    if text:
        return text.strip()
    # Fallback: concatenate candidates if needed
    if getattr(resp, "candidates", None):
        for c in resp.candidates:
            ct = getattr(getattr(c, "content", None), "parts", None)
            if ct:
                for p in ct:
                    t = getattr(p, "text", None)
                    if t:
                        return t.strip()
    return ""

