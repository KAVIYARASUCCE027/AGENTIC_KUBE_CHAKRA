"""
MongoDB Collections — Phase 9.

Defines helper methods to fetch the relevant collections.
"""
from pymongo.collection import Collection
from database.mongo_client import get_db

def get_cpu_incidents_collection() -> Collection:
    """Historical incidents and memory context."""
    db = get_db()
    return db["cpu_incidents"]

def get_memory_metadata_collection() -> Collection:
    """Metadata regarding retention policies or archive pointers."""
    db = get_db()
    return db["memory_metadata"]

def get_approval_requests_collection() -> Collection:
    """Stores human approval requests for the action planner."""
    db = get_db()
    return db["approval_requests"]
