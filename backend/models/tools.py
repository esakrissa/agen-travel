from pydantic.v1 import BaseModel, Field, validator
import re
from utils.validation import validate_id_number


class DateTimeModel(BaseModel):
    """
    Format struktur dan pemformatan tanggal dan waktu
    """
    date: str = Field(..., description="Tanggal dan waktu dalam format 'YYYY-MM-DD HH:MM'. PENTING: Gunakan tanggal masa depan untuk semua konsultasi.")

    # Catatan: Validator Pydantic tidak bisa async, jadi kita perlu menanganinya secara berbeda
    # Untuk saat ini, kita akan menggunakan versi sinkron dan menangani validasi async di tempat lain
    @validator("date")
    def check_format_date(cls, v):
        # Ini adalah placeholder - validasi sebenarnya akan dilakukan dalam konteks async
        return v

class DateModel(BaseModel):
    """
    Format struktur dan pemformatan tanggal
    """
    date: str = Field(..., description="Tanggal dalam format 'YYYY-MM-DD' atau 'DD-MM-YYYY'. PENTING: Gunakan tanggal masa depan untuk semua konsultasi.")

    # Catatan: Validator Pydantic tidak bisa async, jadi kita perlu menanganinya secara berbeda
    # Untuk saat ini, kita akan menggunakan versi sinkron dan menangani validasi async di tempat lain
    @validator("date") 
    def check_format_date(cls, v):
        # Ini adalah placeholder - validasi sebenarnya akan dilakukan dalam konteks async
        return v

class IdModel(BaseModel):
    """
    Format struktur dan pemformatan nomor ID
    """
    id: int = Field(..., description="Nomor ID tanpa titik", pattern=r'^\d{7,8}$')

    @validator("id")
    def check_format_id(cls, v):
        # Menggunakan validasi ID terpusat
        return validate_id_number(v)