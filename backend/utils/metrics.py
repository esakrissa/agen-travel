"""
Definisi metrik Prometheus.
"""

from prometheus_client import Counter, Histogram, Gauge

# Definisi metrik Prometheus
AGENT_INVOCATIONS = Counter(
    "agent_invocations_total",
    "Total number of agent invocations",
    ["agent_type"]
)

AGENT_RESPONSE_TIME = Histogram(
    "agent_response_time_seconds",
    "Time taken for agent to respond",
    ["agent_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf"))
)

BOOKINGS_CREATED = Counter(
    "bookings_created_total",
    "Total number of bookings created",
    ["booking_type"]
)

DATABASE_QUERIES = Counter(
    "database_queries_total",
    "Total number of database queries",
    ["query_type"]
)

ACTIVE_USERS = Gauge(
    "active_users",
    "Number of active users"
)

# Cache metrics
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type", "operation"]
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type", "operation"]
)

CACHE_OPERATIONS = Counter(
    "cache_operations_total",
    "Total number of cache operations",
    ["cache_type", "operation", "status"]
)

CACHE_RESPONSE_TIME = Histogram(
    "cache_response_time_seconds",
    "Time taken for cache operations",
    ["cache_type", "operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float("inf"))
)

CACHE_KEY_COUNT = Gauge(
    "cache_keys_total",
    "Total number of keys in cache by type",
    ["cache_type"]
)
