import os
import logging
import mongomock
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.database import Database
from config.settings import get_settings

logger = logging.getLogger(__name__)

class MongoDBClient:
    """
    Singleton wrapper for PyMongo MongoClient.
    """
    _instance = None
    _client = None
    _db: Database = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        settings = get_settings()
        db_name = settings.DATABASE_NAME
        
        try:
            self._client = mongomock.MongoClient()
            self._db = self._client[db_name]
            logger.info("Successfully connected to mongomock.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            raise


    @property
    def client(self) -> MongoClient:
        return self._client

    @property
    def db(self) -> Database:
        return self._db

def get_db() -> Database:
    """Helper function to get the database instance."""
    return MongoDBClient().db

def get_client() -> MongoClient:
    """Helper function to get the mongo client instance."""
    return MongoDBClient().client
