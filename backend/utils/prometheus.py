"""
Utilitas untuk metrik Prometheus.
"""

from functools import wraps
import time
from utils.metrics import DATABASE_QUERIES, BOOKINGS_CREATED

def track_database_query(query_type):
    """
    Decorator untuk melacak query database.

    Args:
        query_type (str): Tipe query (select, insert, update, delete)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Increment counter untuk query database
            DATABASE_QUERIES.labels(query_type=query_type).inc()

            # Panggil fungsi asli
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def track_booking_created(booking_type):
    """
    Decorator untuk melacak pembuatan booking.

    Args:
        booking_type (str): Tipe booking (hotel, flight)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Panggil fungsi asli
            result = await func(*args, **kwargs)

            # Increment counter untuk booking yang dibuat
            BOOKINGS_CREATED.labels(booking_type=booking_type).inc()

            return result
        return wrapper
    return decorator
