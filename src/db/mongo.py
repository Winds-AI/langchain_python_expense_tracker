"""
MongoDB client and connection management.
"""

from __future__ import annotations

from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from src.config.settings import settings

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured in secrets or environment.")

    _mongo_client = MongoClient(settings.mongodb_uri, appname="py_expense_tracker")
    return _mongo_client


def get_database(db_name: str = "expense_tracker") -> Database:
    client = get_mongo_client()
    return client[db_name]

# Mongo client, connection mgmt
