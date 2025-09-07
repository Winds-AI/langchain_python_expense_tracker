"""
Pydantic models for expenses and extraction results.
"""

from __future__ import annotations

from datetime import datetime as DateTime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    valid: bool = Field(default=True)
    amount: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    datetime: Optional[DateTime] = None
    missing_fields: List[str] = Field(default_factory=list)
    provider: Optional[str] = None
    model: Optional[str] = None
    raw_response: Optional[dict] = None
    error: Optional[str] = None


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    subcategory: str
    description: str
    datetime: DateTime
    provider: str
    model: str
    original_query: str
    created_at: DateTime = Field(default_factory=DateTime.utcnow)


class ExtractionLog(BaseModel):
    original_query: str
    provider: str
    model: str
    created_at: DateTime = Field(default_factory=DateTime.utcnow)
    settings_snapshot: dict = Field(default_factory=dict)
    extraction: ExtractionResult


class ExpenseUpdate(BaseModel):
    """Model for updating existing expenses. All fields are optional."""
    amount: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    datetime: Optional[DateTime] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    original_query: Optional[str] = None

# Pydantic models for expenses
