"""
Definisi metrik Prometheus untuk Telegram Bot.
"""

from prometheus_client import Counter, Histogram, Gauge

# Definisi metrik Prometheus
TELEGRAM_MESSAGES = Counter(
    "telegram_messages_total",
    "Total number of Telegram messages received",
    ["message_type"]
)

TELEGRAM_RESPONSE_TIME = Histogram(
    "telegram_response_time_seconds",
    "Time taken to respond to Telegram messages",
    ["message_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf"))
)

ACTIVE_TELEGRAM_USERS = Gauge(
    "active_telegram_users",
    "Number of active Telegram users"
)

TELEGRAM_API_CALLS = Counter(
    "telegram_api_calls_total",
    "Total number of calls to the backend API",
    ["status"]
)
