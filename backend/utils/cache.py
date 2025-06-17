import redis.asyncio as redis
import json
import logging
import hashlib
import time
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
from datetime import datetime, timedelta
from utils.handler import DatabaseException
from utils.config import get_settings
from utils.metrics import CACHE_HITS, CACHE_MISSES, CACHE_OPERATIONS, CACHE_RESPONSE_TIME, CACHE_KEY_COUNT

# Konfigurasi Redis dari settings
settings = get_settings()
REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_PASSWORD = settings.REDIS_PASSWORD
REDIS_DB = settings.REDIS_DB

# ============================================================================
# REDIS KEY MANAGEMENT CLASSES
# ============================================================================

class RedisKeyCategories:
    """Konstanta untuk kategori Redis keys"""
    SESSION = "session"
    CACHE = "cache"
    RATELIMIT = "ratelimit"
    TEMP = "temp"
    METRICS = "metrics"

class RedisKeySubcategories:
    """Konstanta untuk sub-kategori Redis keys"""
    # Session subcategories
    USER = "user"
    ADMIN = "admin"

    # Cache subcategories
    HOTELS = "hotels"
    FLIGHTS = "flights"
    TOURS = "tours"
    AVAILABILITY = "availability"
    USER_BOOKINGS = "user_bookings"

    # Rate limit subcategories
    REQUEST = "request"
    API = "api"

    # Temp subcategories
    VERIFICATION = "verification"
    RESET = "reset"
    OTP = "otp"

class RedisKeyManager:
    """Manager untuk Redis key generation dan management"""

    BASE_NAMESPACE = "agen_travel"

    @classmethod
    def generate_key(cls, category: str, subcategory: str, identifier: str) -> str:
        """Generate Redis key."""
        return f"{cls.BASE_NAMESPACE}:{category}:{subcategory}:{identifier}"

    @classmethod
    def generate_session_key(cls, user_id: int) -> str:
        """Generate session key untuk user."""
        return cls.generate_key(
            RedisKeyCategories.SESSION,
            RedisKeySubcategories.USER,
            str(user_id)
        )

    @classmethod
    def generate_rate_limit_key(cls, identifier: str) -> str:
        """Generate rate limit key."""
        return cls.generate_key(
            RedisKeyCategories.RATELIMIT,
            RedisKeySubcategories.REQUEST,
            identifier
        )

    @classmethod
    def generate_cache_key(cls, data_type: str, function_name: str, params_hash: str) -> str:
        """Generate cache key untuk data."""
        subcategory = f"{data_type}:{function_name}"
        return cls.generate_key(
            RedisKeyCategories.CACHE,
            subcategory,
            params_hash
        )

    @classmethod
    def generate_temp_key(cls, temp_type: str, identifier: str) -> str:
        """Generate temporary data key."""
        return cls.generate_key(
            RedisKeyCategories.TEMP,
            temp_type,
            identifier
        )

    @classmethod
    def parse_key(cls, key: str) -> Dict[str, str]:
        """Parse Redis key untuk mendapatkan komponen-komponennya."""
        try:
            parts = key.split(':')
            if len(parts) >= 4 and parts[0] == cls.BASE_NAMESPACE:
                return {
                    "namespace": parts[0],
                    "category": parts[1],
                    "subcategory": parts[2],
                    "identifier": ':'.join(parts[3:])
                }
            return {"error": "Invalid key format"}
        except Exception as e:
            logging.warning(f"Error parsing key {key}: {e}")
            return {"error": str(e)}

    @classmethod
    def get_pattern_for_category(cls, category: str, subcategory: Optional[str] = None) -> str:
        """Generate pattern untuk mencari keys berdasarkan kategori."""
        if subcategory:
            return f"{cls.BASE_NAMESPACE}:{category}:{subcategory}:*"
        return f"{cls.BASE_NAMESPACE}:{category}:*"

    @classmethod
    def get_all_session_pattern(cls) -> str:
        """Get pattern untuk semua session keys."""
        return cls.get_pattern_for_category(
            RedisKeyCategories.SESSION,
            RedisKeySubcategories.USER
        )

    @classmethod
    def get_cache_pattern(cls, data_type: Optional[str] = None) -> str:
        """Get pattern untuk cache keys."""
        if data_type:
            return f"{cls.BASE_NAMESPACE}:{RedisKeyCategories.CACHE}:{data_type}:*"
        return cls.get_pattern_for_category(RedisKeyCategories.CACHE)

