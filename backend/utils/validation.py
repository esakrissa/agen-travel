import re
from datetime import datetime
from typing import Optional, Tuple, Union, Dict, Any
from .datetime import get_current_datetime, parse_datetime, format_datetime
from .handler import ValidationException

# Untuk backward compatibility
ValidationError = ValidationException

async def validate_date_format(date_string: str, allow_past: bool = False) -> str:
    """
    Memvalidasi dan menstandarisasi format tanggal.

    Args:
        date_string (str): String tanggal untuk divalidasi
        allow_past (bool): Apakah tanggal masa lalu diperbolehkan

    Returns:
        str: Tanggal terstandarisasi dalam format YYYY-MM-DD

    Raises:
        ValidationException: Jika format tanggal tidak valid atau tanggal sudah lewat
    """
    # Pola tanggal yang valid
    formats_to_try = [
        r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
        r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
    ]

    # Mendapatkan tahun saat ini
    current_year = int(await get_current_datetime("year"))

    for pattern in formats_to_try:
        if re.match(pattern, date_string):
            try:
                # Parse tanggal menggunakan parser terpusat
                date_obj = await parse_datetime(date_string)

                # Memeriksa apakah tanggal sudah lewat
                current_date = await parse_datetime(await get_current_datetime("date"))
                if not allow_past and date_obj.date() < current_date.date():
                    # Secara otomatis memperbarui ke tanggal saat ini
                    date_obj = current_date

                # Mengembalikan format standar
                return await format_datetime(date_obj, "date")
            except Exception as e:
                raise ValidationException(
                    message=f"Tanggal tidak valid",
                    detail={"error": str(e), "input": date_string}
                )

    raise ValidationException(
        message=f"Format tanggal tidak valid",
        detail={
            "expected_formats": ["YYYY-MM-DD", "DD-MM-YYYY"],
            "input": date_string,
            "note": f"Gunakan tahun {current_year} atau lebih baru"
        }
    )

async def validate_datetime_format(datetime_string: str, allow_past: bool = False) -> str:
    """
    Memvalidasi dan menstandarisasi format tanggal dan waktu.

    Args:
        datetime_string (str): String tanggal dan waktu untuk divalidasi
        allow_past (bool): Apakah tanggal dan waktu masa lalu diperbolehkan

    Returns:
        str: Tanggal dan waktu terstandarisasi dalam format YYYY-MM-DD HH:MM

    Raises:
        ValidationException: Jika format tanggal dan waktu tidak valid atau sudah lewat
    """
    # Pola tanggal dan waktu yang valid
    formats_to_try = [
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$',  # YYYY-MM-DD HH:MM
        r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$',  # DD-MM-YYYY HH:MM
        r'^\d{2}-\d{2}-\d{4} \d{2}\.\d{2}$'  # DD-MM-YYYY HH.MM
    ]

    # Mendapatkan tahun saat ini
    current_year = int(await get_current_datetime("year"))

    for pattern in formats_to_try:
        if re.match(pattern, datetime_string):
            try:
                # Parse datetime menggunakan parser terpusat
                dt_obj = await parse_datetime(datetime_string)

                # Memeriksa apakah datetime sudah lewat
                current_dt = await parse_datetime(await get_current_datetime("default"))
                if not allow_past and dt_obj < current_dt:
                    # Secara otomatis memperbarui ke datetime saat ini
                    dt_obj = current_dt

                # Mengembalikan format standar
                return await format_datetime(dt_obj, "db_format")
            except Exception as e:
                raise ValidationException(
                    message=f"Tanggal dan waktu tidak valid",
                    detail={"error": str(e), "input": datetime_string}
                )

    raise ValidationException(
        message=f"Format tanggal dan waktu tidak valid",
        detail={
            "expected_formats": ["YYYY-MM-DD HH:MM", "DD-MM-YYYY HH:MM"],
            "input": datetime_string,
            "note": f"Gunakan tahun {current_year} atau lebih baru"
        }
    )

def validate_id_number(id_number: Union[str, int]) -> int:
    """
    Memvalidasi format nomor ID.

    Args:
        id_number (str or int): Nomor ID untuk divalidasi

    Returns:
        int: Nomor ID yang divalidasi

    Raises:
        ValidationException: Jika format nomor ID tidak valid
    """
    # Konversi ke string untuk validasi
    id_str = str(id_number)

    if not re.match(r'^\d{7,8}$', id_str):
        raise ValidationException(
            message="Nomor ID tidak valid",
            detail={
                "reason": "Nomor ID harus berupa angka dengan panjang 7 atau 8 digit",
                "input": id_str
            }
        )

    # Mengembalikan sebagai integer
    return int(id_str)