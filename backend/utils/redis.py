import os
import logging
import json
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client = None


async def get_redis_client() -> Optional:
    """
    Mendapatkan Redis client sebagai singleton
    
    Returns:
        Redis client atau None jika koneksi gagal
    """
    global _redis_client
    
    try:
        if _redis_client is None:
            try:
                import redis.asyncio as redis
            except ImportError as e:
                logger.error(f"Import error for redis: {e}")
                return None
            
            # Ambil URL Redis dari environment
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            
            try:
                # Connect ke Redis
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.error(f"Error creating Redis client: {e}")
                return None
            
        return _redis_client
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        return None 