"""
Backend FastAPI untuk sistem Travel booking hotel, pesawat dan paket tur.
"""

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from api.router import router
from utils.handler import AppException, handle_exception
from utils.config import get_settings
import asyncio
import uvicorn
from agents.graph import initialize_pool, close_pool
from utils.cache import redis_cache, update_cache_key_metrics
import time
from utils.metrics import AGENT_INVOCATIONS, AGENT_RESPONSE_TIME, BOOKINGS_CREATED, DATABASE_QUERIES, ACTIVE_USERS
from utils.instrumentator import create_instrumentator
from utils.middleware import TimingMiddleware, RateLimitMiddleware

config = get_settings()

# Inisialisasi aplikasi FastAPI
app = FastAPI(
    title="Sistem Multi-Agen Travel API",
    version="1.7.0",
    description="""
## Sistem multi-agen untuk pencarian dan pemesanan layanan travel.

*Memungkinkan pengguna untuk mencari hotel, pesawat, paket tur dan informasi kurs serta artikel travel.*

---

## 🔑 Fitur Utama
- 🏨 **Pencarian & Pemesanan Hotel** - Temukan hotel terbaik sesuai kebutuhan pengguna
- ✈️ **Pencarian & Pemesanan Penerbangan** - Dapatkan jadwal pesawat dengan harga terbaik
- 🏝️ **Paket Wisata** - Jelajahi paket tur menarik ke berbagai destinasi
- 🤖 **Customer Service** - Bantuan untuk mencari informasi kurs dan artikel travel
- 🔐 **Autentikasi Aman** - Sistem login yang aman dengan verifikasi email
- 📱 **Integrasi Telegram** - Akses instan melalui bot Telegram

## 🛠️ Teknologi
- **FastAPI** - Framework web modern dan cepat
- **PostgreSQL** - Database relasional yang handal
- **Redis** - Caching untuk performa optimal
- **LangGraph** - Orkestrasi sistem multi-agen AI
- **Prometheus** - Monitoring dan metrics
- **Supabase Auth** - Autentikasi dan manajemen user

---

> **💡 Tips:** Jelajahi endpoint di bawah untuk dokumentasi lengkap dan testing interaktif.
    """,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Tambahkan middleware untuk mencatat waktu permintaan
app.add_middleware(TimingMiddleware)

# Tambahkan middleware untuk rate limiting
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

# Inisialisasi Prometheus dengan instrumentator yang telah dikonfigurasi
instrumentator = create_instrumentator()

# Instrument dan expose metrics
instrumentator.instrument(app)

@app.get("/metrics", tags=["Default"], include_in_schema=True)
async def get_prometheus_metrics():
    """
    # 📊 Metrik Prometheus

    **Endpoint yang menyediakan metrik Prometheus untuk monitoring sistem.**

    *Menyediakan berbagai metrik aplikasi dalam format Prometheus yang dapat dikonsumsi oleh Grafana dan sistem monitoring lainnya.*

    ## 📈 Metrik yang Tersedia
    - **Request Metrics**: Count dan response time per endpoint
    - **Database Metrics**: Query count dan performance
    - **Cache Metrics**: Hit/miss ratio dan penggunaan
    - **User Metrics**: Active users dan session
    - **Agent Metrics**: AI invocation dan response time

    ## 🔧 Format Response
    ```
    # HELP http_requests_total Total HTTP requests
    # TYPE http_requests_total counter
    http_requests_total{method="GET",endpoint="/health"} 100

    # HELP cache_hits_total Total cache hits
    # TYPE cache_hits_total counter
    cache_hits_total{cache_type="hotels"} 50
    ```

    ## 🎯 Penggunaan
    - **Prometheus**: Scraping metrics
    - **Grafana**: Visualisasi dashboard
    - **Alerting**: Monitoring dan alerting
    - **Performance**: Analisis performa aplikasi
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health", tags=["Default"])
async def health_check():
    """
    # 🏥 Health Check

    **Pemeriksaan kesehatan aplikasi secara real-time.**

    *Endpoint ini digunakan oleh load balancer dan sistem monitoring untuk memastikan aplikasi berjalan normal.*

    ## ✅ Response Success (200)
    ```
    OK
    ```

    ## 🎯 Kegunaan
    - **Load Balancer**: Health check otomatis
    - **Monitoring**: Uptime monitoring
    - **DevOps**: Status aplikasi
    - **Kubernetes**: Liveness probe
    """
    return PlainTextResponse("OK")


# Metrik Prometheus diimpor dari utils.metrics

# Background task untuk mengupdate cache metrics
async def cache_metrics_updater():
    """Background task untuk mengupdate cache metrics secara periodik."""
    while True:
        try:
            await update_cache_key_metrics()
            await asyncio.sleep(30)  # Update setiap 30 detik
        except Exception as e:
            print(f"Error updating cache metrics: {e}")
            await asyncio.sleep(60)  # Tunggu lebih lama jika error

# Startup event untuk menginisialisasi PostgreSQL pool dan Redis cache
@app.on_event("startup")
async def startup_event():
    # Inisialisasi database pool
    await initialize_pool()

    # Inisialisasi MCP tools
    try:
        from mcps import _initialize_mcp_async
        mcp_tools = await _initialize_mcp_async()
        print(f"MCP tools berhasil diinisialisasi: {len(mcp_tools)} tools")
    except Exception as e:
        print(f"Warning: MCP tools gagal diinisialisasi: {e}")

    # Test koneksi Redis cache
    try:
        await redis_cache._get_client()
        print("Redis cache berhasil diinisialisasi")

        # Start background task untuk cache metrics
        asyncio.create_task(cache_metrics_updater())
        print("Cache metrics updater started")

    except Exception as e:
        print(f"Warning: Redis cache gagal diinisialisasi: {e}")


# Shutdown event untuk menutup PostgreSQL pool dan Redis cache
@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup MCP connections
    try:
        from mcps import cleanup_mcp
        await cleanup_mcp()
        print("MCP connections berhasil ditutup")
    except Exception as e:
        print(f"Warning: Error saat menutup MCP connections: {e}")

    # Tutup database pool
    await close_pool()

    # Tutup koneksi Redis cache
    try:
        await redis_cache.close()
        print("Redis cache berhasil ditutup")
    except Exception as e:
        print(f"Warning: Error saat menutup Redis cache: {e}")


# Handler untuk exception aplikasi
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "detail": exc.detail
        },
    )


# Handler untuk exception validasi
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Process error details to ensure they're all serializable
    error_details = []
    for error in exc.errors():
        # Convert any ValueError objects to strings
        if 'exc' in error and isinstance(error['exc'], ValueError):
            error['exc'] = str(error['exc'])
        error_details.append(error)
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Parameter permintaan tidak valid",
            "detail": {"errors": error_details}
        },
    )


# Handler untuk exception yang tidak tertangani
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    http_exception = handle_exception(exc)
    return JSONResponse(
        status_code=http_exception.status_code,
        content=http_exception.detail,
    )


# Setup CORS middleware untuk akses cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS.split(",") if config.CORS_ORIGINS else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files untuk email verification pages
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include router dengan endpoint API utama
app.include_router(router)

print("Backend API sedang berjalan")


# Konfigurasi event loop policy default untuk asyncio
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0")