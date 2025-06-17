-- agen_travel.sql
-- Skema database untuk aplikasi Agen Travel
-- Dibuat pada: 2025-05-12, di-update pada: 2025-06-10

-- Nonaktifkan trigger sementara
SET session_replication_role = 'replica';

-- Drop tabel yang sudah ada jika ada
DROP TABLE IF EXISTS chat_history CASCADE;
DROP TABLE IF EXISTS flight_bookings CASCADE;
DROP TABLE IF EXISTS flight_schedules CASCADE;
DROP TABLE IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS hotel_bookings CASCADE;
DROP TABLE IF EXISTS hotel_rooms CASCADE;
DROP TABLE IF EXISTS hotels CASCADE;
DROP TABLE IF EXISTS tour_bookings CASCADE;
DROP TABLE IF EXISTS tour_schedules CASCADE;
DROP TABLE IF EXISTS tours CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS external_bookings CASCADE;

-- Drop fungsi yang sudah ada jika ada
DROP FUNCTION IF EXISTS create_new_chat CASCADE;
DROP FUNCTION IF EXISTS delete_chat CASCADE;
DROP FUNCTION IF EXISTS execute_sql CASCADE;
DROP FUNCTION IF EXISTS get_all_user_thread_ids CASCADE;
DROP FUNCTION IF EXISTS get_user_thread_id CASCADE;
DROP FUNCTION IF EXISTS save_chat_message CASCADE;
DROP FUNCTION IF EXISTS save_user_thread_mapping CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
DROP FUNCTION IF EXISTS truncate_chat_data CASCADE;

-- Buat tabel

-- Tabel users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nama TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    telepon TEXT,
    alamat TEXT,
    telegram_id TEXT UNIQUE,
    auth_user_id UUID UNIQUE, -- Link ke auth.users Supabase
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes untuk tabel users (untuk performa autentikasi)
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);

-- Tabel untuk sinkronisasi dengan Supabase Auth
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY, -- Sama dengan auth.users.id
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index untuk user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);



