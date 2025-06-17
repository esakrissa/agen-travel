-- data_agen_travel.sql
-- Sample data untuk aplikasi Agen Travel
-- Dibuat pada: 2025-05-12, di-update pada: 2025-06-10
-- Password = "password123" (hashed)

-- Insert data ke tabel hotels
INSERT INTO hotels (id, nama, lokasi, alamat, bintang, fasilitas, deskripsi, foto_url, created_at, updated_at) VALUES
(1, 'Puri Bali Ubud Resort', 'Ubud', 'Jl. Raya Ubud No. 88, Ubud, Bali', 5, ARRAY['Kolam renang', 'Spa', 'Restoran', 'WiFi', 'Balkon pribadi', 'Yoga kelas'], 'Resort mewah di tengah hutan Ubud dengan pemandangan sawah dan sungai. Arsitektur tradisional Bali dengan sentuhan modern.', ARRAY['https://example.com/puri_bali1.jpg', 'https://example.com/puri_bali2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(2, 'Kuta Paradise Hotel', 'Kuta', 'Jl. Pantai Kuta No. 123, Kuta, Bali', 4, ARRAY['Kolam renang', 'Restoran', 'Bar tepi pantai', 'WiFi', 'AC', 'Kamar keluarga'], 'Hotel nyaman dengan lokasi strategis dekat Pantai Kuta, cocok untuk keluarga dan peselancar.', ARRAY['https://example.com/kuta_paradise1.jpg', 'https://example.com/kuta_paradise2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(3, 'Sanur Beach Villa', 'Sanur', 'Jl. Danau Tamblingan No. 45, Sanur, Bali', 5, ARRAY['Vila pribadi', 'Kolam renang pribadi', 'Akses langsung ke pantai', 'Sarapan', 'Spa', 'Layanan kamar 24 jam'], 'Vila mewah dengan akses langsung ke pantai privat di Sanur. Desain tradisional Bali dengan fasilitas modern.', ARRAY['https://example.com/sanur_villa1.jpg', 'https://example.com/sanur_villa2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(4, 'Seminyak Luxury Resort', 'Seminyak', 'Jl. Kayu Aya No. 68, Seminyak, Bali', 5, ARRAY['Butler pribadi', 'Kolam renang', 'Spa', 'Restoran bintang 5', 'Bar rooftop', 'Akses VIP ke klub pantai'], 'Resort bintang 5 dengan layanan eksklusif di jantung Seminyak. Desain kontemporer dengan unsur budaya Bali.', ARRAY['https://example.com/seminyak_luxury1.jpg', 'https://example.com/seminyak_luxury2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(5, 'Jimbaran Bay Hotel', 'Jimbaran', 'Jl. Raya Uluwatu No. 77, Jimbaran, Bali', 4, ARRAY['Pemandangan laut', 'Restoran seafood', 'Kolam renang', 'Spa', 'WiFi', 'Teras pribadi'], 'Hotel dengan pemandangan spektakuler Teluk Jimbaran. Terkenal dengan restoran seafood dan matahari terbenam yang indah.', ARRAY['https://example.com/jimbaran_bay1.jpg', 'https://example.com/jimbaran_bay2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(6, 'Jungle Retreat Ubud', 'Ubud', 'Jl. Raya Monkey Forest No. 112, Ubud, Bali', 4, ARRAY['Kolam renang infinity', 'Yoga pavilion', 'Restoran organik', 'WiFi', 'Spa', 'Shuttle service'], 'Resort yang dikelilingi hutan tropis dengan arsitektur Bali yang otentik dan pemandangan lembah sungai', ARRAY['https://example.com/jungle_retreat1.jpg', 'https://example.com/jungle_retreat2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(7, 'Tegallalang Rice Terrace Resort', 'Tegallalang', 'Jl. Raya Tegallalang No. 88, Gianyar, Bali', 4, ARRAY['Kolam renang', 'Restoran', 'Pemandangan sawah', 'Yoga', 'Spa', 'Tour sepeda'], 'Resort unik dengan pemandangan langsung ke terasering sawah Tegallalang yang ikonik', ARRAY['https://example.com/tegallalang1.jpg', 'https://example.com/tegallalang2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(8, 'Nusa Dua Beach Resort & Spa', 'Nusa Dua', 'ITDC Complex, Nusa Dua, Bali', 5, ARRAY['Kolam renang', 'Spa', 'Private beach club', 'Restoran', 'Gym', 'Water sports'], 'Resort mewah dengan pantai berpasir putih privat di kawasan eksklusif Nusa Dua', ARRAY['https://example.com/nusadua1.jpg', 'https://example.com/nusadua2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(9, 'Uluwatu Cliff Villa', 'Uluwatu', 'Jl. Pantai Suluban, Pecatu, Bali', 5, ARRAY['Infinity pool', 'Akses pantai', 'Restoran', 'Bar', 'Shuttle service', 'Pemandangan laut'], 'Villa mewah di atas tebing Uluwatu dengan pemandangan Samudra Hindia yang memukau', ARRAY['https://example.com/uluwatu1.jpg', 'https://example.com/uluwatu2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00'),
(10, 'Denpasar City Hotel', 'Denpasar', 'Jl. Gatot Subroto Barat No. 345, Denpasar, Bali', 3, ARRAY['WiFi', 'Restoran', 'Meeting room', 'Room service', 'Laundry', 'Parkir gratis'], 'Hotel bisnis yang nyaman di pusat kota Denpasar, dekat dengan berbagai atraksi dan pusat pemerintahan', ARRAY['https://example.com/denpasar1.jpg', 'https://example.com/denpasar2.jpg'], '2025-05-08 06:53:28.654156+00', '2025-05-08 06:53:28.654156+00');

-- Insert data ke tabel users (dengan password dan telegram_id)
INSERT INTO users (id, nama, email, password, telepon, alamat, telegram_id, is_active, is_verified, created_at, updated_at) VALUES
(1, 'Wayan Dharma', 'wayan.dharma@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567890', 'Jl. Danau Tamblingan No. 45, Denpasar, Bali', '499956001', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(2, 'Ni Made Dewi', 'made.dewi@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567891', 'Jl. Sunset Road No. 32, Kuta, Bali', '499956002', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(3, 'Nyoman Agus', 'nyoman.agus@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567892', 'Jl. Raya Ubud No. 112, Ubud, Bali', '499956003', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(4, 'Ni Ketut Ayu', 'ketut.ayu@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567893', 'Jl. Legian No. 77, Legian, Bali', '499956004', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(5, 'I Gede Surya', 'gede.surya@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567894', 'Jl. Ngurah Rai No. 23, Sanur, Bali', '499956005', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(6, 'Putu Eka Suparta', 'putu.eka@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567895', 'Jl. Tukad Badung No. 15, Denpasar, Bali', '499956006', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(7, 'Kadek Ariawan', 'kadek.ariawan@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567896', 'Jl. Padma Utara No. 23, Legian, Bali', '499956007', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(8, 'I Komang Sutama', 'komang.sutama@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567897', 'Jl. Hanoman No. 45, Ubud, Bali', '499956008', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(9, 'I Ketut Sudira', 'ketut.sudira@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567898', 'Jl. Raya Kuta No. 67, Kuta, Bali', '499956009', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(10, 'Ni Putu Seruni', 'putu.seruni@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234567899', 'Jl. Danau Beratan No. 12, Sanur, Bali', '499956010', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(11, 'Ni Made Artini', 'made.artini@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234568000', 'Jl. Double Six No. 8, Seminyak, Bali', '499956011', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(12, 'I Nyoman Sumerta', 'nyoman.sumerta@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234568001', 'Jl. Uluwatu No. 34, Jimbaran, Bali', '499956012', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(13, 'Ni Ketut Sulastri', 'ketut.sulastri@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081234568002', 'Jl. Pantai Mengiat No. 7, Nusa Dua, Bali', '499956013', TRUE, TRUE, '2025-05-08 06:53:29.074568+00', '2025-05-08 06:53:29.074568+00'),
(14, 'Wayan Bagus', 'wayan.bagus@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081233445786', 'Jalan Raya Andon, No. 12, Peliatan Ubud', '499956014', TRUE, TRUE, '2025-05-08 07:14:52.749344+00', '2025-05-08 07:14:52.749344+00'),
(15, 'Made Bagus', 'madebagus.md@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081233445800', 'Jalan Raya Andong', '499956015', TRUE, TRUE, '2025-05-08 07:54:34.452503+00', '2025-05-08 07:54:34.452503+00'),
(16, 'Esa Krissa', 'esakrissa.wayan@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081237401690', 'Br. Tengah Manuaba, Kenderan Tegalalang', '499956016', TRUE, TRUE, '2025-05-12 04:38:08.330807+00', '2025-05-12 04:38:08.330807+00'),
-- User test tambahan untuk testing autentikasi
(17, 'Ketut Bagus', 'ketut.bagus@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081245667333', 'Jl. Raya Test Integrasi', '499956000', TRUE, FALSE, '2025-05-30 13:34:00.101446+00', '2025-05-30 13:34:19.001267+00'),
(18, 'Nyoman Bagus', 'nyomanbagus@gmail.com', '$2b$12$a3/Zygp5zb4Ps8aTdqtLYeVaA2llbiIgid0DU9TxSp2JBmkoQfy9u', '081245667555', 'Jl. Raya Test Integrasi', '499956017', TRUE, FALSE, '2025-05-30 13:27:54.170334+00', '2025-05-30 13:27:54.170340+00');

-- Insert data ke tabel hotel_rooms
INSERT INTO hotel_rooms (id, hotel_id, tipe_kamar, harga, kapasitas, jumlah_tersedia, fasilitas, foto_url, created_at, updated_at) VALUES
(1, 1, 'Deluxe Garden View', 1500000, 2, 15, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Balkon'], ARRAY['https://example.com/puri_room1.jpg', 'https://example.com/puri_room2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(2, 1, 'Premium Pool Access', 2500000, 2, 8, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Akses langsung ke kolam renang'], ARRAY['https://example.com/puri_pool1.jpg', 'https://example.com/puri_pool2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(3, 1, 'Villa Suite', 3000000, 4, 5, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Ruang tamu', 'Kolam renang pribadi'], ARRAY['https://example.com/puri_villa1.jpg', 'https://example.com/puri_villa2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(4, 2, 'Standard Room', 800000, 2, 20, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'WiFi'], ARRAY['https://example.com/kuta_std1.jpg', 'https://example.com/kuta_std2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(5, 2, 'Deluxe Beach View', 1200000, 2, 15, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Balkon dengan pemandangan pantai'], ARRAY['https://example.com/kuta_deluxe1.jpg', 'https://example.com/kuta_deluxe2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(6, 2, 'Family Room', 1500000, 4, 10, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', '2 Tempat Tidur Queen'], ARRAY['https://example.com/kuta_family1.jpg', 'https://example.com/kuta_family2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(7, 3, 'Beach Villa', 2000000, 2, 8, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Akses langsung ke pantai'], ARRAY['https://example.com/sanur_beach1.jpg', 'https://example.com/sanur_beach2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(8, 3, 'Pool Suite', 3000000, 2, 6, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Ruang tamu', 'Kolam renang pribadi'], ARRAY['https://example.com/sanur_pool1.jpg', 'https://example.com/sanur_pool2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(9, 3, 'Presidential Villa', 5000000, 4, 2, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Ruang tamu', 'Kolam renang pribadi', 'Butler'], ARRAY['https://example.com/sanur_pres1.jpg', 'https://example.com/sanur_pres2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(10, 4, 'Luxury Suite', 3500000, 2, 12, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Balkon', 'Jacuzzi'], ARRAY['https://example.com/seminyak_suite1.jpg', 'https://example.com/seminyak_suite2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(11, 4, 'Royal Villa', 7000000, 4, 5, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Ruang tamu', 'Kolam renang pribadi', 'Butler'], ARRAY['https://example.com/seminyak_royal1.jpg', 'https://example.com/seminyak_royal2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(12, 5, 'Ocean View Room', 1200000, 2, 15, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Balkon dengan pemandangan laut'], ARRAY['https://example.com/jimbaran_ocean1.jpg', 'https://example.com/jimbaran_ocean2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(13, 5, 'Seafront Suite', 2500000, 2, 8, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Ruang tamu', 'Balkon luas menghadap laut'], ARRAY['https://example.com/jimbaran_suite1.jpg', 'https://example.com/jimbaran_suite2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(14, 6, 'Jungle View Room', 1200000, 2, 15, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Minibar', 'Balkon dengan pemandangan hutan'], ARRAY['https://example.com/jungle_room1.jpg', 'https://example.com/jungle_room2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(15, 6, 'Riverside Suite', 2000000, 2, 8, ARRAY['Kamar mandi dengan bathtub', 'AC', 'TV', 'Minibar', 'Ruang tamu', 'Balkon dengan pemandangan sungai'], ARRAY['https://example.com/jungle_suite1.jpg', 'https://example.com/jungle_suite2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(16, 7, 'Rice Terrace View', 1500000, 2, 12, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'Balkon', 'Pemandangan sawah'], ARRAY['https://example.com/rice_room1.jpg', 'https://example.com/rice_room2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(17, 7, 'Family Suite', 2800000, 4, 6, ARRAY['Kamar mandi dengan bathtub', 'AC', 'TV', 'Minibar', 'Ruang keluarga', 'Teras luas'], ARRAY['https://example.com/rice_suite1.jpg', 'https://example.com/rice_suite2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(18, 8, 'Ocean View Deluxe', 2500000, 2, 20, ARRAY['Kamar mandi mewah', 'AC', 'Smart TV', 'Minibar', 'Balkon laut'], ARRAY['https://example.com/nusadua_deluxe1.jpg', 'https://example.com/nusadua_deluxe2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(19, 8, 'Beachfront Villa', 4500000, 4, 8, ARRAY['Kamar mandi mewah', 'AC', 'Smart TV', 'Minibar', 'Dapur kecil', 'Teras pantai'], ARRAY['https://example.com/nusadua_villa1.jpg', 'https://example.com/nusadua_villa2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(20, 9, 'Cliff View Suite', 3000000, 2, 10, ARRAY['Kamar mandi dengan bathtub', 'AC', 'TV plasma', 'Minibar', 'Balkon dengan pemandangan laut'], ARRAY['https://example.com/cliff_suite1.jpg', 'https://example.com/cliff_suite2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(21, 9, 'Honeymoon Pool Villa', 5500000, 2, 5, ARRAY['Kamar mandi mewah outdoor', 'AC', 'TV plasma', 'Minibar', 'Kolam renang pribadi', 'Butler service'], ARRAY['https://example.com/cliff_pool1.jpg', 'https://example.com/cliff_pool2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(22, 10, 'Standard Room', 650000, 2, 25, ARRAY['Kamar mandi pribadi', 'AC', 'TV', 'WiFi', 'Meja kerja'], ARRAY['https://example.com/city_std1.jpg', 'https://example.com/city_std2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00'),
(23, 10, 'Business Suite', 1200000, 2, 10, ARRAY['Kamar mandi pribadi', 'AC', 'Smart TV', 'Minibar', 'Ruang kerja', 'Ruang tamu'], ARRAY['https://example.com/city_suite1.jpg', 'https://example.com/city_suite2.jpg'], '2025-05-08 06:53:28.915239+00', '2025-05-08 06:53:28.915239+00');

-- Insert data ke tabel flights
-- Hanya rute DPS-CGK dan CGK-DPS dengan berbagai maskapai (tanpa Malaysia Airlines dan Singapore Airlines)
INSERT INTO flights (id, maskapai, kode_penerbangan, origin, destination, waktu_berangkat, waktu_tiba, durasi, harga, kelas, kursi_tersedia, created_at, updated_at) VALUES
-- Garuda Indonesia
(1, 'Garuda Indonesia', 'GA-402', 'CGK', 'DPS', '08:00:00', '10:40:00', '1h 40m', 1500000, 'Ekonomi', 120, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(2, 'Garuda Indonesia', 'GA-403', 'DPS', 'CGK', '12:30:00', '15:10:00', '1h 40m', 1600000, 'Ekonomi', 110, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(3, 'Garuda Indonesia', 'GA-412', 'CGK', 'DPS', '15:00:00', '17:40:00', '1h 40m', 1450000, 'Ekonomi', 130, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(4, 'Garuda Indonesia', 'GA-409', 'DPS', 'CGK', '18:00:00', '20:40:00', '1h 40m', 1700000, 'Ekonomi', 100, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(5, 'Garuda Indonesia', 'GA-402B', 'CGK', 'DPS', '08:00:00', '10:40:00', '1h 40m', 3500000, 'Bisnis', 20, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(6, 'Garuda Indonesia', 'GA-403B', 'DPS', 'CGK', '12:30:00', '15:10:00', '1h 40m', 3600000, 'Bisnis', 18, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),

-- Lion Air
(7, 'Lion Air', 'JT-012', 'CGK', 'DPS', '06:15:00', '09:00:00', '1h 45m', 750000, 'Ekonomi', 180, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(8, 'Lion Air', 'JT-013', 'DPS', 'CGK', '10:30:00', '13:15:00', '1h 45m', 780000, 'Ekonomi', 175, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(9, 'Lion Air', 'JT-022', 'CGK', 'DPS', '14:00:00', '16:45:00', '1h 45m', 720000, 'Ekonomi', 185, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(10, 'Lion Air', 'JT-023', 'DPS', 'CGK', '19:00:00', '21:45:00', '1h 45m', 800000, 'Ekonomi', 170, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(11, 'Lion Air', 'JT-032', 'CGK', 'DPS', '11:30:00', '14:15:00', '1h 45m', 760000, 'Ekonomi', 180, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(12, 'Lion Air', 'JT-033', 'DPS', 'CGK', '16:30:00', '19:15:00', '1h 45m', 790000, 'Ekonomi', 175, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),

-- Citilink
(13, 'Citilink', 'QG-684', 'CGK', 'DPS', '07:00:00', '09:45:00', '1h 45m', 680000, 'Ekonomi', 160, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(14, 'Citilink', 'QG-685', 'DPS', 'CGK', '11:00:00', '13:45:00', '1h 45m', 700000, 'Ekonomi', 155, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(15, 'Citilink', 'QG-694', 'CGK', 'DPS', '16:30:00', '19:15:00', '1h 45m', 650000, 'Ekonomi', 165, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(16, 'Citilink', 'QG-695', 'DPS', 'CGK', '20:30:00', '23:15:00', '1h 45m', 730000, 'Ekonomi', 150, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(17, 'Citilink', 'QG-704', 'CGK', 'DPS', '13:00:00', '15:45:00', '1h 45m', 670000, 'Ekonomi', 160, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(18, 'Citilink', 'QG-705', 'DPS', 'CGK', '17:00:00', '19:45:00', '1h 45m', 710000, 'Ekonomi', 155, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),

-- Batik Air
(19, 'Batik Air', 'ID-6501', 'CGK', 'DPS', '09:30:00', '12:15:00', '1h 45m', 880000, 'Ekonomi', 150, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(20, 'Batik Air', 'ID-6502', 'DPS', 'CGK', '13:30:00', '16:15:00', '1h 45m', 920000, 'Ekonomi', 145, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(21, 'Batik Air', 'ID-6511', 'CGK', 'DPS', '17:30:00', '20:15:00', '1h 45m', 900000, 'Ekonomi', 150, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(22, 'Batik Air', 'ID-6512', 'DPS', 'CGK', '21:30:00', '00:15:00', '1h 45m', 950000, 'Ekonomi', 145, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),

-- AirAsia
(23, 'AirAsia', 'QZ-7520', 'CGK', 'DPS', '06:30:00', '09:15:00', '1h 45m', 550000, 'Ekonomi', 180, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(24, 'AirAsia', 'QZ-7521', 'DPS', 'CGK', '10:00:00', '12:45:00', '1h 45m', 580000, 'Ekonomi', 178, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(25, 'AirAsia', 'QZ-7530', 'CGK', 'DPS', '12:30:00', '15:15:00', '1h 45m', 570000, 'Ekonomi', 180, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(26, 'AirAsia', 'QZ-7531', 'DPS', 'CGK', '16:00:00', '18:45:00', '1h 45m', 590000, 'Ekonomi', 178, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),

-- Super Air Jet
(27, 'Super Air Jet', 'IU-801', 'CGK', 'DPS', '08:30:00', '11:15:00', '1h 45m', 820000, 'Ekonomi', 140, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(28, 'Super Air Jet', 'IU-802', 'DPS', 'CGK', '14:30:00', '17:15:00', '1h 45m', 850000, 'Ekonomi', 135, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(29, 'Super Air Jet', 'IU-811', 'CGK', 'DPS', '18:30:00', '21:15:00', '1h 45m', 830000, 'Ekonomi', 140, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00'),
(30, 'Super Air Jet', 'IU-812', 'DPS', 'CGK', '22:30:00', '01:15:00', '1h 45m', 860000, 'Ekonomi', 135, '2025-05-08 06:53:28.98249+00', '2025-05-08 06:53:28.98249+00');

-- Insert data ke tabel flight_schedules
-- Jadwal penerbangan untuk tanggal 1-26 Juni 2025 (sample data)
INSERT INTO flight_schedules (id, flight_id, tanggal, is_available, created_at, updated_at) VALUES
-- Garuda Indonesia GA-402 (CGK-DPS) - setiap hari
(1, 1, '2025-06-01', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(2, 1, '2025-06-03', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(3, 1, '2025-06-05', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(4, 1, '2025-06-07', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(5, 1, '2025-06-10', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(6, 1, '2025-06-12', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(7, 1, '2025-06-15', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(8, 1, '2025-06-18', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(9, 1, '2025-06-20', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(10, 1, '2025-06-22', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(11, 1, '2025-06-25', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Garuda Indonesia GA-403 (DPS-CGK)
(12, 2, '2025-06-02', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(13, 2, '2025-06-04', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(14, 2, '2025-06-06', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(15, 2, '2025-06-08', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(16, 2, '2025-06-11', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(17, 2, '2025-06-13', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(18, 2, '2025-06-16', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(19, 2, '2025-06-19', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(20, 2, '2025-06-21', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(21, 2, '2025-06-23', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(22, 2, '2025-06-26', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Lion Air JT-012 (CGK-DPS)
(23, 7, '2025-06-01', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(24, 7, '2025-06-04', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(25, 7, '2025-06-07', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(26, 7, '2025-06-10', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(27, 7, '2025-06-13', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(28, 7, '2025-06-16', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(29, 7, '2025-06-19', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(30, 7, '2025-06-22', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(31, 7, '2025-06-25', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Lion Air JT-013 (DPS-CGK)
(32, 8, '2025-06-02', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(33, 8, '2025-06-05', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(34, 8, '2025-06-08', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(35, 8, '2025-06-11', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(36, 8, '2025-06-14', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(37, 8, '2025-06-17', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(38, 8, '2025-06-20', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(39, 8, '2025-06-23', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(40, 8, '2025-06-26', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Citilink QG-684 (CGK-DPS)
(41, 13, '2025-06-03', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(42, 13, '2025-06-06', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(43, 13, '2025-06-09', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(44, 13, '2025-06-12', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(45, 13, '2025-06-15', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(46, 13, '2025-06-18', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(47, 13, '2025-06-21', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(48, 13, '2025-06-24', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Citilink QG-685 (DPS-CGK)
(49, 14, '2025-06-04', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(50, 14, '2025-06-07', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(51, 14, '2025-06-10', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(52, 14, '2025-06-13', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(53, 14, '2025-06-16', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(54, 14, '2025-06-19', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(55, 14, '2025-06-22', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(56, 14, '2025-06-25', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- AirAsia QZ-7520 (CGK-DPS)
(57, 23, '2025-06-02', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(58, 23, '2025-06-05', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(59, 23, '2025-06-08', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(60, 23, '2025-06-11', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(61, 23, '2025-06-14', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(62, 23, '2025-06-17', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(63, 23, '2025-06-20', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(64, 23, '2025-06-23', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(65, 23, '2025-06-26', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- AirAsia QZ-7521 (DPS-CGK)
(66, 24, '2025-06-03', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(67, 24, '2025-06-06', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(68, 24, '2025-06-09', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(69, 24, '2025-06-12', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(70, 24, '2025-06-15', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(71, 24, '2025-06-18', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(72, 24, '2025-06-21', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(73, 24, '2025-06-24', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Batik Air ID-6501 (CGK-DPS)
(74, 19, '2025-06-01', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(75, 19, '2025-06-04', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(76, 19, '2025-06-07', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(77, 19, '2025-06-10', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(78, 19, '2025-06-13', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(79, 19, '2025-06-16', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(80, 19, '2025-06-19', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(81, 19, '2025-06-22', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(82, 19, '2025-06-25', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Batik Air ID-6502 (DPS-CGK)
(83, 20, '2025-06-02', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(84, 20, '2025-06-05', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(85, 20, '2025-06-08', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(86, 20, '2025-06-11', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(87, 20, '2025-06-14', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(88, 20, '2025-06-17', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(89, 20, '2025-06-20', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(90, 20, '2025-06-23', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),
(91, 20, '2025-06-26', true, '2025-05-08 06:53:29.028516+00', '2025-05-08 06:53:29.028516+00'),

-- Jadwal penerbangan untuk tanggal 1-30 Juli 2025 (Jakarta-Denpasar dan Denpasar-Jakarta)
-- Garuda Indonesia GA-402 (CGK-DPS)
(92, 1, '2025-07-01', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(93, 1, '2025-07-04', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(94, 1, '2025-07-07', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(95, 1, '2025-07-10', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(96, 1, '2025-07-13', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(97, 1, '2025-07-16', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(98, 1, '2025-07-19', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(99, 1, '2025-07-22', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(100, 1, '2025-07-25', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(101, 1, '2025-07-28', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Garuda Indonesia GA-403 (DPS-CGK)
(102, 2, '2025-07-02', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(103, 2, '2025-07-05', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(104, 2, '2025-07-08', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(105, 2, '2025-07-11', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(106, 2, '2025-07-14', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(107, 2, '2025-07-17', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(108, 2, '2025-07-20', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(109, 2, '2025-07-23', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(110, 2, '2025-07-26', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(111, 2, '2025-07-29', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Lion Air JT-012 (CGK-DPS)
(112, 7, '2025-07-03', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(113, 7, '2025-07-06', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(114, 7, '2025-07-09', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(115, 7, '2025-07-12', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(116, 7, '2025-07-15', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(117, 7, '2025-07-18', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(118, 7, '2025-07-21', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(119, 7, '2025-07-24', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(120, 7, '2025-07-27', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(121, 7, '2025-07-30', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Lion Air JT-013 (DPS-CGK)
(122, 8, '2025-07-01', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(123, 8, '2025-07-04', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(124, 8, '2025-07-07', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(125, 8, '2025-07-10', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(126, 8, '2025-07-13', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(127, 8, '2025-07-16', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(128, 8, '2025-07-19', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(129, 8, '2025-07-22', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(130, 8, '2025-07-25', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(131, 8, '2025-07-28', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Citilink QG-684 (CGK-DPS)
(132, 13, '2025-07-02', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(133, 13, '2025-07-05', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(134, 13, '2025-07-08', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(135, 13, '2025-07-11', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(136, 13, '2025-07-14', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(137, 13, '2025-07-17', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(138, 13, '2025-07-20', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(139, 13, '2025-07-23', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(140, 13, '2025-07-26', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(141, 13, '2025-07-29', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Citilink QG-685 (DPS-CGK)
(142, 14, '2025-07-03', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(143, 14, '2025-07-06', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(144, 14, '2025-07-09', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(145, 14, '2025-07-12', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(146, 14, '2025-07-15', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(147, 14, '2025-07-18', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(148, 14, '2025-07-21', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(149, 14, '2025-07-24', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(150, 14, '2025-07-27', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(151, 14, '2025-07-30', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Batik Air ID-6501 (CGK-DPS)
(152, 19, '2025-07-01', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(153, 19, '2025-07-05', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(154, 19, '2025-07-09', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(155, 19, '2025-07-13', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(156, 19, '2025-07-17', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(157, 19, '2025-07-21', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(158, 19, '2025-07-25', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(159, 19, '2025-07-29', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Batik Air ID-6502 (DPS-CGK)
(160, 20, '2025-07-03', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(161, 20, '2025-07-07', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(162, 20, '2025-07-11', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(163, 20, '2025-07-15', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(164, 20, '2025-07-19', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(165, 20, '2025-07-23', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(166, 20, '2025-07-27', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),
(167, 20, '2025-07-30', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),

-- Tambahan jadwal penerbangan untuk 31 Juli 2025
(168, 1, '2025-07-31', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),  -- Garuda Indonesia GA-402 (CGK-DPS)
(169, 8, '2025-07-31', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'),  -- Lion Air JT-013 (DPS-CGK)
(170, 13, '2025-07-31', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'), -- Citilink QG-684 (CGK-DPS)
(171, 20, '2025-07-31', true, '2025-06-10 10:00:00+00', '2025-06-10 10:00:00+00'); -- Batik Air ID-6502 (DPS-CGK)

-- Insert data ke tabel hotel_bookings
INSERT INTO hotel_bookings (id, hotel_id, user_id, nama_pemesan, email, telepon, tanggal_mulai, tanggal_akhir, jumlah_tamu, jumlah_kamar, tipe_kamar, total_harga, status, metode_pembayaran, status_pembayaran, catatan, tanggal_pemesanan, created_at, updated_at) VALUES
(1, 1, 1, 'Wayan Dharma', 'wayan.dharma@gmail.com', '081234567890', '2025-06-01', '2025-06-05', 2, 1, 'Deluxe Garden View', 1350000, 'confirmed', 'transfer bank', 'paid', 'Mohon kamar dengan pemandangan sawah', '2025-05-15', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(2, 2, 2, 'Ni Made Dewi', 'made.dewi@gmail.com', '081234567891', '2025-06-05', '2025-06-10', 4, 2, 'Family Room', 1500000, 'confirmed', 'kartu kredit', 'paid', 'Keluarga dengan 2 anak kecil, butuh extra bed', '2025-05-20', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(3, 3, 3, 'Nyoman Agus', 'nyoman.agus@gmail.com', '081234567892', '2025-06-15', '2025-06-20', 2, 1, 'Beach Villa', 2000000, 'confirmed', 'transfer bank', 'unpaid', 'Honeymoon package dengan dekorasi kamar', '2025-05-25', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(4, 6, 6, 'Putu Eka Suparta', 'putu.eka@gmail.com', '081234567895', '2025-07-01', '2025-07-05', 2, 1, 'Jungle View Room', 1200000, 'confirmed', 'kartu kredit', 'paid', 'Tolong siapkan antar-jemput dari bandara', '2025-06-10', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(5, 7, 7, 'Kadek Ariawan', 'kadek.ariawan@gmail.com', '081234567896', '2025-07-10', '2025-07-13', 2, 1, 'Rice Terrace View', 1500000, 'confirmed', 'transfer bank', 'paid', 'Kamar yang jauh dari jalan raya', '2025-06-15', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(6, 8, 8, 'I Komang Sutama', 'komang.sutama@gmail.com', '081234567897', '2025-07-15', '2025-07-20', 2, 1, 'Ocean View Deluxe', 2500000, 'confirmed', 'e-wallet', 'paid', 'Selebrasi ulang tahun pernikahan', '2025-06-20', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(7, 9, 9, 'I Ketut Sudira', 'ketut.sudira@gmail.com', '081234567898', '2025-08-01', '2025-08-05', 2, 1, 'Cliff View Suite', 3000000, 'pending', 'kartu kredit', 'unpaid', 'Pemandangan sunset', '2025-06-25', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(8, 10, 10, 'Ni Putu Seruni', 'putu.seruni@gmail.com', '081234567899', '2025-08-10', '2025-08-12', 1, 1, 'Business Suite', 1200000, 'confirmed', 'kartu kredit', 'paid', 'Perjalanan bisnis, butuh early check-in', '2025-06-30', '2025-05-08 06:53:29.12254+00', '2025-05-08 06:53:29.12254+00'),
(9, 6, 14, 'Wayan Bagus', 'wayan.bagus@gmail.com', '081233445786', '2025-06-12', '2025-06-14', 2, 1, 'Riverside Suite', 4000000, 'confirmed', 'kartu kredit', 'paid', 'terima kasih, life', '2025-06-09', '2025-05-09 06:57:06.587301+00', '2025-05-09 06:57:06.587301+00'),
(10, 8, 3, 'Nyoman Agus', 'nyoman.agus@gmail.com', '081234567892', '2025-06-29', '2025-07-01', 2, 1, 'Ocean View Deluxe', 5000000, 'pending', NULL, 'unpaid', 'Bisa bisa bisa', '2025-05-12', '2025-05-12 02:06:01.681969+00', '2025-05-12 02:06:01.681969+00'),
(11, 1, 4, 'Ni Ketut Ayu', 'ketut.ayu@gmail.com', '081234567893', '2025-06-29', '2025-07-01', 2, 1, 'Deluxe Garden View', 3000000, 'confirmed', 'kartu kredit', 'paid', NULL, '2025-05-12', '2025-05-12 02:14:16.450621+00', '2025-05-12 02:14:16.450621+00'),
(12, 1, 14, 'Wayan Bagus', 'wayan.bagus@gmail.com', '081233445786', '2025-06-02', '2025-06-04', 2, 1, 'Premium Pool Access', 5000000, 'confirmed', 'transfer bank', 'paid', 'Sukses selalu', '2025-05-12', '2025-05-12 03:51:46.770616+00', '2025-05-12 03:51:46.770616+00'),
(13, 1, 16, 'Esa Krissa', 'esakrissa.wayan@gmail.com', '081237401690', '2025-06-12', '2025-06-14', 2, 1, 'Villa Suite', 6000000, 'confirmed', 'transfer bank', 'paid', 'good lucj', '2025-05-12', '2025-05-12 04:38:11.660035+00', '2025-05-12 04:38:11.660035+00'),
(14, 8, 16, 'Esa Krissa', 'esakrissa.wayan@gmail.com', '081237401690', '2025-06-19', '2025-06-22', 2, 1, 'Beachfront Villa', 13500000, 'confirmed', 'e-wallet', 'paid', 'good luck', '2025-05-12', '2025-05-12 05:55:05.85666+00', '2025-05-12 05:55:05.85666+00');

-- Insert data ke tabel flight_bookings
INSERT INTO flight_bookings (id, flight_id, user_id, nama_pemesan, email, telepon, tanggal_keberangkatan, jumlah_penumpang, kelas_penerbangan, nomor_kursi, total_harga, status, metode_pembayaran, status_pembayaran, catatan, tanggal_pemesanan, created_at, updated_at) VALUES
(1, 1, 4, 'Ni Ketut Ayu', 'ketut.ayu@gmail.com', '081234567893', '2025-06-01', 1, 'Ekonomi', '12A', 1500000, 'confirmed', 'kartu kredit', 'paid', 'Request kursi dekat jendela', '2025-05-15', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(2, 2, 5, 'I Gede Surya', 'gede.surya@gmail.com', '081234567894', '2025-06-01', 1, 'Ekonomi', '8F', 1600000, 'confirmed', 'e-wallet', 'paid', 'Membawa bagasi 20kg', '2025-05-16', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(3, 17, 1, 'Wayan Dharma', 'wayan.dharma@gmail.com', '081234567890', '2025-06-03', 2, 'Ekonomi', '15A,15B', 1300000, 'cancelled', 'transfer bank', 'refunded', 'Perjalanan bisnis dengan kolega', '2025-05-18', '2025-05-08 06:53:29.172522+00', '2025-05-08 15:10:58.24811+00'),
(4, 18, 2, 'Ni Made Dewi', 'made.dewi@gmail.com', '081234567891', '2025-06-05', 1, 'Bisnis', '2C', 3500000, 'confirmed', 'kartu kredit', 'paid', 'Request vegetarian meal', '2025-05-20', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(5, 19, 11, 'Ni Made Artini', 'made.artini@gmail.com', '081234568000', '2025-07-05', 1, 'Ekonomi', '15D', 880000, 'confirmed', 'kartu kredit', 'paid', 'Bagasi tambahan 10kg', '2025-06-10', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(6, 21, 12, 'I Nyoman Sumerta', 'nyoman.sumerta@gmail.com', '081234568001', '2025-07-10', 2, 'Ekonomi', '12A,12B', 1100000, 'confirmed', 'transfer bank', 'paid', 'Perjalanan dengan anak', '2025-06-15', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(7, 23, 13, 'Ni Ketut Sulastri', 'ketut.sulastri@gmail.com', '081234568002', '2025-07-20', 1, 'Ekonomi', '8C', 2800000, 'confirmed', 'e-wallet', 'paid', 'Pertama kali ke Singapura', '2025-06-20', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(8, 25, 6, 'Putu Eka Suparta', 'putu.eka@gmail.com', '081234567895', '2025-08-01', 1, 'Ekonomi', '20F', 3200000, 'pending', 'kartu kredit', 'unpaid', 'Butuh bantuan kursi roda', '2025-06-25', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(9, 27, 7, 'Kadek Ariawan', 'kadek.ariawan@gmail.com', '081234567896', '2025-08-10', 2, 'Ekonomi', '14D,14E', 3900000, 'confirmed', 'kartu kredit', 'paid', 'Request makanan halal', '2025-06-30', '2025-05-08 06:53:29.172522+00', '2025-05-08 06:53:29.172522+00'),
(13, 3, 15, 'Made Bagus', 'madebagus.md@gmail.com', '081233445800', '2025-06-03', 2, 'Ekonomi', 'A1, B1', 2900000, 'cancelled', 'kartu kredit', 'refunded', 'Booking dong', '2025-05-08', '2025-05-08 07:55:18.416102+00', '2025-05-08 15:56:53.857348+00'),
(14, 4, 14, 'Wayan Bagus', 'wayan.bagus@gmail.com', '081233445786', '2025-06-01', 2, 'Ekonomi', 'A1, B1', 3400000, 'confirmed', 'kartu kredit', 'paid', 'bisa yok bisa', '2025-05-09', '2025-05-09 06:55:13.906746+00', '2025-05-09 06:55:13.906746+00'),
(15, 1, 3, 'Nyoman Agus', 'nyoman.agus@gmail.com', '081234567892', '2025-06-02', 1, 'Ekonomi', 'A1', 1500000, 'pending', NULL, 'unpaid', 'Bisa bisa bisa', '2025-05-12', '2025-05-12 02:06:01.465928+00', '2025-05-12 02:06:01.465928+00'),
(16, 2, 4, 'Ni Ketut Ayu', 'ketut.ayu@gmail.com', '081234567893', '2025-06-01', 1, 'Ekonomi', 'A1', 1600000, 'confirmed', 'kartu kredit', 'paid', NULL, '2025-05-12', '2025-05-12 02:14:16.235857+00', '2025-05-12 02:14:16.235857+00'),
(17, 4, 16, 'Esa Krissa', 'esakrissa.wayan@gmail.com', '081237401690', '2025-06-03', 2, 'Ekonomi', 'A1, B1', 3400000, 'cancelled', 'transfer bank', 'refunded', NULL, '2025-05-12', '2025-05-12 05:38:50.830064+00', '2025-05-12 13:50:52.256378+00');

-- Insert data ke tabel chat_history
-- Data chat_history telah dihapus untuk sample data yang bersih

-- Insert data tour untuk Bali
INSERT INTO tours (nama, destinasi, deskripsi, durasi, harga, kapasitas, fasilitas, itinerary, foto_url, rating, kategori, tingkat_kesulitan, include_transport, include_meal, include_guide) VALUES
('Ubud Cultural Tour', 'Ubud', 'Jelajahi kebudayaan Bali yang autentik di Ubud dengan mengunjungi pura-pura bersejarah, sawah terasering, dan pasar tradisional', '8 jam', 450000, 15,
 ARRAY['Transport AC', 'Guide berpengalaman', 'Makan siang', 'Air mineral', 'Tiket masuk'],
 ARRAY['08:00 - Penjemputan di hotel', '09:00 - Pura Tirta Empul', '11:00 - Sawah Terasering Tegallalang', '12:30 - Makan siang di restoran lokal', '14:00 - Pasar Ubud', '15:30 - Monkey Forest Sanctuary', '16:30 - Kembali ke hotel'],
 ARRAY['https://example.com/ubud1.jpg', 'https://example.com/ubud2.jpg'], 4.8, 'Budaya', 'mudah', true, true, true),

('Kintamani Volcano Tour', 'Kintamani', 'Nikmati pemandangan spektakuler Gunung Batur dan Danau Batur sambil menikmati udara sejuk pegunungan', '10 jam', 550000, 12,
 ARRAY['Transport AC', 'Guide berpengalaman', 'Makan siang buffet', 'Air mineral', 'Tiket masuk'],
 ARRAY['07:00 - Penjemputan di hotel', '09:30 - Penelokan viewpoint', '11:00 - Desa Trunyan', '12:30 - Makan siang buffet di Kintamani', '14:00 - Hot spring Toya Devasya', '15:30 - Desa Penglipuran', '17:00 - Kembali ke hotel'],
 ARRAY['https://example.com/kintamani1.jpg', 'https://example.com/kintamani2.jpg'], 4.7, 'Alam', 'sedang', true, true, true),

('Tanah Lot Sunset Tour', 'Tabanan', 'Saksikan matahari terbenam yang menakjubkan di Pura Tanah Lot, salah satu pura paling ikonik di Bali', '6 jam', 350000, 20,
 ARRAY['Transport AC', 'Guide berpengalaman', 'Air mineral', 'Tiket masuk'],
 ARRAY['13:00 - Penjemputan di hotel', '14:30 - Pura Taman Ayun', '16:00 - Pasar Canggu', '17:30 - Pura Tanah Lot', '18:30 - Sunset viewing', '19:30 - Kembali ke hotel'],
 ARRAY['https://example.com/tanahlot1.jpg', 'https://example.com/tanahlot2.jpg'], 4.9, 'Spiritual', 'mudah', true, false, true),

('East Bali Adventure', 'Karangasem', 'Petualangan ke Bali Timur mengunjungi Pura Lempuyang, Tirta Gangga, dan Pantai Virgin', '12 jam', 650000, 10,
 ARRAY['Transport AC', 'Guide berpengalaman', 'Makan siang', 'Air mineral', 'Tiket masuk'],
 ARRAY['06:00 - Penjemputan di hotel', '08:30 - Pura Lempuyang (Gates of Heaven)', '11:00 - Tirta Gangga Water Palace', '12:30 - Makan siang di restoran lokal', '14:00 - Pantai Virgin (White Sand Beach)', '16:00 - Desa Tenganan', '18:00 - Kembali ke hotel'],
 ARRAY['https://example.com/eastbali1.jpg', 'https://example.com/eastbali2.jpg'], 4.6, 'Petualangan', 'sedang', true, true, true),

('Sekumpul Waterfall Trek', 'Buleleng', 'Trekking menuju air terjun tersembunyi Sekumpul yang dikenal sebagai air terjun terindah di Bali', '8 jam', 500000, 8,
 ARRAY['Transport AC', 'Guide trekking', 'Makan siang', 'Air mineral', 'Peralatan trekking'],
 ARRAY['07:00 - Penjemputan di hotel', '09:30 - Briefing dan persiapan trekking', '10:00 - Mulai trekking ke Sekumpul', '12:00 - Sampai di air terjun, berenang dan foto', '13:00 - Makan siang di warung lokal', '14:30 - Trekking kembali', '16:00 - Kembali ke hotel'],
 ARRAY['https://example.com/sekumpul1.jpg', 'https://example.com/sekumpul2.jpg'], 4.5, 'Petualangan', 'sulit', true, true, true),

('Bali Swing & Instagram Tour', 'Ubud', 'Tour foto Instagram terbaik di Bali dengan ayunan di atas hutan dan spot foto yang menakjubkan', '6 jam', 400000, 12,
 ARRAY['Transport AC', 'Guide fotografer', 'Tiket masuk', 'Air mineral', 'Foto digital'],
 ARRAY['09:00 - Penjemputan di hotel', '10:30 - Bali Swing Ubud', '12:00 - Tegallalang Rice Terrace', '13:00 - Makan siang dengan view sawah', '14:30 - Tegenungan Waterfall', '16:00 - Kembali ke hotel'],
 ARRAY['https://example.com/swing1.jpg', 'https://example.com/swing2.jpg'], 4.7, 'Fotografi', 'mudah', true, true, true),

('Nusa Penida Day Trip', 'Nusa Penida', 'Eksplorasi pulau eksotis Nusa Penida dengan pantai-pantai tersembunyi dan pemandangan spektakuler', '12 jam', 750000, 10,
 ARRAY['Fast boat', 'Transport di Nusa Penida', 'Guide lokal', 'Makan siang', 'Snorkeling gear'],
 ARRAY['06:00 - Penjemputan di hotel', '07:30 - Berangkat dengan fast boat', '09:00 - Kelingking Beach', '11:00 - Angel Billabong', '12:30 - Makan siang di Broken Beach', '14:00 - Crystal Bay (snorkeling)', '16:00 - Kembali ke Bali', '18:00 - Tiba di hotel'],
 ARRAY['https://example.com/nusapenida1.jpg', 'https://example.com/nusapenida2.jpg'], 4.8, 'Petualangan', 'sedang', true, true, true),

('Mount Batur Sunrise Trekking', 'Kintamani', 'Pendakian gunung berapi aktif untuk menyaksikan sunrise spektakuler dari puncak Gunung Batur', '8 jam', 600000, 15,
 ARRAY['Transport AC', 'Guide pendakian', 'Sarapan di puncak', 'Senter', 'Air mineral'],
 ARRAY['02:00 - Penjemputan di hotel', '03:30 - Tiba di basecamp', '04:00 - Mulai pendakian', '06:00 - Sunrise di puncak', '07:00 - Sarapan dengan telur rebus vulkanik', '08:30 - Turun gunung', '10:00 - Hot spring Toya Devasya', '12:00 - Kembali ke hotel'],
 ARRAY['https://example.com/batur1.jpg', 'https://example.com/batur2.jpg'], 4.6, 'Petualangan', 'sulit', true, true, true),

('Bali Temple Hopping', 'Bali', 'Kunjungi pura-pura paling suci dan bersejarah di Bali dalam satu hari', '10 jam', 500000, 20,
 ARRAY['Transport AC', 'Guide spiritual', 'Sarung dan selendang', 'Makan siang', 'Air mineral'],
 ARRAY['08:00 - Penjemputan di hotel', '09:00 - Pura Besakih (Mother Temple)', '11:30 - Pura Kehen', '12:30 - Makan siang tradisional', '14:00 - Pura Tirta Empul', '15:30 - Pura Gunung Kawi', '17:00 - Kembali ke hotel'],
 ARRAY['https://example.com/temple1.jpg', 'https://example.com/temple2.jpg'], 4.4, 'Spiritual', 'mudah', true, true, true),

('Dolphin Watching Lovina', 'Lovina', 'Saksikan lumba-lumba liar di perairan Lovina saat sunrise dengan perahu tradisional', '6 jam', 350000, 16,
 ARRAY['Perahu tradisional', 'Guide lokal', 'Sarapan ringan', 'Air mineral', 'Life jacket'],
 ARRAY['05:00 - Penjemputan di hotel', '06:00 - Tiba di pantai Lovina', '06:30 - Berangkat dengan perahu', '07:00 - Dolphin watching', '08:30 - Kembali ke pantai', '09:00 - Sarapan di warung lokal', '11:00 - Kembali ke hotel'],
 ARRAY['https://example.com/dolphin1.jpg', 'https://example.com/dolphin2.jpg'], 4.3, 'Alam', 'mudah', true, true, true);

-- Insert jadwal tour untuk 1-30 Juni 2025
INSERT INTO tour_schedules (tour_id, tanggal, waktu_mulai, waktu_selesai, jumlah_tersedia)
SELECT
    t.id,
    ('2025-06-01'::date + (s.day_offset - 1 || ' days')::interval)::date,
    CASE
        WHEN t.nama LIKE '%Sunset%' THEN '13:00'::time
        WHEN t.nama LIKE '%Waterfall%' THEN '07:00'::time
        WHEN t.nama LIKE '%Sunrise%' THEN '02:00'::time
        ELSE '08:00'::time
    END,
    CASE
        WHEN t.nama LIKE '%Sunset%' THEN '19:30'::time
        WHEN t.nama LIKE '%East Bali%' THEN '20:00'::time
        WHEN t.nama LIKE '%Waterfall%' THEN '16:00'::time
        WHEN t.nama LIKE '%Nusa Penida%' THEN '18:00'::time
        WHEN t.nama LIKE '%Sunrise%' THEN '12:00'::time
        ELSE '17:00'::time
    END,
    t.kapasitas
FROM tours t
CROSS JOIN generate_series(1, 30) AS s(day_offset);

-- Insert jadwal tour untuk 1-31 Juli 2025
INSERT INTO tour_schedules (tour_id, tanggal, waktu_mulai, waktu_selesai, jumlah_tersedia)
SELECT
    t.id,
    ('2025-07-01'::date + (s.day_offset - 1 || ' days')::interval)::date,
    CASE
        WHEN t.nama LIKE '%Sunset%' THEN '13:00'::time
        WHEN t.nama LIKE '%Waterfall%' THEN '07:00'::time
        WHEN t.nama LIKE '%Sunrise%' THEN '02:00'::time
        ELSE '08:00'::time
    END,
    CASE
        WHEN t.nama LIKE '%Sunset%' THEN '19:30'::time
        WHEN t.nama LIKE '%East Bali%' THEN '20:00'::time
        WHEN t.nama LIKE '%Waterfall%' THEN '16:00'::time
        WHEN t.nama LIKE '%Nusa Penida%' THEN '18:00'::time
        WHEN t.nama LIKE '%Sunrise%' THEN '12:00'::time
        ELSE '17:00'::time
    END,
    t.kapasitas
FROM tours t
CROSS JOIN generate_series(1, 31) AS s(day_offset);

-- Atur nilai sequence untuk melanjutkan dari ID terakhir yang di-insert
SELECT setval('hotels_id_seq', (SELECT MAX(id) FROM hotels), true);
SELECT setval('hotel_rooms_id_seq', (SELECT MAX(id) FROM hotel_rooms), true);
SELECT setval('flights_id_seq', (SELECT MAX(id) FROM flights), true);
SELECT setval('flight_schedules_id_seq', (SELECT MAX(id) FROM flight_schedules), true);
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users), true);
SELECT setval('hotel_bookings_id_seq', (SELECT MAX(id) FROM hotel_bookings), true);
SELECT setval('flight_bookings_id_seq', (SELECT MAX(id) FROM flight_bookings), true);
SELECT setval('chat_history_id_seq', (SELECT MAX(id) FROM chat_history), true);
SELECT setval('tours_id_seq', (SELECT MAX(id) FROM tours), true);
SELECT setval('tour_schedules_id_seq', (SELECT MAX(id) FROM tour_schedules), true);
SELECT setval('tour_bookings_id_seq', (SELECT MAX(id) FROM tour_bookings), true);

-- Insert contoh data pemesanan tour (hanya yang tanggal pemesanan Juni ke atas)
INSERT INTO tour_bookings (tour_id, user_id, nama_pemesan, email, telepon, tanggal_tour, jumlah_peserta, total_harga, status, metode_pembayaran, status_pembayaran, catatan, tanggal_pemesanan) VALUES
(5, 5, 'I Gede Surya', 'gede.surya@gmail.com', '081234567894', '2025-06-05', 1, 500000, 'confirmed', 'transfer bank', 'paid', 'Solo traveler, join group tour', '2025-06-01'),
(6, 6, 'Putu Eka Suparta', 'putu.eka@gmail.com', '081234567895', '2025-06-10', 2, 800000, 'confirmed', 'kartu kredit', 'paid', 'Instagram photos important', '2025-06-03'),
(7, 7, 'Kadek Ariawan', 'kadek.ariawan@gmail.com', '081234567896', '2025-06-15', 6, 4500000, 'confirmed', 'transfer bank', 'paid', 'Group tour dengan teman-teman', '2025-06-05'),
(8, 8, 'I Komang Sutama', 'komang.sutama@gmail.com', '081234567897', '2025-06-20', 2, 1200000, 'confirmed', 'e-wallet', 'paid', 'Experienced trekker, challenging route preferred', '2025-06-08'),
(9, 9, 'I Ketut Sudira', 'ketut.sudira@gmail.com', '081234567898', '2025-06-25', 4, 3000000, 'confirmed', 'kartu kredit', 'paid', 'Family with elderly parents, easy pace', '2025-06-10'),
(10, 10, 'Ni Putu Seruni', 'putu.seruni@gmail.com', '081234567899', '2025-06-30', 2, 700000, 'pending', NULL, 'unpaid', 'Spiritual journey, meditation focus', '2025-06-12'),
(1, 11, 'Ni Made Artini', 'made.artini@gmail.com', '081234568000', '2025-06-18', 3, 1350000, 'confirmed', 'transfer bank', 'paid', 'Early morning pickup preferred', '2025-06-15'),
(2, 12, 'I Nyoman Sumerta', 'nyoman.sumerta@gmail.com', '081234568001', '2025-06-22', 2, 1100000, 'cancelled', 'kartu kredit', 'refunded', 'Change of travel plans', '2025-06-18'),
(3, 13, 'Ni Ketut Sulastri', 'ketut.sulastri@gmail.com', '081234568002', '2025-06-28', 5, 1750000, 'confirmed', 'e-wallet', 'paid', 'Corporate team building activity', '2025-06-20');

-- Perbarui jadwal tour untuk mengurangi jumlah tersedia berdasarkan pemesanan Juni
UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 1
WHERE tour_id = 5 AND tanggal = '2025-06-05';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 2
WHERE tour_id = 6 AND tanggal = '2025-06-10';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 6
WHERE tour_id = 7 AND tanggal = '2025-06-15';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 3
WHERE tour_id = 1 AND tanggal = '2025-06-18';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 2
WHERE tour_id = 8 AND tanggal = '2025-06-20';

-- Slot untuk pemesanan yang dibatalkan dikembalikan
UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia + 2
WHERE tour_id = 2 AND tanggal = '2025-06-22';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 4
WHERE tour_id = 9 AND tanggal = '2025-06-25';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 5
WHERE tour_id = 3 AND tanggal = '2025-06-28';

UPDATE tour_schedules
SET jumlah_tersedia = jumlah_tersedia - 2
WHERE tour_id = 10 AND tanggal = '2025-06-30';

-- Atur nilai sequence untuk tabel tour
SELECT setval('tours_id_seq', (SELECT MAX(id) FROM tours), true);
SELECT setval('tour_schedules_id_seq', (SELECT MAX(id) FROM tour_schedules), true);
SELECT setval('tour_bookings_id_seq', (SELECT MAX(id) FROM tour_bookings), true);
