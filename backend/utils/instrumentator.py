"""
Konfigurasi Prometheus FastAPI Instrumentator.
"""

from prometheus_fastapi_instrumentator import Instrumentator

def create_instrumentator():
    """
    Membuat dan mengkonfigurasi Prometheus FastAPI Instrumentator.

    Returns:
        Instrumentator: Instrumentator yang telah dikonfigurasi
    """
    # Di versi 1.7.0, kita dapat menggunakan instrumentator dengan metrik default
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="inprogress",
        inprogress_labels=True,
    )

    return instrumentator
