-- drop_agen_travel.sql
-- Script untuk menghapus semua tabel, fungsi, trigger, dan data dari database Agen Travel
-- Dibuat pada: 2025-01-27, di-update pada: 2025-06-10
-- Gunakan script ini untuk reset database sebelum menjalankan agen_travel.sql -> data_agen_travel.sql

-- Nonaktifkan trigger sementara untuk menghindari masalah dependency
SET session_replication_role = 'replica';

-- Hapus semua trigger terlebih dahulu
DROP TRIGGER IF EXISTS update_users_updated_at ON users CASCADE;
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles CASCADE;
DROP TRIGGER IF EXISTS update_chat_history_updated_at ON chat_history CASCADE;
DROP TRIGGER IF EXISTS update_tours_updated_at ON tours CASCADE;
DROP TRIGGER IF EXISTS update_tour_schedules_updated_at ON tour_schedules CASCADE;
DROP TRIGGER IF EXISTS update_tour_bookings_updated_at ON tour_bookings CASCADE;
DROP TRIGGER IF EXISTS update_external_bookings_updated_at ON external_bookings CASCADE;

-- Hapus semua fungsi
-- Fungsi chat management
DROP FUNCTION IF EXISTS create_new_chat(text, text, text) CASCADE;
DROP FUNCTION IF EXISTS delete_chat(text) CASCADE;
DROP FUNCTION IF EXISTS execute_sql(text) CASCADE;
DROP FUNCTION IF EXISTS get_all_user_thread_ids(text) CASCADE;
DROP FUNCTION IF EXISTS get_user_thread_id(text, text) CASCADE;
DROP FUNCTION IF EXISTS save_chat_message(text, text, text, text, text) CASCADE;
DROP FUNCTION IF EXISTS save_user_thread_mapping(text, text, text) CASCADE;
DROP FUNCTION IF EXISTS truncate_chat_data() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Fungsi autentikasi dan user management
DROP FUNCTION IF EXISTS register_user(text, text, text, text, text, text) CASCADE;
DROP FUNCTION IF EXISTS login_user(text, text) CASCADE;
DROP FUNCTION IF EXISTS link_telegram_user(integer, text) CASCADE;
DROP FUNCTION IF EXISTS get_user_by_telegram_id(text) CASCADE;
DROP FUNCTION IF EXISTS sync_user_with_auth() CASCADE;

-- Hapus semua tabel dalam urutan yang benar (child tables dulu, kemudian parent tables)
-- Tabel booking dan schedule (child tables)
DROP TABLE IF EXISTS external_bookings CASCADE;
DROP TABLE IF EXISTS tour_bookings CASCADE;
DROP TABLE IF EXISTS tour_schedules CASCADE;
DROP TABLE IF EXISTS flight_bookings CASCADE;
DROP TABLE IF EXISTS flight_schedules CASCADE;
DROP TABLE IF EXISTS hotel_bookings CASCADE;
DROP TABLE IF EXISTS hotel_rooms CASCADE;

-- Tabel chat dan checkpoint
DROP TABLE IF EXISTS chat_history CASCADE;
DROP TABLE IF EXISTS checkpoint_writes CASCADE;
DROP TABLE IF EXISTS checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS checkpoints CASCADE;
DROP TABLE IF EXISTS checkpoint_migrations CASCADE;

-- Tabel utama (parent tables)
DROP TABLE IF EXISTS tours CASCADE;
DROP TABLE IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS hotels CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Hapus semua sequence yang mungkin tersisa
DROP SEQUENCE IF EXISTS chat_history_id_seq CASCADE;
DROP SEQUENCE IF EXISTS checkpoint_migrations_v_seq CASCADE;
DROP SEQUENCE IF EXISTS external_bookings_id_seq CASCADE;
DROP SEQUENCE IF EXISTS flight_bookings_id_seq CASCADE;
DROP SEQUENCE IF EXISTS flight_schedules_id_seq CASCADE;
DROP SEQUENCE IF EXISTS flights_id_seq CASCADE;
DROP SEQUENCE IF EXISTS hotel_bookings_id_seq CASCADE;
DROP SEQUENCE IF EXISTS hotel_rooms_id_seq CASCADE;
DROP SEQUENCE IF EXISTS hotels_id_seq CASCADE;
DROP SEQUENCE IF EXISTS tour_bookings_id_seq CASCADE;
DROP SEQUENCE IF EXISTS tour_schedules_id_seq CASCADE;
DROP SEQUENCE IF EXISTS tours_id_seq CASCADE;
DROP SEQUENCE IF EXISTS users_id_seq CASCADE;