-- Tabel hotels
CREATE TABLE hotels (
    id SERIAL PRIMARY KEY,
    nama TEXT NOT NULL,
    lokasi TEXT NOT NULL,
    alamat TEXT NOT NULL,
    bintang INTEGER NOT NULL,
    fasilitas TEXT[],
    deskripsi TEXT,
    foto_url TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel hotel rooms
CREATE TABLE hotel_rooms (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER REFERENCES hotels(id),
    tipe_kamar TEXT NOT NULL,
    harga INTEGER NOT NULL,
    kapasitas INTEGER NOT NULL,
    jumlah_tersedia INTEGER NOT NULL,
    fasilitas TEXT[],
    foto_url TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel hotel bookings
CREATE TABLE hotel_bookings (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER REFERENCES hotels(id),
    user_id INTEGER REFERENCES users(id),
    nama_pemesan TEXT NOT NULL,
    email TEXT NOT NULL,
    telepon TEXT NOT NULL,
    tanggal_mulai DATE NOT NULL,
    tanggal_akhir DATE NOT NULL,
    jumlah_tamu INTEGER NOT NULL,
    jumlah_kamar INTEGER NOT NULL,
    tipe_kamar TEXT NOT NULL,
    total_harga INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    metode_pembayaran TEXT,
    status_pembayaran TEXT NOT NULL DEFAULT 'unpaid',
    catatan TEXT,
    tanggal_pemesanan DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel flights
CREATE TABLE flights (
    id SERIAL PRIMARY KEY,
    maskapai TEXT NOT NULL,
    kode_penerbangan TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    waktu_berangkat TIME NOT NULL,
    waktu_tiba TIME NOT NULL,
    durasi TEXT NOT NULL,
    harga INTEGER NOT NULL,
    kelas TEXT NOT NULL,
    kursi_tersedia INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel flight schedules
CREATE TABLE flight_schedules (
    id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(id),
    tanggal DATE NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel flight bookings
CREATE TABLE flight_bookings (
    id SERIAL PRIMARY KEY,
    flight_id INTEGER REFERENCES flights(id),
    user_id INTEGER REFERENCES users(id),
    nama_pemesan TEXT NOT NULL,
    email TEXT NOT NULL,
    telepon TEXT NOT NULL,
    tanggal_keberangkatan DATE NOT NULL,
    jumlah_penumpang INTEGER NOT NULL,
    kelas_penerbangan TEXT,
    nomor_kursi TEXT,
    total_harga INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    metode_pembayaran TEXT,
    status_pembayaran TEXT NOT NULL DEFAULT 'unpaid',
    catatan TEXT,
    tanggal_pemesanan DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel tours
CREATE TABLE tours (
    id SERIAL PRIMARY KEY,
    nama TEXT NOT NULL,
    destinasi TEXT NOT NULL,
    deskripsi TEXT NOT NULL,
    durasi TEXT NOT NULL,
    harga INTEGER NOT NULL,
    kapasitas INTEGER NOT NULL,
    fasilitas TEXT[],
    itinerary TEXT[],
    foto_url TEXT[],
    rating DECIMAL(2,1) DEFAULT 0.0,
    kategori TEXT NOT NULL,
    tingkat_kesulitan TEXT DEFAULT 'mudah',
    include_transport BOOLEAN DEFAULT TRUE,
    include_meal BOOLEAN DEFAULT TRUE,
    include_guide BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel tour schedules
CREATE TABLE tour_schedules (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER REFERENCES tours(id),
    tanggal DATE NOT NULL,
    waktu_mulai TIME NOT NULL,
    waktu_selesai TIME NOT NULL,
    jumlah_tersedia INTEGER NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel tour bookings
CREATE TABLE tour_bookings (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER REFERENCES tours(id),
    user_id INTEGER REFERENCES users(id),
    nama_pemesan TEXT NOT NULL,
    email TEXT NOT NULL,
    telepon TEXT NOT NULL,
    tanggal_tour DATE NOT NULL,
    jumlah_peserta INTEGER NOT NULL,
    total_harga INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    metode_pembayaran TEXT,
    status_pembayaran TEXT NOT NULL DEFAULT 'unpaid',
    catatan TEXT,
    tanggal_pemesanan DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel untuk external bookings dari sumber eksternal
CREATE TABLE external_bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    
    -- Source dan tipe booking
    booking_source TEXT NOT NULL, -- 'booking_com', 'airbnb', 'tripadvisor'
    booking_type TEXT NOT NULL,   -- 'hotel', 'flight', 'attraction', 'restaurant'
    
    -- Data pemesan (konsisten dengan hotel_bookings dan flight_bookings)
    nama_pemesan TEXT NOT NULL,
    email TEXT NOT NULL,
    telepon TEXT NOT NULL,
    
    -- Data booking dari external (flexible JSON)
    external_data JSONB NOT NULL, -- Raw data dari MCP tools
    external_id TEXT,             -- ID dari platform eksternal
    external_url TEXT,            -- URL ke listing eksternal
    
    -- Data booking yang dinormalisasi (konsisten dengan existing tables)
    nama_produk TEXT NOT NULL,    -- Nama hotel/flight/attraction/restaurant
    lokasi TEXT,                  -- Lokasi produk
    tanggal_mulai DATE NOT NULL,  -- Check-in/departure/visit date (konsisten dengan hotel_bookings)
    tanggal_akhir DATE,           -- Check-out/return (nullable untuk attraction/restaurant)
    jumlah_tamu INTEGER NOT NULL, -- Guests/passengers/visitors (konsisten dengan hotel_bookings.jumlah_tamu)
    
    -- Data spesifik berdasarkan tipe booking
    booking_details JSONB,        -- Detail spesifik per tipe (kamar, kelas, dll)
    
    -- Pricing (konsisten dengan existing tables, menggunakan INTEGER seperti hotel_bookings)
    total_harga INTEGER NOT NULL, -- Menggunakan INTEGER untuk konsistensi dengan existing tables
    currency TEXT DEFAULT 'IDR',
    
    -- Status (konsisten dengan hotel_bookings dan flight_bookings)
    status TEXT NOT NULL DEFAULT 'pending',
    metode_pembayaran TEXT,
    status_pembayaran TEXT NOT NULL DEFAULT 'unpaid',
    
    -- Catatan dan metadata (konsisten dengan existing tables)
    catatan TEXT,
    
    -- Timestamps (konsisten dengan existing tables)
    tanggal_pemesanan DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel chat history
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    user_message TEXT,
    ai_message TEXT,
    platform TEXT DEFAULT 'telegram',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Buat indexes
CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX idx_chat_history_thread_id ON chat_history(thread_id);
CREATE INDEX chat_history_user_id_platform_updated_at_idx ON chat_history(user_id, platform, updated_at DESC);

CREATE INDEX idx_hotel_lokasi ON hotels(lokasi);

CREATE INDEX idx_hotel_bookings_user_id ON hotel_bookings(user_id);
CREATE INDEX idx_hotel_bookings_hotel_id ON hotel_bookings(hotel_id);
CREATE INDEX idx_hotel_bookings_tanggal_mulai ON hotel_bookings(tanggal_mulai);

CREATE INDEX idx_flight_bookings_user_id ON flight_bookings(user_id);
CREATE INDEX idx_flight_bookings_flight_id ON flight_bookings(flight_id);
CREATE INDEX idx_flight_bookings_tanggal_keberangkatan ON flight_bookings(tanggal_keberangkatan);

CREATE INDEX idx_flight_schedules_tanggal ON flight_schedules(tanggal);

CREATE INDEX idx_tours_destinasi ON tours(destinasi);
CREATE INDEX idx_tours_kategori ON tours(kategori);
CREATE INDEX idx_tour_schedules_tanggal ON tour_schedules(tanggal);
CREATE INDEX idx_tour_bookings_user_id ON tour_bookings(user_id);
CREATE INDEX idx_tour_bookings_tour_id ON tour_bookings(tour_id);
CREATE INDEX idx_tour_bookings_tanggal_tour ON tour_bookings(tanggal_tour);

-- Indexes untuk tabel external_bookings
CREATE INDEX idx_external_bookings_user_id ON external_bookings(user_id);
CREATE INDEX idx_external_bookings_booking_source ON external_bookings(booking_source);
CREATE INDEX idx_external_bookings_booking_type ON external_bookings(booking_type);
CREATE INDEX idx_external_bookings_status ON external_bookings(status);
CREATE INDEX idx_external_bookings_tanggal_mulai ON external_bookings(tanggal_mulai);
CREATE INDEX idx_external_bookings_status_pembayaran ON external_bookings(status_pembayaran);
CREATE INDEX idx_external_bookings_external_id ON external_bookings(external_id);
CREATE INDEX idx_external_bookings_user_status ON external_bookings(user_id, status);
CREATE INDEX idx_external_bookings_source_type ON external_bookings(booking_source, booking_type);

-- Constraints untuk external_bookings
ALTER TABLE external_bookings ADD CONSTRAINT chk_booking_source 
    CHECK (booking_source IN ('booking_com', 'airbnb', 'tripadvisor'));

ALTER TABLE external_bookings ADD CONSTRAINT chk_booking_type 
    CHECK (booking_type IN ('hotel', 'flight', 'attraction', 'restaurant'));

ALTER TABLE external_bookings ADD CONSTRAINT chk_status 
    CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed'));

ALTER TABLE external_bookings ADD CONSTRAINT chk_status_pembayaran 
    CHECK (status_pembayaran IN ('unpaid', 'paid', 'failed', 'refunded'));

ALTER TABLE external_bookings ADD CONSTRAINT chk_metode_pembayaran 
    CHECK (metode_pembayaran IS NULL OR metode_pembayaran IN ('transfer bank', 'kartu kredit', 'e-wallet'));

-- Constraint untuk validasi kombinasi booking_source dan booking_type
ALTER TABLE external_bookings ADD CONSTRAINT chk_valid_source_type_combination
    CHECK (
        (booking_source = 'booking_com' AND booking_type IN ('hotel', 'flight')) OR
        (booking_source = 'airbnb' AND booking_type = 'hotel') OR
        (booking_source = 'tripadvisor' AND booking_type IN ('attraction', 'restaurant'))
    );

-- Constraint untuk validasi tanggal
ALTER TABLE external_bookings ADD CONSTRAINT chk_tanggal_valid
    CHECK (tanggal_akhir IS NULL OR tanggal_akhir >= tanggal_mulai);

-- Buat functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION execute_sql(query TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    EXECUTE 'SELECT json_agg(t) FROM (' || query || ') t' INTO result;
    RETURN COALESCE(result, '[]'::JSONB);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION truncate_chat_data()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    deleted_chat INTEGER;
BEGIN
    -- Delete chat history data
    -- Tambahkan WHERE 1=1 clauses untuk memenuhi Supabase security policy
    DELETE FROM chat_history WHERE 1=1;
    GET DIAGNOSTICS deleted_chat = ROW_COUNT;

    -- Format sebagai array dari single object untuk kompatibilitas Supabase client
    SELECT jsonb_build_array(
        jsonb_build_object(
            'status', 'success',
            'message', 'Berhasil menghapus semua data chat',
            'deleted_at', now(),
            'rows_deleted', jsonb_build_object(
                'chat_history', deleted_chat
            )
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_user_thread_id(p_user_id TEXT, p_platform TEXT DEFAULT 'telegram')
RETURNS TEXT AS $$
DECLARE
    v_thread_id TEXT;
BEGIN
    -- Cari thread_id terbaru untuk user_id
    SELECT thread_id INTO v_thread_id
    FROM chat_history
    WHERE user_id = p_user_id
    AND platform = p_platform
    ORDER BY updated_at DESC
    LIMIT 1;

    RETURN v_thread_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION save_user_thread_mapping(p_user_id TEXT, p_thread_id TEXT, p_platform TEXT DEFAULT 'telegram')
RETURNS VOID AS $$
BEGIN
    -- Cek apakah sudah ada entri untuk user_id ini
    IF EXISTS (
        SELECT 1 FROM chat_history
        WHERE user_id = p_user_id
        AND platform = p_platform
        LIMIT 1
    ) THEN
        -- Update thread_id jika berbeda
        UPDATE chat_history
        SET thread_id = p_thread_id,
            updated_at = NOW()
        WHERE user_id = p_user_id
        AND platform = p_platform
        AND thread_id != p_thread_id;
    ELSE
        -- Insert entri baru jika belum ada
        INSERT INTO chat_history (
            user_id,
            thread_id,
            platform,
            created_at,
            updated_at
        ) VALUES (
            p_user_id,
            p_thread_id,
            p_platform,
            NOW(),
            NOW()
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION save_chat_message(p_user_id TEXT, p_thread_id TEXT, p_user_message TEXT, p_ai_message TEXT, p_platform TEXT DEFAULT 'telegram')
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- Simpan pesan dalam chat_history
    INSERT INTO chat_history (
        user_id,
        thread_id,
        user_message,
        ai_message,
        platform,
        created_at,
        updated_at
    ) VALUES (
        p_user_id,
        p_thread_id,
        p_user_message,
        p_ai_message,
        p_platform,
        NOW(),
        NOW()
    )
    RETURNING to_jsonb(chat_history.*) INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_all_user_thread_ids(p_platform TEXT DEFAULT 'telegram')
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    WITH latest_threads AS (
        SELECT DISTINCT ON (user_id) user_id, thread_id, updated_at
        FROM chat_history
        WHERE platform = p_platform
        ORDER BY user_id, updated_at DESC
    )
    SELECT json_agg(json_build_object('user_id', user_id, 'thread_id', thread_id))
    INTO v_result
    FROM latest_threads;

    RETURN COALESCE(v_result, '[]'::JSONB);
END;
$$ LANGUAGE plpgsql;

-- Fungsi untuk menghapus chat beserta semua data terkait
CREATE OR REPLACE FUNCTION delete_chat(p_thread_id text)
 RETURNS TABLE(
    status text,
    message text,
    thread_id text,
    deleted_at timestamptz,
    chat_history_deleted integer
 )
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    deleted_chat_history INTEGER;
BEGIN
    -- Hapus semua chat history untuk chat tertentu (termasuk yang kosong)
    DELETE FROM chat_history ch WHERE ch.thread_id = p_thread_id;
    GET DIAGNOSTICS deleted_chat_history = ROW_COUNT;

    -- Return sebagai table row
    RETURN QUERY SELECT
        'success'::text,
        'Berhasil menghapus chat dan semua data terkait'::text,
        p_thread_id,
        now(),
        deleted_chat_history;
END;
$function$;

-- Fungsi untuk membuat chat baru untuk user
CREATE OR REPLACE FUNCTION create_new_chat(p_user_id text, p_new_thread_id text, p_platform text DEFAULT 'telegram'::text)
 RETURNS TABLE(
    status text,
    message text,
    user_id text,
    old_thread_id text,
    new_thread_id text,
    platform text,
    created_at timestamptz
 )
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_old_thread_id TEXT;
BEGIN
    -- Dapatkan thread_id lama jika ada (untuk informasi)
    SELECT ch.thread_id INTO v_old_thread_id
    FROM chat_history ch
    WHERE ch.user_id = p_user_id
    AND ch.platform = p_platform
    ORDER BY ch.updated_at DESC
    LIMIT 1;

    -- Simpan mapping chat baru
    PERFORM save_user_thread_mapping(p_user_id, p_new_thread_id, p_platform);

    -- Return sebagai table row
    RETURN QUERY SELECT
        'success'::text,
        'Chat baru berhasil dibuat'::text,
        p_user_id,
        v_old_thread_id,
        p_new_thread_id,
        p_platform,
        now();
END;
$function$;

-- ========================================
-- FUNGSI AUTENTIKASI DAN USER MANAGEMENT
-- ========================================

-- Buat fungsi untuk registrasi user
CREATE OR REPLACE FUNCTION register_user(
    p_nama TEXT,
    p_email TEXT,
    p_password TEXT,
    p_telepon TEXT DEFAULT NULL,
    p_alamat TEXT DEFAULT NULL,
    p_telegram_id TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_user_id INTEGER;
    v_result JSONB;
BEGIN
    -- Cek apakah email sudah terdaftar
    IF EXISTS (SELECT 1 FROM users WHERE email = p_email) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Email sudah terdaftar',
            'error_code', 'EMAIL_EXISTS'
        );
    END IF;

    -- Cek apakah telegram_id sudah terdaftar (jika diberikan)
    IF p_telegram_id IS NOT NULL AND EXISTS (SELECT 1 FROM users WHERE telegram_id = p_telegram_id) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Telegram ID sudah terdaftar',
            'error_code', 'TELEGRAM_ID_EXISTS'
        );
    END IF;

    -- Insert user baru
    INSERT INTO users (
        nama,
        email,
        password,
        telepon,
        alamat,
        telegram_id,
        is_active,
        is_verified,
        last_login,
        created_at,
        updated_at
    ) VALUES (
        p_nama,
        p_email,
        p_password,  -- Password sudah di-hash dari aplikasi
        p_telepon,
        p_alamat,
        p_telegram_id,
        TRUE,
        FALSE, -- User baru perlu verifikasi
        NOW(), -- Set last_login saat registrasi berhasil
        NOW(),
        NOW()
    )
    RETURNING id INTO v_user_id;

    -- Return success response
    SELECT jsonb_build_object(
        'success', true,
        'user_id', v_user_id,
        'message', 'User berhasil didaftarkan'
    ) INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Buat fungsi untuk login user
CREATE OR REPLACE FUNCTION login_user(
    p_email TEXT,
    p_password TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_user RECORD;
    v_result JSONB;
BEGIN
    -- Cari user berdasarkan email
    SELECT id, nama, email, password, telepon, alamat, telegram_id, is_active, is_verified
    INTO v_user
    FROM users
    WHERE email = p_email;

    -- Cek apakah user ditemukan
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Email atau password salah',
            'error_code', 'INVALID_CREDENTIALS'
        );
    END IF;

    -- Cek apakah user aktif
    IF NOT v_user.is_active THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Akun tidak aktif',
            'error_code', 'ACCOUNT_INACTIVE'
        );
    END IF;

    -- Password verification akan dilakukan di aplikasi Python
    -- Fungsi ini hanya return user data untuk verification di aplikasi

    -- Update last_login
    UPDATE users
    SET last_login = NOW(), updated_at = NOW()
    WHERE id = v_user.id;

    -- Return success response dengan data user
    SELECT jsonb_build_object(
        'success', true,
        'user', jsonb_build_object(
            'id', v_user.id,
            'nama', v_user.nama,
            'email', v_user.email,
            'telepon', v_user.telepon,
            'alamat', v_user.alamat,
            'telegram_id', v_user.telegram_id,
            'is_verified', v_user.is_verified
        ),
        'message', 'Login berhasil'
    ) INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Buat fungsi untuk link telegram user dengan existing user
CREATE OR REPLACE FUNCTION link_telegram_user(
    p_user_id INTEGER,
    p_telegram_id TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- Cek apakah user_id valid
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_user_id) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'User tidak ditemukan',
            'error_code', 'USER_NOT_FOUND'
        );
    END IF;

    -- Cek apakah telegram_id sudah digunakan
    IF EXISTS (SELECT 1 FROM users WHERE telegram_id = p_telegram_id AND id != p_user_id) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Telegram ID sudah digunakan',
            'error_code', 'TELEGRAM_ID_EXISTS'
        );
    END IF;

    -- Update telegram_id
    UPDATE users
    SET telegram_id = p_telegram_id, updated_at = NOW()
    WHERE id = p_user_id;

    RETURN jsonb_build_object(
        'success', true,
        'message', 'Telegram user berhasil di-link'
    );
END;
$$ LANGUAGE plpgsql;

-- Buat fungsi untuk mendapatkan user berdasarkan telegram_id
CREATE OR REPLACE FUNCTION get_user_by_telegram_id(p_telegram_id TEXT)
RETURNS JSONB AS $$
DECLARE
    v_user RECORD;
    v_result JSONB;
BEGIN
    -- Cari user berdasarkan telegram_id
    SELECT id, nama, email, telepon, alamat, telegram_id, auth_user_id, is_active, is_verified, last_login
    INTO v_user
    FROM users
    WHERE telegram_id = p_telegram_id AND is_active = TRUE;

    -- Cek apakah user ditemukan
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'User tidak ditemukan',
            'error_code', 'USER_NOT_FOUND'
        );
    END IF;

    -- Return user data
    SELECT jsonb_build_object(
        'success', true,
        'user', jsonb_build_object(
            'id', v_user.id,
            'nama', v_user.nama,
            'email', v_user.email,
            'telepon', v_user.telepon,
            'alamat', v_user.alamat,
            'telegram_id', v_user.telegram_id,
            'auth_user_id', v_user.auth_user_id,
            'is_verified', v_user.is_verified,
            'last_login', v_user.last_login
        )
    ) INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Fungsi untuk sinkronisasi user dengan Supabase Auth
CREATE OR REPLACE FUNCTION sync_user_with_auth()
RETURNS TRIGGER AS $$
BEGIN
    -- Update is_verified berdasarkan auth.users
    UPDATE users
    SET is_verified = NEW.email_confirmed_at IS NOT NULL,
        updated_at = NOW()
    WHERE auth_user_id = NEW.id;

    -- Update user_profiles
    INSERT INTO user_profiles (id, user_id, synced_at)
    SELECT NEW.id, u.id, NOW()
    FROM users u
    WHERE u.auth_user_id = NEW.id
    ON CONFLICT (id) DO UPDATE SET
        synced_at = NOW(),
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



-- Buat triggers
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_history_updated_at
BEFORE UPDATE ON chat_history
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tours_updated_at
BEFORE UPDATE ON tours
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tour_schedules_updated_at
BEFORE UPDATE ON tour_schedules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tour_bookings_updated_at
BEFORE UPDATE ON tour_bookings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_external_bookings_updated_at
BEFORE UPDATE ON external_bookings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Aktifkan kembali triggers
SET session_replication_role = 'origin';

-- Grant all privileges untuk semua tabel untuk menghindari RLS dan masalah perizinan
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO PUBLIC;

-- Grant khusus untuk tabel-tabel utama
GRANT ALL ON users TO PUBLIC;
GRANT ALL ON user_profiles TO PUBLIC;
GRANT ALL ON hotels TO PUBLIC;
GRANT ALL ON hotel_rooms TO PUBLIC;
GRANT ALL ON hotel_bookings TO PUBLIC;
GRANT ALL ON flights TO PUBLIC;
GRANT ALL ON flight_schedules TO PUBLIC;
GRANT ALL ON flight_bookings TO PUBLIC;
GRANT ALL ON tours TO PUBLIC;
GRANT ALL ON tour_schedules TO PUBLIC;
GRANT ALL ON tour_bookings TO PUBLIC;
GRANT ALL ON chat_history TO PUBLIC;
GRANT ALL ON external_bookings TO PUBLIC;

-- Grant untuk sequences
GRANT ALL ON users_id_seq TO PUBLIC;
GRANT ALL ON hotels_id_seq TO PUBLIC;
GRANT ALL ON hotel_rooms_id_seq TO PUBLIC;
GRANT ALL ON hotel_bookings_id_seq TO PUBLIC;
GRANT ALL ON flights_id_seq TO PUBLIC;
GRANT ALL ON flight_schedules_id_seq TO PUBLIC;
GRANT ALL ON flight_bookings_id_seq TO PUBLIC;
GRANT ALL ON tours_id_seq TO PUBLIC;
GRANT ALL ON tour_schedules_id_seq TO PUBLIC;
GRANT ALL ON tour_bookings_id_seq TO PUBLIC;
GRANT ALL ON chat_history_id_seq TO PUBLIC;
GRANT ALL ON external_bookings_id_seq TO PUBLIC;

-- Grant permissions untuk fungsi autentikasi
GRANT EXECUTE ON FUNCTION register_user(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION login_user(TEXT, TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION link_telegram_user(INTEGER, TEXT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_user_by_telegram_id(TEXT) TO PUBLIC;

-- Disable RLS untuk semua tabel
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE hotels DISABLE ROW LEVEL SECURITY;
ALTER TABLE hotel_rooms DISABLE ROW LEVEL SECURITY;
ALTER TABLE hotel_bookings DISABLE ROW LEVEL SECURITY;
ALTER TABLE flights DISABLE ROW LEVEL SECURITY;
ALTER TABLE flight_schedules DISABLE ROW LEVEL SECURITY;
ALTER TABLE flight_bookings DISABLE ROW LEVEL SECURITY;
ALTER TABLE tours DISABLE ROW LEVEL SECURITY;
ALTER TABLE tour_schedules DISABLE ROW LEVEL SECURITY;
ALTER TABLE tour_bookings DISABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE external_bookings DISABLE ROW LEVEL SECURITY;

-- Tambahkan komentar untuk dokumentasi
COMMENT ON TABLE external_bookings IS 'Tabel untuk menyimpan booking dari sumber eksternal (Booking.com, Airbnb, TripAdvisor)';
COMMENT ON COLUMN external_bookings.booking_source IS 'Sumber booking: booking_com, airbnb, tripadvisor';
COMMENT ON COLUMN external_bookings.booking_type IS 'Tipe booking: hotel, flight, attraction, restaurant';
COMMENT ON COLUMN external_bookings.external_data IS 'Raw data JSON dari MCP tools';
COMMENT ON COLUMN external_bookings.external_id IS 'ID produk dari platform eksternal';
COMMENT ON COLUMN external_bookings.booking_details IS 'Detail spesifik per tipe booking (kamar, kelas, dll)';
COMMENT ON COLUMN external_bookings.total_harga IS 'Total harga dalam format INTEGER (konsisten dengan existing tables)';
