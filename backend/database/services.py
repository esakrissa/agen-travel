from database.engine import travel_booking_engine
from utils.handler import ValidationException, DatabaseException, NotFoundException, log_exception
from utils.prometheus import track_database_query, track_booking_created
from utils.cache import cache_result, invalidate_hotel_cache, invalidate_flight_cache, invalidate_tour_cache, invalidate_user_bookings_cache

# Fungsi-fungsi layer service untuk CRUD hotel dan pemesanan perjalanan
@track_database_query("select")
@cache_result("hotels", ttl=3600)
async def get_all_hotels():
    """
    Mendapatkan semua data hotel dari database.

    Returns:
        DataFrame: Semua data hotel

    Raises:
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_all_hotels()

@track_database_query("select")
@cache_result("hotels", ttl=3600)
async def get_hotel_by_id(hotel_id):
    """
    Mendapatkan data hotel berdasarkan ID.

    Args:
        hotel_id (int): ID hotel yang dicari

    Returns:
        Dict: Data hotel dengan kamar-kamarnya

    Raises:
        ValidationException: Jika ID hotel tidak valid
        NotFoundException: Jika hotel tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_hotel_by_id(hotel_id)

@track_database_query("select")
@cache_result("hotels", ttl=3600)
async def filter_hotels_by_location(location):
    """
    Memfilter hotel berdasarkan lokasi.

    Args:
        location (str): Lokasi yang dicari

    Returns:
        DataFrame: DataFrame berisi hotel yang telah difilter

    Raises:
        ValidationException: Jika lokasi tidak valid
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.filter_hotels_by_location(location)

@track_database_query("select")
@cache_result("availability", ttl=300)  # Cache pendek untuk ketersediaan
async def get_available_rooms(hotel_id, check_in_date, check_out_date, guests=1):
    """
    Mendapatkan kamar yang tersedia untuk hotel tertentu pada rentang tanggal tertentu.

    Args:
        hotel_id (int): ID hotel
        check_in_date (str): Tanggal check-in (format: YYYY-MM-DD)
        check_out_date (str): Tanggal check-out (format: YYYY-MM-DD)
        guests (int): Jumlah tamu

    Returns:
        List[Dict]: Daftar kamar yang tersedia

    Raises:
        ValidationException: Jika parameter input tidak valid
        NotFoundException: Jika hotel tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_available_rooms(hotel_id, check_in_date, check_out_date, guests)

@track_database_query("insert")
@track_booking_created("hotel")
async def create_hotel_booking(booking_data):
    """
    Membuat pemesanan hotel baru.

    Args:
        booking_data (Dict): Data pemesanan hotel

    Returns:
        Dict: Data pemesanan yang telah dibuat

    Raises:
        ValidationException: Jika data pemesanan tidak valid
        DatabaseException: Jika operasi database gagal
    """
    result = await travel_booking_engine.create_hotel_booking(booking_data)

    # Invalidate cache terkait hotel setelah booking berhasil
    if result:
        hotel_id = booking_data.get('hotel_id')
        user_id = booking_data.get('user_id')

        # Invalidate cache hotel dan ketersediaan kamar
        await invalidate_hotel_cache(hotel_id)

        # Invalidate cache booking user
        if user_id:
            await invalidate_user_bookings_cache(user_id)

    return result

@track_database_query("select")
@cache_result("user_bookings", ttl=600)
async def get_user_bookings(user_id):
    """
    Mendapatkan semua pemesanan hotel dan penerbangan untuk pengguna tertentu.

    Args:
        user_id (int): ID pengguna

    Returns:
        Dict: Dictionary berisi pemesanan hotel dan penerbangan pengguna

    Raises:
        ValidationException: Jika ID pengguna tidak valid
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_user_bookings(user_id)

# Fungsi-fungsi layer service untuk penerbangan
@track_database_query("select")
@cache_result("flights", ttl=1800)
async def get_all_flights():
    """
    Mendapatkan semua data penerbangan dari database.

    Returns:
        DataFrame: Semua data penerbangan

    Raises:
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_all_flights()

