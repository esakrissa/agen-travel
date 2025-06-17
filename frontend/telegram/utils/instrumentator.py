"""
Konfigurasi Prometheus FastAPI Instrumentator untuk Telegram Bot.
"""

from prometheus_fastapi_instrumentator import Instrumentator

def create_instrumentator():
    """
    Membuat dan mengkonfigurasi Prometheus FastAPI Instrumentator untuk Telegram Bot.

    Returns:
        Instrumentator: Instrumentator yang telah dikonfigurasi
    """
    # Di versi 6.1.0, kita dapat menggunakan instrumentator dengan metrik default
    instrumentator = Instrumentator()
    
    return instrumentator