-- Hapus semua index yang mungkin tersisa
-- Index autentikasi
DROP INDEX IF EXISTS idx_users_telegram_id CASCADE;
DROP INDEX IF EXISTS idx_users_email_active CASCADE;
DROP INDEX IF EXISTS idx_users_is_active CASCADE;
DROP INDEX IF EXISTS idx_users_auth_user_id CASCADE;
DROP INDEX IF EXISTS idx_user_profiles_user_id CASCADE;

-- Index chat dan aplikasi
DROP INDEX IF EXISTS idx_chat_history_user_id CASCADE;
DROP INDEX IF EXISTS idx_chat_history_thread_id CASCADE;
DROP INDEX IF EXISTS chat_history_user_id_platform_updated_at_idx CASCADE;
DROP INDEX IF EXISTS idx_hotel_lokasi CASCADE;
DROP INDEX IF EXISTS idx_hotel_bookings_user_id CASCADE;
DROP INDEX IF EXISTS idx_hotel_bookings_hotel_id CASCADE;
DROP INDEX IF EXISTS idx_hotel_bookings_tanggal_mulai CASCADE;
DROP INDEX IF EXISTS idx_flight_bookings_user_id CASCADE;
DROP INDEX IF EXISTS idx_flight_bookings_flight_id CASCADE;
DROP INDEX IF EXISTS idx_flight_bookings_tanggal_keberangkatan CASCADE;
DROP INDEX IF EXISTS idx_flight_schedules_tanggal CASCADE;
DROP INDEX IF EXISTS idx_tours_destinasi CASCADE;
DROP INDEX IF EXISTS idx_tours_kategori CASCADE;
DROP INDEX IF EXISTS idx_tour_schedules_tanggal CASCADE;
DROP INDEX IF EXISTS idx_tour_bookings_user_id CASCADE;
DROP INDEX IF EXISTS idx_tour_bookings_tour_id CASCADE;
DROP INDEX IF EXISTS idx_tour_bookings_tanggal_tour CASCADE;
DROP INDEX IF EXISTS checkpoints_thread_id_idx CASCADE;
DROP INDEX IF EXISTS checkpoint_blobs_thread_id_idx CASCADE;
DROP INDEX IF EXISTS checkpoint_writes_thread_id_idx CASCADE;

-- Index external bookings
DROP INDEX IF EXISTS idx_external_bookings_user_id CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_booking_source CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_booking_type CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_status CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_tanggal_mulai CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_status_pembayaran CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_external_id CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_user_status CASCADE;
DROP INDEX IF EXISTS idx_external_bookings_source_type CASCADE;

-- Hapus semua view yang mungkin ada
DROP VIEW IF EXISTS v_hotel_availability CASCADE;
DROP VIEW IF EXISTS v_flight_availability CASCADE;
DROP VIEW IF EXISTS v_tour_availability CASCADE;
DROP VIEW IF EXISTS v_booking_summary CASCADE;

-- Hapus semua type yang mungkin ada
DROP TYPE IF EXISTS booking_status CASCADE;
DROP TYPE IF EXISTS payment_status CASCADE;
DROP TYPE IF EXISTS payment_method CASCADE;
DROP TYPE IF EXISTS flight_class CASCADE;
DROP TYPE IF EXISTS tour_difficulty CASCADE;

-- Hapus semua constraints yang mungkin ada
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_booking_source CASCADE;
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_booking_type CASCADE;
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_status CASCADE;
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_status_pembayaran CASCADE;
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_metode_pembayaran CASCADE;
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_valid_source_type_combination CASCADE;
ALTER TABLE IF EXISTS external_bookings DROP CONSTRAINT IF EXISTS chk_tanggal_valid CASCADE;

-- Aktifkan kembali trigger
SET session_replication_role = 'origin';

-- Tampilkan pesan konfirmasi
SELECT 'Database Agen Travel berhasil direset. Semua tabel, fungsi , trigger, sequence, index, view, dan type telah dihapus.' AS status;
SELECT 'Sekarang Anda dapat menjalankan agen_travel.sql diikuti dengan data_agen_travel.sql untuk inisialisasi ulang database.' AS next_step;