@track_database_query("select")
@cache_result("flights", ttl=1800)
async def get_flight_by_id(flight_id):
    """
    Mendapatkan data penerbangan berdasarkan ID.

    Args:
        flight_id (int): ID penerbangan yang dicari

    Returns:
        Dict: Data penerbangan

    Raises:
        ValidationException: Jika ID penerbangan tidak valid
        NotFoundException: Jika penerbangan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_flight_by_id(flight_id)

@track_database_query("select")
@cache_result("database_search", ttl=900)
async def search_flights(origin=None, destination=None, date=None, airline=None):
    """
    Mencari penerbangan berdasarkan kriteria tertentu.

    Args:
        origin (str, optional): Kode bandara asal
        destination (str, optional): Kode bandara tujuan
        date (str, optional): Tanggal penerbangan (format: YYYY-MM-DD)
        airline (str, optional): Nama maskapai

    Returns:
        DataFrame: DataFrame berisi penerbangan yang telah difilter

    Raises:
        ValidationException: Jika parameter tidak valid
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.search_flights(origin, destination, date, airline)

@track_database_query("select")
@cache_result("flights", ttl=1800)
async def get_flight_schedules(flight_id, start_date, end_date=None):
    """
    Mendapatkan jadwal penerbangan untuk ID penerbangan tertentu dalam rentang tanggal.

    Args:
        flight_id (int): ID penerbangan
        start_date (str): Tanggal mulai (format: YYYY-MM-DD)
        end_date (str, optional): Tanggal akhir (format: YYYY-MM-DD)

    Returns:
        List[Dict]: Daftar jadwal penerbangan

    Raises:
        ValidationException: Jika parameter tidak valid
        NotFoundException: Jika penerbangan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_flight_schedules(flight_id, start_date, end_date)

@track_database_query("insert")
@track_booking_created("flight")
async def create_flight_booking(booking_data):
    """
    Membuat pemesanan penerbangan baru.

    Args:
        booking_data (Dict): Data pemesanan penerbangan

    Returns:
        Dict: Data pemesanan yang telah dibuat

    Raises:
        ValidationException: Jika data pemesanan tidak valid
        DatabaseException: Jika operasi database gagal
    """
    result = await travel_booking_engine.create_flight_booking(booking_data)

    # Invalidate cache terkait penerbangan setelah booking berhasil
    if result:
        flight_id = booking_data.get('flight_id')
        user_id = booking_data.get('user_id')

        # Invalidate cache penerbangan dan ketersediaan kursi
        await invalidate_flight_cache(flight_id)

        # Invalidate cache booking user
        if user_id:
            await invalidate_user_bookings_cache(user_id)

    return result

@track_database_query("update")
async def update_hotel_booking_payment(booking_id, payment_data):
    """
    Memperbarui status pembayaran untuk pemesanan hotel.

    Args:
        booking_id (int): ID pemesanan hotel
        payment_data (Dict): Data pembayaran yang akan diperbarui

    Returns:
        Dict: Data pemesanan yang telah diperbarui

    Raises:
        ValidationException: Jika data pembayaran tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.update_hotel_booking_payment(booking_id, payment_data)

@track_database_query("update")
async def update_flight_booking_payment(booking_id, payment_data):
    """
    Memperbarui status pembayaran untuk pemesanan penerbangan.

    Args:
        booking_id (int): ID pemesanan penerbangan
        payment_data (Dict): Data pembayaran yang akan diperbarui

    Returns:
        Dict: Data pemesanan yang telah diperbarui

    Raises:
        ValidationException: Jika data pembayaran tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.update_flight_booking_payment(booking_id, payment_data)

@track_database_query("select")
async def get_hotel_booking_by_id(booking_id):
    """
    Mendapatkan detail pemesanan hotel berdasarkan ID.

    Args:
        booking_id (int): ID pemesanan hotel

    Returns:
        Dict: Data pemesanan hotel

    Raises:
        ValidationException: Jika ID pemesanan tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_hotel_booking_by_id(booking_id)

