"""
Business logic for running extraction and saving results to MongoDB.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Tuple

from src.ai.chains import run_extraction
from src.ai.providers import ProviderName
from src.db.indexes import ensure_indexes
from src.db.mongo import get_database
from src.models.expense import ExpenseCreate, ExpenseUpdate, ExtractionLog, ExtractionResult
from src.utils.datetime_utils import to_utc
from src.repositories.expenses_repo import ExpensesRepository


def extract_and_save(original_query: str, provider: ProviderName, model: str, settings_snapshot: Dict) -> Tuple[ExtractionResult, str, str]:
    db = get_database()
    ensure_indexes(db)
    repo = ExpensesRepository(db)

    result, debug = run_extraction(provider, model, original_query)

    # Always log the attempt
    log = ExtractionLog(
        original_query=original_query,
        provider=provider,
        model=model,
        settings_snapshot=settings_snapshot,
        extraction=result,
    )
    log_id = repo.insert_log(log)

    expense_id = ""
    if result.valid and result.amount is not None and result.category and result.subcategory and result.description:
        expense = ExpenseCreate(
            amount=float(result.amount),
            category=result.category,
            subcategory=result.subcategory,
            description=result.description,
            datetime=to_utc(result.datetime) if isinstance(result.datetime, datetime) else datetime.utcnow(),
            provider=provider,
            model=model,
            original_query=original_query,
        )
        expense_id = repo.insert_expense(expense)

    # Attach debug extras
    result.raw_response = {**(result.raw_response or {}), **{"debug": debug}}

    return result, expense_id, log_id


def delete_expense(expense_id: str) -> bool:
    """Delete an expense by ID."""
    db = get_database()
    ensure_indexes(db)
    repo = ExpensesRepository(db)
    return repo.delete_expense(expense_id)


def update_expense(expense_id: str, updates: ExpenseUpdate) -> Optional[Dict[str, Any]]:
    """Update an expense by ID."""
    db = get_database()
    ensure_indexes(db)
    repo = ExpensesRepository(db)
    return repo.update_expense(expense_id, updates)


def get_expense_by_id(expense_id: str) -> Optional[Dict[str, Any]]:
    """Get an expense by ID."""
    db = get_database()
    ensure_indexes(db)
    repo = ExpensesRepository(db)
    return repo.get_expense_by_id(expense_id)