class RedisKeyValidator:
    """Validator untuk memastikan Redis keys menggunakan format yang benar"""

    @staticmethod
    def is_valid_key(key: str) -> bool:
        """Validasi apakah key."""
        parsed = RedisKeyManager.parse_key(key)
        return "error" not in parsed

    @staticmethod
    def validate_category(category: str) -> bool:
        """Validasi kategori."""
        valid_categories = [
            RedisKeyCategories.SESSION,
            RedisKeyCategories.CACHE,
            RedisKeyCategories.RATELIMIT,
            RedisKeyCategories.TEMP,
            RedisKeyCategories.METRICS
        ]
        return category in valid_categories

    @staticmethod
    def get_key_info(key: str) -> Dict[str, Any]:
        """Mendapatkan informasi detail tentang Redis key."""
        parsed = RedisKeyManager.parse_key(key)
        if "error" in parsed:
            return parsed

        info = {
            "key": key,
            "namespace": parsed["namespace"],
            "category": parsed["category"],
            "subcategory": parsed["subcategory"],
            "identifier": parsed["identifier"],
            "is_valid": RedisKeyValidator.is_valid_key(key),
            "category_valid": RedisKeyValidator.validate_category(parsed["category"]),
            "parsed_at": datetime.now().isoformat()
        }

        # Tambahkan informasi spesifik berdasarkan kategori
        if parsed["category"] == RedisKeyCategories.SESSION:
            info["key_type"] = "User Session"
            info["user_id"] = parsed["identifier"]
        elif parsed["category"] == RedisKeyCategories.CACHE:
            info["key_type"] = "Data Cache"
            info["data_type"] = parsed["subcategory"].split(':')[0] if ':' in parsed["subcategory"] else parsed["subcategory"]
        elif parsed["category"] == RedisKeyCategories.RATELIMIT:
            info["key_type"] = "Rate Limiting"
            info["target"] = parsed["identifier"]
        elif parsed["category"] == RedisKeyCategories.TEMP:
            info["key_type"] = "Temporary Data"
            info["temp_type"] = parsed["subcategory"]

        return info

# ============================================================================
# REDIS CACHE CLASS
# ============================================================================

# TTL default untuk berbagai jenis cache (dalam detik)
DEFAULT_TTL = {
    'hotels': 3600,  # 1 jam untuk data hotel
    'flights': 1800,  # 30 menit untuk data penerbangan
    'tours': 3600,    # 1 jam untuk data tour
    'availability': 300,  # 5 menit untuk ketersediaan
    'user_bookings': 600,  # 10 menit untuk booking user
    'database_search': 900,  # 15 menit untuk hasil pencarian database
    'web_search': 1800,  # 30 menit untuk hasil pencarian web/API eksternal
}

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # 1 menit
RATE_LIMIT_MAX_REQUESTS = 100  # maksimal 100 request per menit per IP


