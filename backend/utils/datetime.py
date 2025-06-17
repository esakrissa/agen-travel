from datetime import datetime, timedelta, timezone
from typing import Optional
from .handler import ValidationException
import asyncio
import zoneinfo

# Fungsi helper untuk menjalankan datetime.strptime di thread terpisah
async def async_strptime(date_string: str, format_string: str) -> datetime:
    """
    Versi asynchronous dari datetime.strptime yang berjalan di thread terpisah.

    Args:
        date_string (str): String yang akan di-parse
        format_string (str): String format

    Returns:
        datetime: Objek datetime hasil parsing
    """
    return await asyncio.to_thread(datetime.strptime, date_string, format_string)

# Fungsi helper untuk mendapatkan datetime saat ini secara asynchronous
async def async_now() -> datetime:
    """
    Versi asynchronous dari datetime.now() yang berjalan di thread terpisah.

    Returns:
        datetime: Objek datetime saat ini
    """
    return await asyncio.to_thread(datetime.now)

# Timezone standar untuk aplikasi - Waktu Indonesia Tengah (WITA)
DEFAULT_TIMEZONE = 'Asia/Makassar'

# Cache objek timezone untuk menghindari operasi I/O berulang
_WITA_TZ = None

async def get_timezone():
    """
    Mendapatkan objek timezone WITA (UTC+8) secara asynchronous.

    Returns:
        timezone: Objek timezone WITA
    """
    global _WITA_TZ

    # Mengembalikan timezone yang di-cache jika tersedia
    if _WITA_TZ is not None:
        return _WITA_TZ

    # Menggunakan offset UTC+8 tetap sebagai fallback jika zoneinfo gagal
    try:
        # Menjalankan operasi zoneinfo yang blocking di thread terpisah
        _WITA_TZ = await asyncio.to_thread(zoneinfo.ZoneInfo, DEFAULT_TIMEZONE)
        return _WITA_TZ
    except Exception as e:
        # Fallback ke offset UTC+8 tetap jika zoneinfo gagal
        _WITA_TZ = timezone(timedelta(hours=8))
        return _WITA_TZ

async def get_current_datetime(format_type="default"):
    """
    Mendapatkan tanggal dan waktu saat ini dalam timezone WITA.

    Args:
        format_type (str): Jenis format yang diinginkan
            - "default": YYYY-MM-DD HH:MM:SS
            - "date": YYYY-MM-DD
            - "time": HH:MM:SS
            - "year": YYYY

    Returns:
        str: Tanggal dan waktu saat ini dalam format yang diminta
    """
    # Mengatur timezone ke WITA
    wita_tz = await get_timezone()
    now = datetime.now(wita_tz)

    if format_type == "default":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return now.strftime("%Y-%m-%d")
    elif format_type == "time":
        return now.strftime("%H:%M:%S")
    elif format_type == "year":
        return now.strftime("%Y")
    elif format_type == "month":
        return now.strftime("%m")
    elif format_type == "day":
        return now.strftime("%d")
    elif format_type == "iso":
        return now.isoformat()
    elif format_type == "timestamp":
        return int(now.timestamp())
    elif format_type == "db_format":
        return now.strftime("%Y-%m-%d %H:%M")
    elif format_type == "display":
        return now.strftime("%d-%m-%Y %H:%M")
    else:
        return now.strftime("%Y-%m-%d %H:%M:%S")

def format_time_wita(time_str):
    """
    Format string waktu dan tambahkan timezone WITA.

    Args:
        time_str (str): String waktu dalam format HH:MM atau HH.MM atau HH:MM:SS

    Returns:
        str: String waktu terformat dengan timezone WITA
    """
    if not time_str:
        return "00:00 WITA"

    try:
        if ':' in time_str:
            # Memisahkan string waktu dan mengambil bagian jam dan menit
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
        elif '.' in time_str:
            hours, minutes = map(int, time_str.split('.'))
        else:
            # Mengembalikan apa adanya jika format tidak dikenal
            return f"{time_str} WITA"

        # Format dengan timezone WITA
        return f"{hours:02d}:{minutes:02d} WITA"
    except Exception:
        # Jika parsing gagal, kembalikan string asli dengan WITA
        return f"{time_str} WITA"

async def is_date_in_past(date_str):
    """
    Memeriksa apakah suatu tanggal berada di masa lalu

    Args:
        date_str (str): String tanggal dalam format YYYY-MM-DD atau YYYY-MM-DD HH:MM

    Returns:
        bool: True jika tanggal berada di masa lalu, False jika tidak
    """
    try:
        # Mengatur timezone ke WITA
        wita_tz = await get_timezone()
        now = datetime.now(wita_tz)

        # Menangani format tanggal yang berbeda
        date_obj = await parse_datetime(date_str)

        # Membandingkan dengan tanggal saat ini
        return date_obj < now
    except Exception:
        # Jika penguraian gagal, defaultnya adalah False
        return False

