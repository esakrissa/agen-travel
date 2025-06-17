from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """Model untuk request registrasi user baru"""
    nama: str = Field(..., min_length=2, max_length=100, description="Nama lengkap user")
    email: EmailStr = Field(..., description="Alamat email user")
    password: str = Field(..., min_length=6, max_length=100, description="Password user")
    telepon: Optional[str] = Field(None, max_length=20, description="Nomor telepon user")
    alamat: Optional[str] = Field(None, max_length=500, description="Alamat lengkap user")
    telegram_id: Optional[str] = Field(None, description="Telegram ID (opsional)")

    @validator('password')
    def validate_password(cls, v):
        """Validasi password harus memiliki minimal 6 karakter"""
        if len(v) < 6:
            raise ValueError('Password harus minimal 6 karakter')
        return v

    @validator('telepon')
    def validate_telepon(cls, v):
        """Validasi format nomor telepon"""
        if v is not None:
            # Hapus spasi dan karakter non-digit
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError('Nomor telepon harus minimal 10 digit')
        return v


class UserLoginRequest(BaseModel):
    """Model untuk request login user"""
    email: EmailStr = Field(..., description="Alamat email user")
    password: str = Field(..., description="Password user")


class UserResponse(BaseModel):
    """Model untuk response data user"""
    id: int = Field(..., description="ID user")
    nama: str = Field(..., description="Nama lengkap user")
    email: str = Field(..., description="Alamat email user")
    telepon: Optional[str] = Field(None, description="Nomor telepon user")
    alamat: Optional[str] = Field(None, description="Alamat lengkap user")
    telegram_id: Optional[str] = Field(None, description="Telegram ID")
    is_active: bool = Field(..., description="Status aktif user")
    is_verified: bool = Field(..., description="Status verifikasi user")
    last_login: Optional[datetime] = Field(None, description="Waktu login terakhir")
    created_at: datetime = Field(..., description="Waktu pembuatan akun")


class AuthResponse(BaseModel):
    """Model untuk response autentikasi"""
    success: bool = Field(..., description="Status keberhasilan operasi")
    message: str = Field(..., description="Pesan hasil operasi")
    access_token: Optional[str] = Field(None, description="JWT access token")
    token_type: str = Field(default="bearer", description="Tipe token")
    expires_in: Optional[int] = Field(None, description="Waktu kadaluarsa token dalam detik")
    user: Optional[UserResponse] = Field(None, description="Data user")


class TokenData(BaseModel):
    """Model untuk data dalam JWT token"""
    user_id: int = Field(..., description="ID user")
    email: str = Field(..., description="Email user")
    exp: int = Field(..., description="Waktu kadaluarsa token")
    iat: int = Field(..., description="Waktu pembuatan token")


class LinkTelegramRequest(BaseModel):
    """Model untuk request link telegram user"""
    telegram_id: str = Field(..., description="Telegram ID")


class PasswordChangeRequest(BaseModel):
    """Model untuk request ubah password"""
    current_password: str = Field(..., description="Password saat ini")
    new_password: str = Field(..., min_length=6, max_length=100, description="Password baru")

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validasi password baru harus memiliki minimal 6 karakter"""
        if len(v) < 6:
            raise ValueError('Password baru harus minimal 6 karakter')
        return v


class UserUpdateRequest(BaseModel):
    """Model untuk request update data user"""
    nama: Optional[str] = Field(None, min_length=2, max_length=100, description="Nama lengkap user")
    telepon: Optional[str] = Field(None, max_length=20, description="Nomor telepon user")
    alamat: Optional[str] = Field(None, max_length=500, description="Alamat lengkap user")

    @validator('telepon')
    def validate_telepon(cls, v):
        """Validasi format nomor telepon"""
        if v is not None:
            # Hapus spasi dan karakter non-digit
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError('Nomor telepon harus minimal 10 digit')
        return v


class ErrorResponse(BaseModel):
    """Model untuk response error"""
    success: bool = Field(default=False, description="Status keberhasilan operasi")
    error: str = Field(..., description="Pesan error")
    error_code: Optional[str] = Field(None, description="Kode error")
    detail: Optional[Dict[str, Any]] = Field(None, description="Detail tambahan error")


class SessionData(BaseModel):
    """Model untuk data session user"""
    user_id: int = Field(..., description="ID user")
    email: str = Field(..., description="Email user")
    nama: str = Field(..., description="Nama user")
    telepon: Optional[str] = Field(None, description="Nomor telepon user")
    alamat: Optional[str] = Field(None, description="Alamat user")
    telegram_id: Optional[str] = Field(None, description="Telegram ID")
    is_verified: bool = Field(..., description="Status verifikasi user")
    access_token: Optional[str] = Field(None, description="JWT access token")
    token_expires_at: Optional[datetime] = Field(None, description="Waktu kadaluarsa token")
    login_time: datetime = Field(..., description="Waktu login")
    last_activity: datetime = Field(..., description="Waktu aktivitas terakhir")


class TelegramAuthRequest(BaseModel):
    """Model untuk request autentikasi via Telegram"""
    telegram_id: str = Field(..., description="Telegram ID")
    first_name: Optional[str] = Field(None, description="Nama depan dari Telegram")
    last_name: Optional[str] = Field(None, description="Nama belakang dari Telegram")
    username: Optional[str] = Field(None, description="Username Telegram")


class TelegramLinkResponse(BaseModel):
    """Model untuk response link Telegram"""
    success: bool = Field(..., description="Status keberhasilan operasi")
    message: str = Field(..., description="Pesan hasil operasi")
    user_found: bool = Field(..., description="Apakah user ditemukan")
    requires_registration: bool = Field(default=False, description="Apakah perlu registrasi")
    user: Optional[UserResponse] = Field(None, description="Data user jika ditemukan")


class UserProfileUpdateRequest(BaseModel):
    """Model untuk request update profile dengan telegram_id"""
    telegram_id: str = Field(..., description="Telegram ID untuk identifikasi user")
    nama: Optional[str] = Field(None, min_length=2, max_length=100, description="Nama lengkap user")
    telepon: Optional[str] = Field(None, max_length=20, description="Nomor telepon user")
    alamat: Optional[str] = Field(None, max_length=500, description="Alamat lengkap user")
    
    @validator('telepon')
    def validate_telepon(cls, v):
        """Validasi format nomor telepon"""
        if v is not None and v != "string":  # Skip validation if value is "string" (default value)
            # Hapus spasi dan karakter non-digit
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError('Nomor telepon harus minimal 10 digit')
        return v
