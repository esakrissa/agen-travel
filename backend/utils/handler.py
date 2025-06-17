"""
Penanganan error standar untuk sistem travel booking.
Modul ini menyediakan kelas exception kustom dan fungsi error handling.
"""

from fastapi import HTTPException, status
from typing import Dict, Any, Optional, Type
import logging

# Konfigurasi logging
logger = logging.getLogger(__name__)

# Exception dasar sistem travel booking
class AppException(Exception):
    """Exception dasar untuk semua exception khusus sistem travel booking."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


# Tipe exception spesifik
class ValidationException(AppException):
    """Exception untuk error validasi."""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class NotFoundException(AppException):
    """Exception untuk error resource tidak ditemukan."""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class AuthenticationException(AppException):
    """Exception untuk error autentikasi."""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class AuthorizationException(AppException):
    """Exception untuk error otorisasi."""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DatabaseException(AppException):
    """Exception untuk error database."""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ExternalServiceException(AppException):
    """Exception untuk error layanan eksternal."""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


# Fungsi helper untuk penanganan error
def log_exception(exception: Exception) -> None:
    """Mencatat exception dengan level yang sesuai berdasarkan tipe."""
    if isinstance(exception, ValidationException) or isinstance(exception, NotFoundException):
        logger.warning(f"{type(exception).__name__}: {str(exception)}")
    else:
        logger.error(f"{type(exception).__name__}: {str(exception)}", exc_info=True)


def handle_exception(exception: Exception) -> HTTPException:
    """Mengubah exception apapun menjadi HTTPException untuk respons API yang konsisten."""
    log_exception(exception)
    
    if isinstance(exception, AppException):
        return HTTPException(
            status_code=exception.status_code,
            detail={
                "error": type(exception).__name__,
                "message": exception.message,
                "detail": exception.detail
            }
        )
    
    # Menangani exception yang tidak terduga
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "InternalServerError",
            "message": "Terjadi kesalahan yang tidak terduga",
            "detail": {"original_error": str(exception)}
        }
    )