async def parse_datetime(dt_str):
    """
    Parse string datetime menjadi objek datetime.
    Menangani berbagai format tanggal dan waktu.

    Args:
        dt_str (str): String datetime dalam berbagai format

    Returns:
        datetime: Objek datetime yang sudah di-parse dan di-localize ke timezone WITA

    Raises:
        ValidationException: Jika string datetime tidak dapat di-parse
    """
    # Mengatur timezone ke WITA
    wita_tz = await get_timezone()
    dt = None

    try:
        # Menangani berbagai format
        if ' ' in dt_str:  # Memiliki komponen waktu
            date_part, time_part = dt_str.split(' ', 1)

            # Mencoba menentukan format tanggal
            if '-' in date_part:
                parts = date_part.split('-')
                if len(parts[0]) == 4:  # YYYY-MM-DD
                    if ':' in time_part:  # Format HH:MM
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                    elif '.' in time_part:  # Format HH.MM
                        dt = datetime.strptime(f"{date_part} {time_part.replace('.', ':')}", "%Y-%m-%d %H:%M")
                else:  # DD-MM-YYYY
                    if ':' in time_part:  # Format HH:MM
                        dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
                    elif '.' in time_part:  # Format HH.MM
                        dt = datetime.strptime(f"{date_part} {time_part.replace('.', ':')}", "%d-%m-%Y %H:%M")
        elif 'T' in dt_str:  # Format ISO
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            # Konversi ke timezone WITA
            dt = dt.astimezone(wita_tz)
            return dt
        else:  # Hanya tanggal
            if '-' in dt_str:
                parts = dt_str.split('-')
                if len(parts[0]) == 4:  # YYYY-MM-DD
                    dt = datetime.strptime(dt_str, "%Y-%m-%d")
                else:  # DD-MM-YYYY
                    dt = datetime.strptime(dt_str, "%d-%m-%Y")

        # Membuat datetime timezone aware (WITA)
        if dt:
            dt = dt.replace(tzinfo=wita_tz)
            return dt
    except Exception:
        # Mencoba format umum lainnya sebagai fallback
        for fmt in [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]:
            try:
                dt = datetime.strptime(dt_str, fmt)
                dt = dt.replace(tzinfo=wita_tz)
                return dt
            except ValueError:
                continue

    # Jika semua upaya parsing gagal, raise ValidationException
    raise ValidationException(
        message="Format tanggal/waktu tidak valid",
        detail={
            "input": dt_str,
            "supported_formats": [
                "YYYY-MM-DD",
                "DD-MM-YYYY",
                "YYYY-MM-DD HH:MM",
                "DD-MM-YYYY HH:MM",
                "Format ISO (YYYY-MM-DDThh:mm:ss)"
            ]
        }
    )

async def format_datetime(dt, format_type="default"):
    """
    Format objek datetime ke string dengan format tertentu.

    Args:
        dt (datetime): Objek datetime untuk diformat
        format_type (str): Jenis format output
            - "default": YYYY-MM-DD HH:MM:SS
            - "date": YYYY-MM-DD
            - "db_format": Format untuk database

    Returns:
        str: String datetime terformat
    """
    if not dt:
        return ""

    # Memastikan datetime memiliki timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=await get_timezone())

    if format_type == "default":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return dt.strftime("%Y-%m-%d")
    elif format_type == "time":
        return dt.strftime("%H:%M:%S")
    elif format_type == "db_format":
        return dt.strftime("%Y-%m-%d %H:%M")
    elif format_type == "display":
        return dt.strftime("%d-%m-%Y %H:%M")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

async def convert_datetime_format(dt_str, output_format="db_format"):
    """
    Mengkonversi string datetime dari satu format ke format lainnya.
    Menangani format YYYY-MM-DD dan DD-MM-YYYY.

    Args:
        dt_str (str): String datetime untuk dikonversi
        output_format (str): Format output yang diinginkan

    Returns:
        str: String datetime terformat untuk output yang diminta
    """
    try:
        # Parse string menggunakan parser terpusat
        dt = await parse_datetime(dt_str)

        # Mengembalikan datetime terformat
        return await format_datetime(dt, output_format)
    except Exception:
        # Mengembalikan string asli jika parsing gagal
        return dt_str

async def add_days(date_str, days):
    """
    Menambahkan sejumlah hari ke tanggal.

    Args:
        date_str (str): String tanggal dalam format YYYY-MM-DD atau YYYY-MM-DD HH:MM
        days (int): Jumlah hari untuk ditambahkan

    Returns:
        str: Tanggal baru dalam format yang sama dengan input
    """
    try:
        dt = await parse_datetime(date_str)
        new_dt = dt + timedelta(days=days)

        # Mengembalikan dalam format yang sama dengan input
        if ' ' in date_str:
            return await format_datetime(new_dt, "default")
        else:
            return await format_datetime(new_dt, "date")
    except ValueError:
        return date_str

async def get_date_difference(date_str1, date_str2):
    """
    Mendapatkan perbedaan dalam hari antara dua tanggal.

    Args:
        date_str1 (str): String tanggal pertama
        date_str2 (str): String tanggal kedua

    Returns:
        int: Perbedaan hari antara kedua tanggal
    """
    try:
        dt1 = await parse_datetime(date_str1)
        dt2 = await parse_datetime(date_str2)

        diff = dt2 - dt1
        return diff.days
    except ValueError:
        return None