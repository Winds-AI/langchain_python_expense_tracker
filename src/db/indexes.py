"""
MongoDB index creation helpers.
"""

from __future__ import annotations

from pymongo.database import Database


def ensure_indexes(db: Database) -> None:
    expenses = db["expenses"]
    expenses.create_index("created_at")
    expenses.create_index("datetime")
    expenses.create_index([("category", 1), ("subcategory", 1)])
    expenses.create_index("provider")
    expenses.create_index("model")

    logs = db["extraction_logs"]
    logs.create_index("created_at")
    logs.create_index("provider")
    logs.create_index("model")

# Index creation helpers
