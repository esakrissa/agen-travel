import pytest
import time
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.redis_utils import redis_cache
from utils.cache_decorators import cache_result


@pytest.fixture(autouse=True)
def setup_teardown():
    """
    Setup before each test and cleanup after.
    """
    # Setup
    redis_cache.flush()
    
    # Run the test
    yield
    
    # Teardown
    redis_cache.flush()


# Mock function with a counter to verify if it's called
class MockFunctions:
    def __init__(self):
        self.counter = 0
    
    @cache_result(prefix="test")
    def expensive_operation(self, a, b):
        self.counter += 1
        return a + b
    
    @cache_result(prefix="ttl_test", ttl=1)
    def ttl_operation(self, value):
        self.counter += 1
        return f"Processed {value}"
    
    @cache_result(key_builder=lambda value: f"custom_key_{value}")
    def custom_key_operation(self, value):
        self.counter += 1
        return f"Custom key result: {value}"


def test_cache_result_basic():
    """
    Test basic caching functionality.
    """
    mock = MockFunctions()
    
    # First call - should execute the function
    result1 = mock.expensive_operation(5, 10)
    assert result1 == 15
    assert mock.counter == 1
    
    # Second call with same arguments - should use cache
    result2 = mock.expensive_operation(5, 10)
    assert result2 == 15
    assert mock.counter == 1  # Counter should not increase
    
    # Call with different arguments - should execute the function again
    result3 = mock.expensive_operation(10, 20)
    assert result3 == 30
    assert mock.counter == 2


def test_cache_result_ttl():
    """
    Test TTL functionality of the cache decorator.
    """
    mock = MockFunctions()
    
    # First call
    result1 = mock.ttl_operation("test")
    assert result1 == "Processed test"
    assert mock.counter == 1
    
    # Second call immediately - should use cache
    result2 = mock.ttl_operation("test")
    assert result2 == "Processed test"
    assert mock.counter == 1
    
    # Wait for TTL to expire
    time.sleep(1.5)
    
    # Call after TTL expired - should execute the function again
    result3 = mock.ttl_operation("test")
    assert result3 == "Processed test"
    assert mock.counter == 2


def test_custom_key_builder():
    """
    Test custom key builder functionality.
    """
    mock = MockFunctions()
    
    # First call
    result1 = mock.custom_key_operation("test")
    assert result1 == "Custom key result: test"
    assert mock.counter == 1
    
    # Second call - should use cache
    result2 = mock.custom_key_operation("test")
    assert result2 == "Custom key result: test"
    assert mock.counter == 1
    
    # Verify the custom key is used
    assert redis_cache.exists("custom_key_test") is True


def test_clear_cache():
    """
    Test clearing cache functionality.
    """
    mock = MockFunctions()
    
    # First call
    result1 = mock.expensive_operation(5, 10)
    assert result1 == 15
    assert mock.counter == 1
    
    # Second call - should use cache
    result2 = mock.expensive_operation(5, 10)
    assert result2 == 15
    assert mock.counter == 1
    
    # Clear cache for these arguments
    mock.expensive_operation.clear_cache(5, 10)
    
    # Call again - should execute the function again
    result3 = mock.expensive_operation(5, 10)
    assert result3 == 15
    assert mock.counter == 2