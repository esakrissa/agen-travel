"""
Middleware untuk FastAPI di Telegram Bot.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

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
