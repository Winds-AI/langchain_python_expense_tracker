"""
LangChain chain assembly for expense extraction.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Tuple, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence

from src.ai.prompts import EXTRACTION_PROMPT
from src.ai.providers import get_llm, ProviderName
from src.models.expense import ExtractionResult
from src.services.category_service import CategoryService
from src.utils.datetime_utils import now_ist_iso, parse_to_utc, UTC


def build_extraction_chain(provider: ProviderName, model: str) -> RunnableSequence:
    llm = get_llm(provider, model)
    chain = EXTRACTION_PROMPT | llm | StrOutputParser()
    return chain


def _build_categories_block() -> str:
    """Build a compact categories/subcategories text block for the prompt."""
    try:
        service = CategoryService()
        categories = service.get_all_categories()
        lines: List[str] = []
        for cat in categories:
            subs = ", ".join(sub.name for sub in cat.subcategories) if cat.subcategories else "None"
            lines.append(f"- {cat.name}: {subs}")
        return "\n".join(lines) if lines else "- Food: Snacks, Breakfast, Lunch, Dinner\n- Transportation: Bus, Taxi, Train\n- Utilities: Electricity, Water, Internet"
    except Exception:
        # Fallback static minimal list if DB unavailable
        return "- Food: Snacks, Breakfast, Lunch, Dinner\n- Transportation: Bus, Taxi, Train\n- Utilities: Electricity, Water, Internet"


def run_extraction(provider: ProviderName, model: str, text: str) -> Tuple[ExtractionResult, dict]:
    chain = build_extraction_chain(provider, model)
    categories_block = _build_categories_block()
    raw_text = chain.invoke({"text": text, "now_iso": now_ist_iso(), "categories_block": categories_block})
    raw: dict
    try:
        raw = json.loads(raw_text)
    except Exception:
        raw = {"valid": False, "missing_fields": ["amount"], "error": "Invalid JSON from model", "raw": raw_text}

    result = ExtractionResult(
        valid=bool(raw.get("valid", True)),
        amount=raw.get("amount"),
        category=raw.get("category"),
        subcategory=raw.get("subcategory"),
        description=raw.get("description"),
        datetime=parse_to_utc(raw.get("datetime")) if raw.get("datetime") else datetime.now(tz=UTC),
        missing_fields=list(raw.get("missing_fields", [])),
        provider=provider,
        model=model,
        raw_response=raw,
        error=raw.get("error"),
    )
    return result, {"prompt_output": raw_text, "parsed": raw}

