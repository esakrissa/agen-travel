import pytest
import time
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.redis_utils import redis_cache


@pytest.fixture(autouse=True)
def setup_teardown():
    """
    Setup before each test and cleanup after.
    """
    # Setup - ensure we have a clean db before test
    redis_cache.flush()
    
    # Run the test
    yield
    
    # Teardown - clean up after test
    redis_cache.flush()


def test_set_get():
    """
    Test setting and getting values from the cache.
    """
    # Test with string
    assert redis_cache.set("test_key", "test_value") is True
    assert redis_cache.get("test_key") == "test_value"
    
    # Test with number
    assert redis_cache.set("test_num", 42) is True
    assert redis_cache.get("test_num") == 42
    
    # Test with dictionary
    test_dict = {"name": "John", "age": 30}
    assert redis_cache.set("test_dict", test_dict) is True
    assert redis_cache.get("test_dict") == test_dict
    
    # Test with list
    test_list = [1, 2, 3, "four", {"five": 5}]
    assert redis_cache.set("test_list", test_list) is True
    assert redis_cache.get("test_list") == test_list


def test_ttl():
    """
    Test that cache entries expire properly.
    """
    # Set a key with a short TTL (1 second)
    assert redis_cache.set("ttl_test", "will expire", ttl=1) is True
    
    # Verify it exists
    assert redis_cache.exists("ttl_test") is True
    assert redis_cache.get("ttl_test") == "will expire"
    
    # Wait for expiry
    time.sleep(1.5)
    
    # Verify it has expired
    assert redis_cache.exists("ttl_test") is False
    assert redis_cache.get("ttl_test") is None


def test_delete():
    """
    Test deleting keys from the cache.
    """
    # Set a key
    redis_cache.set("delete_test", "delete me")
    
    # Verify it exists
    assert redis_cache.exists("delete_test") is True
    
    # Delete it
    assert redis_cache.delete("delete_test") is True
    
    # Verify it's gone
    assert redis_cache.exists("delete_test") is False
    assert redis_cache.get("delete_test") is None
    
    # Deleting non-existent key should return False
    assert redis_cache.delete("nonexistent") is False


def test_exists():
    """
    Test checking if keys exist in the cache.
    """
    # Key should not exist initially
    assert redis_cache.exists("exist_test") is False
    
    # Set the key
    redis_cache.set("exist_test", "I exist")
    
    # Now it should exist
    assert redis_cache.exists("exist_test") is True


def test_flush():
    """
    Test flushing the cache.
    """
    # Set multiple keys
    redis_cache.set("flush_test1", "value1")
    redis_cache.set("flush_test2", "value2")
    
    # Verify they exist
    assert redis_cache.exists("flush_test1") is True
    assert redis_cache.exists("flush_test2") is True
    
    # Flush the cache
    assert redis_cache.flush() is True
    
    # Verify all keys are gone
    assert redis_cache.exists("flush_test1") is False
    assert redis_cache.exists("flush_test2") is False 