@track_database_query("select")
async def get_flight_booking_by_id(booking_id):
    """
    Mendapatkan detail pemesanan penerbangan berdasarkan ID.

    Args:
        booking_id (int): ID pemesanan penerbangan

    Returns:
        Dict: Data pemesanan penerbangan

    Raises:
        ValidationException: Jika ID pemesanan tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_flight_booking_by_id(booking_id)

# Tambahkan fungsi service baru:

@track_database_query("select")
async def get_user_by_email(email):
    """
    Mencari user berdasarkan email

    Args:
        email (str): Email user yang dicari

    Returns:
        Optional[Dict]: Data user jika ditemukan, None jika tidak
    """
    return await travel_booking_engine.get_user_by_email(email)

@track_database_query("insert")
async def create_user(user_data):
    """
    Membuat user baru

    Args:
        user_data (Dict): Data user yang akan dibuat

    Returns:
        Dict: Data user yang telah dibuat

    Raises:
        ValidationException: Jika data user tidak valid
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.create_user(user_data)

@track_database_query("update")
async def process_hotel_cancellation(booking_id):
    """
    Membatalkan pemesanan hotel.

    Args:
        booking_id (int): ID pemesanan hotel

    Returns:
        Dict: Data pemesanan yang telah diperbarui

    Raises:
        ValidationException: Jika ID pemesanan tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    # Ambil data booking sebelum cancel untuk invalidation
    booking_data = await travel_booking_engine.get_hotel_booking_by_id(booking_id)

    result = await travel_booking_engine.cancel_hotel_booking(booking_id)

    # Invalidate cache setelah cancellation berhasil
    if result and booking_data:
        hotel_id = booking_data.get('hotel_id')
        user_id = booking_data.get('user_id')

        # Invalidate cache hotel dan ketersediaan kamar (karena kamar kembali tersedia)
        await invalidate_hotel_cache(hotel_id)

        # Invalidate cache booking user
        if user_id:
            await invalidate_user_bookings_cache(user_id)

    return result

@track_database_query("update")
async def process_flight_cancellation(booking_id):
    """
    Membatalkan pemesanan penerbangan.

    Args:
        booking_id (int): ID pemesanan penerbangan

    Returns:
        Dict: Data pemesanan yang telah diperbarui

    Raises:
        ValidationException: Jika ID pemesanan tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    # Ambil data booking sebelum cancel untuk invalidation
    booking_data = await travel_booking_engine.get_flight_booking_by_id(booking_id)

    result = await travel_booking_engine.cancel_flight_booking(booking_id)

    # Invalidate cache setelah cancellation berhasil
    if result and booking_data:
        flight_id = booking_data.get('flight_id')
        user_id = booking_data.get('user_id')

        # Invalidate cache penerbangan dan ketersediaan kursi (karena kursi kembali tersedia)
        await invalidate_flight_cache(flight_id)

        # Invalidate cache booking user
        if user_id:
            await invalidate_user_bookings_cache(user_id)

    return result

# Fungsi-fungsi layer service untuk tour
@track_database_query("select")
@cache_result("tours", ttl=3600)
async def get_all_tours():
    """
    Mendapatkan semua data tour dari database.

    Returns:
        DataFrame: Semua data tour

    Raises:
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_all_tours()

@track_database_query("select")
@cache_result("tours", ttl=3600)
async def get_tour_by_id(tour_id):
    """
    Mendapatkan data tour berdasarkan ID.

    Args:
        tour_id (int): ID tour yang dicari

    Returns:
        Dict: Data tour

    Raises:
        ValidationException: Jika ID tour tidak valid
        NotFoundException: Jika tour tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_tour_by_id(tour_id)

