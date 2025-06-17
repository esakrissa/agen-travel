from models.tools import DateModel
from pydantic.v1 import BaseModel, Field
from typing import Optional

# Supervisor Agent
class ToSupervisor(BaseModel):
    """Meneruskan pekerjaan kembali ke supervisor agent."""

    request: str = Field(
        description="Pertanyaan lanjutan yang perlu diklarifikasi sebelum melanjutkan."
    )


class ToCustomerService(BaseModel):
    """Mendapatkan informasi riwayat pemesanan dan detail booking pengguna"""

    user_id: Optional[str] = Field(
        default=None, description="ID pengguna untuk mengambil riwayat pemesanan"
    )
    booking_id: Optional[str] = Field(
        default=None, description="ID booking untuk detail pemesanan spesifik"
    )
    request: str = Field(
        description="Informasi tambahan atau permintaan dari pengguna mengenai riwayat atau detail booking."
    )


class ToHotelAgent(BaseModel):
    """Meneruskan pekerjaan ke sub agen untuk menangani pencarian dan pemesanan hotel."""

    desired_date: DateModel = Field(
        description="Tanggal yang diinginkan untuk check-in hotel"
    )
    location: Optional[str] = Field(
        default=None, description="Lokasi hotel yang diinginkan"
    )
    hotel_name: Optional[str] = Field(
        default=None, description="Nama hotel yang diinginkan untuk pencarian"
    )
    request: str = Field(
        description="Informasi tambahan atau permintaan dari pengguna mengenai hotel."
    )


class ToFlightAgent(BaseModel):
    """Meneruskan pekerjaan ke sub agen untuk menangani pencarian dan pemesanan penerbangan."""

    desired_date: DateModel = Field(
        description="Tanggal yang diinginkan untuk keberangkatan penerbangan"
    )
    route: Optional[str] = Field(
        default=None, description="Rute penerbangan yang diinginkan (asal-tujuan)"
    )
    flight_number: Optional[str] = Field(
        default=None, description="Nomor penerbangan yang diinginkan"
    )
    request: str = Field(
        description="Informasi tambahan atau permintaan dari pengguna mengenai penerbangan."
    )


class ToTourAgent(BaseModel):
    """Meneruskan pekerjaan ke sub agen untuk menangani pencarian dan pemesanan paket tour."""

    desired_date: DateModel = Field(
        description="Tanggal yang diinginkan untuk tour"
    )
    destination: Optional[str] = Field(
        default=None, description="Destinasi tour yang diinginkan"
    )
    tour_name: Optional[str] = Field(
        default=None, description="Nama paket tour yang diinginkan"
    )
    request: str = Field(
        description="Informasi tambahan atau permintaan dari pengguna mengenai paket tour."
    )


class CompleteOrEscalate(BaseModel):
    """Tool untuk menandai tugas saat ini sebagai selesai dan/atau untuk mengalihkan kontrol percakapan ke supervisor,
    yang dapat mengarahkan ulang percakapan berdasarkan kebutuhan pengguna."""

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "Pengguna berubah pikiran terkait permintaan saat ini.",
            },
            "example 2": {
                "cancel": True,
                "reason": "Saya telah menyelesaikan permintaan pengguna.",
            },
            "example 3": {
                "cancel": False,
                "reason": "Saya perlu mencari tanggal dan waktu pengguna untuk informasi lebih lanjut.",
            },
        }