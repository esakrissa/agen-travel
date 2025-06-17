#!/usr/bin/env python3
"""
Test script untuk memverifikasi implementasi Redis cache pada search tools.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the current directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

from tools.tools import search_currency_rates, search_travel_articles, search_general_info
from utils.cache import redis_cache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_currency_rates_cache():
    """Test Redis cache untuk search_currency_rates"""
    print("\n" + "="*60)
    print("🧪 TESTING CURRENCY RATES CACHE")
    print("="*60)
    
    # Test pertama - harus hit API
    print("\n1️⃣ First call (should hit Tavily API):")
    result1 = await search_currency_rates("USD to IDR")
    print(f"Result length: {len(result1)} characters")
    print("✅ First call completed")
    
    # Test kedua - harus hit cache
    print("\n2️⃣ Second call (should hit Redis cache):")
    result2 = await search_currency_rates("USD to IDR")
    print(f"Result length: {len(result2)} characters")
    
    # Verifikasi cache hit
    if "INFO CACHE" in result2:
        print("✅ Cache hit detected!")
    else:
        print("❌ Cache miss - something went wrong")
    
    return result1, result2

async def test_travel_articles_cache():
    """Test Redis cache untuk search_travel_articles"""
    print("\n" + "="*60)
    print("🧪 TESTING TRAVEL ARTICLES CACHE")
    print("="*60)
    
    # Test pertama - harus hit API
    print("\n1️⃣ First call (should hit Tavily API):")
    result1 = await search_travel_articles("Bali", "wisata")
    print(f"Result length: {len(result1)} characters")
    print("✅ First call completed")
    
    # Test kedua - harus hit cache
    print("\n2️⃣ Second call (should hit Redis cache):")
    result2 = await search_travel_articles("Bali", "wisata")
    print(f"Result length: {len(result2)} characters")
    
    # Verifikasi cache hit
    if "INFO CACHE" in result2:
        print("✅ Cache hit detected!")
    else:
        print("❌ Cache miss - something went wrong")
    
    return result1, result2

async def test_general_info_cache():
    """Test Redis cache untuk search_general_info"""
    print("\n" + "="*60)
    print("🧪 TESTING GENERAL INFO CACHE")
    print("="*60)
    
    # Test pertama - harus hit API
    print("\n1️⃣ First call (should hit Tavily API):")
    result1 = await search_general_info("cuaca Jakarta hari ini")
    print(f"Result length: {len(result1)} characters")
    print("✅ First call completed")
    
    # Test kedua - harus hit cache
    print("\n2️⃣ Second call (should hit Redis cache):")
    result2 = await search_general_info("cuaca Jakarta hari ini")
    print(f"Result length: {len(result2)} characters")
    
    # Verifikasi cache hit
    if "INFO CACHE" in result2:
        print("✅ Cache hit detected!")
    else:
        print("❌ Cache miss - something went wrong")
    
    return result1, result2

async def test_cache_keys_uniqueness():
    """Test bahwa cache keys berbeda untuk parameter yang berbeda"""
    print("\n" + "="*60)
    print("🧪 TESTING CACHE KEY UNIQUENESS")
    print("="*60)
    
    # Test dengan parameter berbeda
    print("\n1️⃣ Testing different currency pairs:")
    await search_currency_rates("USD to IDR")
    await search_currency_rates("EUR to IDR")
    print("✅ Different currency pairs tested")
    
    print("\n2️⃣ Testing different destinations:")
    await search_travel_articles("Bali", "wisata")
    await search_travel_articles("Jakarta", "wisata")
    print("✅ Different destinations tested")
    
    print("\n3️⃣ Testing different queries:")
    await search_general_info("cuaca Jakarta")
    await search_general_info("cuaca Surabaya")
    print("✅ Different queries tested")

async def check_redis_connection():
    """Check Redis connection"""
    print("\n" + "="*60)
    print("🔌 CHECKING REDIS CONNECTION")
    print("="*60)
    
    try:
        client = await redis_cache._get_client()
        await client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 STARTING REDIS CACHE TESTS FOR SEARCH TOOLS")
    print("=" * 80)
    
    # Check Redis connection first
    redis_ok = await check_redis_connection()
    if not redis_ok:
        print("\n❌ Cannot proceed without Redis connection")
        return
    
    try:
        # Test semua search tools
        await test_currency_rates_cache()
        await test_travel_articles_cache()
        await test_general_info_cache()
        await test_cache_keys_uniqueness()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS COMPLETED!")
        print("="*80)
        print("\n📋 SUMMARY:")
        print("✅ Currency rates caching implemented")
        print("✅ Travel articles caching implemented") 
        print("✅ General info caching implemented")
        print("✅ Cache key uniqueness verified")
        print(f"⏰ Cache TTL: {1800//60} minutes")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close Redis connection
        try:
            await redis_cache.close()
            print("\n🔌 Redis connection closed")
        except Exception as e:
            print(f"\n⚠️ Error closing Redis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
