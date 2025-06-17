import os
import pytest
import redis
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()


def get_redis_connection():
    """
    Create a Redis connection using environment variables.
    """
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    db = int(os.getenv("REDIS_DB", 0))
    password = os.getenv("REDIS_PASSWORD", None)
    
    # Create Redis connection
    redis_conn = redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True
    )
    
    return redis_conn


def test_redis_connection():
    """
    Test if Redis connection can be established.
    """
    # Get Redis connection
    redis_conn = get_redis_connection()
    
    # Test connection with a ping
    response = redis_conn.ping()
    
    # Assert that the ping response is True
    assert response is True, "Failed to connect to Redis"


def test_redis_set_get():
    """
    Test if Redis can set and get values.
    """
    # Get Redis connection
    redis_conn = get_redis_connection()
    
    # Set a test key-value pair
    test_key = "test_key"
    test_value = "test_value"
    redis_conn.set(test_key, test_value)
    
    # Get the value
    retrieved_value = redis_conn.get(test_key)
    
    # Clean up
    redis_conn.delete(test_key)
    
    # Assert that the retrieved value matches the set value
    assert retrieved_value == test_value, "Redis set/get operations failed" 