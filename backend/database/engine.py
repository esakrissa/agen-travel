from utils.config import get_supabase_client
import pandas as pd
from utils.datetime import parse_datetime, format_datetime, convert_datetime_format, get_current_datetime, async_strptime, async_now
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from utils.handler import DatabaseException, ValidationException, NotFoundException


class TravelBookingEngine:
    """
    Data Access Object untuk tabel-tabel terkait travel booking (hotel dan penerbangan).
    Mengimplementasikan semua operasi database sebagai metode pada kelas ini.
    """

    def __init__(self):
        """Inisialisasi repository dengan client Supabase"""
        self._client = None  # Inisialisasi dengan fungsi async
        self._hotels_table = 'hotels'
        self._hotel_rooms_table = 'hotel_rooms'
        self._flights_table = 'flights'
        self._flight_schedules_table = 'flight_schedules'
        self._hotel_bookings_table = 'hotel_bookings'
        self._flight_bookings_table = 'flight_bookings'
        self._users_table = 'users'
        self._tours_table = 'tours'
        self._tour_schedules_table = 'tour_schedules'
        self._tour_bookings_table = 'tour_bookings'

    async def _get_client(self):
        """Mendapatkan client Supabase"""
        if self._client is None:
            self._client = await get_supabase_client()
        return self._client

    def _to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """Mengonversi data ke DataFrame untuk kompatibilitas"""
        if data:
            return pd.DataFrame(data)
        else:
            # Mengembalikan DataFrame kosong
            return pd.DataFrame()

    async def get_all_hotels(self) -> pd.DataFrame:
        """
        Mengambil semua data hotel dari database.

        Returns:
            pd.DataFrame: Semua data hotel

        Raises:
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info("Mengambil semua data hotel dari database")

            # Get async client
            client = await self._get_client()

            response = await client.table(self._hotels_table).select('*').execute()

            result_count = len(response.data) if response.data else 0
            logging.info(f"Ditemukan {result_count} hotel")

            return self._to_dataframe(response.data)

        except Exception as e:
            logging.error(f"Error saat mengambil data hotel: {e}")
            raise DatabaseException(
                message="Gagal mengambil data hotel",
                detail={"original_error": str(e)}
            )

    async def get_hotel_by_id(self, hotel_id: int) -> Dict:
        """
        Mengambil data hotel berdasarkan ID.

        Args:
            hotel_id (int): ID hotel yang dicari

        Returns:
            Dict: Data hotel

        Raises:
            ValidationException: Jika ID hotel tidak valid
            NotFoundException: Jika hotel tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mengambil data hotel dengan ID: {hotel_id}")

            if not hotel_id:
                raise ValidationException(
                    message="ID hotel tidak boleh kosong",
                    detail={"hotel_id": hotel_id}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._hotels_table) \
                .select('*') \
                .eq('id', hotel_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise NotFoundException(
                    message=f"Hotel dengan ID {hotel_id} tidak ditemukan",
                    detail={"hotel_id": hotel_id}
                )

            # Ambil data kamar hotel
            rooms_response = await client.table(self._hotel_rooms_table) \
                .select('*') \
                .eq('hotel_id', hotel_id) \
                .execute()

            # Gabungkan data hotel dengan data kamar
            hotel_data = response.data[0]
            hotel_data['kamar'] = rooms_response.data if rooms_response.data else []

            return hotel_data

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil data hotel: {e}")
            raise DatabaseException(
                message=f"Gagal mengambil data hotel dengan ID {hotel_id}",
                detail={"hotel_id": hotel_id, "original_error": str(e)}
            )

    async def filter_hotels_by_location(self, location: str) -> pd.DataFrame:
        """
        Memfilter hotel berdasarkan lokasi.

        Args:
            location (str): Lokasi yang dicari

        Returns:
            pd.DataFrame: DataFrame berisi hotel yang telah difilter

        Raises:
            ValidationException: Jika lokasi tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Memfilter hotel berdasarkan lokasi: '{location}'")

            if not location or len(location.strip()) == 0:
                raise ValidationException(
                    message="Lokasi tidak boleh kosong",
                    detail={"location": location}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._hotels_table) \
                .select('*') \
                .ilike('lokasi', f"%{location}%") \
                .execute()

            result_count = len(response.data) if response.data else 0
            logging.info(f"Ditemukan {result_count} hotel di lokasi {location}")

            return self._to_dataframe(response.data)

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat memfilter hotel berdasarkan lokasi: {e}")
            raise DatabaseException(
                message="Gagal memfilter hotel berdasarkan lokasi",
                detail={"location": location, "original_error": str(e)}
            )

    async def get_available_rooms(self, hotel_id: int, check_in_date: str, check_out_date: str,
                                 guests: int = 1) -> List[Dict]:
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
        try:
            logging.info(f"Mencari kamar tersedia untuk hotel ID {hotel_id} dari {check_in_date} hingga {check_out_date}")

            # Validasi input
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
                check_in_dt = await async_strptime(check_in_date, "%Y-%m-%d")
                check_out_dt = await async_strptime(check_out_date, "%Y-%m-%d")

                if check_in_dt >= check_out_dt:
                    raise ValidationException(
                        message="Tanggal check-out harus setelah tanggal check-in",
                        detail={"check_in_date": check_in_date, "check_out_date": check_out_date}
                    )
            except ValueError:
                raise ValidationException(
                    message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD",
                    detail={"check_in_date": check_in_date, "check_out_date": check_out_date}
                )

            # Get async client
            client = await self._get_client()

            # Periksa apakah hotel ada
            hotel_response = await client.table(self._hotels_table) \
                .select('*') \
                .eq('id', hotel_id) \
                .execute()

            if not hotel_response.data or len(hotel_response.data) == 0:
                raise NotFoundException(
                    message=f"Hotel dengan ID {hotel_id} tidak ditemukan",
                    detail={"hotel_id": hotel_id}
                )

            # Ambil semua kamar hotel
            rooms_response = await client.table(self._hotel_rooms_table) \
                .select('*') \
                .eq('hotel_id', hotel_id) \
                .gte('kapasitas', guests) \
                .gt('jumlah_tersedia', 0) \
                .execute()

            if not rooms_response.data:
                logging.info(f"Tidak ada kamar tersedia untuk hotel {hotel_id}")
                return []

            # Mengembalikan data kamar yang tersedia berdasarkan data aktual di database
            # Tidak perlu perhitungan manual karena jumlah_tersedia sudah diupdate saat booking/cancel
            logging.info(f"Ditemukan {len(rooms_response.data)} kamar tersedia untuk hotel {hotel_id}")
            return rooms_response.data

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mencari kamar tersedia: {e}")
            raise DatabaseException(
                message="Gagal mencari kamar tersedia",
                detail={
                    "hotel_id": hotel_id,
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "original_error": str(e)
                }
            )

    async def create_hotel_booking(self, booking_data: Dict) -> Dict:
        """
        Membuat pemesanan hotel baru dan mengurangi jumlah kamar tersedia.

        Args:
            booking_data (Dict): Data pemesanan hotel

        Returns:
            Dict: Data pemesanan yang telah dibuat

        Raises:
            ValidationException: Jika data pemesanan tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Membuat pemesanan hotel baru: {booking_data}")

            # Validasi data pemesanan
            required_fields = ['hotel_id', 'nama_pemesan', 'email', 'telepon',
                              'tanggal_mulai', 'tanggal_akhir', 'jumlah_tamu',
                              'jumlah_kamar', 'tipe_kamar', 'total_harga']

            for field in required_fields:
                if field not in booking_data or not booking_data[field]:
                    raise ValidationException(
                        message=f"Field {field} wajib diisi",
                        detail={"booking_data": booking_data}
                    )

            # Get async client
            client = await self._get_client()

            # Cek ketersediaan kamar sebelum booking
            room_response = await client.table(self._hotel_rooms_table) \
                .select('*') \
                .eq('hotel_id', booking_data['hotel_id']) \
                .eq('tipe_kamar', booking_data['tipe_kamar']) \
                .execute()

            if not room_response.data or len(room_response.data) == 0:
                raise ValidationException(
                    message=f"Tipe kamar {booking_data['tipe_kamar']} tidak ditemukan",
                    detail={"hotel_id": booking_data['hotel_id'], "tipe_kamar": booking_data['tipe_kamar']}
                )

            room_data = room_response.data[0]
            if room_data['jumlah_tersedia'] < booking_data['jumlah_kamar']:
                raise ValidationException(
                    message=f"Hanya tersedia {room_data['jumlah_tersedia']} kamar tipe {booking_data['tipe_kamar']}",
                    detail={"jumlah_kamar": booking_data['jumlah_kamar'], "tersedia": room_data['jumlah_tersedia']}
                )

            # Buat pemesanan baru
            response = await client.table(self._hotel_bookings_table) \
                .insert(booking_data) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise DatabaseException(
                    message="Gagal membuat pemesanan hotel",
                    detail={"booking_data": booking_data}
                )

            # Update jumlah kamar tersedia (kurangi sesuai jumlah yang dipesan)
            new_available = room_data['jumlah_tersedia'] - booking_data['jumlah_kamar']
            await client.table(self._hotel_rooms_table) \
                .update({'jumlah_tersedia': new_available}) \
                .eq('id', room_data['id']) \
                .execute()

            logging.info(f"Pemesanan hotel berhasil dibuat dengan ID: {response.data[0]['id']}")
            logging.info(f"Jumlah kamar {booking_data['tipe_kamar']} berkurang dari {room_data['jumlah_tersedia']} menjadi {new_available}")

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat membuat pemesanan hotel: {e}")
            raise DatabaseException(
                message="Gagal membuat pemesanan hotel",
                detail={"booking_data": booking_data, "original_error": str(e)}
            )

    async def get_user_bookings(self, user_id: int) -> Dict:
        """
        Mendapatkan semua pemesanan hotel, penerbangan, dan tur untuk pengguna tertentu.

        Args:
            user_id (int): ID pengguna

        Returns:
            Dict: Dictionary berisi pemesanan hotel, penerbangan, dan tur pengguna

        Raises:
            ValidationException: Jika ID pengguna tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mengambil semua pemesanan untuk pengguna ID: {user_id}")

            if not user_id:
                raise ValidationException(
                    message="ID pengguna tidak boleh kosong",
                    detail={"user_id": user_id}
                )

            # Get async client
            client = await self._get_client()

            # Ambil pemesanan hotel
            hotel_bookings_response = await client.table(self._hotel_bookings_table) \
                .select('*, hotels(nama, lokasi, bintang)') \
                .eq('user_id', user_id) \
                .execute()

            # Ambil pemesanan penerbangan
            flight_bookings_response = await client.table(self._flight_bookings_table) \
                .select('*, flights(maskapai, kode_penerbangan, origin, destination)') \
                .eq('user_id', user_id) \
                .execute()

            # Ambil pemesanan tour
            tour_bookings_response = await client.table(self._tour_bookings_table) \
                .select('*, tours(nama, destinasi, durasi)') \
                .eq('user_id', user_id) \
                .execute()

            return {
                'hotel_bookings': hotel_bookings_response.data if hotel_bookings_response.data else [],
                'flight_bookings': flight_bookings_response.data if flight_bookings_response.data else [],
                'tour_bookings': tour_bookings_response.data if tour_bookings_response.data else []
            }

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil pemesanan pengguna: {e}")
            raise DatabaseException(
                message="Gagal mengambil pemesanan pengguna",
                detail={"user_id": user_id, "original_error": str(e)}
            )

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Mencari user berdasarkan email

        Args:
            email (str): Email user yang dicari

        Returns:
            Optional[Dict]: Data user jika ditemukan, None jika tidak
        """
        try:
            logging.info(f"Mencari user dengan email: {email}")

            if not email:
                raise ValidationException(
                    message="Email tidak boleh kosong",
                    detail={"email": email}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._users_table) \
                .select('*') \
                .eq('email', email) \
                .execute()

            if response.data and len(response.data) > 0:
                logging.info(f"User dengan email {email} ditemukan")
                return response.data[0]

            logging.info(f"User dengan email {email} tidak ditemukan")
            return None

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat mencari user berdasarkan email: {e}")
            return None

    async def create_user(self, user_data: Dict) -> Dict:
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
        try:
            logging.info(f"Membuat user baru: {user_data}")

            # Validasi data user
            required_fields = ['nama', 'email', 'telepon']

            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    raise ValidationException(
                        message=f"Field {field} wajib diisi",
                        detail={"user_data": user_data}
                    )

            # Get async client
            client = await self._get_client()

            # Periksa apakah email sudah terdaftar
            existing_user = await self.get_user_by_email(user_data['email'])
            if existing_user:
                raise ValidationException(
                    message=f"Email {user_data['email']} sudah terdaftar",
                    detail={"email": user_data['email']}
                )

            # Buat user baru
            response = await client.table(self._users_table) \
                .insert(user_data) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise DatabaseException(
                    message="Gagal membuat user baru",
                    detail={"user_data": user_data}
                )

            logging.info(f"User baru berhasil dibuat dengan ID: {response.data[0]['id']}")

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat membuat user baru: {e}")
            raise DatabaseException(
                message="Gagal membuat user baru",
                detail={"user_data": user_data, "original_error": str(e)}
            )

    async def get_all_flights(self) -> pd.DataFrame:
        """
        Mengambil semua data penerbangan dari database.

        Returns:
            pd.DataFrame: Semua data penerbangan

        Raises:
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info("Mengambil semua data penerbangan dari database")

            # Get async client
            client = await self._get_client()

            response = await client.table(self._flights_table).select('*').execute()

            result_count = len(response.data) if response.data else 0
            logging.info(f"Ditemukan {result_count} penerbangan")

            return self._to_dataframe(response.data)

        except Exception as e:
            logging.error(f"Error saat mengambil data penerbangan: {e}")
            raise DatabaseException(
                message="Gagal mengambil data penerbangan",
                detail={"original_error": str(e)}
            )

    async def get_flight_by_id(self, flight_id: int) -> Dict:
        """
        Mengambil data penerbangan berdasarkan ID.

        Args:
            flight_id (int): ID penerbangan yang dicari

        Returns:
            Dict: Data penerbangan

        Raises:
            ValidationException: Jika ID penerbangan tidak valid
            NotFoundException: Jika penerbangan tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mengambil data penerbangan dengan ID: {flight_id}")

            if not flight_id:
                raise ValidationException(
                    message="ID penerbangan tidak boleh kosong",
                    detail={"flight_id": flight_id}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._flights_table) \
                .select('*') \
                .eq('id', flight_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise NotFoundException(
                    message=f"Penerbangan dengan ID {flight_id} tidak ditemukan",
                    detail={"flight_id": flight_id}
                )

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil data penerbangan: {e}")
            raise DatabaseException(
                message=f"Gagal mengambil data penerbangan dengan ID {flight_id}",
                detail={"flight_id": flight_id, "original_error": str(e)}
            )

    async def search_flights(self, origin: str = None, destination: str = None,
                           date: str = None, airline: str = None) -> pd.DataFrame:
        """
        Mencari penerbangan berdasarkan kriteria tertentu.

        Args:
            origin (str, optional): Kode bandara asal
            destination (str, optional): Kode bandara tujuan
            date (str, optional): Tanggal penerbangan (format: YYYY-MM-DD)
            airline (str, optional): Nama maskapai

        Returns:
            pd.DataFrame: DataFrame berisi penerbangan yang telah difilter

        Raises:
            ValidationException: Jika parameter tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mencari penerbangan dengan kriteria: origin={origin}, destination={destination}, date={date}, airline={airline}")

            # Minimal harus ada satu kriteria pencarian
            if not origin and not destination and not date and not airline:
                raise ValidationException(
                    message="Minimal satu kriteria pencarian harus diisi",
                    detail={"origin": origin, "destination": destination, "date": date, "airline": airline}
                )

            # Validasi format tanggal jika disediakan
            if date:
                try:
                    search_date = await async_strptime(date, "%Y-%m-%d")
                    # Pastikan tanggal tidak di masa lalu
                    now = await async_now()
                    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    if search_date < today:
                        logging.warning(f"Tanggal pencarian {date} adalah tanggal di masa lalu")
                except ValueError:
                    raise ValidationException(
                        message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD",
                        detail={"date": date}
                    )

            # Get async client
            client = await self._get_client()

            # Membangun query dasar
            query = client.table(self._flights_table).select('*')

            # Menambahkan filter berdasarkan parameter yang diberikan
            if origin:
                query = query.eq('origin', origin)

            if destination:
                query = query.eq('destination', destination)

            if airline:
                query = query.ilike('maskapai', f"%{airline}%")

            # Eksekusi query
            response = await query.execute()
            flights_df = self._to_dataframe(response.data)

            # Filter berdasarkan tanggal jika tanggal disediakan
            if date and not flights_df.empty:
                flight_ids = flights_df['id'].tolist()

                logging.info(f"Mendapatkan jadwal untuk {len(flight_ids)} penerbangan pada tanggal {date}")

                # Ambil jadwal penerbangan yang tersedia untuk tanggal tersebut
                schedules_response = await client.table(self._flight_schedules_table) \
                    .select('flight_id,is_available') \
                    .in_('flight_id', flight_ids) \
                    .eq('tanggal', date) \
                    .execute()

                if schedules_response.data:
                    available_flight_ids = [item['flight_id'] for item in schedules_response.data if item.get('is_available', False)]
                    logging.info(f"Ditemukan {len(available_flight_ids)} dari {len(flight_ids)} penerbangan yang tersedia pada tanggal {date}")

                    if available_flight_ids:
                        flights_df = flights_df[flights_df['id'].isin(available_flight_ids)]
                    else:
                        # Jika tidak ada penerbangan yang tersedia pada tanggal tersebut, kembalikan DataFrame kosong
                        logging.warning(f"Tidak ada penerbangan yang tersedia pada tanggal {date}")
                        return pd.DataFrame()
                else:
                    # Jika tidak ada jadwal sama sekali untuk tanggal tersebut, kembalikan DataFrame kosong
                    logging.warning(f"Tidak ada jadwal penerbangan untuk tanggal {date}")
                    return pd.DataFrame()

            result_count = len(flights_df) if not flights_df.empty else 0
            logging.info(f"Ditemukan {result_count} penerbangan yang sesuai kriteria")

            return flights_df

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat mencari penerbangan: {e}")
            raise DatabaseException(
                message="Gagal mencari penerbangan",
                detail={
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "airline": airline,
                    "original_error": str(e)
                }
            )

    async def get_flight_schedules(self, flight_id: int, start_date: str, end_date: str = None) -> List[Dict]:
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
        try:
            if not flight_id or not start_date:
                raise ValidationException(
                    message="ID penerbangan dan tanggal mulai harus diisi",
                    detail={"flight_id": flight_id, "start_date": start_date}
                )

            # Validasi format tanggal
            try:
                start_dt = await async_strptime(start_date, "%Y-%m-%d")
                if end_date:
                    end_dt = await async_strptime(end_date, "%Y-%m-%d")

                    if start_dt > end_dt:
                        raise ValidationException(
                            message="Tanggal mulai tidak boleh setelah tanggal akhir",
                            detail={"start_date": start_date, "end_date": end_date}
                        )
            except ValueError:
                raise ValidationException(
                    message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD",
                    detail={"start_date": start_date, "end_date": end_date}
                )

            # Get async client
            client = await self._get_client()

            # Periksa apakah penerbangan ada
            flight_response = await client.table(self._flights_table) \
                .select('*') \
                .eq('id', flight_id) \
                .execute()

            if not flight_response.data or len(flight_response.data) == 0:
                raise NotFoundException(
                    message=f"Penerbangan dengan ID {flight_id} tidak ditemukan",
                    detail={"flight_id": flight_id}
                )

            # Log untuk debugging
            logging.info(f"Mencari jadwal penerbangan ID {flight_id} untuk tanggal {start_date} hingga {end_date or start_date}")

            # Membangun query untuk jadwal
            query = client.table(self._flight_schedules_table) \
                .select('*') \
                .eq('flight_id', flight_id) \
                .gte('tanggal', start_date)

            if end_date:
                query = query.lte('tanggal', end_date)

            # Eksekusi query
            schedules_response = await query.execute()

            schedules = schedules_response.data if schedules_response.data else []

            # Log hasil pencarian
            found_count = len(schedules)
            available_count = len([s for s in schedules if s.get('is_available', False)])
            logging.info(f"Ditemukan {found_count} jadwal penerbangan, {available_count} tersedia")

            if found_count == 0:
                logging.warning(f"Tidak ditemukan jadwal untuk penerbangan ID {flight_id} pada tanggal {start_date}")

            return schedules

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil jadwal penerbangan: {e}")
            raise DatabaseException(
                message="Gagal mengambil jadwal penerbangan",
                detail={
                    "flight_id": flight_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "original_error": str(e)
                }
            )

    async def create_flight_booking(self, booking_data: Dict) -> Dict:
        """
        Membuat pemesanan penerbangan baru dan mengurangi jumlah kursi tersedia.

        Args:
            booking_data (Dict): Data pemesanan penerbangan

        Returns:
            Dict: Data pemesanan yang telah dibuat

        Raises:
            ValidationException: Jika data pemesanan tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Membuat pemesanan penerbangan baru: {booking_data}")

            # Validasi data pemesanan
            required_fields = ['flight_id', 'nama_pemesan', 'email', 'telepon',
                              'tanggal_keberangkatan', 'jumlah_penumpang',
                              'kelas_penerbangan', 'total_harga']

            for field in required_fields:
                if field not in booking_data or not booking_data[field]:
                    raise ValidationException(
                        message=f"Field {field} wajib diisi",
                        detail={"booking_data": booking_data}
                    )

            # Get async client
            client = await self._get_client()

            # Cek ketersediaan kursi sebelum booking
            flight_response = await client.table(self._flights_table) \
                .select('*') \
                .eq('id', booking_data['flight_id']) \
                .execute()

            if not flight_response.data or len(flight_response.data) == 0:
                raise ValidationException(
                    message=f"Penerbangan dengan ID {booking_data['flight_id']} tidak ditemukan",
                    detail={"flight_id": booking_data['flight_id']}
                )

            flight_data = flight_response.data[0]
            if flight_data['kursi_tersedia'] < booking_data['jumlah_penumpang']:
                raise ValidationException(
                    message=f"Hanya tersedia {flight_data['kursi_tersedia']} kursi",
                    detail={"jumlah_penumpang": booking_data['jumlah_penumpang'], "tersedia": flight_data['kursi_tersedia']}
                )

            # Buat pemesanan baru
            response = await client.table(self._flight_bookings_table) \
                .insert(booking_data) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise DatabaseException(
                    message="Gagal membuat pemesanan penerbangan",
                    detail={"booking_data": booking_data}
                )

            # Update jumlah kursi tersedia (kurangi sesuai jumlah penumpang)
            new_available = flight_data['kursi_tersedia'] - booking_data['jumlah_penumpang']
            await client.table(self._flights_table) \
                .update({'kursi_tersedia': new_available}) \
                .eq('id', booking_data['flight_id']) \
                .execute()

            logging.info(f"Pemesanan penerbangan berhasil dibuat dengan ID: {response.data[0]['id']}")
            logging.info(f"Jumlah kursi penerbangan {flight_data['kode_penerbangan']} berkurang dari {flight_data['kursi_tersedia']} menjadi {new_available}")

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat membuat pemesanan penerbangan: {e}")
            raise DatabaseException(
                message="Gagal membuat pemesanan penerbangan",
                detail={"booking_data": booking_data, "original_error": str(e)}
            )

    async def update_hotel_booking_payment(self, booking_id: int, payment_data: Dict) -> Dict:
        """
        Memperbarui status pembayaran untuk pemesanan hotel.

        Args:
            booking_id (int): ID pemesanan hotel
            payment_data (Dict): Data pembayaran yang akan diperbarui, contoh:
                {
                    "metode_pembayaran": "transfer bank",
                    "status_pembayaran": "paid",
                    "status": "confirmed"
                }

        Returns:
            Dict: Data pemesanan yang telah diperbarui

        Raises:
            ValidationException: Jika data pembayaran tidak valid
            NotFoundException: Jika pemesanan tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Memperbarui status pembayaran untuk pemesanan hotel ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Validasi status pembayaran jika ada
            if 'status_pembayaran' in payment_data:
                valid_payment_statuses = ['unpaid', 'paid', 'failed', 'refunded']
                if payment_data['status_pembayaran'] not in valid_payment_statuses:
                    raise ValidationException(
                        message=f"Status pembayaran tidak valid. Pilihan: {', '.join(valid_payment_statuses)}",
                        detail={"status_pembayaran": payment_data['status_pembayaran']}
                    )

            # Validasi status pemesanan jika ada
            if 'status' in payment_data:
                valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed']
                if payment_data['status'] not in valid_statuses:
                    raise ValidationException(
                        message=f"Status pemesanan tidak valid. Pilihan: {', '.join(valid_statuses)}",
                        detail={"status": payment_data['status']}
                    )

            # Get async client
            client = await self._get_client()

            # Cek apakah pemesanan ada
            booking_response = await client.table(self._hotel_bookings_table) \
                .select('*') \
                .eq('id', booking_id) \
                .execute()

            if not booking_response.data or len(booking_response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan hotel dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            # Update data pembayaran
            update_response = await client.table(self._hotel_bookings_table) \
                .update(payment_data) \
                .eq('id', booking_id) \
                .execute()

            if not update_response.data or len(update_response.data) == 0:
                raise DatabaseException(
                    message=f"Gagal memperbarui pembayaran untuk pemesanan hotel ID {booking_id}",
                    detail={"booking_id": booking_id, "payment_data": payment_data}
                )

            logging.info(f"Pembayaran untuk pemesanan hotel ID {booking_id} berhasil diperbarui")

            return update_response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat memperbarui pembayaran hotel: {e}")
            raise DatabaseException(
                message="Gagal memperbarui pembayaran hotel",
                detail={"booking_id": booking_id, "payment_data": payment_data, "original_error": str(e)}
            )

    async def update_flight_booking_payment(self, booking_id: int, payment_data: Dict) -> Dict:
        """
        Memperbarui status pembayaran untuk pemesanan penerbangan.

        Args:
            booking_id (int): ID pemesanan penerbangan
            payment_data (Dict): Data pembayaran yang akan diperbarui, contoh:
                {
                    "metode_pembayaran": "kartu kredit",
                    "status_pembayaran": "paid",
                    "status": "confirmed"
                }

        Returns:
            Dict: Data pemesanan yang telah diperbarui

        Raises:
            ValidationException: Jika data pembayaran tidak valid
            NotFoundException: Jika pemesanan tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Memperbarui status pembayaran untuk pemesanan penerbangan ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Validasi status pembayaran jika ada
            if 'status_pembayaran' in payment_data:
                valid_payment_statuses = ['unpaid', 'paid', 'failed', 'refunded']
                if payment_data['status_pembayaran'] not in valid_payment_statuses:
                    raise ValidationException(
                        message=f"Status pembayaran tidak valid. Pilihan: {', '.join(valid_payment_statuses)}",
                        detail={"status_pembayaran": payment_data['status_pembayaran']}
                    )

            # Validasi status pemesanan jika ada
            if 'status' in payment_data:
                valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed']
                if payment_data['status'] not in valid_statuses:
                    raise ValidationException(
                        message=f"Status pemesanan tidak valid. Pilihan: {', '.join(valid_statuses)}",
                        detail={"status": payment_data['status']}
                    )

            # Get async client
            client = await self._get_client()

            # Cek apakah pemesanan ada
            booking_response = await client.table(self._flight_bookings_table) \
                .select('*') \
                .eq('id', booking_id) \
                .execute()

            if not booking_response.data or len(booking_response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan penerbangan dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            # Update data pembayaran
            update_response = await client.table(self._flight_bookings_table) \
                .update(payment_data) \
                .eq('id', booking_id) \
                .execute()

            if not update_response.data or len(update_response.data) == 0:
                raise DatabaseException(
                    message=f"Gagal memperbarui pembayaran untuk pemesanan penerbangan ID {booking_id}",
                    detail={"booking_id": booking_id, "payment_data": payment_data}
                )

            logging.info(f"Pembayaran untuk pemesanan penerbangan ID {booking_id} berhasil diperbarui")

            return update_response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat memperbarui pembayaran penerbangan: {e}")
            raise DatabaseException(
                message="Gagal memperbarui pembayaran penerbangan",
                detail={"booking_id": booking_id, "payment_data": payment_data, "original_error": str(e)}
            )

    async def get_hotel_booking_by_id(self, booking_id: int) -> Dict:
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
        try:
            logging.info(f"Mendapatkan detail pemesanan hotel ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            # Ambil data pemesanan
            response = await client.table(self._hotel_bookings_table) \
                .select('*, hotels(nama, lokasi, bintang)') \
                .eq('id', booking_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan hotel dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            logging.info(f"Pemesanan hotel dengan ID {booking_id} ditemukan")

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil detail pemesanan hotel: {e}")
            raise DatabaseException(
                message="Gagal mengambil detail pemesanan hotel",
                detail={"booking_id": booking_id, "original_error": str(e)}
            )

    async def get_flight_booking_by_id(self, booking_id: int) -> Dict:
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
        try:
            logging.info(f"Mendapatkan detail pemesanan penerbangan ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            # Ambil data pemesanan
            response = await client.table(self._flight_bookings_table) \
                .select('*, flights(maskapai, kode_penerbangan, origin, destination, waktu_berangkat, waktu_tiba, durasi)') \
                .eq('id', booking_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan penerbangan dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            logging.info(f"Pemesanan penerbangan dengan ID {booking_id} ditemukan")

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil detail pemesanan penerbangan: {e}")
            raise DatabaseException(
                message="Gagal mengambil detail pemesanan penerbangan",
                detail={"booking_id": booking_id, "original_error": str(e)}
            )

    async def cancel_hotel_booking(self, booking_id: int) -> Dict:
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
        try:
            logging.info(f"Membatalkan pemesanan hotel dengan ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            # Periksa apakah pemesanan ada
            booking_response = await client.table(self._hotel_bookings_table) \
                .select('*') \
                .eq('id', booking_id) \
                .execute()

            if not booking_response.data or len(booking_response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan hotel dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            current_booking = booking_response.data[0]

            # Periksa apakah pemesanan sudah dibatalkan
            if current_booking['status'] == 'cancelled':
                return current_booking

            # Periksa apakah pemesanan sudah selesai
            if current_booking['status'] == 'completed':
                raise ValidationException(
                    message="Tidak dapat membatalkan pemesanan yang sudah selesai",
                    detail={"booking_id": booking_id, "status": current_booking['status']}
                )

            # Update status pemesanan menjadi 'cancelled'
            update_data = {
                'status': 'cancelled',
                'updated_at': (await async_now()).isoformat()
            }

            # Jika sudah dibayar, set status pembayaran menjadi 'refunded'
            if current_booking['status_pembayaran'] == 'paid':
                update_data['status_pembayaran'] = 'refunded'

            update_response = await client.table(self._hotel_bookings_table) \
                .update(update_data) \
                .eq('id', booking_id) \
                .execute()

            if not update_response.data or len(update_response.data) == 0:
                raise DatabaseException(
                    message=f"Gagal membatalkan pemesanan hotel dengan ID {booking_id}",
                    detail={"booking_id": booking_id}
                )

            # Kembalikan jumlah kamar yang dibatalkan ke stok tersedia
            room_response = await client.table(self._hotel_rooms_table) \
                .select('*') \
                .eq('hotel_id', current_booking['hotel_id']) \
                .eq('tipe_kamar', current_booking['tipe_kamar']) \
                .execute()

            if room_response.data and len(room_response.data) > 0:
                room_data = room_response.data[0]
                new_available = room_data['jumlah_tersedia'] + current_booking['jumlah_kamar']
                await client.table(self._hotel_rooms_table) \
                    .update({'jumlah_tersedia': new_available}) \
                    .eq('id', room_data['id']) \
                    .execute()

                logging.info(f"Jumlah kamar {current_booking['tipe_kamar']} dikembalikan dari {room_data['jumlah_tersedia']} menjadi {new_available}")

            return update_response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat membatalkan pemesanan hotel: {e}")
            raise DatabaseException(
                message=f"Gagal membatalkan pemesanan hotel dengan ID {booking_id}",
                detail={"booking_id": booking_id, "original_error": str(e)}
            )

    async def cancel_flight_booking(self, booking_id: int) -> Dict:
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
        try:
            logging.info(f"Membatalkan pemesanan penerbangan dengan ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            # Periksa apakah pemesanan ada
            booking_response = await client.table(self._flight_bookings_table) \
                .select('*') \
                .eq('id', booking_id) \
                .execute()

            if not booking_response.data or len(booking_response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan penerbangan dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            current_booking = booking_response.data[0]

            # Periksa apakah pemesanan sudah dibatalkan
            if current_booking['status'] == 'cancelled':
                return current_booking

            # Periksa apakah pemesanan sudah selesai
            if current_booking['status'] == 'completed':
                raise ValidationException(
                    message="Tidak dapat membatalkan pemesanan yang sudah selesai",
                    detail={"booking_id": booking_id, "status": current_booking['status']}
                )

            # Update status pemesanan menjadi 'cancelled'
            update_data = {
                'status': 'cancelled',
                'updated_at': (await async_now()).isoformat()
            }

            # Jika sudah dibayar, set status pembayaran menjadi 'refunded'
            if current_booking['status_pembayaran'] == 'paid':
                update_data['status_pembayaran'] = 'refunded'

            update_response = await client.table(self._flight_bookings_table) \
                .update(update_data) \
                .eq('id', booking_id) \
                .execute()

            if not update_response.data or len(update_response.data) == 0:
                raise DatabaseException(
                    message=f"Gagal membatalkan pemesanan penerbangan dengan ID {booking_id}",
                    detail={"booking_id": booking_id}
                )

            # Kembalikan jumlah kursi yang dibatalkan ke stok tersedia
            flight_response = await client.table(self._flights_table) \
                .select('*') \
                .eq('id', current_booking['flight_id']) \
                .execute()

            if flight_response.data and len(flight_response.data) > 0:
                flight_data = flight_response.data[0]
                new_available = flight_data['kursi_tersedia'] + current_booking['jumlah_penumpang']
                await client.table(self._flights_table) \
                    .update({'kursi_tersedia': new_available}) \
                    .eq('id', current_booking['flight_id']) \
                    .execute()

                logging.info(f"Jumlah kursi penerbangan {flight_data['kode_penerbangan']} dikembalikan dari {flight_data['kursi_tersedia']} menjadi {new_available}")

            return update_response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat membatalkan pemesanan penerbangan: {e}")
            raise DatabaseException(
                message=f"Gagal membatalkan pemesanan penerbangan dengan ID {booking_id}",
                detail={"booking_id": booking_id, "original_error": str(e)}
            )

    # Tour methods
    async def get_all_tours(self) -> pd.DataFrame:
        """
        Mengambil semua data tur dari database.

        Returns:
            pd.DataFrame: Semua data tur

        Raises:
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info("Mengambil semua data tur dari database")

            # Get async client
            client = await self._get_client()

            response = await client.table(self._tours_table).select('*').execute()

            result_count = len(response.data) if response.data else 0
            logging.info(f"Ditemukan {result_count} tur")

            return self._to_dataframe(response.data)

        except Exception as e:
            logging.error(f"Error saat mengambil data tur: {e}")
            raise DatabaseException(
                message="Gagal mengambil data tur",
                detail={"original_error": str(e)}
            )

    async def get_tour_by_id(self, tour_id: int) -> Dict:
        """
        Mengambil data tur berdasarkan ID.

        Args:
            tour_id (int): ID tur yang dicari

        Returns:
            Dict: Data tur

        Raises:
            ValidationException: Jika ID tur tidak valid
            NotFoundException: Jika tur tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mengambil data tur dengan ID: {tour_id}")

            if not tour_id:
                raise ValidationException(
                    message="ID tur tidak boleh kosong",
                    detail={"tour_id": tour_id}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._tours_table) \
                .select('*') \
                .eq('id', tour_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise NotFoundException(
                    message=f"Tur dengan ID {tour_id} tidak ditemukan",
                    detail={"tour_id": tour_id}
                )

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil data tur: {e}")
            raise DatabaseException(
                message=f"Gagal mengambil data tur dengan ID {tour_id}",
                detail={"tour_id": tour_id, "original_error": str(e)}
            )

    async def search_tours_by_destination(self, destination: str) -> pd.DataFrame:
        """
        Mencari tur berdasarkan destinasi.

        Args:
            destination (str): Destinasi yang dicari

        Returns:
            pd.DataFrame: DataFrame berisi tur yang telah difilter

        Raises:
            ValidationException: Jika destinasi tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mencari tur berdasarkan destinasi: '{destination}'")

            if not destination or len(destination.strip()) == 0:
                raise ValidationException(
                    message="Destinasi tidak boleh kosong",
                    detail={"destination": destination}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._tours_table) \
                .select('*') \
                .or_(f"destinasi.ilike.%{destination}%,nama.ilike.%{destination}%") \
                .execute()

            result_count = len(response.data) if response.data else 0
            logging.info(f"Ditemukan {result_count} tur di destinasi {destination}")

            return self._to_dataframe(response.data)

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat mencari tur berdasarkan destinasi: {e}")
            raise DatabaseException(
                message="Gagal mencari tur berdasarkan destinasi",
                detail={"destination": destination, "original_error": str(e)}
            )

    async def check_tour_availability(self, tour_id: int, tanggal: str) -> Optional[Dict]:
        """
        Memeriksa ketersediaan tur pada tanggal tertentu.

        Args:
            tour_id (int): ID tur
            tanggal (str): Tanggal tur (format: YYYY-MM-DD)

        Returns:
            Optional[Dict]: Data ketersediaan tur jika tersedia

        Raises:
            ValidationException: Jika parameter tidak valid
            NotFoundException: Jika tur tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Memeriksa ketersediaan tur ID {tour_id} pada tanggal {tanggal}")

            if not tour_id or not tanggal:
                raise ValidationException(
                    message="ID tur dan tanggal harus diisi",
                    detail={"tour_id": tour_id, "tanggal": tanggal}
                )

            # Validasi format tanggal
            try:
                await async_strptime(tanggal, "%Y-%m-%d")
            except ValueError:
                raise ValidationException(
                    message="Format tanggal tidak valid. Gunakan format YYYY-MM-DD",
                    detail={"tanggal": tanggal}
                )

            # Get async client
            client = await self._get_client()

            # Periksa apakah tur ada
            tour_response = await client.table(self._tours_table) \
                .select('*') \
                .eq('id', tour_id) \
                .execute()

            if not tour_response.data or len(tour_response.data) == 0:
                raise NotFoundException(
                    message=f"Tur dengan ID {tour_id} tidak ditemukan",
                    detail={"tour_id": tour_id}
                )

            # Periksa jadwal tur
            schedule_response = await client.table(self._tour_schedules_table) \
                .select('*') \
                .eq('tour_id', tour_id) \
                .eq('tanggal', tanggal) \
                .eq('is_available', True) \
                .gt('jumlah_tersedia', 0) \
                .execute()

            if schedule_response.data and len(schedule_response.data) > 0:
                schedule_data = schedule_response.data[0]
                tour_data = tour_response.data[0]

                return {
                    'schedule_id': schedule_data['id'],
                    'tour_id': tour_id,
                    'nama_tour': tour_data['nama'],
                    'tanggal': tanggal,
                    'waktu_mulai': schedule_data['waktu_mulai'],
                    'waktu_selesai': schedule_data['waktu_selesai'],
                    'jumlah_tersedia': schedule_data['jumlah_tersedia'],
                    'harga': tour_data['harga']
                }

            logging.info(f"Tur ID {tour_id} tidak tersedia pada tanggal {tanggal}")
            return None

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat memeriksa ketersediaan tur: {e}")
            raise DatabaseException(
                message="Gagal memeriksa ketersediaan tur",
                detail={"tour_id": tour_id, "tanggal": tanggal, "original_error": str(e)}
            )

    async def create_tour_booking(self, booking_data: Dict) -> Dict:
        """
        Membuat pemesanan tur baru dan mengurangi jumlah tersedia.

        Args:
            booking_data (Dict): Data pemesanan tur

        Returns:
            Dict: Data pemesanan yang telah dibuat

        Raises:
            ValidationException: Jika data pemesanan tidak valid
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Membuat pemesanan tur baru: {booking_data}")

            # Validasi data pemesanan
            required_fields = ['tour_id', 'nama_pemesan', 'email', 'telepon',
                              'tanggal_tour', 'jumlah_peserta', 'total_harga']

            for field in required_fields:
                if field not in booking_data or not booking_data[field]:
                    raise ValidationException(
                        message=f"Field {field} wajib diisi",
                        detail={"booking_data": booking_data}
                    )

            # Get async client
            client = await self._get_client()

            # Cek ketersediaan tur sebelum booking
            availability = await self.check_tour_availability(booking_data['tour_id'], booking_data['tanggal_tour'])
            if not availability or availability['jumlah_tersedia'] < booking_data['jumlah_peserta']:
                raise ValidationException(
                    message=f"Tur tidak tersedia atau jumlah ketersediaan tidak cukup pada tanggal {booking_data['tanggal_tour']}",
                    detail={"tour_id": booking_data['tour_id'], "tanggal": booking_data['tanggal_tour']}
                )

            # Buat pemesanan baru
            try:
                response = await client.table(self._tour_bookings_table) \
                    .insert(booking_data) \
                    .execute()
            except Exception as insert_error:
                logging.error(f"Error detail saat insert tour booking: {insert_error}")
                logging.error(f"Data yang dikirim: {booking_data}")
                raise insert_error

            if not response.data or len(response.data) == 0:
                raise DatabaseException(
                    message="Gagal membuat pemesanan tur",
                    detail={"booking_data": booking_data}
                )

            # Update jumlah tersedia (kurangi sesuai jumlah peserta)
            new_available = availability['jumlah_tersedia'] - booking_data['jumlah_peserta']
            await client.table(self._tour_schedules_table) \
                .update({'jumlah_tersedia': new_available}) \
                .eq('tour_id', booking_data['tour_id']) \
                .eq('tanggal', booking_data['tanggal_tour']) \
                .execute()

            logging.info(f"Pemesanan tur berhasil dibuat dengan ID: {response.data[0]['id']}")
            logging.info(f"Jumlah paket tur berkurang dari {availability['jumlah_tersedia']} menjadi {new_available}")

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except Exception as e:
            logging.error(f"Error saat membuat pemesanan tur: {e}")
            raise DatabaseException(
                message="Gagal membuat pemesanan tur",
                detail={"booking_data": booking_data, "original_error": str(e)}
            )

    async def update_tour_booking_payment(self, booking_id: int, payment_data: Dict) -> Dict:
        """
        Memperbarui status pembayaran untuk pemesanan tur.

        Args:
            booking_id (int): ID pemesanan tur
            payment_data (Dict): Data pembayaran yang akan diperbarui

        Returns:
            Dict: Data pemesanan yang telah diperbarui

        Raises:
            ValidationException: Jika data pembayaran tidak valid
            NotFoundException: Jika pemesanan tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Memperbarui status pembayaran untuk pemesanan tour ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            # Cek apakah pemesanan ada
            booking_response = await client.table(self._tour_bookings_table) \
                .select('*') \
                .eq('id', booking_id) \
                .execute()

            if not booking_response.data or len(booking_response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan tur dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            # Update data pembayaran
            update_response = await client.table(self._tour_bookings_table) \
                .update(payment_data) \
                .eq('id', booking_id) \
                .execute()

            if not update_response.data or len(update_response.data) == 0:
                raise DatabaseException(
                    message=f"Gagal memperbarui pembayaran untuk pemesanan tour ID {booking_id}",
                    detail={"booking_id": booking_id, "payment_data": payment_data}
                )

            logging.info(f"Pembayaran untuk pemesanan tour ID {booking_id} berhasil diperbarui")

            return update_response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat memperbarui pembayaran tur: {e}")
            raise DatabaseException(
                message="Gagal memperbarui pembayaran tur",
                detail={"booking_id": booking_id, "payment_data": payment_data, "original_error": str(e)}
            )

    async def cancel_tour_booking(self, booking_id: int) -> Dict:
        """
        Membatalkan pemesanan tur dan mengembalikan jumlah tersedia.

        Args:
            booking_id (int): ID pemesanan tur

        Returns:
            Dict: Data pemesanan yang telah diperbarui

        Raises:
            ValidationException: Jika ID pemesanan tidak valid
            NotFoundException: Jika pemesanan tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Membatalkan pemesanan tur dengan ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            # Ambil data pemesanan untuk mendapatkan info tur dan tanggal
            booking_response = await client.table(self._tour_bookings_table) \
                .select('*') \
                .eq('id', booking_id) \
                .execute()

            if not booking_response.data or len(booking_response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan tur dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            current_booking = booking_response.data[0]

            # Periksa apakah pemesanan sudah dibatalkan
            if current_booking['status'] == 'cancelled':
                return current_booking

            # Periksa apakah pemesanan sudah selesai
            if current_booking['status'] == 'completed':
                raise ValidationException(
                    message="Tidak dapat membatalkan pemesanan yang sudah selesai",
                    detail={"booking_id": booking_id, "status": current_booking['status']}
                )

            # Update status pemesanan menjadi 'cancelled'
            update_data = {
                'status': 'cancelled',
                'updated_at': (await async_now()).isoformat()
            }

            # Jika sudah dibayar, set status pembayaran menjadi 'refunded'
            if current_booking['status_pembayaran'] == 'paid':
                update_data['status_pembayaran'] = 'refunded'

            update_response = await client.table(self._tour_bookings_table) \
                .update(update_data) \
                .eq('id', booking_id) \
                .execute()

            if not update_response.data or len(update_response.data) == 0:
                raise DatabaseException(
                    message=f"Gagal membatalkan pemesanan tur dengan ID {booking_id}",
                    detail={"booking_id": booking_id}
                )

            # Kembalikan jumlah paket tur yang dibatalkan ke stok tersedia
            schedule_response = await client.table(self._tour_schedules_table) \
                .select('*') \
                .eq('tour_id', current_booking['tour_id']) \
                .eq('tanggal', current_booking['tanggal_tour']) \
                .execute()

            if schedule_response.data and len(schedule_response.data) > 0:
                schedule_data = schedule_response.data[0]
                new_available = schedule_data['jumlah_tersedia'] + current_booking['jumlah_peserta']
                await client.table(self._tour_schedules_table) \
                    .update({'jumlah_tersedia': new_available}) \
                    .eq('id', schedule_data['id']) \
                    .execute()

                logging.info(f"Jumlah paket tur dikembalikan dari {schedule_data['jumlah_tersedia']} menjadi {new_available}")

            return update_response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat membatalkan pemesanan tur: {e}")
            raise DatabaseException(
                message=f"Gagal membatalkan pemesanan tur dengan ID {booking_id}",
                detail={"booking_id": booking_id, "original_error": str(e)}
            )

    async def get_tour_booking_by_id(self, booking_id: int) -> Dict:
        """
        Mendapatkan detail pemesanan tur berdasarkan ID.

        Args:
            booking_id (int): ID pemesanan tur

        Returns:
            Dict: Data pemesanan tur

        Raises:
            ValidationException: Jika ID pemesanan tidak valid
            NotFoundException: Jika pemesanan tidak ditemukan
            DatabaseException: Jika operasi database gagal
        """
        try:
            logging.info(f"Mengambil detail pemesanan tur dengan ID: {booking_id}")

            if not booking_id:
                raise ValidationException(
                    message="ID pemesanan tidak boleh kosong",
                    detail={"booking_id": booking_id}
                )

            # Get async client
            client = await self._get_client()

            response = await client.table(self._tour_bookings_table) \
                .select('*, tours(nama, destinasi, durasi)') \
                .eq('id', booking_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                raise NotFoundException(
                    message=f"Pemesanan tur dengan ID {booking_id} tidak ditemukan",
                    detail={"booking_id": booking_id}
                )

            return response.data[0]

        except ValidationException:
            # Re-raise validation exception
            raise
        except NotFoundException:
            # Re-raise not found exception
            raise
        except Exception as e:
            logging.error(f"Error saat mengambil detail pemesanan tur: {e}")
            raise DatabaseException(
                message=f"Gagal mengambil detail pemesanan tur dengan ID {booking_id}",
                detail={"booking_id": booking_id, "original_error": str(e)}
            )

# Inisialisasi instance global dari TravelBookingEngine
travel_booking_engine = TravelBookingEngine()