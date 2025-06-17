from models.tools import DateModel, DateTimeModel, IdModel
from typing import Literal, Optional, List, Dict, Any
from langchain_core.tools import tool
import pandas as pd
import logging
import os
import httpx
import asyncio
from database.services import (
    get_all_hotels,
    get_hotel_by_id,
    filter_hotels_by_location,
    get_available_rooms,
    create_hotel_booking,
    get_user_bookings,
    get_all_flights,
    get_flight_by_id,
    search_flights,
    get_flight_schedules,
    create_flight_booking,
    get_user_by_email,
    update_hotel_booking_payment,
    update_flight_booking_payment,
    get_hotel_booking_by_id,
    get_flight_booking_by_id,
    process_hotel_cancellation,
    process_flight_cancellation,
    get_all_tours,
    get_tour_by_id,
    create_tour_booking,
    update_tour_booking_payment,
    get_tour_booking_by_id,
    process_tour_cancellation
)
from utils.datetime import get_current_datetime, parse_datetime, format_datetime, async_strptime, async_now
from utils.handler import ValidationException, DatabaseException, NotFoundException, log_exception
from utils.cache import redis_cache
from utils.metrics import CACHE_HITS, CACHE_MISSES, CACHE_OPERATIONS, CACHE_RESPONSE_TIME
from datetime import datetime

# Tavily API configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_AVAILABLE = bool(TAVILY_API_KEY)

if not TAVILY_AVAILABLE:
    print("❌ TAVILY_API_KEY not found in environment variables")

