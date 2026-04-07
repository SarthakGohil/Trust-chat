import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "apun")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
db = client[DB_NAME]

# Collections
try:
    users_collection = db["users"]
    messages_collection = db["messages"]
except Exception:
    users_collection = db["users"]
    messages_collection = db["messages"]

def setup_indices():
    """Set up database indices for performance and TTL."""
    # Index for fast user lookups
    users_collection.create_index([("username", ASCENDING)], unique=True)
    
    # Indices for fast message retrieval
    messages_collection.create_index([("timestamp", DESCENDING)])
    messages_collection.create_index([("sender", ASCENDING)])
    messages_collection.create_index([("receiver", ASCENDING)])
    
    # TTL Index: Auto-delete messages older than 30 days
    # 30 days in seconds = 30 * 24 * 60 * 60
    messages_collection.create_index([("timestamp", ASCENDING)], expireAfterSeconds=2592000)

def get_last_messages(limit=50):
    """Retrieve the last N messages."""
    return list(messages_collection.find().sort("timestamp", DESCENDING).limit(limit))

def init_db():
    try:
        setup_indices()
    except Exception:
        return