class RedisCache:
    """
    Redis cache manager untuk aplikasi travel booking.
    Mengelola koneksi Redis, caching, dan invalidation.
    """

    def __init__(self):
        self._pool = None
        self._client = None

    async def _get_client(self) -> redis.Redis:
        """Mendapatkan client Redis dengan connection pooling"""
        if self._client is None:
            try:
                self._pool = redis.ConnectionPool(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    db=REDIS_DB,
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True
                )
                self._client = redis.Redis(connection_pool=self._pool)

                # Test koneksi
                await self._client.ping()
                logging.info("Koneksi Redis berhasil dibuat")

            except Exception as e:
                logging.error(f"Gagal membuat koneksi Redis: {e}")
                raise DatabaseException(
                    message="Gagal terhubung ke Redis cache",
                    detail={"error": str(e)}
                )

        return self._client

    async def close(self):
        """Menutup koneksi Redis"""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    def _generate_cache_key(self, category: str, subcategory: str, *args, **kwargs) -> str:
        """
        Generate cache key yang unik.

        Args:
            category (str): Kategori utama (cache, session, ratelimit, etc)
            subcategory (str): Sub-kategori (user, hotel, flight, etc)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            str: Cache key yang unik dengan format: agen_travel:{category}:{subcategory}:{hash}
        """
        # Gabungkan semua parameter menjadi string
        params_str = f"{args}_{sorted(kwargs.items())}"

        # Hash untuk memastikan key tidak terlalu panjang
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        return f"agen_travel:{category}:{subcategory}:{params_hash}"

    def generate_session_key(self, user_id: int) -> str:
        """
        Generate session key untuk user menggunakan RedisKeyManager.

        Args:
            user_id (int): ID user

        Returns:
            str: Session key dengan format: agen_travel:session:user:{user_id}
        """
        return RedisKeyManager.generate_session_key(user_id)

    def generate_rate_limit_key(self, identifier: str) -> str:
        """
        Generate rate limit key menggunakan RedisKeyManager.

        Args:
            identifier (str): Identifier unik (IP, user ID, etc)

        Returns:
            str: Rate limit key dengan format: agen_travel:ratelimit:request:{identifier}
        """
        return RedisKeyManager.generate_rate_limit_key(identifier)

    def generate_temp_key(self, temp_type: str, identifier: str) -> str:
        """
        Generate temporary data key menggunakan RedisKeyManager.

        Args:
            temp_type (str): Jenis data temporary (verification, reset, etc)
            identifier (str): Identifier unik

        Returns:
            str: Temporary key dengan format: agen_travel:temp:{temp_type}:{identifier}
        """
        return RedisKeyManager.generate_temp_key(temp_type, identifier)

    async def get(self, key: str) -> Optional[Any]:
        """
        Mengambil data dari cache.

        Args:
            key (str): Cache key

        Returns:
            Optional[Any]: Data dari cache atau None jika tidak ada
        """
        try:
            client = await self._get_client()
            cached_data = await client.get(key)

            if cached_data:
                data = json.loads(cached_data)

                # Tentukan apakah key ini seharusnya mengembalikan DataFrame
                # Fungsi yang mengembalikan DataFrame (list/collection)
                dataframe_functions = [
                    'get_all_hotels', 'get_all_flights', 'get_all_tours',
                    'search_flights', 'search_tours_by_destination',
                    'filter_hotels_by_location'
                ]
                should_be_dataframe = any(func_name in key for func_name in dataframe_functions)

                # Jika data adalah list dan seharusnya DataFrame, konversi ke DataFrame
                if isinstance(data, list) and should_be_dataframe:
                    import pandas as pd
                    if data and len(data) > 0 and isinstance(data[0], dict):
                        return pd.DataFrame(data)
                    else:
                        # List kosong atau tidak berisi dict, return DataFrame kosong
                        return pd.DataFrame()

                # Jika data bukan list/dict tapi seharusnya DataFrame, cache miss
                elif should_be_dataframe and not isinstance(data, list):
                    logging.warning(f"Cache data format tidak sesuai untuk key {key}, akan di-refresh")
                    return None

                return data

            return None

        except Exception as e:
            logging.warning(f"Gagal mengambil data dari cache {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Menyimpan data ke cache.

        Args:
            key (str): Cache key
            value (Any): Data yang akan disimpan
            ttl (int): Time to live dalam detik

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            client = await self._get_client()

            # Jika value adalah DataFrame, konversi ke list of dicts
            import pandas as pd
            if isinstance(value, pd.DataFrame):
                value = value.to_dict('records')

            serialized_value = json.dumps(value, default=str)

            await client.setex(key, ttl, serialized_value)
            logging.debug(f"Data berhasil disimpan ke cache: {key}")
            return True

        except Exception as e:
            logging.warning(f"Gagal menyimpan data ke cache {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Menghapus data dari cache.

        Args:
            key (str): Cache key

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            client = await self._get_client()
            result = await client.delete(key)

            if result:
                logging.debug(f"Cache berhasil dihapus: {key}")

            return bool(result)

        except Exception as e:
            logging.warning(f"Gagal menghapus cache {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Menghapus semua cache yang sesuai dengan pattern.

        Args:
            pattern (str): Pattern untuk cache key (contoh: "agen_travel:hotels:*")

        Returns:
            int: Jumlah cache yang dihapus
        """
        try:
            client = await self._get_client()
            keys = await client.keys(pattern)

            if keys:
                deleted_count = await client.delete(*keys)
                logging.info(f"Berhasil menghapus {deleted_count} cache dengan pattern: {pattern}")
                return deleted_count

            return 0

        except Exception as e:
            logging.warning(f"Gagal menghapus cache dengan pattern {pattern}: {e}")
            return 0


# Instance global Redis cache
redis_cache = RedisCache()


def _extract_cache_type_from_key(key: str) -> str:
    """
    Ekstrak cache type dari cache key.

    Args:
        key (str): Cache key

    Returns:
        str: Cache type
    """
    try:
        # Format key: agen_travel:{category}:{subcategory}:{hash/identifier}
        parts = key.split(':')
        if len(parts) >= 3 and parts[0] == 'agen_travel':
            # Return category:subcategory untuk lebih spesifik
            if len(parts) >= 4:
                return f"{parts[1]}:{parts[2]}"
            return parts[1]
        return 'unknown'
    except:
        return 'unknown'


def cache_result(cache_type: str, ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """
    Decorator untuk caching hasil fungsi database.

    Args:
        cache_type (str): Jenis cache (hotels, flights, tours, dll)
        ttl (Optional[int]): Time to live, jika None akan menggunakan default
        key_prefix (Optional[str]): Prefix tambahan untuk cache key

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            # Tentukan TTL
            cache_ttl = ttl if ttl is not None else DEFAULT_TTL.get(cache_type, 3600)

            # Generate cache key menggunakan RedisKeyManager
            data_type = cache_type
            if key_prefix:
                data_type = f"{key_prefix}:{cache_type}"

            # Generate hash untuk parameters
            params_str = f"{args}_{sorted(kwargs.items())}"
            params_hash = hashlib.md5(params_str.encode()).hexdigest()

            cache_key = RedisKeyManager.generate_cache_key(data_type, func.__name__, params_hash)

            # Coba ambil dari cache
            cached_result = await redis_cache.get(cache_key)
            if cached_result is not None:
                # Cache hit - record metrics
                CACHE_HITS.labels(cache_type=cache_type, operation="get").inc()
                CACHE_OPERATIONS.labels(cache_type=cache_type, operation="get", status="hit").inc()

                # Record response time
                response_time = time.time() - start_time
                CACHE_RESPONSE_TIME.labels(cache_type=cache_type, operation="get").observe(response_time)

                logging.debug(f"Cache hit untuk {func.__name__}: {cache_key}")
                return cached_result

            # Cache miss - record metrics
            CACHE_MISSES.labels(cache_type=cache_type, operation="get").inc()
            CACHE_OPERATIONS.labels(cache_type=cache_type, operation="get", status="miss").inc()

            # Jika tidak ada di cache, eksekusi fungsi
            logging.debug(f"Cache miss untuk {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

            # Simpan hasil ke cache
            if result is not None:
                set_start_time = time.time()
                success = await redis_cache.set(cache_key, result, cache_ttl)

                # Record set operation metrics
                set_status = "success" if success else "error"
                CACHE_OPERATIONS.labels(cache_type=cache_type, operation="set", status=set_status).inc()

                # Record set response time
                set_response_time = time.time() - set_start_time
                CACHE_RESPONSE_TIME.labels(cache_type=cache_type, operation="set").observe(set_response_time)

            # Record total response time
            total_response_time = time.time() - start_time
            CACHE_RESPONSE_TIME.labels(cache_type=cache_type, operation="total").observe(total_response_time)

            return result

        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str):
    """
    Menghapus cache berdasarkan pattern.

    Args:
        pattern (str): Pattern cache yang akan dihapus (sudah termasuk agen_travel: jika perlu)
    """
    # Jika pattern belum include agen_travel:, tambahkan
    if not pattern.startswith("agen_travel:"):
        pattern = f"agen_travel:{pattern}"

    await redis_cache.delete_pattern(pattern)


async def invalidate_hotel_cache(hotel_id: Optional[int] = None):
    """
    Invalidate cache terkait hotel.

    Args:
        hotel_id (Optional[int]): ID hotel spesifik, jika None akan hapus semua cache hotel
    """
    if hotel_id:
        # Hapus cache hotel spesifik 
        patterns = [
            f"cache:hotels:*{hotel_id}*",
            f"cache:availability:*{hotel_id}*"
        ]
    else:
        # Hapus semua cache hotel
        patterns = [
            "cache:hotels:*",
            "cache:availability:*hotel*"
        ]

    for pattern in patterns:
        await invalidate_cache_pattern(pattern)


async def invalidate_flight_cache(flight_id: Optional[int] = None):
    """
    Invalidate cache terkait penerbangan.

    Args:
        flight_id (Optional[int]): ID penerbangan spesifik
    """
    if flight_id:
        patterns = [
            f"cache:flights:*{flight_id}*",
            f"cache:availability:*{flight_id}*"
        ]
    else:
        patterns = [
            "cache:flights:*",
            "cache:availability:*flight*"
        ]

    for pattern in patterns:
        await invalidate_cache_pattern(pattern)


async def invalidate_tour_cache(tour_id: Optional[int] = None):
    """
    Invalidate cache terkait tour.

    Args:
        tour_id (Optional[int]): ID tour spesifik
    """
    if tour_id:
        patterns = [
            f"cache:tours:*{tour_id}*",
            f"cache:availability:*{tour_id}*"
        ]
    else:
        patterns = [
            "cache:tours:*",
            "cache:availability:*tour*"
        ]

    for pattern in patterns:
        await invalidate_cache_pattern(pattern)


async def invalidate_user_bookings_cache(user_id: int):
    """
    Invalidate cache booking untuk user tertentu.

    Args:
        user_id (int): ID user
    """
    await invalidate_cache_pattern(f"cache:user_bookings:*{user_id}*")


async def invalidate_user_session(user_id: int):
    """
    Invalidate session untuk user tertentu.

    Args:
        user_id (int): ID user
    """
    session_key = redis_cache.generate_session_key(user_id)
    await redis_cache.delete(session_key)
    logging.info(f"Session invalidated untuk user {user_id}")


async def get_all_user_sessions() -> List[str]:
    """
    Mendapatkan semua session keys yang aktif menggunakan RedisKeyManager.

    Returns:
        List[str]: List session keys
    """
    try:
        client = await redis_cache._get_client()
        pattern = RedisKeyManager.get_all_session_pattern()
        session_keys = await client.keys(pattern)
        return session_keys
    except Exception as e:
        logging.warning(f"Gagal mendapatkan session keys: {e}")
        return []


async def cleanup_expired_sessions():
    """
    Cleanup session yang sudah expired (utility function untuk maintenance).
    """
    try:
        session_keys = await get_all_user_sessions()
        cleaned_count = 0

        for session_key in session_keys:
            session_data = await redis_cache.get(session_key)
            if not session_data:
                # Session sudah expired secara natural
                cleaned_count += 1

        logging.info(f"Session cleanup completed. {cleaned_count} expired sessions cleaned.")
        return cleaned_count

    except Exception as e:
        logging.error(f"Error during session cleanup: {e}")
        return 0


# Rate limiting functions
async def check_rate_limit(identifier: str, max_requests: int = RATE_LIMIT_MAX_REQUESTS) -> bool:
    """
    Memeriksa rate limit untuk identifier tertentu (biasanya IP address).

    Args:
        identifier (str): Identifier unik (IP address, user ID, dll)
        max_requests (int): Maksimal request yang diizinkan

    Returns:
        bool: True jika masih dalam batas, False jika sudah melebihi
    """
    try:
        client = await redis_cache._get_client()
        key = redis_cache.generate_rate_limit_key(identifier)

        # Gunakan sliding window counter
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)

        # Hapus request yang sudah expired
        await client.zremrangebyscore(key, 0, window_start.timestamp())

        # Hitung jumlah request dalam window
        current_requests = await client.zcard(key)

        if current_requests >= max_requests:
            return False

        # Tambahkan request baru
        await client.zadd(key, {str(current_time.timestamp()): current_time.timestamp()})
        await client.expire(key, RATE_LIMIT_WINDOW)

        return True

    except Exception as e:
        logging.warning(f"Gagal memeriksa rate limit untuk {identifier}: {e}")
        # Jika Redis error, izinkan request (fail open)
        return True


async def get_rate_limit_info(identifier: str) -> Dict[str, int]:
    """
    Mendapatkan informasi rate limit untuk identifier.

    Args:
        identifier (str): Identifier unik

    Returns:
        Dict[str, int]: Informasi rate limit
    """
    try:
        client = await redis_cache._get_client()
        key = redis_cache.generate_rate_limit_key(identifier)

        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)

        # Hapus request yang expired
        await client.zremrangebyscore(key, 0, window_start.timestamp())

        # Hitung request saat ini
        current_requests = await client.zcard(key)
        remaining_requests = max(0, RATE_LIMIT_MAX_REQUESTS - current_requests)

        return {
            "current_requests": current_requests,
            "max_requests": RATE_LIMIT_MAX_REQUESTS,
            "remaining_requests": remaining_requests,
            "window_seconds": RATE_LIMIT_WINDOW
        }

    except Exception as e:
        logging.warning(f"Gagal mendapatkan info rate limit untuk {identifier}: {e}")
        return {
            "current_requests": 0,
            "max_requests": RATE_LIMIT_MAX_REQUESTS,
            "remaining_requests": RATE_LIMIT_MAX_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW
        }


async def update_cache_key_metrics():
    """
    Update metrics untuk jumlah cache keys per type.
    Fungsi ini bisa dipanggil secara periodik untuk monitoring.
    """
    try:
        client = await redis_cache._get_client()

        # Get all keys dengan pattern agen_travel:*
        all_keys = await client.keys("agen_travel:*")

        # Count keys per cache type
        cache_type_counts = {}
        for key in all_keys:
            cache_type = _extract_cache_type_from_key(key)
            cache_type_counts[cache_type] = cache_type_counts.get(cache_type, 0) + 1

        # Update metrics
        for cache_type, count in cache_type_counts.items():
            CACHE_KEY_COUNT.labels(cache_type=cache_type).set(count)

        logging.debug(f"Cache key metrics updated: {cache_type_counts}")

    except Exception as e:
        logging.warning(f"Gagal mengupdate cache key metrics: {e}")
