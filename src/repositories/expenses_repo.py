"""
MongoDB CRUD for expenses and extraction logs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pymongo.database import Database

from src.models.expense import ExpenseCreate, ExpenseUpdate, ExtractionLog
from src.utils.validation import redact_sensitive_data


class ExpensesRepository:
    def __init__(self, db: Database):
        self._db = db
        self._expenses = db["expenses"]
        self._logs = db["extraction_logs"]

    def insert_expense(self, data: ExpenseCreate) -> str:
        result = self._expenses.insert_one(data.model_dump())
        return str(result.inserted_id)

    def insert_log(self, log: ExtractionLog) -> str:
        payload: Dict[str, Any] = log.model_dump()
        # Redact sensitive fields from settings_snapshot if present
        snapshot = payload.get("settings_snapshot")
        if isinstance(snapshot, dict):
            payload["settings_snapshot"] = redact_sensitive_data(snapshot)
        if "extraction" in payload and isinstance(payload["extraction"], dict):
            payload["extraction"]["datetime"] = payload["extraction"].get("datetime")
        result = self._logs.insert_one(payload)
        return str(result.inserted_id)

    # NEW: query helpers
    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return most recent expenses sorted by created_at desc."""
        cursor = self._expenses.find({}).sort("created_at", -1).limit(int(limit))
        return list(cursor)

    def list_expenses(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        start_end_utc: Optional[Tuple] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Generic list with optional filters."""
        query: Dict[str, Any] = {}
        if category:
            query["category"] = category
        if subcategory:
            query["subcategory"] = subcategory
        if start_end_utc and len(start_end_utc) == 2:
            start, end = start_end_utc
            query["datetime"] = {"$gte": start, "$lte": end}
        cursor = self._expenses.find(query).sort("datetime", -1).limit(int(limit))
        return list(cursor)

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID. Returns True if deleted, False if not found."""
        result = self._expenses.delete_one({"_id": expense_id})
        return result.deleted_count > 0

    def update_expense(self, expense_id: str, updates: ExpenseUpdate) -> Optional[Dict[str, Any]]:
        """Update an expense by ID. Returns the updated expense or None if not found."""
        # Convert Pydantic model to dict, excluding None values
        update_dict = updates.model_dump(exclude_unset=True)
        if not update_dict:
            return None

        # Add updated_at timestamp
        from datetime import datetime
        update_dict["updated_at"] = datetime.utcnow()

        result = self._expenses.update_one(
            {"_id": expense_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            # Return the updated expense
            updated = self._expenses.find_one({"_id": expense_id})
            return updated
        return None

    def get_expense_by_id(self, expense_id: str) -> Optional[Dict[str, Any]]:
        """Get a single expense by ID."""
        return self._expenses.find_one({"_id": expense_id})