# Helper function untuk mengekstrak user context
def extract_user_context_from_state(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Ekstrak user context dari state agent.

    Args:
        state: State dari agent yang berisi user_context

    Returns:
        Dict dengan user context atau None jika tidak ada
    """
    try:
        user_context = state.get('user_context')
        if user_context and isinstance(user_context, dict):
            return user_context
        return None
    except Exception as e:
        logging.warning(f"Error mengekstrak user context: {e}")
        return None

def get_user_data_from_context(user_context: Optional[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """
    Ekstrak data user dari user context.

    Args:
        user_context: User context dari authentication

    Returns:
        Dict dengan data user (nama, email, telepon, user_id)
    """
    if not user_context:
        return {
            "user_id": None,
            "nama": None,
            "email": None,
            "telepon": None,
            "alamat": None
        }

    return {
        "user_id": user_context.get("user_id"),
        "nama": user_context.get("nama"),
        "email": user_context.get("email"),
        "telepon": user_context.get("telepon"),
        "alamat": user_context.get("alamat")
    }

@tool
async def get_hotels():
    """
    Mendapatkan daftar semua hotel yang tersedia.

    Returns:
        String: Daftar semua hotel
    """
    try:
        logging.info("Mengambil daftar semua hotel")

        hotels_df = await get_all_hotels()

        if hotels_df.empty:
            return "Tidak ada hotel yang tersedia saat ini."

        hotels_count = len(hotels_df)
        hotels_list = []

        for _, hotel in hotels_df.iterrows():
            hotel_info = f"🏨 {hotel['nama']} ({hotel['bintang']}⭐)\n"
            hotel_info += f"   📍 {hotel['lokasi']}, {hotel['alamat']}\n"
            hotel_info += f"   🆔 ID: {hotel['id']}\n"

            hotels_list.append(hotel_info)

        result = f"Ditemukan {hotels_count} hotel tersedia:\n\n"
        result += "\n".join(hotels_list)
        result += "\n\nUntuk melihat detail hotel dan kamar yang tersedia, gunakan ID hotel."

        return result

    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil daftar hotel: {str(e)}"

@tool
async def search_hotels_by_location(location: str):
    """
    Mencari hotel berdasarkan lokasi.

    Args:
        location (str): Lokasi hotel yang ingin dicari (contoh: "Kuta", "Ubud", "Seminyak")

    Returns:
        String: Daftar hotel di lokasi tersebut
    """
    try:
        if not location or len(location.strip()) == 0:
            raise ValidationException(
                message="Lokasi tidak boleh kosong",
                detail={"location": location}
            )

        logging.info(f"Mencari hotel di lokasi: {location}")

        hotels_df = await filter_hotels_by_location(location)

        if hotels_df.empty:
            return f"Tidak ditemukan hotel di lokasi {location}."

        hotels_count = len(hotels_df)
        hotels_list = []

        for _, hotel in hotels_df.iterrows():
            hotel_info = f"🏨 {hotel['nama']} ({hotel['bintang']}⭐)\n"
            hotel_info += f"   📍 {hotel['lokasi']}, {hotel['alamat']}\n"
            hotel_info += f"   🆔 ID: {hotel['id']}\n"

            # Tambahkan fasilitas jika ada
            if 'fasilitas' in hotel and hotel['fasilitas']:
                hotel_info += f"   ✨ Fasilitas: {', '.join(hotel['fasilitas'])}\n"

            hotels_list.append(hotel_info)

        result = f"Ditemukan {hotels_count} hotel di {location}:\n\n"
        result += "\n".join(hotels_list)
        result += "\n\nUntuk melihat detail hotel dan kamar yang tersedia, gunakan ID hotel."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mencari hotel: {str(e)}"

@tool
async def get_hotel_details(hotel_id: int):
    """
    Mendapatkan detail lengkap hotel berdasarkan ID.

    Args:
        hotel_id (int): ID hotel yang ingin dilihat detailnya

    Returns:
        String: Informasi detail tentang hotel
    """
    try:
        if not hotel_id:
            raise ValidationException(
                message="ID hotel tidak boleh kosong",
                detail={"hotel_id": hotel_id}
            )

        logging.info(f"Mengambil detail hotel dengan ID: {hotel_id}")

        hotel_data = await get_hotel_by_id(hotel_id)

        # Format informasi hotel
        hotel_info = f"🏨 {hotel_data['nama']} ({hotel_data['bintang']}⭐)\n"
        hotel_info += f"📍 {hotel_data['lokasi']}, {hotel_data['alamat']}\n\n"

        if hotel_data['deskripsi']:
            hotel_info += f"📝 Deskripsi:\n{hotel_data['deskripsi']}\n\n"

        if 'fasilitas' in hotel_data and hotel_data['fasilitas']:
            hotel_info += f"✨ Fasilitas hotel:\n{', '.join(hotel_data['fasilitas'])}\n\n"

        # Tambahkan informasi kamar
        if 'kamar' in hotel_data and hotel_data['kamar']:
            hotel_info += "🛏️ Tipe Kamar:\n"
            for kamar in hotel_data['kamar']:
                hotel_info += f"  • {kamar['tipe_kamar']}\n"
                hotel_info += f"    - Harga: Rp {kamar['harga']:,}/malam\n"
                hotel_info += f"    - Kapasitas: {kamar['kapasitas']} orang\n"
                hotel_info += f"    - Tersedia: {kamar['jumlah_tersedia']} kamar\n"

                if 'fasilitas' in kamar and kamar['fasilitas']:
                    hotel_info += f"    - Fasilitas: {', '.join(kamar['fasilitas'])}\n"
                hotel_info += "\n"

        hotel_info += "Untuk memeriksa ketersediaan kamar, silakan berikan tanggal check-in, check-out, dan jumlah tamu."

        return hotel_info

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil detail hotel: {str(e)}"

@tool
async def check_available_rooms(hotel_id: int, check_in_date: str, check_out_date: str, guests: int = 1):
    """
    Memeriksa kamar yang tersedia di hotel tertentu pada rentang tanggal tertentu.

    Args:
        hotel_id (int): ID hotel
        check_in_date (str): Tanggal check-in dalam format YYYY-MM-DD
        check_out_date (str): Tanggal check-out dalam format YYYY-MM-DD
        guests (int): Jumlah tamu (default: 1)

    Returns:
        String: Daftar kamar yang tersedia
    """
    try:
        if not hotel_id:
            raise ValidationException(
                message="ID hotel tidak boleh kosong",
                detail={"hotel_id": hotel_id}
            )

        if not check_in_date or not check_out_date:
            raise ValidationException(
                message="Tanggal check-in dan check-out harus diisi",
                detail={"check_in_date": check_in_date, "check_out_date": check_out_date}
            )

        # Validasi format tanggal
        try:
            await async_strptime(check_in_date, "%Y-%m-%d")
            await async_strptime(check_out_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationException(
                message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2023-12-31)",
                detail={"check_in_date": check_in_date, "check_out_date": check_out_date}
            )

        logging.info(f"Memeriksa kamar tersedia di hotel {hotel_id} dari {check_in_date} sampai {check_out_date} untuk {guests} tamu")

        # Ambil detail hotel untuk informasi nama
        hotel_data = await get_hotel_by_id(hotel_id)
        hotel_name = hotel_data.get('nama', f"Hotel ID {hotel_id}")

        available_rooms = await get_available_rooms(hotel_id, check_in_date, check_out_date, guests)

        if not available_rooms:
            return f"Maaf, tidak ada kamar yang tersedia di {hotel_name} untuk tanggal {check_in_date} hingga {check_out_date} dengan kapasitas {guests} orang."

        result = f"🏨 Kamar tersedia di {hotel_name}\n"
        result += f"📅 Tanggal: {check_in_date} hingga {check_out_date}\n"
        result += f"👥 Jumlah tamu: {guests} orang\n\n"

        for room in available_rooms:
            result += f"🛏️ {room['tipe_kamar']}\n"
            result += f"   💰 Harga: Rp {room['harga']:,}/malam\n"
            result += f"   👥 Kapasitas: {room['kapasitas']} orang\n"
            result += f"   🔢 Tersedia: {room['jumlah_tersedia']} kamar\n"

            if 'fasilitas' in room and room['fasilitas']:
                result += f"   ✨ Fasilitas: {', '.join(room['fasilitas'])}\n"

            # Hitung total harga untuk seluruh masa inap
            check_in_dt = await async_strptime(check_in_date, "%Y-%m-%d")
            check_out_dt = await async_strptime(check_out_date, "%Y-%m-%d")
            nights = (check_out_dt - check_in_dt).days
            total_price = room['harga'] * nights

            result += f"   📝 Total untuk {nights} malam: Rp {total_price:,}\n\n"

        # Removed explicit booking instruction to allow agent prompt to handle this
        result += "Di atas adalah informasi kamar yang tersedia. Kamar ini tersedia untuk periode waktu yang Anda minta."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil ketersediaan kamar: {str(e)}"

@tool
async def book_hotel_room(hotel_id: int, check_in_date: str, check_out_date: str,
                          jumlah_tamu: int, jumlah_kamar: int, tipe_kamar: str,
                          nama_pemesan: str = "", email: str = "", telepon: str = "",
                          user_id: Optional[int] = None, catatan: Optional[str] = None):
    """
    Membuat pemesanan kamar hotel. Data user akan diambil dari user context jika tersedia.

    Args:
        hotel_id (int): ID hotel
        check_in_date (str): Tanggal check-in dalam format YYYY-MM-DD
        check_out_date (str): Tanggal check-out dalam format YYYY-MM-DD
        jumlah_tamu (int): Jumlah tamu yang menginap
        jumlah_kamar (int): Jumlah kamar yang dipesan
        tipe_kamar (str): Tipe kamar yang dipesan
        nama_pemesan (str, optional): Nama lengkap pemesan (akan diambil dari user context jika kosong)
        email (str, optional): Alamat email pemesan (akan diambil dari user context jika kosong)
        telepon (str, optional): Nomor telepon pemesan (akan diambil dari user context jika kosong)
        user_id (int, optional): ID pengguna jika sudah terdaftar
        catatan (str, optional): Catatan tambahan untuk pemesanan

    Returns:
        String: Konfirmasi pemesanan berhasil
    """
    try:
        # Validasi input dasar
        if not hotel_id or not check_in_date or not check_out_date:
            raise ValidationException(
                message="Hotel ID, tanggal check-in dan check-out harus diisi",
                detail={"hotel_id": hotel_id, "check_in_date": check_in_date, "check_out_date": check_out_date}
            )

        # Validasi data user - jika tidak ada nama, email, atau telepon, berikan pesan yang jelas
        if not nama_pemesan or not email or not telepon:
            missing_fields = []
            if not nama_pemesan:
                missing_fields.append("nama_pemesan")
            if not email:
                missing_fields.append("email")
            if not telepon:
                missing_fields.append("telepon")

            raise ValidationException(
                message=f"Data user tidak lengkap. Pastikan user sudah login atau berikan data: {', '.join(missing_fields)}",
                detail={"missing_fields": missing_fields}
            )

        # Validasi format tanggal
        try:
            check_in_dt = await async_strptime(check_in_date, "%Y-%m-%d")
            check_out_dt = await async_strptime(check_out_date, "%Y-%m-%d")

            if check_in_dt >= check_out_dt:
                raise ValidationException(
                    message="Tanggal check-out harus setelah tanggal check-in",
                    detail={"check_in_date": check_in_date, "check_out_date": check_out_date}
                )

            nights = (check_out_dt - check_in_dt).days
        except ValueError:
            raise ValidationException(
                message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2023-12-31)",
                detail={"check_in_date": check_in_date, "check_out_date": check_out_date}
            )

        # Ambil detail hotel dan kamar untuk validasi dan perhitungan harga
        hotel_data = await get_hotel_by_id(hotel_id)

        # Periksa apakah tipe kamar tersedia
        available_rooms = await get_available_rooms(hotel_id, check_in_date, check_out_date, jumlah_tamu)

        selected_room = None
        for room in available_rooms:
            if room['tipe_kamar'] == tipe_kamar:
                selected_room = room
                break

        if not selected_room:
            raise ValidationException(
                message=f"Tipe kamar '{tipe_kamar}' tidak tersedia untuk tanggal yang dipilih",
                detail={"tipe_kamar": tipe_kamar, "hotel_id": hotel_id}
            )

        # Periksa apakah jumlah kamar yang diminta tersedia
        if jumlah_kamar > selected_room['jumlah_tersedia']:
            raise ValidationException(
                message=f"Hanya tersedia {selected_room['jumlah_tersedia']} kamar tipe {tipe_kamar}",
                detail={"jumlah_kamar": jumlah_kamar, "tersedia": selected_room['jumlah_tersedia']}
            )

        # Cek dan proses user_id - user registration sudah dihandle di authentication
        if not user_id:
            # Cek apakah email sudah terdaftar
            existing_user = await get_user_by_email(email)
            if existing_user:
                # Gunakan user_id yang sudah ada
                user_id = existing_user['id']
                logging.info(f"Menggunakan user yang sudah terdaftar dengan ID: {user_id}")
            else:
                logging.info(f"User dengan email {email} tidak ditemukan. Booking akan dilanjutkan tanpa user_id.")

        # Hitung total harga
        total_harga = selected_room['harga'] * nights * jumlah_kamar

        # Buat data pemesanan
        booking_data = {
            "hotel_id": hotel_id,
            "user_id": user_id,
            "nama_pemesan": nama_pemesan,
            "email": email,
            "telepon": telepon,
            "tanggal_mulai": check_in_date,
            "tanggal_akhir": check_out_date,
            "jumlah_tamu": jumlah_tamu,
            "jumlah_kamar": jumlah_kamar,
            "tipe_kamar": tipe_kamar,
            "total_harga": total_harga,
            "status": "pending",
            "metode_pembayaran": None,
            "status_pembayaran": "unpaid",
            "catatan": catatan
        }

        # Simpan pemesanan ke database
        booking_result = await create_hotel_booking(booking_data)

        # Format pesan konfirmasi
        result = "✅ Pemesanan hotel berhasil dibuat!\n\n"
        result += f"🏨 {hotel_data['nama']}\n"
        result += f"🛏️ {tipe_kamar} - {jumlah_kamar} kamar\n"
        result += f"📅 Check-in: {check_in_date}\n"
        result += f"📅 Check-out: {check_out_date}\n"
        result += f"🌙 Durasi: {nights} malam\n"
        result += f"👥 Tamu: {jumlah_tamu} orang\n"

        if catatan:
            result += f"📝 Catatan: {catatan}\n"

        result += f"\n💰 Total: Rp {total_harga:,}\n"
        result += f"💳 Status pembayaran: Belum dibayar\n\n"
        result += f"🆔 ID Pemesanan: {booking_result['id']}\n"

        logging.info(f"Pemesanan hotel berhasil dibuat dengan ID: {booking_result['id']}")

        result += "\nSilakan lakukan pembayaran untuk mengkonfirmasi pemesanan Anda."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat membuat pemesanan: {str(e)}"

@tool
async def get_user_booking_history(user_id: int):
    """
    Mendapatkan riwayat pemesanan untuk pengguna tertentu.

    Args:
        user_id (int): ID pengguna

    Returns:
        String: Riwayat pemesanan hotel, penerbangan, dan tour pengguna
    """
    try:
        if not user_id:
            raise ValidationException(
                message="ID pengguna tidak boleh kosong",
                detail={"user_id": user_id}
            )

        logging.info(f"Mengambil riwayat pemesanan untuk pengguna ID: {user_id}")

        booking_data = await get_user_bookings(user_id)

        hotel_bookings = booking_data.get('hotel_bookings', [])
        flight_bookings = booking_data.get('flight_bookings', [])
        tour_bookings = booking_data.get('tour_bookings', [])

        if not hotel_bookings and not flight_bookings and not tour_bookings:
            return f"Tidak ditemukan riwayat pemesanan untuk pengguna dengan ID {user_id}."

        result = f"📋 Riwayat Pemesanan - User ID: {user_id}\n\n"

        # Format hotel bookings
        if hotel_bookings:
            result += "🏨 PEMESANAN HOTEL:\n"
            result += "-------------------\n\n"

            for booking in hotel_bookings:
                hotel_info = booking.get('hotels', {})
                hotel_name = hotel_info.get('nama', f"Hotel ID {booking.get('hotel_id')}")

                result += f"🆔 Booking ID: {booking.get('id')}\n"
                result += f"🏨 {hotel_name}\n"
                result += f"📅 {booking.get('tanggal_mulai')} s/d {booking.get('tanggal_akhir')}\n"
                result += f"🛏️ {booking.get('tipe_kamar')} - {booking.get('jumlah_kamar')} kamar\n"
                result += f"👥 {booking.get('jumlah_tamu')} tamu\n"
                result += f"💰 Rp {booking.get('total_harga'):,}\n"
                result += f"📊 Status: {booking.get('status')}\n"
                result += f"💳 Pembayaran: {booking.get('status_pembayaran')}\n"

                if booking.get('catatan'):
                    result += f"📝 Catatan: {booking.get('catatan')}\n"

                result += "\n"

        # Format flight bookings
        if flight_bookings:
            result += "✈️ PEMESANAN PENERBANGAN:\n"
            result += "-------------------------\n\n"

            for booking in flight_bookings:
                flight_info = booking.get('flights', {})
                airline = flight_info.get('maskapai', "")
                flight_code = flight_info.get('kode_penerbangan', "")
                origin = flight_info.get('origin', "")
                destination = flight_info.get('destination', "")

                result += f"🆔 Booking ID: {booking.get('id')}\n"
                result += f"✈️ {airline} ({flight_code})\n"
                result += f"🛫 {origin} → {destination}\n"
                result += f"📅 Tanggal: {booking.get('tanggal_keberangkatan')}\n"
                result += f"👥 {booking.get('jumlah_penumpang')} penumpang\n"
                result += f"💺 Kelas: {booking.get('kelas_penerbangan')}\n"

                # Tampilkan nomor kursi jika tersedia
                if booking.get('nomor_kursi'):
                    result += f"💺 Nomor Kursi: {booking.get('nomor_kursi')}\n"

                result += f"💰 Rp {booking.get('total_harga'):,}\n"
                result += f"📊 Status: {booking.get('status')}\n"
                result += f"💳 Pembayaran: {booking.get('status_pembayaran')}\n"

                if booking.get('catatan'):
                    result += f"📝 Catatan: {booking.get('catatan')}\n"

                result += "\n"

        # Format tour bookings
        if tour_bookings:
            result += "🎯 PEMESANAN TOUR:\n"
            result += "-------------------\n\n"

            for booking in tour_bookings:
                tour_info = booking.get('tours', {})
                tour_name = tour_info.get('nama', f"Tour ID {booking.get('tour_id')}")
                destinasi = tour_info.get('destinasi', "")
                durasi = tour_info.get('durasi', "")

                result += f"🆔 Booking ID: {booking.get('id')}\n"
                result += f"🎯 {tour_name}\n"
                result += f"📍 Destinasi: {destinasi}\n"
                result += f"⏱️ Durasi: {durasi}\n"
                result += f"📅 Tanggal tour: {booking.get('tanggal_tour')}\n"
                result += f"👥 {booking.get('jumlah_peserta')} peserta\n"
                result += f"💰 Rp {booking.get('total_harga'):,}\n"
                result += f"📊 Status: {booking.get('status')}\n"
                result += f"💳 Pembayaran: {booking.get('status_pembayaran')}\n"

                if booking.get('catatan'):
                    result += f"📝 Catatan: {booking.get('catatan')}\n"

                result += "\n"

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil riwayat pemesanan: {str(e)}"

# Flight-related tools
@tool
async def get_flights():
    """
    Mendapatkan daftar semua penerbangan yang tersedia.

    Returns:
        String: Daftar semua penerbangan
    """
    try:
        logging.info("Mengambil daftar semua penerbangan")

        flights_df = await get_all_flights()

        if flights_df.empty:
            return "Tidak ada penerbangan yang tersedia saat ini."

        flights_count = len(flights_df)
        flights_list = []

        for _, flight in flights_df.iterrows():
            flight_info = f"✈️ {flight['maskapai']} ({flight['kode_penerbangan']})\n"
            flight_info += f"   🛫 {flight['origin']} → {flight['destination']}\n"
            flight_info += f"   🕒 {flight['waktu_berangkat']} - {flight['waktu_tiba']} ({flight['durasi']})\n"
            flight_info += f"   💰 Harga: Rp {flight['harga']:,} ({flight['kelas']})\n"
            flight_info += f"   🪑 Kursi tersedia: {flight['kursi_tersedia']}\n"
            flight_info += f"   🆔 ID: {flight['id']}\n"

            flights_list.append(flight_info)

        result = f"Ditemukan {flights_count} penerbangan tersedia:\n\n"
        result += "\n".join(flights_list)
        result += "\n\nUntuk memeriksa jadwal penerbangan, tentukan tanggal perjalanan dengan ID penerbangan."

        return result

    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil daftar penerbangan: {str(e)}"

@tool
async def search_flights_by_route(origin: str, destination: str, date: str = None):
    """
    Mencari penerbangan berdasarkan rute (asal dan tujuan) dan tanggal.

    Args:
        origin (str): Kode bandara asal (contoh: "CGK" untuk Jakarta, "DPS" untuk Denpasar)
        destination (str): Kode bandara tujuan
        date (str, optional): Tanggal penerbangan dalam format YYYY-MM-DD

    Returns:
        String: Daftar penerbangan yang sesuai dengan kriteria
    """
    try:
        if not origin or not destination:
            raise ValidationException(
                message="Kode bandara asal dan tujuan harus diisi",
                detail={"origin": origin, "destination": destination}
            )

        # Validasi format tanggal jika disediakan
        if date:
            try:
                await async_strptime(date, "%Y-%m-%d")
            except ValueError:
                raise ValidationException(
                    message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2023-12-31)",
                    detail={"date": date}
                )

        # Jika tanggal tidak disediakan, gunakan tanggal hari ini
        now = await async_now()
        current_date = now.strftime("%Y-%m-%d")
        search_date = date if date else current_date

        logging.info(f"Mencari penerbangan dari {origin} ke {destination} pada tanggal {search_date}")

        flights_df = await search_flights(origin=origin, destination=destination, date=search_date)

        if flights_df.empty:
            return f"Tidak ditemukan penerbangan dari {origin} ke {destination} pada tanggal {search_date}"

        flights_count = len(flights_df)
        flights_list = []

        for _, flight in flights_df.iterrows():
            flight_info = f"✈️ {flight['maskapai']} ({flight['kode_penerbangan']})\n"
            flight_info += f"   🛫 {flight['origin']} → {flight['destination']}\n"
            flight_info += f"   📅 Tanggal: {search_date}\n"
            flight_info += f"   🕒 {flight['waktu_berangkat']} - {flight['waktu_tiba']} ({flight['durasi']})\n"
            flight_info += f"   💰 Harga: Rp {flight['harga']:,} ({flight['kelas']})\n"
            flight_info += f"   🪑 Kursi tersedia: {flight['kursi_tersedia']}\n"
            flight_info += f"   🆔 ID: {flight['id']}\n"

            flights_list.append(flight_info)

        result = f"Ditemukan {flights_count} penerbangan dari {origin} ke {destination} pada tanggal {search_date}:\n\n"
        result += "\n".join(flights_list)
        result += "\n\nUntuk memesan penerbangan, gunakan ID penerbangan."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mencari penerbangan: {str(e)}"

@tool
async def get_flight_details(flight_id: int, date: str = None):
    """
    Mendapatkan detail lengkap penerbangan berdasarkan ID dan memeriksa ketersediaan pada tanggal tertentu.

    Args:
        flight_id (int): ID penerbangan yang ingin dilihat detailnya
        date (str, optional): Tanggal penerbangan dalam format YYYY-MM-DD untuk memeriksa ketersediaan

    Returns:
        String: Informasi detail tentang penerbangan
    """
    try:
        if not flight_id:
            raise ValidationException(
                message="ID penerbangan tidak boleh kosong",
                detail={"flight_id": flight_id}
            )

        logging.info(f"Mengambil detail penerbangan dengan ID: {flight_id}")

        flight_data = await get_flight_by_id(flight_id)

        # Format informasi penerbangan
        flight_info = f"✈️ {flight_data['maskapai']} ({flight_data['kode_penerbangan']})\n"
        flight_info += f"🛫 Rute: {flight_data['origin']} → {flight_data['destination']}\n"
        flight_info += f"🕒 Waktu: {flight_data['waktu_berangkat']} - {flight_data['waktu_tiba']} ({flight_data['durasi']})\n"
        flight_info += f"💰 Harga: Rp {flight_data['harga']:,}\n"
        flight_info += f"💺 Kelas: {flight_data['kelas']}\n"
        flight_info += f"🪑 Kursi tersedia: {flight_data['kursi_tersedia']}\n\n"

        # Jika tanggal tidak disediakan, gunakan tanggal hari ini
        check_date = date
        if not check_date:
            now = await async_now()
            check_date = now.strftime("%Y-%m-%d")
            flight_info += f"⚠️ Tanggal tidak disediakan, memeriksa ketersediaan untuk tanggal hari ini ({check_date})\n\n"

        # Periksa ketersediaan pada tanggal
        try:
            await async_strptime(check_date, "%Y-%m-%d")

            schedules = await get_flight_schedules(flight_id, check_date, check_date)

            if schedules and any(schedule.get('is_available', False) for schedule in schedules):
                flight_info += f"✅ Penerbangan tersedia pada tanggal {check_date}\n\n"
            else:
                flight_info += f"❌ Penerbangan tidak tersedia pada tanggal {check_date}\n\n"

        except ValueError:
            flight_info += "⚠️ Format tanggal tidak valid. Gunakan format YYYY-MM-DD\n\n"

        flight_info += "Untuk memesan penerbangan ini, berikan tanggal keberangkatan, nama lengkap, email, nomor telepon, dan jumlah penumpang."

        return flight_info

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil detail penerbangan: {str(e)}"

@tool
async def book_flight(flight_id: int, tanggal_keberangkatan: str, nama_pemesan: str = "", email: str = "",
                     telepon: str = "", jumlah_penumpang: int = 0, kelas_penerbangan: str = None,
                     user_id: Optional[int] = None, catatan: Optional[str] = None):
    """
    Membuat pemesanan penerbangan.

    Args:
        flight_id (int): ID penerbangan
        tanggal_keberangkatan (str): Tanggal keberangkatan dalam format YYYY-MM-DD
        nama_pemesan (str, optional): Nama lengkap pemesan
        email (str, optional): Alamat email pemesan
        telepon (str, optional): Nomor telepon pemesan
        jumlah_penumpang (int, optional): Jumlah penumpang
        kelas_penerbangan (str, optional): Kelas penerbangan (Ekonomi/Bisnis/dll)
        user_id (int, optional): ID pengguna jika sudah terdaftar
        catatan (str, optional): Catatan tambahan untuk pemesanan

    Returns:
        String: Konfirmasi pemesanan berhasil
    """
    try:
        # Cek apakah hanya email yang diberikan, jika ya coba ambil data user dari database
        if email and (not nama_pemesan or not telepon):
            existing_user = await get_user_by_email(email)
            if existing_user:
                nama_pemesan = existing_user.get('nama', nama_pemesan)
                telepon = existing_user.get('telepon', telepon)
                user_id = existing_user.get('id', user_id)
                logging.info(f"User dengan email {email} ditemukan, menggunakan data yang sudah ada")

        # Validasi input dasar setelah mencoba mengambil data user
        if not flight_id or not tanggal_keberangkatan or not nama_pemesan or not email or not telepon or not jumlah_penumpang:
            raise ValidationException(
                message="Semua data pemesanan harus diisi",
                detail={"flight_id": flight_id, "tanggal_keberangkatan": tanggal_keberangkatan}
            )

        # Validasi format tanggal
        try:
            booking_date = await async_strptime(tanggal_keberangkatan, "%Y-%m-%d")
            # Pastikan tanggal tidak di masa lalu
            now = await async_now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if booking_date < today:
                raise ValidationException(
                    message="Tanggal keberangkatan tidak boleh di masa lalu",
                    detail={"tanggal_keberangkatan": tanggal_keberangkatan}
                )
        except ValueError:
            raise ValidationException(
                message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2023-12-31)",
                detail={"tanggal_keberangkatan": tanggal_keberangkatan}
            )

        # Ambil detail penerbangan untuk validasi dan perhitungan harga
        flight_data = await get_flight_by_id(flight_id)

        logging.info(f"Mendapatkan jadwal penerbangan untuk tanggal {tanggal_keberangkatan}")

        # Periksa ketersediaan penerbangan pada tanggal tersebut
        schedules = await get_flight_schedules(flight_id, tanggal_keberangkatan, tanggal_keberangkatan)

        if not schedules:
            raise ValidationException(
                message=f"Tidak ada jadwal penerbangan ID {flight_id} pada tanggal {tanggal_keberangkatan}",
                detail={"flight_id": flight_id, "tanggal_keberangkatan": tanggal_keberangkatan}
            )

        available_schedules = [s for s in schedules if s.get('is_available', False)]
        if not available_schedules:
            raise ValidationException(
                message=f"Penerbangan tidak tersedia pada tanggal {tanggal_keberangkatan}. Silakan pilih tanggal lain.",
                detail={"flight_id": flight_id, "tanggal_keberangkatan": tanggal_keberangkatan}
            )

        # Periksa ketersediaan kursi
        if jumlah_penumpang > flight_data['kursi_tersedia']:
            raise ValidationException(
                message=f"Jumlah kursi yang tersedia ({flight_data['kursi_tersedia']}) tidak mencukupi untuk {jumlah_penumpang} penumpang",
                detail={"jumlah_penumpang": jumlah_penumpang, "kursi_tersedia": flight_data['kursi_tersedia']}
            )

        # Selalu gunakan kelas penerbangan dari data penerbangan
        kelas_penerbangan = flight_data['kelas']

        # Hitung total harga
        total_harga = flight_data['harga'] * jumlah_penumpang

        # Generate nomor kursi secara random
        nomor_kursi = None
        if jumlah_penumpang > 0:
            import random
            seat_letters = ["A", "B", "C", "D", "E", "F"]
            max_rows = 30  # Asumsi pesawat memiliki maksimal 30 baris

            # Generate semua kemungkinan kursi
            all_seats = []
            for row in range(1, max_rows + 1):
                for letter in seat_letters:
                    all_seats.append(f"{letter}{row}")

            # Pilih kursi secara random tanpa duplikasi
            selected_seats = random.sample(all_seats, min(jumlah_penumpang, len(all_seats)))
            # Urutkan kursi untuk tampilan yang lebih rapi
            selected_seats.sort(key=lambda x: (int(x[1:]), x[0]))
            nomor_kursi = ", ".join(selected_seats)

        # Buat data pemesanan
        booking_data = {
            "flight_id": flight_id,
            "user_id": user_id,
            "nama_pemesan": nama_pemesan,
            "email": email,
            "telepon": telepon,
            "tanggal_keberangkatan": tanggal_keberangkatan,
            "jumlah_penumpang": jumlah_penumpang,
            "kelas_penerbangan": kelas_penerbangan,
            "nomor_kursi": nomor_kursi,
            "total_harga": total_harga,
            "status": "pending",
            "metode_pembayaran": None,
            "status_pembayaran": "unpaid",
            "catatan": catatan
        }

        # Simpan pemesanan ke database
        booking_result = await create_flight_booking(booking_data)

        # Format pesan konfirmasi
        result = "✅ Pemesanan penerbangan berhasil dibuat!\n\n"
        result += f"✈️ {flight_data['maskapai']} ({flight_data['kode_penerbangan']})\n"
        result += f"🛫 {flight_data['origin']} → {flight_data['destination']}\n"
        result += f"📅 Tanggal: {tanggal_keberangkatan}\n"
        result += f"🕒 Waktu: {flight_data['waktu_berangkat']} - {flight_data['waktu_tiba']} ({flight_data['durasi']})\n"
        result += f"👥 Penumpang: {jumlah_penumpang} orang\n"
        result += f"💺 Kelas: {kelas_penerbangan}\n"

        if nomor_kursi:
            result += f"💺 Nomor Kursi: {nomor_kursi}\n"

        if catatan:
            result += f"📝 Catatan: {catatan}\n"

        result += f"\n💰 Total: Rp {total_harga:,}\n"
        result += f"💳 Status pembayaran: Belum dibayar\n\n"
        result += f"🆔 ID Pemesanan: {booking_result['id']}\n\n"
        result += "Silakan lakukan pembayaran untuk mengkonfirmasi pemesanan Anda."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat membuat pemesanan: {str(e)}"

# User registration tools dihapus karena sudah dihandle di authentication system

@tool
async def get_current_datetime(format_type: str = "datetime"):
    """
    Mendapatkan tanggal dan waktu saat ini.

    Args:
        format_type (str): Format yang diinginkan ('date', 'time', 'datetime')

    Returns:
        String: Tanggal/waktu saat ini dalam format yang diminta
    """
    try:
        now = await async_now()

        if format_type == "date":
            return now.strftime("%Y-%m-%d")
        elif format_type == "time":
            return now.strftime("%H:%M:%S")
        elif format_type == "datetime":
            return now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return now.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        logging.error(f"Error getting current datetime: {e}")
        return "Error getting current datetime"

@tool
async def process_hotel_payment(booking_id: int, metode_pembayaran: str):
    """
    Memproses pembayaran untuk pemesanan hotel.

    Args:
        booking_id: ID pemesanan hotel
        metode_pembayaran: Metode pembayaran ('transfer bank', 'kartu kredit', 'e-wallet')

    Returns:
        String berisi konfirmasi pembayaran atau pesan error
    """
    try:
        logging.info(f"Memproses pembayaran untuk pemesanan hotel ID: {booking_id}")

        # Validasi metode pembayaran
        valid_methods = ['transfer bank', 'kartu kredit', 'e-wallet']
        if metode_pembayaran not in valid_methods:
            raise ValidationException(
                message=f"Metode pembayaran tidak valid. Pilihan: {', '.join(valid_methods)}",
                detail={"metode_pembayaran": metode_pembayaran}
            )

        # Buat data pembayaran
        payment_data = {
            "metode_pembayaran": metode_pembayaran,
            "status_pembayaran": "paid",
            "status": "confirmed"
        }

        # Update pembayaran
        result = await update_hotel_booking_payment(booking_id, payment_data)

        # Ambil detail pemesanan untuk respons
        hotel_data = await get_hotel_by_id(result['hotel_id'])

        # Format konfirmasi pembayaran
        response = "💳 Pembayaran berhasil dikonfirmasi!\n\n"
        response += f"🏨 {hotel_data['nama']}\n"
        response += f"🛏️ {result['tipe_kamar']} - {result['jumlah_kamar']} kamar\n"
        response += f"📅 Check-in: {result['tanggal_mulai']}\n"
        response += f"📅 Check-out: {result['tanggal_akhir']}\n"
        response += f"👥 Tamu: {result['jumlah_tamu']} orang\n\n"
        response += f"💰 Total: Rp {result['total_harga']:,}\n"
        response += f"💳 Metode pembayaran: {metode_pembayaran}\n"
        response += f"📊 Status: {result['status']}\n\n"
        response += f"🆔 ID Pemesanan: {booking_id}\n\n"
        response += "Terima kasih atas pembayaran Anda. Detail pemesanan telah dikirimkan ke email Anda."

        return response

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat memproses pembayaran: {str(e)}"

@tool
async def process_flight_payment(booking_id: int, metode_pembayaran: str):
    """
    Memproses pembayaran untuk pemesanan penerbangan.

    Args:
        booking_id: ID pemesanan penerbangan
        metode_pembayaran: Metode pembayaran ('transfer bank', 'kartu kredit', 'e-wallet')

    Returns:
        String berisi konfirmasi pembayaran atau pesan error
    """
    try:
        logging.info(f"Memproses pembayaran untuk pemesanan penerbangan ID: {booking_id}")

        # Validasi metode pembayaran
        valid_methods = ['transfer bank', 'kartu kredit', 'e-wallet']
        if metode_pembayaran not in valid_methods:
            raise ValidationException(
                message=f"Metode pembayaran tidak valid. Pilihan: {', '.join(valid_methods)}",
                detail={"metode_pembayaran": metode_pembayaran}
            )

        # Buat data pembayaran
        payment_data = {
            "metode_pembayaran": metode_pembayaran,
            "status_pembayaran": "paid",
            "status": "confirmed"
        }

        # Update pembayaran
        result = await update_flight_booking_payment(booking_id, payment_data)

        # Ambil detail pemesanan untuk respons
        flight_data = await get_flight_by_id(result['flight_id'])

        # Format konfirmasi pembayaran
        response = "💳 Pembayaran berhasil dikonfirmasi!\n\n"
        response += f"✈️ {flight_data['maskapai']} ({flight_data['kode_penerbangan']})\n"
        response += f"🛫 {flight_data['origin']} → {flight_data['destination']}\n"
        response += f"📅 Tanggal: {result['tanggal_keberangkatan']}\n"
        response += f"🕒 Waktu: {flight_data['waktu_berangkat']} - {flight_data['waktu_tiba']} ({flight_data['durasi']})\n"
        response += f"👥 Penumpang: {result['jumlah_penumpang']} orang\n"
        response += f"💺 Kelas: {result['kelas_penerbangan']}\n"

        if result.get('nomor_kursi'):
            response += f"💺 Nomor Kursi: {result['nomor_kursi']}\n"

        response += f"\n💰 Total: Rp {result['total_harga']:,}\n"
        response += f"💳 Metode pembayaran: {metode_pembayaran}\n"
        response += f"📊 Status: {result['status']}\n"
        response += f"💳 Status pembayaran: {result['status_pembayaran']}\n"

        if result.get('catatan'):
            response += f"\n📝 Catatan: {result['catatan']}\n"

        response += "\nTerima kasih atas pembayaran Anda. Detail pemesanan dan e-tiket telah dikirimkan ke email Anda."

        return response

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat memproses pembayaran: {str(e)}"

@tool
async def check_unpaid_bookings(user_id: int):
    """
    Memeriksa pemesanan yang belum dibayar untuk pengguna.

    Args:
        user_id: ID pengguna

    Returns:
        String berisi daftar pemesanan yang belum dibayar dan instruksi pembayaran
    """
    try:
        logging.info(f"Memeriksa pemesanan yang belum dibayar untuk pengguna ID: {user_id}")

        # Ambil semua pemesanan pengguna
        bookings = await get_user_bookings(user_id)
        hotel_bookings = bookings.get('hotel_bookings', [])
        flight_bookings = bookings.get('flight_bookings', [])
        tour_bookings = bookings.get('tour_bookings', [])

        # Filter pemesanan yang belum dibayar
        unpaid_hotel_bookings = [b for b in hotel_bookings if b.get('status_pembayaran') == 'unpaid']
        unpaid_flight_bookings = [b for b in flight_bookings if b.get('status_pembayaran') == 'unpaid']
        unpaid_tour_bookings = [b for b in tour_bookings if b.get('status_pembayaran') == 'unpaid']

        if not unpaid_hotel_bookings and not unpaid_flight_bookings and not unpaid_tour_bookings:
            return "✅ Anda tidak memiliki pemesanan yang belum dibayar saat ini."

        result = "📋 PEMESANAN YANG BELUM DIBAYAR:\n"
        result += "==============================\n\n"

        # Format pemesanan hotel yang belum dibayar
        if unpaid_hotel_bookings:
            result += "🏨 PEMESANAN HOTEL:\n"
            result += "-------------------\n\n"

            for booking in unpaid_hotel_bookings:
                hotel_info = booking.get('hotels', {})
                hotel_name = hotel_info.get('nama', f"Hotel ID {booking.get('hotel_id')}")

                result += f"🆔 Booking ID: {booking.get('id')}\n"
                result += f"🏨 {hotel_name}\n"
                result += f"📅 {booking.get('tanggal_mulai')} s/d {booking.get('tanggal_akhir')}\n"
                result += f"🛏️ {booking.get('tipe_kamar')} - {booking.get('jumlah_kamar')} kamar\n"
                result += f"💰 Total: Rp {booking.get('total_harga'):,}\n\n"

        # Format pemesanan penerbangan yang belum dibayar
        if unpaid_flight_bookings:
            result += "✈️ PEMESANAN PENERBANGAN:\n"
            result += "-------------------------\n\n"

            for booking in unpaid_flight_bookings:
                flight_info = booking.get('flights', {})
                airline = flight_info.get('maskapai', "")
                flight_code = flight_info.get('kode_penerbangan', "")
                origin = flight_info.get('origin', "")
                destination = flight_info.get('destination', "")

                result += f"🆔 Booking ID: {booking.get('id')}\n"
                result += f"✈️ {airline} ({flight_code})\n"
                result += f"🛫 {origin} → {destination}\n"
                result += f"📅 Tanggal: {booking.get('tanggal_keberangkatan')}\n"
                result += f"👥 {booking.get('jumlah_penumpang')} penumpang\n"
                result += f"💺 Kelas: {booking.get('kelas_penerbangan')}\n"

                # Tampilkan nomor kursi jika tersedia
                if booking.get('nomor_kursi'):
                    result += f"💺 Nomor Kursi: {booking.get('nomor_kursi')}\n"

                result += f"💰 Total: Rp {booking.get('total_harga'):,}\n\n"

        # Format pemesanan tour yang belum dibayar
        if unpaid_tour_bookings:
            result += "🎯 PEMESANAN TOUR:\n"
            result += "-------------------\n\n"

            for booking in unpaid_tour_bookings:
                tour_info = booking.get('tours', {})
                tour_name = tour_info.get('nama', f"Tour ID {booking.get('tour_id')}")
                destinasi = tour_info.get('destinasi', "")

                result += f"🆔 Booking ID: {booking.get('id')}\n"
                result += f"🎯 {tour_name}\n"
                result += f"📍 Destinasi: {destinasi}\n"
                result += f"📅 Tanggal tour: {booking.get('tanggal_tour')}\n"
                result += f"💰 Total: Rp {booking.get('total_harga'):,}\n\n"

        # Tambahkan instruksi pembayaran
        result += "💳 CARA MELAKUKAN PEMBAYARAN:\n"
        result += "-----------------------------\n\n"
        result += "1️⃣ Pilih metode pembayaran: transfer bank, kartu kredit, atau e-wallet\n"
        result += "2️⃣ Untuk melakukan pembayaran, gunakan perintah berikut:\n\n"

        if unpaid_hotel_bookings:
            result += "   Untuk pemesanan hotel:\n"
            result += "   \"Saya ingin membayar booking hotel dengan ID [booking_id] menggunakan [metode_pembayaran]\"\n\n"

        if unpaid_flight_bookings:
            result += "   Untuk pemesanan penerbangan:\n"
            result += "   \"Saya ingin membayar booking penerbangan dengan ID [booking_id] menggunakan [metode_pembayaran]\"\n\n"

        if unpaid_tour_bookings:
            result += "   Untuk pemesanan tour:\n"
            result += "   \"Saya ingin membayar booking tour dengan ID [booking_id] menggunakan [metode_pembayaran]\"\n\n"

        result += "Catatan: Booking yang tidak dibayar akan otomatis dibatalkan setelah 24 jam."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat memeriksa pemesanan: {str(e)}"

@tool
async def get_booking_details(booking_id: int, booking_type: str):
    """
    Mendapatkan detail pemesanan berdasarkan ID.

    Args:
        booking_id: ID pemesanan
        booking_type: Jenis pemesanan ('hotel', 'flight', atau 'tour')

    Returns:
        String berisi detail pemesanan
    """
    try:
        logging.info(f"Mendapatkan detail pemesanan {booking_type} ID: {booking_id}")

        if booking_type not in ['hotel', 'flight', 'tour']:
            raise ValidationException(
                message="Jenis pemesanan tidak valid. Pilihan: hotel, flight, tour",
                detail={"booking_type": booking_type}
            )

        # Ambil detail pemesanan berdasarkan jenisnya
        if booking_type == 'hotel':
            booking = await get_hotel_booking_by_id(booking_id)
            hotel_data = await get_hotel_by_id(booking['hotel_id'])

            # Format detail pemesanan hotel
            result = "🏨 DETAIL PEMESANAN HOTEL\n"
            result += "=======================\n\n"
            result += f"🆔 Booking ID: {booking['id']}\n"
            result += f"🏨 {hotel_data['nama']}\n"
            result += f"📍 {hotel_data['lokasi']}\n"
            result += f"⭐ {hotel_data['bintang']} bintang\n\n"
            result += f"👤 Pemesan: {booking['nama_pemesan']}\n"
            result += f"📧 Email: {booking['email']}\n"
            result += f"📞 Telepon: {booking['telepon']}\n\n"
            result += f"🛏️ {booking['tipe_kamar']} - {booking['jumlah_kamar']} kamar\n"
            result += f"👥 Tamu: {booking['jumlah_tamu']} orang\n"
            result += f"📅 Check-in: {booking['tanggal_mulai']}\n"
            result += f"📅 Check-out: {booking['tanggal_akhir']}\n\n"
            result += f"💰 Total: Rp {booking['total_harga']:,}\n"
            result += f"💳 Metode pembayaran: {booking['metode_pembayaran'] or 'Belum dipilih'}\n"
            result += f"📊 Status: {booking['status']}\n"
            result += f"💳 Status pembayaran: {booking['status_pembayaran']}\n"

            if booking['catatan']:
                result += f"\n📝 Catatan: {booking['catatan']}\n"

            # Tambahkan opsi pembayaran jika belum dibayar
            if booking['status_pembayaran'] == 'unpaid':
                result += "\n⚠️ Pemesanan ini belum dibayar. Silakan lakukan pembayaran untuk mengkonfirmasi pemesanan Anda."
                result += "\n💳 Gunakan perintah: \"Saya ingin membayar booking hotel dengan ID " + str(booking['id']) + " menggunakan [metode_pembayaran]\""
            elif booking['status_pembayaran'] == 'paid':
                result += "\n✅ Pemesanan ini telah dibayar dan dikonfirmasi."

        elif booking_type == 'flight':
            booking = await get_flight_booking_by_id(booking_id)
            flight_data = await get_flight_by_id(booking['flight_id'])

            # Format detail pemesanan penerbangan
            result = "✈️ DETAIL PEMESANAN PENERBANGAN\n"
            result += "==============================\n\n"
            result += f"🆔 Booking ID: {booking['id']}\n"
            result += f"✈️ {flight_data['maskapai']} ({flight_data['kode_penerbangan']})\n"
            result += f"🛫 {flight_data['origin']} → {flight_data['destination']}\n"
            result += f"📅 Tanggal: {booking['tanggal_keberangkatan']}\n"
            result += f"🕒 Waktu: {flight_data['waktu_berangkat']} - {flight_data['waktu_tiba']} ({flight_data['durasi']})\n\n"
            result += f"👤 Pemesan: {booking['nama_pemesan']}\n"
            result += f"📧 Email: {booking['email']}\n"
            result += f"📞 Telepon: {booking['telepon']}\n\n"
            result += f"👥 Penumpang: {booking['jumlah_penumpang']} orang\n"
            result += f"💺 Kelas: {booking['kelas_penerbangan']}\n"

            if booking['nomor_kursi']:
                result += f"💺 Nomor kursi: {booking['nomor_kursi']}\n"

            result += f"\n💰 Total: Rp {booking['total_harga']:,}\n"
            result += f"💳 Metode pembayaran: {booking['metode_pembayaran'] or 'Belum dipilih'}\n"
            result += f"📊 Status: {booking['status']}\n"
            result += f"💳 Status pembayaran: {booking['status_pembayaran']}\n"

            if booking['catatan']:
                result += f"\n📝 Catatan: {booking['catatan']}\n"

            # Tambahkan opsi pembayaran jika belum dibayar
            if booking['status_pembayaran'] == 'unpaid':
                result += "\n⚠️ Pemesanan ini belum dibayar. Silakan lakukan pembayaran untuk mengkonfirmasi pemesanan Anda."
                result += "\n💳 Gunakan perintah: \"Saya ingin membayar booking penerbangan dengan ID " + str(booking['id']) + " menggunakan [metode_pembayaran]\""
            elif booking['status_pembayaran'] == 'paid':
                result += "\n✅ Pemesanan ini telah dibayar dan dikonfirmasi."

        else:  # tour
            booking = await get_tour_booking_by_id(booking_id)
            tour_data = await get_tour_by_id(booking['tour_id'])

            # Format detail pemesanan tour
            result = "🎯 DETAIL PEMESANAN TOUR\n"
            result += "========================\n\n"
            result += f"🆔 Booking ID: {booking['id']}\n"
            result += f"🎯 {tour_data['nama']}\n"
            result += f"📍 Destinasi: {tour_data['destinasi']}\n"
            result += f"⏱️ Durasi: {tour_data['durasi']}\n"
            result += f"📅 Tanggal tour: {booking['tanggal_tour']}\n\n"
            result += f"👤 Pemesan: {booking['nama_pemesan']}\n"
            result += f"📧 Email: {booking['email']}\n"
            result += f"📞 Telepon: {booking['telepon']}\n\n"
            result += f"👥 Peserta: {booking['jumlah_peserta']} orang\n"
            result += f"💰 Total: Rp {booking['total_harga']:,}\n"
            result += f"💳 Metode pembayaran: {booking['metode_pembayaran'] or 'Belum dipilih'}\n"
            result += f"📊 Status: {booking['status']}\n"
            result += f"💳 Status pembayaran: {booking['status_pembayaran']}\n"

            if booking['catatan']:
                result += f"\n📝 Catatan: {booking['catatan']}\n"

            # Tambahkan opsi pembayaran jika belum dibayar
            if booking['status_pembayaran'] == 'unpaid':
                result += "\n⚠️ Pemesanan ini belum dibayar. Silakan lakukan pembayaran untuk mengkonfirmasi pemesanan Anda."
                result += "\n💳 Gunakan perintah: \"Saya ingin membayar booking tour dengan ID " + str(booking['id']) + " menggunakan [metode_pembayaran]\""
            elif booking['status_pembayaran'] == 'paid':
                result += "\n✅ Pemesanan ini telah dibayar dan dikonfirmasi."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil detail pemesanan: {str(e)}"

@tool
async def cancel_hotel_booking(booking_id: int):
    """
    Membatalkan pemesanan hotel.

    Args:
        booking_id (int): ID pemesanan hotel yang ingin dibatalkan

    Returns:
        String: Informasi pembatalan pemesanan hotel
    """
    try:
        if not booking_id:
            raise ValidationException(
                message="ID pemesanan hotel tidak boleh kosong",
                detail={"booking_id": booking_id}
            )

        logging.info(f"Membatalkan pemesanan hotel dengan ID: {booking_id}")

        # Mendapatkan informasi pemesanan untuk pesan konfirmasi
        booking_data = await get_hotel_booking_by_id(booking_id)
        hotel_data = await get_hotel_by_id(booking_data["hotel_id"])

        # Proses pembatalan
        updated_booking = await process_hotel_cancellation(booking_id)

        result = "✅ Pemesanan hotel berhasil dibatalkan\n\n"
        result += f"🏨 Hotel: {hotel_data['nama']}\n"
        result += f"📅 Tanggal: {booking_data['tanggal_mulai']} - {booking_data['tanggal_akhir']}\n"
        result += f"👤 Pemesan: {booking_data['nama_pemesan']}\n"
        result += f"💰 Total: Rp {booking_data['total_harga']:,}\n"

        if updated_booking["status_pembayaran"] == "refunded":
            result += f"\n💸 Status Pembayaran: REFUNDED (Dana akan dikembalikan)"

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat membatalkan pemesanan hotel: {str(e)}"

@tool
async def cancel_flight_booking(booking_id: int):
    """
    Membatalkan pemesanan penerbangan.

    Args:
        booking_id (int): ID pemesanan penerbangan yang ingin dibatalkan

    Returns:
        String: Informasi pembatalan pemesanan penerbangan
    """
    try:
        if not booking_id:
            raise ValidationException(
                message="ID pemesanan penerbangan tidak boleh kosong",
                detail={"booking_id": booking_id}
            )

        logging.info(f"Membatalkan pemesanan penerbangan dengan ID: {booking_id}")

        # Mendapatkan informasi pemesanan untuk pesan konfirmasi
        booking_data = await get_flight_booking_by_id(booking_id)
        flight_data = await get_flight_by_id(booking_data["flight_id"])

        # Proses pembatalan
        updated_booking = await process_flight_cancellation(booking_id)

        result = "✅ Pemesanan penerbangan berhasil dibatalkan\n\n"
        result += f"✈️ Penerbangan: {flight_data['maskapai']} ({flight_data['kode_penerbangan']})\n"
        result += f"🌍 Rute: {flight_data['origin']} → {flight_data['destination']}\n"
        result += f"📅 Tanggal: {booking_data['tanggal_keberangkatan']}\n"
        result += f"👤 Pemesan: {booking_data['nama_pemesan']}\n"
        result += f"👥 Penumpang: {booking_data['jumlah_penumpang']} orang\n"
        result += f"💺 Kelas: {booking_data['kelas_penerbangan']}\n"

        # Tampilkan nomor kursi jika tersedia
        if booking_data.get('nomor_kursi'):
            result += f"💺 Nomor Kursi: {booking_data['nomor_kursi']}\n"

        result += f"💰 Total: Rp {booking_data['total_harga']:,}\n"

        if updated_booking["status_pembayaran"] == "refunded":
            result += f"\n💸 Status Pembayaran: REFUNDED (Dana akan dikembalikan)"

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat membatalkan pemesanan penerbangan: {str(e)}"

# Tour Tools
@tool
async def get_tours():
    """
    Mendapatkan daftar semua paket tour yang tersedia.

    Returns:
        String: Daftar semua paket tour
    """
    try:
        logging.info("Mengambil daftar semua tour")

        tours_df = await get_all_tours()

        if tours_df.empty:
            return "Tidak ada paket tour yang tersedia saat ini."

        tours_count = len(tours_df)
        tours_list = []

        for _, tour in tours_df.iterrows():
            tour_info = f"🏝️ {tour['nama']} (⭐{tour['rating']})\n"
            tour_info += f"   📍 {tour['destinasi']}\n"
            tour_info += f"   ⏱️ Durasi: {tour['durasi']}\n"
            tour_info += f"   💰 Harga: Rp {tour['harga']:,}/orang\n"
            tour_info += f"   👥 Kapasitas: {tour['kapasitas']} orang\n"
            tour_info += f"   🆔 ID: {tour['id']}\n"

            tours_list.append(tour_info)

        result = f"Ditemukan {tours_count} paket tour tersedia:\n\n"
        result += "\n".join(tours_list)
        result += "\n\nUntuk melihat detail tour dan ketersediaan, gunakan ID tour."

        return result

    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil daftar tour: {str(e)}"

@tool
async def search_tours_by_destination(destination: str):
    """
    Mencari paket tour berdasarkan destinasi.

    Args:
        destination (str): Destinasi tour yang ingin dicari (contoh: "Ubud", "Kintamani", "Bali")

    Returns:
        String: Daftar tour di destinasi tersebut
    """
    try:
        if not destination or len(destination.strip()) == 0:
            raise ValidationException(
                message="Destinasi tidak boleh kosong",
                detail={"destination": destination}
            )

        logging.info(f"Mencari tour di destinasi: {destination}")

        # Import fungsi dari database.services untuk menghindari recursive call
        from database.services import search_tours_by_destination as service_search_tours_by_destination
        tours_df = await service_search_tours_by_destination(destination)

        if tours_df.empty:
            return f"Tidak ditemukan paket tour di destinasi {destination}."

        tours_count = len(tours_df)
        tours_list = []

        for _, tour in tours_df.iterrows():
            tour_info = f"🏝️ {tour['nama']} (⭐{tour['rating']})\n"
            tour_info += f"   📍 {tour['destinasi']}\n"
            tour_info += f"   ⏱️ Durasi: {tour['durasi']}\n"
            tour_info += f"   💰 Harga: Rp {tour['harga']:,}/orang\n"
            tour_info += f"   👥 Kapasitas: {tour['kapasitas']} orang\n"
            tour_info += f"   🏷️ Kategori: {tour['kategori']}\n"
            tour_info += f"   🆔 ID: {tour['id']}\n"

            tours_list.append(tour_info)

        result = f"Ditemukan {tours_count} paket tour di {destination}:\n\n"
        result += "\n".join(tours_list)
        result += "\n\nUntuk melihat detail tour dan ketersediaan, gunakan ID tour."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mencari tour: {str(e)}"

@tool
async def get_tour_details(tour_id: int):
    """
    Mendapatkan detail lengkap paket tour berdasarkan ID.

    Args:
        tour_id (int): ID tour yang ingin dilihat detailnya

    Returns:
        String: Informasi detail tentang paket tour
    """
    try:
        if not tour_id:
            raise ValidationException(
                message="ID tour tidak boleh kosong",
                detail={"tour_id": tour_id}
            )

        logging.info(f"Mengambil detail tour dengan ID: {tour_id}")

        tour_data = await get_tour_by_id(tour_id)

        # Format informasi tour
        tour_info = f"🏝️ {tour_data['nama']} (⭐{tour_data['rating']})\n"
        tour_info += f"📍 Destinasi: {tour_data['destinasi']}\n"
        tour_info += f"⏱️ Durasi: {tour_data['durasi']}\n"
        tour_info += f"💰 Harga: Rp {tour_data['harga']:,}/orang\n"
        tour_info += f"👥 Kapasitas: {tour_data['kapasitas']} orang\n"
        tour_info += f"🏷️ Kategori: {tour_data['kategori']}\n"
        tour_info += f"📊 Tingkat Kesulitan: {tour_data['tingkat_kesulitan']}\n\n"

        if tour_data['deskripsi']:
            tour_info += f"📝 Deskripsi:\n{tour_data['deskripsi']}\n\n"

        # Include information
        includes = []
        if tour_data.get('include_transport'):
            includes.append("🚌 Transportasi")
        if tour_data.get('include_meal'):
            includes.append("🍽️ Makanan")
        if tour_data.get('include_guide'):
            includes.append("👨‍🏫 Guide")

        if includes:
            tour_info += f"✅ Termasuk: {', '.join(includes)}\n\n"

        if 'fasilitas' in tour_data and tour_data['fasilitas']:
            tour_info += f"✨ Fasilitas:\n{', '.join(tour_data['fasilitas'])}\n\n"

        if 'itinerary' in tour_data and tour_data['itinerary']:
            tour_info += "📋 Itinerary:\n"
            for i, item in enumerate(tour_data['itinerary'], 1):
                tour_info += f"  {i}. {item}\n"
            tour_info += "\n"

        tour_info += "Untuk memeriksa ketersediaan dan memesan, silakan berikan tanggal yang diinginkan."

        return tour_info

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengambil detail tour: {str(e)}"

@tool
async def check_tour_availability(tour_id: int, tanggal: str):
    """
    Memeriksa ketersediaan paket tour pada tanggal tertentu.

    Args:
        tour_id (int): ID tour
        tanggal (str): Tanggal tour dalam format YYYY-MM-DD

    Returns:
        String: Informasi ketersediaan tour
    """
    try:
        if not tour_id or not tanggal:
            raise ValidationException(
                message="ID tour dan tanggal harus diisi",
                detail={"tour_id": tour_id, "tanggal": tanggal}
            )

        # Validasi format tanggal
        try:
            await async_strptime(tanggal, "%Y-%m-%d")
        except ValueError:
            raise ValidationException(
                message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2023-12-31)",
                detail={"tanggal": tanggal}
            )

        logging.info(f"Memeriksa ketersediaan tour {tour_id} pada tanggal {tanggal}")

        # Import fungsi dari database.services untuk menghindari recursive call
        from database.services import check_tour_availability as service_check_tour_availability
        availability = await service_check_tour_availability(tour_id, tanggal)

        if not availability:
            return f"Maaf, tour dengan ID {tour_id} tidak tersedia pada tanggal {tanggal}."

        result = f"✅ Tour tersedia!\n\n"
        result += f"🏝️ {availability['nama_tour']}\n"
        result += f"📅 Tanggal: {tanggal}\n"
        result += f"⏰ Waktu: {availability['waktu_mulai']} - {availability['waktu_selesai']}\n"
        result += f"👥 Jumlah tersedia: {availability['jumlah_tersedia']} orang\n"
        result += f"💰 Harga: Rp {availability['harga']:,}/orang\n\n"
        result += "Tour ini tersedia untuk tanggal yang Anda pilih. Silakan lakukan pemesanan jika berminat."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mengecek ketersediaan tour: {str(e)}"

@tool
async def book_tour(tour_id: int, tanggal_tour: str, nama_pemesan: str, email: str,
                   telepon: str, jumlah_peserta: int, user_id: Optional[int] = None,
                   catatan: Optional[str] = None):
    """
    Membuat pemesanan paket tour.

    Args:
        tour_id (int): ID tour
        tanggal_tour (str): Tanggal tour dalam format YYYY-MM-DD
        nama_pemesan (str): Nama lengkap pemesan
        email (str): Alamat email pemesan
        telepon (str): Nomor telepon pemesan
        jumlah_peserta (int): Jumlah peserta tour
        user_id (int, optional): ID pengguna jika sudah terdaftar
        catatan (str, optional): Catatan tambahan untuk pemesanan

    Returns:
        String: Konfirmasi pemesanan berhasil
    """
    try:
        # Validasi input dasar
        if not tour_id or not tanggal_tour or not nama_pemesan or not email or not telepon:
            raise ValidationException(
                message="Semua data pemesanan harus diisi",
                detail={"tour_id": tour_id, "tanggal_tour": tanggal_tour}
            )

        # Validasi format tanggal
        try:
            await async_strptime(tanggal_tour, "%Y-%m-%d")
        except ValueError:
            raise ValidationException(
                message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2023-12-31)",
                detail={"tanggal_tour": tanggal_tour}
            )

        # Ambil detail tour untuk validasi dan perhitungan harga
        tour_data = await get_tour_by_id(tour_id)

        # Periksa ketersediaan tour
        from database.services import check_tour_availability as service_check_tour_availability
        availability = await service_check_tour_availability(tour_id, tanggal_tour)
        if not availability:
            raise ValidationException(
                message=f"Tour tidak tersedia pada tanggal {tanggal_tour}",
                detail={"tour_id": tour_id, "tanggal": tanggal_tour}
            )

        # Periksa apakah jumlah peserta tidak melebihi jumlah tersedia
        if jumlah_peserta > availability['jumlah_tersedia']:
            raise ValidationException(
                message=f"Hanya tersedia {availability['jumlah_tersedia']} slot untuk tanggal tersebut",
                detail={"jumlah_peserta": jumlah_peserta, "tersedia": availability['jumlah_tersedia']}
            )

        # Cek dan proses user_id
        if not user_id:
            # Cek apakah email sudah terdaftar
            existing_user = await get_user_by_email(email)

            if existing_user:
                # Gunakan user_id yang sudah ada
                user_id = existing_user['id']
                logging.info(f"Menggunakan user yang sudah terdaftar dengan ID: {user_id}")
            else:
                logging.info(f"User dengan email {email} tidak ditemukan. Booking akan dilanjutkan tanpa user_id.")

        # Hitung total harga
        total_harga = tour_data['harga'] * jumlah_peserta

        # Buat data pemesanan (sama seperti hotel dan flight booking)
        booking_data = {
            "tour_id": tour_id,
            "user_id": user_id,
            "nama_pemesan": nama_pemesan,
            "email": email,
            "telepon": telepon,
            "tanggal_tour": tanggal_tour,
            "jumlah_peserta": jumlah_peserta,
            "total_harga": total_harga,
            "status": "pending",
            "metode_pembayaran": None,
            "status_pembayaran": "unpaid",
            "catatan": catatan
        }



        # Simpan pemesanan ke database
        booking_result = await create_tour_booking(booking_data)

        # Format pesan konfirmasi
        result = "✅ Pemesanan tour berhasil dibuat!\n\n"
        result += f"🏝️ {tour_data['nama']}\n"
        result += f"📍 {tour_data['destinasi']}\n"
        result += f"📅 Tanggal: {tanggal_tour}\n"
        result += f"⏰ Waktu: {availability['waktu_mulai']} - {availability['waktu_selesai']}\n"
        result += f"👥 Peserta: {jumlah_peserta} orang\n"

        if catatan:
            result += f"📝 Catatan: {catatan}\n"

        result += f"\n💰 Total: Rp {total_harga:,}\n"
        result += f"💳 Status pembayaran: Belum dibayar\n\n"
        result += f"🆔 ID Pemesanan: {booking_result['id']}\n"

        # Info pendaftaran telah dihapus karena user registration sekarang dihandle oleh sistem autentikasi

        logging.info(f"Pemesanan tour berhasil dibuat dengan ID: {booking_result['id']}")

        result += "\nSilakan lakukan pembayaran untuk mengkonfirmasi pemesanan Anda."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat membuat pemesanan tour: {str(e)}"

@tool
async def process_tour_payment(booking_id: int, metode_pembayaran: str):
    """
    Memproses pembayaran untuk pemesanan tour.

    Args:
        booking_id (int): ID pemesanan tour
        metode_pembayaran (str): Metode pembayaran (contoh: "transfer bank", "kartu kredit", "e-wallet")

    Returns:
        String: Konfirmasi pembayaran berhasil
    """
    try:
        if not booking_id or not metode_pembayaran:
            raise ValidationException(
                message="ID pemesanan dan metode pembayaran harus diisi",
                detail={"booking_id": booking_id, "metode_pembayaran": metode_pembayaran}
            )

        logging.info(f"Memproses pembayaran untuk pemesanan tour ID: {booking_id}")

        # Ambil detail pemesanan sebelum update
        booking_data = await get_tour_booking_by_id(booking_id)

        # Data pembayaran
        payment_data = {
            "metode_pembayaran": metode_pembayaran,
            "status_pembayaran": "paid",
            "status": "confirmed"
        }

        # Update status pembayaran
        updated_booking = await update_tour_booking_payment(booking_id, payment_data)

        # Format pesan konfirmasi
        result = "✅ Pembayaran tour berhasil diproses!\n\n"
        result += f"🆔 ID Pemesanan: {booking_id}\n"

        tour_data = booking_data.get('tours', {})
        tour_name = tour_data.get('nama', f"Tour ID {booking_data.get('tour_id')}")

        result += f"🏝️ {tour_name}\n"
        result += f"📍 {tour_data.get('destinasi', 'N/A')}\n"
        result += f"📅 Tanggal: {booking_data.get('tanggal_tour')}\n"
        result += f"👤 Pemesan: {booking_data.get('nama_pemesan')}\n"
        result += f"👥 Peserta: {booking_data.get('jumlah_peserta')} orang\n"
        result += f"💰 Total: Rp {booking_data.get('total_harga'):,}\n"
        result += f"💳 Metode: {metode_pembayaran}\n"
        result += f"📊 Status: CONFIRMED\n\n"
        result += "Terima kasih! Pemesanan tour Anda telah dikonfirmasi."

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat memproses pembayaran tour: {str(e)}"

@tool
async def cancel_tour_booking(booking_id: int):
    """
    Membatalkan pemesanan tour.

    Args:
        booking_id (int): ID pemesanan tour yang akan dibatalkan

    Returns:
        String: Konfirmasi pembatalan berhasil
    """
    try:
        if not booking_id:
            raise ValidationException(
                message="ID pemesanan tidak boleh kosong",
                detail={"booking_id": booking_id}
            )

        logging.info(f"Membatalkan pemesanan tour dengan ID: {booking_id}")

        # Ambil detail pemesanan sebelum dibatalkan
        booking_data = await get_tour_booking_by_id(booking_id)

        # Batalkan pemesanan
        updated_booking = await process_tour_cancellation(booking_id)

        # Format pesan konfirmasi
        result = "✅ Pemesanan tour berhasil dibatalkan!\n\n"
        result += f"🆔 ID Pemesanan: {booking_id}\n"

        tour_data = booking_data.get('tours', {})
        tour_name = tour_data.get('nama', f"Tour ID {booking_data.get('tour_id')}")

        result += f"🏝️ {tour_name}\n"
        result += f"📍 {tour_data.get('destinasi', 'N/A')}\n"
        result += f"📅 Tanggal: {booking_data.get('tanggal_tour')}\n"
        result += f"👤 Pemesan: {booking_data.get('nama_pemesan')}\n"
        result += f"👥 Peserta: {booking_data.get('jumlah_peserta')} orang\n"
        result += f"💰 Total: Rp {booking_data.get('total_harga'):,}\n"

        if updated_booking["status_pembayaran"] == "refunded":
            result += f"\n💸 Status Pembayaran: REFUNDED (Dana akan dikembalikan)"

        return result

    except ValidationException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except NotFoundException as e:
        log_exception(e)
        return f"Error: {e.message}"
    except DatabaseException as e:
        log_exception(e)
        return f"Error sistem: {e.message}"
    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat membatalkan pemesanan tour: {str(e)}"


# ===== TAVILY WEB SEARCH HELPER FUNCTIONS =====

import re
import hashlib

# TTL untuk cache search tools (30 menit = 1800 detik)
SEARCH_CACHE_TTL = 1800

def generate_search_cache_key(tool_name: str, **params) -> str:
    """
    Generate cache key untuk search tools berdasarkan nama tool dan parameter.

    Args:
        tool_name (str): Nama tool (currency_rates, travel_articles, general_info)
        **params: Parameter pencarian

    Returns:
        str: Cache key yang unik
    """
    # Gabungkan semua parameter menjadi string yang konsisten
    params_str = "_".join([f"{k}:{v}" for k, v in sorted(params.items())])

    # Hash untuk memastikan key tidak terlalu panjang dan konsisten
    params_hash = hashlib.md5(params_str.encode()).hexdigest()

    return f"agen_travel:web_search:{tool_name}:{params_hash}"

async def get_cached_search_result(cache_key: str) -> Optional[Dict]:
    """
    Mengambil hasil pencarian dari cache.

    Args:
        cache_key (str): Cache key

    Returns:
        Optional[Dict]: Hasil pencarian dari cache atau None jika tidak ada
    """
    import time
    start_time = time.time()

    try:
        cached_result = await redis_cache.get(cache_key)

        # Record metrics
        cache_type = "web_search"
        if cached_result:
            CACHE_HITS.labels(cache_type=cache_type, operation="get").inc()
            CACHE_OPERATIONS.labels(cache_type=cache_type, operation="get", status="hit").inc()
            logging.info(f"Cache hit untuk web search: {cache_key}")
        else:
            CACHE_MISSES.labels(cache_type=cache_type, operation="get").inc()
            CACHE_OPERATIONS.labels(cache_type=cache_type, operation="get", status="miss").inc()
            logging.info(f"Cache miss untuk web search: {cache_key}")

        # Record response time
        response_time = time.time() - start_time
        CACHE_RESPONSE_TIME.labels(cache_type=cache_type, operation="get").observe(response_time)

        return cached_result

    except Exception as e:
        # Record error metrics
        CACHE_OPERATIONS.labels(cache_type="web_search", operation="get", status="error").inc()
        logging.warning(f"Error mengambil cache {cache_key}: {e}")
        return None

async def set_search_cache(cache_key: str, result: Dict) -> bool:
    """
    Menyimpan hasil pencarian ke cache.

    Args:
        cache_key (str): Cache key
        result (Dict): Hasil pencarian yang akan disimpan

    Returns:
        bool: True jika berhasil disimpan
    """
    import time
    start_time = time.time()

    try:
        success = await redis_cache.set(cache_key, result, SEARCH_CACHE_TTL)

        # Record metrics
        cache_type = "web_search"
        status = "success" if success else "error"
        CACHE_OPERATIONS.labels(cache_type=cache_type, operation="set", status=status).inc()

        # Record response time
        response_time = time.time() - start_time
        CACHE_RESPONSE_TIME.labels(cache_type=cache_type, operation="set").observe(response_time)

        if success:
            logging.info(f"Hasil pencarian berhasil disimpan ke cache: {cache_key}")
        return success

    except Exception as e:
        # Record error metrics
        CACHE_OPERATIONS.labels(cache_type="search", operation="set", status="error").inc()
        logging.warning(f"Error menyimpan cache {cache_key}: {e}")
        return False

def extract_currency_rate(text: str, currency_pair: str = "USD to IDR") -> str:
    """
    Ekstrak nilai kurs mata uang dari teks konten.

    Args:
        text (str): Konten teks untuk dicari
        currency_pair (str): Pasangan mata uang yang dicari

    Returns:
        str: Informasi nilai kurs yang diekstrak atau string kosong
    """
    if not text:
        return ""

    # Pola regex untuk mencari nilai kurs
    patterns = [
        r'1\s*USD\s*=\s*([0-9,]+\.?[0-9]*)\s*IDR',
        r'USD/IDR\s*([0-9,]+\.?[0-9]*)',
        r'([0-9,]+\.?[0-9]*)\s*rupiah',
        r'Rp\s*([0-9,]+\.?[0-9]*)',
        r'([0-9,]+\.?[0-9]*)\s*Indonesian\s*Rupiah',
        r'exchange\s*rate.*?([0-9,]+\.?[0-9]*)',
        r'rate.*?([0-9,]+\.?[0-9]*)\s*IDR'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Kembalikan match pertama yang masuk akal (harus > 10000 untuk USD to IDR)
            for match in matches:
                try:
                    value = float(match.replace(',', ''))
                    if 10000 <= value <= 20000:  # Range yang masuk akal untuk USD to IDR
                        return f"1 USD = Rp {match}"
                except ValueError:
                    continue

    return ""



def format_source_info(title: str, url: str, index: int) -> str:
    """
    Format informasi sumber dengan konsisten.

    Args:
        title (str): Judul sumber
        url (str): URL sumber
        index (int): Nomor urut sumber

    Returns:
        str: Informasi sumber yang terformat
    """
    clean_title = title if title and title != 'N/A' else f"Sumber {index}"
    # Hapus semua spasi dari URL
    clean_url = url.replace(' ', '') if url and url != 'N/A' else url

    return f"🏦 **Sumber {index}: {clean_title}**\n🔗 **Link:** {clean_url}\n"

async def search_tavily_api(query: str, topic: str = "general", max_results: int = 5, include_answer: bool = True) -> dict:
    """
    Melakukan pencarian web menggunakan Tavily API secara langsung.

    Args:
        query (str): Query pencarian
        topic (str): Topik pencarian ("general", "finance", "news", dll.)
        max_results (int): Jumlah maksimal hasil pencarian
        include_answer (bool): Apakah menyertakan jawaban yang dihasilkan AI

    Returns:
        dict: Response dari Tavily API
    """
    if not TAVILY_API_KEY:
        return {"error": "Kunci API Tavily tidak ditemukan. Silakan set TAVILY_API_KEY di file .env Anda."}

    payload = {
        "query": query,
        "topic": topic,
        "search_depth": "advanced",  # Gunakan advanced untuk hasil yang lebih baik
        "chunks_per_source": 5,      # Tingkatkan chunks untuk konten lebih banyak
        "max_results": max_results,
        "time_range": None,
        "days": 3,
        "include_answer": include_answer,
        "include_raw_content": True,  # Sertakan raw content untuk info detail
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [],       # Kosong untuk pencarian lebih luas dan terbaru
        "exclude_domains": []
    }

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TAVILY_SEARCH_URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logging.error(f"Kesalahan HTTP Tavily API: {e}")
        return {"error": f"Kesalahan HTTP: {str(e)}"}
    except Exception as e:
        logging.error(f"Kesalahan Tavily API: {e}")
        return {"error": f"Kesalahan API: {str(e)}"}

# ===== TAVILY WEB SEARCH TOOLS =====

@tool
async def search_currency_rates(currency_pair: str = "USD to IDR"):
    """
    Mencari informasi kurs mata uang terkini menggunakan web search dengan Redis cache.

    Args:
        currency_pair (str): Pasangan mata uang yang dicari (contoh: "USD to IDR", "EUR to IDR")

    Returns:
        String: Informasi kurs mata uang terkini
    """
    try:
        logging.info(f"Mencari kurs mata uang: {currency_pair}")

        # Check if Tavily is available
        if not TAVILY_AVAILABLE:
            return "❌ Maaf, fitur pencarian web sedang tidak tersedia. Pastikan TAVILY_API_KEY sudah diset di environment variables."

        # Generate cache key berdasarkan currency pair
        cache_key = generate_search_cache_key("currency_rates", currency_pair=currency_pair)

        # Cek cache terlebih dahulu
        cached_result = await get_cached_search_result(cache_key)
        if cached_result:
            # Jika ada di cache, kembalikan hasil dari cache dengan indikator
            cached_response = cached_result.get('result', '')
            cache_info = f"\n\n🔄 **INFO CACHE:** Data ini diambil dari cache (TTL: {SEARCH_CACHE_TTL//60} menit)\n"
            cache_info += f"💾 Untuk data terbaru, tunggu hingga cache expired atau coba lagi nanti."
            return cached_response + cache_info

        # Query pencarian yang lebih spesifik untuk mendapatkan nilai kurs aktual
        query = f"{currency_pair} exchange rate today berapa rupiah 1 dollar nilai kurs hari ini"

        # Lakukan pencarian menggunakan Tavily API langsung
        search_results = await search_tavily_api(
            query=query,
            topic="finance",  # Gunakan topic finance untuk kurs
            max_results=3,
            include_answer=True
        )

        # Log pencarian query saja
        logging.info(f"Pencarian Tavily: {query}")

        # Handle error response
        if "error" in search_results:
            return f"❌ Terjadi kesalahan saat mencari informasi kurs: {search_results['error']}"

        if not search_results.get('results'):
            return f"Maaf, tidak dapat menemukan informasi kurs {currency_pair} saat ini."

        # Format hasil pencarian dengan data yang jelas
        result = f"💱 **INFORMASI KURS {currency_pair.upper()} HARI INI**\n\n"

        # Tampilkan answer dari Tavily jika ada (ringkasan AI)
        answer = search_results.get('answer', '')
        if answer and answer.strip():
            result += f"📈 **RINGKASAN KURS:**\n{answer}\n\n"

        # Coba ekstrak nilai kurs dari semua sumber
        extracted_rates = []
        results_list = search_results.get('results', [])

        for item in results_list:
            content = item.get('content', '')
            raw_content = item.get('raw_content', '')
            all_content = f"{content} {raw_content}"

            rate = extract_currency_rate(all_content, currency_pair)
            if rate:
                extracted_rates.append(rate)

        # Tampilkan nilai kurs yang ditemukan
        if extracted_rates:
            result += f"💰 **NILAI KURS DITEMUKAN:**\n"
            for rate in extracted_rates[:3]:  # Maksimal 3 nilai
                result += f"• {rate}\n"
            result += "\n"

        # Tampilkan detail dari setiap sumber dengan format yang konsisten
        for i, item in enumerate(results_list[:3], 1):
            title = item.get('title', 'N/A')
            url = item.get('url', 'N/A')
            content = item.get('content', 'N/A')
            raw_content = item.get('raw_content', '')

            # Log URL sumber dari Tavily
            logging.info(f"URL sumber dari Tavily: {url.replace(' ', '') if url and url != 'N/A' else url}")

            # Format header sumber dengan URL yang bersih
            result += format_source_info(title, url, i)

            # Prioritaskan raw_content untuk informasi lebih detail
            display_content = raw_content if raw_content and raw_content.strip() else content

            if display_content and display_content != 'N/A' and len(display_content.strip()) > 0:
                # Tampilkan konten lengkap untuk informasi kurs
                result += f"📊 **Informasi:** {display_content}\n"

                # Coba ekstrak nilai kurs dari konten ini
                rate = extract_currency_rate(display_content, currency_pair)
                if rate:
                    result += f"💱 **Nilai Kurs Ditemukan:** {rate}\n"
            else:
                result += f"📊 **Informasi:** Silakan kunjungi link di atas untuk detail lengkap\n"

            result += "\n"

        result += "💡 **CATATAN PENTING:**\n"
        result += "• Kurs dapat berubah sewaktu-waktu\n"
        result += "• Untuk transaksi resmi, silakan cek langsung ke bank atau money changer\n"
        result += "• Kurs di atas adalah untuk referensi saja"

        # Simpan hasil ke cache untuk penggunaan selanjutnya
        cache_data = {
            'result': result,
            'search_results': search_results,
            'timestamp': datetime.now().isoformat(),
            'currency_pair': currency_pair
        }
        await set_search_cache(cache_key, cache_data)

        # Tambahkan info bahwa data fresh dari API
        result += f"\n\n🆕 **INFO:** Data fresh dari Tavily API (disimpan ke cache untuk {SEARCH_CACHE_TTL//60} menit)"

        return result

    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mencari informasi kurs: {str(e)}"


@tool
async def search_travel_articles(destination: str = "Indonesia", topic: str = "wisata"):
    """
    Mencari artikel dan informasi travel terkini menggunakan web search dengan Redis cache.

    Args:
        destination (str): Destinasi wisata yang dicari (contoh: "Bali", "Jakarta", "Indonesia")
        topic (str): Topik artikel (contoh: "wisata", "kuliner", "hotel", "tips travel")

    Returns:
        String: Artikel dan informasi travel terkini
    """
    try:
        logging.info(f"Mencari artikel travel: {destination} - {topic}")

        # Check if Tavily is available
        if not TAVILY_AVAILABLE:
            return "❌ Maaf, fitur pencarian web sedang tidak tersedia. Pastikan TAVILY_API_KEY sudah diset di environment variables."

        # Generate cache key berdasarkan destination dan topic
        cache_key = generate_search_cache_key("travel_articles", destination=destination, topic=topic)

        # Cek cache terlebih dahulu
        cached_result = await get_cached_search_result(cache_key)
        if cached_result:
            # Jika ada di cache, kembalikan hasil dari cache dengan indikator
            cached_response = cached_result.get('result', '')
            cache_info = f"\n\n🔄 **INFO CACHE:** Data ini diambil dari cache (TTL: {SEARCH_CACHE_TTL//60} menit)\n"
            cache_info += f"💾 Untuk artikel terbaru, tunggu hingga cache expired atau coba lagi nanti."
            return cached_response + cache_info

        # Query pencarian yang lebih spesifik untuk travel
        query = f"{topic} {destination} travel Indonesia artikel tips panduan wisata"

        # Lakukan pencarian menggunakan Tavily API langsung
        search_results = await search_tavily_api(
            query=query,
            topic="general",  # Gunakan topic general untuk travel
            max_results=5,
            include_answer=False  # Tidak perlu answer untuk artikel
        )

        # Log pencarian query saja
        logging.info(f"Pencarian Tavily: {query}")

        # Handle error response
        if "error" in search_results:
            return f"❌ Terjadi kesalahan saat mencari artikel travel: {search_results['error']}"

        if not search_results.get('results'):
            return f"Maaf, tidak dapat menemukan artikel tentang {topic} di {destination} saat ini."

        # Format hasil pencarian
        result = f"📰 **ARTIKEL TRAVEL: {topic.title()} di {destination.title()}**\n\n"

        # Tampilkan detail dari setiap artikel dengan format yang konsisten
        results_list = search_results.get('results', [])
        for i, item in enumerate(results_list[:5], 1):
            title = item.get('title', 'N/A')
            url = item.get('url', 'N/A')
            content = item.get('content', 'N/A')
            raw_content = item.get('raw_content', '')

            # Log URL sumber dari Tavily
            logging.info(f"URL sumber dari Tavily: {url.replace(' ', '') if url and url != 'N/A' else url}")

            # Format header artikel dengan URL yang dibersihkan dari spasi
            clean_title = title if title and title != 'N/A' else f"Artikel {i}"
            # Hapus semua spasi dari URL
            clean_url = url.replace(' ', '') if url and url != 'N/A' else url

            result += f"📖 **{i}. {clean_title}**\n"
            result += f"🔗 **Sumber:** {clean_url}\n"

            # Prioritaskan raw_content untuk artikel lengkap
            display_content = raw_content if raw_content and raw_content.strip() else content

            if display_content and display_content != 'N/A' and len(display_content.strip()) > 0:
                # Tampilkan konten artikel lengkap
                result += f"📝 **Isi Artikel:** {display_content}\n"
            else:
                result += f"📝 **Isi Artikel:** Silakan kunjungi link di atas untuk membaca artikel lengkap\n"

            result += "\n"

        result += "✈️ *Semoga informasi ini membantu perencanaan perjalanan Anda!*"

        # Simpan hasil ke cache untuk penggunaan selanjutnya
        cache_data = {
            'result': result,
            'search_results': search_results,
            'timestamp': datetime.now().isoformat(),
            'destination': destination,
            'topic': topic
        }
        await set_search_cache(cache_key, cache_data)

        # Tambahkan info bahwa data fresh dari API
        result += f"\n\n🆕 **INFO:** Data fresh dari Tavily API (disimpan ke cache untuk {SEARCH_CACHE_TTL//60} menit)"

        return result

    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mencari artikel travel: {str(e)}"


@tool
async def search_general_info(query: str):
    """
    Mencari informasi umum menggunakan web search dengan Redis cache untuk pertanyaan yang tidak terkait langsung dengan booking.

    Args:
        query (str): Pertanyaan atau topik yang ingin dicari

    Returns:
        String: Informasi umum hasil pencarian web
    """
    try:
        logging.info(f"Mencari informasi umum: {query}")

        # Check if Tavily is available
        if not TAVILY_AVAILABLE:
            return "❌ Maaf, fitur pencarian web sedang tidak tersedia. Pastikan TAVILY_API_KEY sudah diset di environment variables."

        # Generate cache key berdasarkan query
        cache_key = generate_search_cache_key("general_info", query=query)

        # Cek cache terlebih dahulu
        cached_result = await get_cached_search_result(cache_key)
        if cached_result:
            # Jika ada di cache, kembalikan hasil dari cache dengan indikator
            cached_response = cached_result.get('result', '')
            cache_info = f"\n\n🔄 **INFO CACHE:** Data ini diambil dari cache (TTL: {SEARCH_CACHE_TTL//60} menit)\n"
            cache_info += f"💾 Untuk informasi terbaru, tunggu hingga cache expired atau coba lagi nanti."
            return cached_response + cache_info

        # Lakukan pencarian menggunakan Tavily API langsung
        search_results = await search_tavily_api(
            query=query,
            topic="general",
            max_results=3,
            include_answer=True  # Include answer untuk ringkasan
        )

        # Log pencarian query saja
        logging.info(f"Pencarian Tavily: {query}")

        # Handle error response
        if "error" in search_results:
            return f"❌ Terjadi kesalahan saat mencari informasi: {search_results['error']}"

        if not search_results.get('results'):
            return f"Maaf, tidak dapat menemukan informasi tentang '{query}' saat ini."

        # Format hasil pencarian
        result = f"🔍 **HASIL PENCARIAN: {query}**\n\n"

        # Tampilkan answer dari Tavily jika ada (ringkasan AI)
        answer = search_results.get('answer', '')
        if answer and answer.strip():
            result += f"💡 **RINGKASAN:**\n{answer}\n\n"

        # Tampilkan detail dari setiap sumber dengan format yang konsisten
        results_list = search_results.get('results', [])
        for i, item in enumerate(results_list[:3], 1):
            title = item.get('title', 'N/A')
            url = item.get('url', 'N/A')
            content = item.get('content', 'N/A')
            raw_content = item.get('raw_content', '')

            # Log URL sumber dari Tavily
            logging.info(f"URL sumber dari Tavily: {url.replace(' ', '') if url and url != 'N/A' else url}")

            # Format header sumber dengan URL yang bersih
            result += format_source_info(title, url, i)

            # Prioritaskan raw_content untuk informasi lebih detail
            display_content = raw_content if raw_content and raw_content.strip() else content

            if display_content and display_content != 'N/A' and len(display_content.strip()) > 0:
                result += f"📄 **Informasi:** {display_content}\n"
            else:
                result += f"📄 **Informasi:** Silakan kunjungi link di atas untuk detail lengkap\n"

            result += "\n"

        # Simpan hasil ke cache untuk penggunaan selanjutnya
        cache_data = {
            'result': result,
            'search_results': search_results,
            'timestamp': datetime.now().isoformat(),
            'query': query
        }
        await set_search_cache(cache_key, cache_data)

        # Tambahkan info bahwa data fresh dari API
        result += f"\n🆕 **INFO:** Data fresh dari Tavily API (disimpan ke cache untuk {SEARCH_CACHE_TTL//60} menit)"

        return result

    except Exception as e:
        log_exception(e)
        return f"Terjadi kesalahan saat mencari informasi: {str(e)}"