@track_database_query("select")
@cache_result("database_search", ttl=900)
async def search_tours_by_destination(destination):
    """
    Mencari tour berdasarkan destinasi.

    Args:
        destination (str): Destinasi yang dicari

    Returns:
        DataFrame: DataFrame berisi tour yang telah difilter

    Raises:
        ValidationException: Jika destinasi tidak valid
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.search_tours_by_destination(destination)

@track_database_query("select")
@cache_result("availability", ttl=300)
async def check_tour_availability(tour_id, tanggal):
    """
    Memeriksa ketersediaan tour pada tanggal tertentu.

    Args:
        tour_id (int): ID tour
        tanggal (str): Tanggal tour (format: YYYY-MM-DD)

    Returns:
        Optional[Dict]: Data ketersediaan tour jika tersedia

    Raises:
        ValidationException: Jika parameter tidak valid
        NotFoundException: Jika tour tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.check_tour_availability(tour_id, tanggal)

@track_database_query("insert")
@track_booking_created("tour")
async def create_tour_booking(booking_data):
    """
    Membuat pemesanan tour baru.

    Args:
        booking_data (Dict): Data pemesanan tour

    Returns:
        Dict: Data pemesanan yang telah dibuat

    Raises:
        ValidationException: Jika data pemesanan tidak valid
        DatabaseException: Jika operasi database gagal
    """
    result = await travel_booking_engine.create_tour_booking(booking_data)

    # Invalidate cache terkait tour setelah booking berhasil
    if result:
        tour_id = booking_data.get('tour_id')
        user_id = booking_data.get('user_id')

        # Invalidate cache tour dan ketersediaan slot
        await invalidate_tour_cache(tour_id)

        # Invalidate cache booking user
        if user_id:
            await invalidate_user_bookings_cache(user_id)

    return result

@track_database_query("update")
async def update_tour_booking_payment(booking_id, payment_data):
    """
    Memperbarui status pembayaran untuk pemesanan tour.

    Args:
        booking_id (int): ID pemesanan tour
        payment_data (Dict): Data pembayaran yang akan diperbarui

    Returns:
        Dict: Data pemesanan yang telah diperbarui

    Raises:
        ValidationException: Jika data pembayaran tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.update_tour_booking_payment(booking_id, payment_data)

@track_database_query("update")
async def process_tour_cancellation(booking_id):
    """
    Membatalkan pemesanan tour.

    Args:
        booking_id (int): ID pemesanan tour

    Returns:
        Dict: Data pemesanan yang telah diperbarui

    Raises:
        ValidationException: Jika ID pemesanan tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    # Ambil data booking sebelum cancel untuk invalidation
    booking_data = await travel_booking_engine.get_tour_booking_by_id(booking_id)

    result = await travel_booking_engine.cancel_tour_booking(booking_id)

    # Invalidate cache setelah cancellation berhasil
    if result and booking_data:
        tour_id = booking_data.get('tour_id')
        user_id = booking_data.get('user_id')

        # Invalidate cache tour dan ketersediaan slot (karena slot kembali tersedia)
        await invalidate_tour_cache(tour_id)

        # Invalidate cache booking user
        if user_id:
            await invalidate_user_bookings_cache(user_id)

    return result

@track_database_query("select")
async def get_tour_booking_by_id(booking_id):
    """
    Mendapatkan detail pemesanan tour berdasarkan ID.

    Args:
        booking_id (int): ID pemesanan tour

    Returns:
        Dict: Data pemesanan tour

    Raises:
        ValidationException: Jika ID pemesanan tidak valid
        NotFoundException: Jika pemesanan tidak ditemukan
        DatabaseException: Jika operasi database gagal
    """
    return await travel_booking_engine.get_tour_booking_by_id(booking_id)