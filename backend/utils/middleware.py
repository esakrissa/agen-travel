"""
Middleware untuk FastAPI.
"""

import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from utils.cache import check_rate_limit, get_rate_limit_info
from datetime import datetime, timedelta
import logging

class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware untuk mencatat waktu permintaan.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Mencatat waktu permintaan dan menambahkan ke state request.

        Args:
            request (Request): Permintaan HTTP
            call_next (Callable): Fungsi untuk memanggil handler berikutnya

        Returns:
            Response: Respons HTTP
        """
        # Catat waktu mulai
        request.state.start_time = time.time()

        # Panggil handler berikutnya
        response = await call_next(request)

        # Catat waktu selesai
        request.state.end_time = time.time()

        # Hitung durasi
        request.state.duration = request.state.end_time - request.state.start_time

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware untuk rate limiting berdasarkan IP address.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        """
        Inisialisasi rate limit middleware.

        Args:
            app: Aplikasi FastAPI
            max_requests (int): Maksimal request per window
            window_seconds (int): Window waktu dalam detik
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        """
        Memeriksa rate limit sebelum memproses request.

        Args:
            request (Request): Permintaan HTTP
            call_next (Callable): Fungsi untuk memanggil handler berikutnya

        Returns:
            Response: Respons HTTP atau error rate limit
        """
        # Ambil IP address client
        client_ip = self._get_client_ip(request)

        # Skip rate limiting untuk health check dan metrics
        if request.url.path in ["/health", "/metrics", "/", "/openapi.json"]:
            return await call_next(request)

        try:
            # Periksa rate limit
            is_allowed = await check_rate_limit(client_ip, self.max_requests)

            if not is_allowed:
                # Ambil informasi rate limit terbaru untuk header response
                rate_info = await get_rate_limit_info(client_ip)

                logging.warning(f"Rate limit exceeded untuk IP {client_ip} - {rate_info.get('current_requests', 0)}/{self.max_requests} requests")

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "RateLimitExceeded",
                        "message": "Terlalu banyak permintaan. Silakan coba lagi nanti.",
                        "detail": {
                            "max_requests": self.max_requests,
                            "window_seconds": self.window_seconds,
                            "current_requests": rate_info.get("current_requests", 0),
                            "remaining_requests": rate_info.get("remaining_requests", 0),
                            "reset_time": self.window_seconds,
                            "client_ip": client_ip
                        }
                    },
                    headers=self._build_rate_limit_headers(rate_info, exceeded=True)
                )

            # Lanjutkan ke handler berikutnya
            response = await call_next(request)

            # Ambil informasi rate limit terbaru setelah request
            rate_info_after = await get_rate_limit_info(client_ip)

            # Tambahkan header rate limit info ke response
            for header_name, header_value in self._build_rate_limit_headers(rate_info_after).items():
                response.headers[header_name] = header_value

            return response

        except Exception as e:
            # Jika Redis error, lanjutkan tanpa rate limiting (fail open)
            logging.warning(f"Rate limiting error untuk IP {client_ip}: {e}")
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """
        Mendapatkan IP address client dari request.

        Args:
            request (Request): Permintaan HTTP

        Returns:
            str: IP address client
        """
        # Cek header X-Forwarded-For (untuk proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Ambil IP pertama jika ada multiple IP
            return forwarded_for.split(",")[0].strip()

        # Cek header X-Real-IP (untuk nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback ke client IP dari connection
        if hasattr(request, "client") and request.client:
            return request.client.host

        # Default fallback
        return "unknown"

    def _build_rate_limit_headers(self, rate_info: dict, exceeded: bool = False) -> dict:
        current_requests = rate_info.get("current_requests", 0)
        remaining_requests = rate_info.get("remaining_requests", 0)
        window_seconds = rate_info.get("window_seconds", self.window_seconds)

        # Hitung reset time (timestamp kapan window akan reset)
        import time
        reset_timestamp = int(time.time()) + window_seconds

        headers = {
            # Standard rate limit headers
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(remaining_requests),
            "X-RateLimit-Reset": str(reset_timestamp),
            "X-RateLimit-Window": str(window_seconds),

            # Additional informative headers
            "X-RateLimit-Used": str(current_requests),
            "X-RateLimit-Policy": f"{self.max_requests};w={window_seconds}",
            "X-RateLimit-Scope": "ip",
            "X-RateLimit-Usage-Percent": str(round((current_requests / self.max_requests) * 100, 1)),
        }

        # Tambahkan header khusus saat rate limit exceeded
        if exceeded:
            headers["Retry-After"] = str(window_seconds)
            headers["X-RateLimit-Exceeded"] = "true"
            headers["X-RateLimit-Exceeded-By"] = str(current_requests - self.max_requests)

        return headers
