import os
import logging
import uuid
import httpx
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
import re
from utils.config import postgres_client, supabase_client
from utils.metrics import TELEGRAM_MESSAGES, TELEGRAM_RESPONSE_TIME, ACTIVE_TELEGRAM_USERS, TELEGRAM_API_CALLS
from utils.instrumentator import create_instrumentator
from utils.middleware import TimingMiddleware
from handlers.auth import AuthHandler

# Load variabel environment
load_dotenv()

# Konfigurasi logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Vairabel environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
API_URL = os.getenv("API_URL")
PORT = int(os.getenv("PORT", 8443))

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Mengelola lifecycle aplikasi FastAPI."""
    # Startup
    logger.info("Memulai startup aplikasi...")

    # Setup webhook
    await setup_webhook()
    logger.info("Setup webhook bot selesai")

    # Muat thread ID dari Supabase
    await load_thread_ids_from_supabase()
    logger.info(f"Memuat {len(user_threads)} thread ID ke memori")

    yield

    # Shutdown (jika diperlukan)
    logger.info("Aplikasi sedang shutdown...")

# FastAPI app untuk menangani webhook
app = FastAPI(lifespan=lifespan)

# Tambahkan middleware untuk mencatat waktu permintaan
app.add_middleware(TimingMiddleware)

# Inisialisasi Prometheus dengan instrumentator yang telah dikonfigurasi
instrumentator = create_instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=True, should_gzip=True)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Inisialisasi auth handler
auth_handler = AuthHandler(bot)

# Dictionary untuk memetakan status dialog ke nama agen
agent_dict = {
    'supervisor': 'Agen Supervisor',
    'customer_service': 'Customer Service',
    'hotel_agent': 'Agen Hotel',
    'flight_agent': 'Agen Pesawat',
    'tour_agent': 'Agen Tur'
}

# Dictionary untuk menyimpan ID thread untuk pengguna
user_threads = {}

async def get_thread_id(user_id):
    """Mendapatkan atau membuat thread ID untuk pengguna."""
    # Coba dapatkan thread ID dari Supabase RPC
    thread_id = await postgres_client.get_user_thread_id(str(user_id))

    # Jika tidak ada di Supabase RPC, coba dari Supabase REST API
    if not thread_id:
        thread_id = await supabase_client.get_thread_id(str(user_id))

    # Jika tidak ada di database, cek di memori lokal
    if not thread_id and user_id in user_threads:
        thread_id = user_threads[user_id]
        # Simpan ke database untuk persistensi
        await postgres_client.save_chat_message(str(user_id), thread_id, "thread_id_mapping", "thread_id_mapping")

    # Jika masih tidak ada, buat thread ID baru
    if not thread_id:
        thread_id = str(uuid.uuid4())
        user_threads[user_id] = thread_id
        # Simpan ke database untuk persistensi
        await postgres_client.save_chat_message(str(user_id), thread_id, "thread_id_mapping", "thread_id_mapping")

    return thread_id

async def make_api_call(prompt: str, thread_id: str) -> dict:
    """Memanggil API dan mengembalikan respons dalam bentuk dictionary."""
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json={"query": prompt},
                headers={"X-THREAD-ID": thread_id},
                timeout=60.0
            )
            response.raise_for_status()
            TELEGRAM_API_CALLS.labels(status="success").inc()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API mengembalikan error: {e.response.status_code}")
        TELEGRAM_API_CALLS.labels(status="error").inc()
    except Exception as e:
        logger.error(f"Terjadi error: {str(e)}")
        TELEGRAM_API_CALLS.labels(status="error").inc()
    finally:
        # Mencatat waktu respons API
        response_time = time.time() - start_time
        TELEGRAM_RESPONSE_TIME.labels(message_type="api_call").observe(response_time)

    return {"answer": "Maaf, saya mengalami error saat memproses permintaan Anda."}

async def make_api_call_with_user_context(prompt: str, thread_id: str, user_id: int) -> dict:
    """Memanggil API dengan user context dan mengembalikan respons dalam bentuk dictionary."""
    start_time = time.time()
    try:
        # Dapatkan user session
        user_session = auth_handler.get_user_session(user_id)

        # Siapkan headers dengan user context
        headers = {"X-THREAD-ID": thread_id}

        # Siapkan payload dengan user context
        payload = {"query": prompt}

        if user_session and user_session.get("authenticated"):
            user_data = user_session.get("user_data", {})
            # Inject user context ke payload
            payload["user_context"] = {
                "user_id": user_data.get("id"),
                "nama": user_data.get("nama"),
                "email": user_data.get("email"),
                "telepon": user_data.get("telepon"),
                "alamat": user_data.get("alamat"),
                "telegram_id": user_data.get("telegram_id"),
                "is_verified": user_data.get("is_verified", False)
            }

            # Tambahkan access token ke headers jika ada
            access_token = user_session.get("access_token")
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=60.0
            )
            response.raise_for_status()
            TELEGRAM_API_CALLS.labels(status="success").inc()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API mengembalikan error: {e.response.status_code}")
        TELEGRAM_API_CALLS.labels(status="error").inc()
    except Exception as e:
        logger.error(f"Terjadi error: {str(e)}")
        TELEGRAM_API_CALLS.labels(status="error").inc()
    finally:
        # Mencatat waktu respons API
        response_time = time.time() - start_time
        TELEGRAM_RESPONSE_TIME.labels(message_type="api_call").observe(response_time)

    return {"answer": "Maaf, saya mengalami error saat memproses permintaan Anda."}


async def handle_start_command(chat_id, user_id, user_first_name):
    """Menangani perintah /start dengan authentication check."""
    try:
        # Cek status autentikasi user menggunakan Redis check yang aman
        is_authenticated = await auth_handler.is_user_authenticated(user_id)

        # Dapatkan thread ID untuk pengguna ini
        thread_id = await get_thread_id(user_id)

        if is_authenticated:
            # User sudah login - pesan informatif dan intuitif
            session = auth_handler.get_user_session(user_id)
            user_data = session.get("user_data", {}) if session else {}
            user_name = user_data.get("nama", user_first_name)

            welcome_message = (
                f"✈️ *Selamat datang kembali, {user_name}!*\n\n"
                f"_Proyek Tugas Akhir Sistem Multi-Agen Travel_\n\n"
                f"🤖 *Agen Travel AI siap membantu:*\n"
                f"🏨 Hotel • ✈️ Penerbangan • 🏝️ Tur • 📞 Support\n\n"
                f"💬 *Coba fitur dengan ketik:*\n"
                f"• \"Carikan hotel di Ubud tanggal 25 Juni\"\n"
                f"• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                f"• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n\n"
                f"📖 */help* untuk panduan lengkap"
            )
        else:
            # User belum login - pesan informatif dan jelas
            welcome_message = (
                f"✈️ *Selamat datang di Agen Travel AI!*\n\n"
                f"_Proyek Tugas Akhir Sistem Multi-Agen Travel_\n\n"
                f"🤖 *Layanan tersedia:*\n"
                f"🏨 Hotel • ✈️ Penerbangan • 🏝️ Tur • 📞 Support\n\n"
                f"🔐 *Mulai sekarang:*\n"
                f"📝 /register - Daftar akun baru\n"
                f"🔑 /login - Masuk dengan akun\n\n"
                f"💬 *Setelah login, coba ketik:*\n"
                f"• \"Carikan hotel di Ubud tanggal 25 Juni\"\n"
                f"• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                f"• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n\n"
                f"📖 */help* untuk panduan lengkap"
            )

        await bot.send_message(
            chat_id=chat_id,
            text=welcome_message,
            parse_mode="Markdown"
        )

        # Simpan pesan selamat datang ke database
        # Coba Supabase RPC terlebih dahulu
        postgres_result = await postgres_client.save_chat_message(
            str(user_id),
            thread_id,
            "/start",
            welcome_message
        )

        # Jika Supabase RPC gagal, gunakan Supabase REST API sebagai fallback
        if not postgres_result:
            await supabase_client.save_chat_message(
                str(user_id),
                thread_id,
                "/start",
                welcome_message
            )

    except Exception as e:
        logger.error(f"Error saat handle start command: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Terjadi kesalahan saat memproses perintah /start. Silakan coba lagi."
        )


async def handle_newchat_command(chat_id, user_id, user_first_name):
    """Menangani perintah /newchat - membuat chat baru tanpa menghapus yang lama."""
    try:
        # Cek autentikasi user terlebih dahulu
        if not await auth_handler.is_user_authenticated(user_id):
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "🔐 *Anda belum login!*\n\n"
                    "Untuk menggunakan fitur percakapan baru, silakan:\n"
                    "📝 /register - Registrasi akun baru\n"
                    "🔑 /login - Login dengan akun yang sudah ada\n\n"
                    "Setelah login, Anda dapat membuat percakapan baru."
                ),
                parse_mode="Markdown"
            )
            return

        # Kirim pesan loading
        loading_message = await bot.send_message(
            chat_id=chat_id,
            text="⏳ Membuat percakapan baru..."
        )

        # Panggil API untuk membuat chat baru
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL.replace('/response/', '')}/chat/{user_id}",
                params={"platform": "telegram"},
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()

        # Update thread ID di memori lokal
        new_thread_id = result.get('thread_id')
        if new_thread_id:
            user_threads[user_id] = new_thread_id

        # Hapus pesan loading
        await bot.delete_message(chat_id=chat_id, message_id=loading_message.message_id)

        # Ambil nama user dari session untuk personalisasi
        session = auth_handler.get_user_session(user_id)
        user_data = session.get("user_data", {}) if session else {}
        user_name = user_data.get("nama", user_first_name)

        # Pesan 1: Konfirmasi percakapan baru berhasil dibuat (dengan detail)
        initial_success_message = (
            f"✅ *Percakapan baru berhasil dibuat!*\n\n"
            f"Halo {user_name}! Anda sekarang memulai percakapan baru."
        )

        success_msg = await bot.send_message(
            chat_id=chat_id,
            text=initial_success_message,
            parse_mode="Markdown"
        )

        # Delay kecil untuk transisi yang lebih smooth (500ms)
        await asyncio.sleep(0.5)

        # Pesan 2: Tutorial singkat dan elegant
        welcome_message = (
            "🚀 *Siap membantu perjalanan Anda!*\n\n"
            "💬 *Coba ketik:*\n"
            "• \"Halo\" untuk memulai\n"
            "• \"Carikan hotel di Ubud untuk tanggal 25 Juni\"\n"
            "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
            "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n\n"
            "📖 Ketik */help* untuk panduan lengkap"
        )

        await bot.send_message(
            chat_id=chat_id,
            text=welcome_message,
            parse_mode="Markdown"
        )

        # Callback effect di background - edit pesan 1 setelah 3 detik
        async def callback_edit():
            await asyncio.sleep(3)
            final_success_message = "✅ *Percakapan baru berhasil dibuat!*"
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=success_msg.message_id,
                    text=final_success_message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Gagal mengedit pesan success: {e}")

        # Jalankan callback edit di background tanpa menunggu
        asyncio.create_task(callback_edit())

        # Simpan pesan command ke database
        postgres_result = await postgres_client.save_chat_message(
            str(user_id),
            new_thread_id,
            "/newchat",
            initial_success_message
        )

        if not postgres_result:
            await supabase_client.save_chat_message(
                str(user_id),
                new_thread_id,
                "/newchat",
                initial_success_message
            )

    except Exception as e:
        logger.error(f"Error saat membuat thread baru: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Maaf, terjadi kesalahan saat membuat percakapan baru. Silakan coba lagi."
        )


async def clear_telegram_chat_history(chat_id):
    """Menghapus semua pesan dalam chat Telegram dengan penanganan error yang lebih baik."""
    try:
        # Kirim pesan sementara untuk mendapatkan message_id terbaru
        temp_message = await bot.send_message(chat_id=chat_id, text="🔍 Mencari pesan...")
        current_message_id = temp_message.message_id

        # Hapus pesan sementara
        try:
            await bot.delete_message(chat_id=chat_id, message_id=current_message_id)
        except Exception as e:
            logger.warning(f"Gagal menghapus pesan sementara: {e}")

        # Coba hapus pesan dari message_id terbaru mundur ke belakang
        deleted_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 3  # Kurangi toleransi untuk menghentikan lebih cepat
        max_attempts = 1000  # Tingkatkan maksimal attempts

        for i in range(1, max_attempts + 1):
            try:
                message_id_to_delete = current_message_id - i
                if message_id_to_delete <= 0:
                    # Sudah mencapai message_id 0 atau negatif, berhenti
                    logger.info(f"Mencapai message_id {message_id_to_delete}, menghentikan proses")
                    break

                await bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
                deleted_count += 1
                consecutive_failures = 0  # Reset counter karena berhasil hapus

                # Tambahkan delay kecil untuk menghindari rate limiting
                await asyncio.sleep(0.1)  # Perlambat sedikit untuk stabilitas

            except Exception as e:
                error_msg = str(e).lower()

                # Cek jenis error spesifik
                if "bad request" in error_msg and "message to delete not found" in error_msg:
                    # Pesan tidak ditemukan, ini normal - lanjutkan tanpa menghitung sebagai failure
                    logger.debug(f"Pesan {message_id_to_delete} tidak ditemukan (normal)")
                    await asyncio.sleep(0.02)
                    continue
                elif "bad request" in error_msg and "message can't be deleted" in error_msg:
                    # Pesan tidak bisa dihapus (mungkin terlalu lama), lanjutkan
                    logger.debug(f"Pesan {message_id_to_delete} tidak bisa dihapus (terlalu lama)")
                    await asyncio.sleep(0.02)
                    continue
                elif "too many requests" in error_msg or "rate limit" in error_msg:
                    # Rate limiting, tunggu lebih lama
                    logger.warning(f"Rate limit detected, menunggu 2 detik...")
                    await asyncio.sleep(2.0)
                    continue
                else:
                    # Error lain, hitung sebagai failure
                    consecutive_failures += 1
                    logger.debug(f"Error menghapus pesan {message_id_to_delete}: {e}")

                # Jika sudah 3 kali berturut-turut gagal, kemungkinan sudah tidak ada pesan lagi
                if consecutive_failures >= max_consecutive_failures:
                    logger.info(f"Gagal menghapus {max_consecutive_failures} pesan berturut-turut, menghentikan proses")
                    break

                # Delay untuk failure
                await asyncio.sleep(0.05)

        logger.info(f"Berhasil menghapus {deleted_count} pesan dari chat {chat_id}")
        return deleted_count

    except Exception as e:
        logger.error(f"Error saat menghapus riwayat chat Telegram: {e}")
        return 0


async def handle_deletechat_command(chat_id, user_id, user_first_name):
    """Menangani perintah /deletechat - menampilkan konfirmasi terlebih dahulu."""
    try:
        # Cek autentikasi user terlebih dahulu
        if not await auth_handler.is_user_authenticated(user_id):
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "🔐 *Anda belum login!*\n\n"
                    "Untuk menggunakan fitur hapus percakapan, silakan:\n"
                    "📝 /register - Registrasi akun baru\n"
                    "🔑 /login - Login dengan akun yang sudah ada\n\n"
                    "Setelah login, Anda dapat menghapus riwayat percakapan."
                ),
                parse_mode="Markdown"
            )
            return

        # Ambil nama user dari session untuk personalisasi
        session = auth_handler.get_user_session(user_id)
        user_data = session.get("user_data", {}) if session else {}
        user_name = user_data.get("nama", user_first_name)

        # Buat inline keyboard untuk konfirmasi
        keyboard = [
            [
                InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"deletechat_confirm_{user_id}"),
                InlineKeyboardButton("❌ Batal", callback_data=f"deletechat_cancel_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Kirim pesan konfirmasi dengan tombol
        confirmation_message = (
            f"⚠️ *Konfirmasi Hapus Riwayat Percakapan*\n\n"
            f"Halo {user_name}! Anda akan menghapus:\n\n"
            f"• 🗄️ Semua riwayat percakapan di database\n"
            f"• 💬 Semua pesan di chat Telegram ini\n"
            f"• 📝 Semua data checkpoint dan konteks\n\n"
            f"⚠️ *Tindakan ini tidak dapat dibatalkan!*\n\n"
            f"Apakah Anda yakin ingin melanjutkan?"
        )

        await bot.send_message(
            chat_id=chat_id,
            text=confirmation_message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error saat menampilkan konfirmasi deletechat: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Maaf, terjadi kesalahan saat memproses perintah. Silakan coba lagi."
        )


async def execute_deletechat(chat_id, user_id, user_first_name):
    """Menjalankan proses penghapusan chat yang sebenarnya."""
    try:
        # Kirim pesan loading
        loading_message = await bot.send_message(
            chat_id=chat_id,
            text="⏳ Menghapus riwayat percakapan..."
        )

        # Dapatkan thread ID lama
        old_thread_id = await get_thread_id(user_id)

        # Panggil API untuk menghapus chat lama
        async with httpx.AsyncClient() as client:
            if old_thread_id:
                delete_response = await client.delete(
                    f"{API_URL.replace('/response/', '')}/chat/{old_thread_id}",
                    timeout=10.0
                )
                delete_response.raise_for_status()

            # Panggil API untuk membuat chat baru
            create_response = await client.post(
                f"{API_URL.replace('/response/', '')}/chat/{user_id}",
                params={"platform": "telegram"},
                timeout=10.0
            )
            create_response.raise_for_status()
            result = create_response.json()

        # Update thread ID di memori lokal
        new_thread_id = result.get('thread_id')
        if new_thread_id:
            user_threads[user_id] = new_thread_id

        # Update pesan loading untuk tahap berikutnya
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=loading_message.message_id,
            text="🧹 Membersihkan riwayat chat Telegram..."
        )

        # Hapus semua pesan dalam chat Telegram
        deleted_count = await clear_telegram_chat_history(chat_id)

        # Hapus pesan loading setelah selesai
        try:
            await bot.delete_message(chat_id=chat_id, message_id=loading_message.message_id)
        except Exception as e:
            logger.warning(f"Gagal menghapus pesan loading final: {e}")

        # Ambil nama user dari session untuk personalisasi
        session = auth_handler.get_user_session(user_id)
        user_data = session.get("user_data", {}) if session else {}
        user_name = user_data.get("nama", user_first_name)

        # Pesan 1: Konfirmasi riwayat berhasil dihapus (dengan detail)
        initial_success_message = (
            f"✅ *Riwayat percakapan berhasil dihapus!*\n\n"
            f"Halo {user_name}! Riwayat percakapan Anda telah dihapus dari:\n"
            f"• 🗄️ Database sistem\n"
            f"• 💬 Chat Telegram ({deleted_count} pesan dihapus)"
        )

        success_msg = await bot.send_message(
            chat_id=chat_id,
            text=initial_success_message,
            parse_mode="Markdown"
        )

        # Delay kecil untuk transisi yang lebih smooth (500ms)
        await asyncio.sleep(0.5)

        # Pesan 2: Tutorial singkat dan elegant
        welcome_message = (
            "🚀 *Siap membantu perjalanan Anda!*\n\n"
            "💬 *Coba ketik:*\n"
            "• \"Halo\" untuk memulai\n"
            "• \"Carikan hotel di Ubud untuk tanggal 25 Juni\"\n"
            "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
            "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n\n"
            "📖 Ketik */help* untuk panduan lengkap"
        )

        await bot.send_message(
            chat_id=chat_id,
            text=welcome_message,
            parse_mode="Markdown"
        )

        # Callback effect di background - edit pesan 1 setelah 3 detik
        async def callback_edit():
            await asyncio.sleep(3)
            final_success_message = "✅ *Riwayat percakapan berhasil dihapus!*"
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=success_msg.message_id,
                    text=final_success_message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Gagal mengedit pesan success: {e}")

        # Jalankan callback edit di background tanpa menunggu
        asyncio.create_task(callback_edit())

        # Simpan pesan command ke database
        postgres_result = await postgres_client.save_chat_message(
            str(user_id),
            new_thread_id,
            "/deletechat",
            initial_success_message
        )

        if not postgres_result:
            await supabase_client.save_chat_message(
                str(user_id),
                new_thread_id,
                "/deletechat",
                initial_success_message
            )

    except Exception as e:
        logger.error(f"Error saat menghapus thread: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Maaf, terjadi kesalahan saat menghapus riwayat percakapan. Silakan coba lagi."
        )


async def handle_deletechat_callback(callback_query):
    """Menangani callback dari tombol konfirmasi deletechat."""
    try:
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        user_first_name = callback_query.from_user.first_name
        callback_data = callback_query.data

        # Ambil nama user dari session untuk personalisasi
        session = auth_handler.get_user_session(user_id)
        user_data = session.get("user_data", {}) if session else {}
        user_name = user_data.get("nama", user_first_name)

        if callback_data.startswith("deletechat_confirm_"):
            # User mengkonfirmasi penghapusan
            # Hapus pesan konfirmasi
            await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)

            # Jalankan proses penghapusan
            await execute_deletechat(chat_id, user_id, user_first_name)

        elif callback_data.startswith("deletechat_cancel_"):
            # User membatalkan penghapusan
            # Edit pesan konfirmasi menjadi pesan pembatalan (dengan detail)
            initial_cancel_message = (
                f"❌ *Penghapusan Dibatalkan*\n\n"
                f"Halo {user_name}! Riwayat percakapan Anda tetap aman."
            )

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=initial_cancel_message,
                parse_mode="Markdown"
            )

            # Delay kecil untuk transisi yang lebih smooth (500ms)
            await asyncio.sleep(0.5)

            # Pesan 2: Tutorial singkat dan elegant
            welcome_message = (
                "🚀 *Siap membantu perjalanan Anda!*\n\n"
                "💬 *Coba ketik:*\n"
                "• \"Halo\" untuk memulai\n"
                "• \"Carikan hotel di Ubud untuk tanggal 25 Juni\"\n"
                "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n\n"
                "📖 Ketik */help* untuk panduan lengkap"
            )

            await bot.send_message(
                chat_id=chat_id,
                text=welcome_message,
                parse_mode="Markdown"
            )

            # Callback effect di background - edit pesan 1 setelah 3 detik
            async def callback_edit():
                await asyncio.sleep(3)
                final_cancel_message = "❌ *Penghapusan Dibatalkan*"
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=callback_query.message.message_id,
                        text=final_cancel_message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Gagal mengedit pesan cancel: {e}")

            # Jalankan callback edit di background tanpa menunggu
            asyncio.create_task(callback_edit())

        # Jawab callback query untuk menghilangkan loading di tombol
        await bot.answer_callback_query(callback_query.id)

    except Exception as e:
        logger.error(f"Error saat menangani callback deletechat: {e}")
        try:
            await bot.answer_callback_query(
                callback_query.id,
                text="❌ Terjadi kesalahan. Silakan coba lagi.",
                show_alert=True
            )
        except:
            pass


def detect_request_type(message_text):
    """Mendeteksi jenis permintaan berdasarkan teks pesan."""
    message_lower = message_text.lower()

    # MCP Tools Detection - Prioritas tertinggi untuk deteksi MCP
    # Booking.com MCP keywords - HANYA yang spesifik menyebutkan platform
    booking_mcp_keywords = ['booking.com', 'booking com', 'pakai booking.com', 'gunakan booking.com', 'cari dengan booking.com']
    mcp_keywords = ['mcp', 'mcp tools', 'gunakan mcp', 'pakai mcp', 'cari dengan mcp', 'data real-time', 'data realtime',
                   'real time', 'terbaru', 'update', 'langsung dari']

    # Airbnb MCP keywords
    airbnb_mcp_keywords = ['airbnb', 'air bnb', 'pakai airbnb', 'gunakan airbnb', 'cari dengan airbnb']

    # TripAdvisor MCP keywords
    tripadvisor_mcp_keywords = ['tripadvisor', 'trip advisor', 'tripadvisor.com', 'pakai tripadvisor',
                               'gunakan tripadvisor', 'cari dengan tripadvisor']

    # Hotel/accommodation keywords for MCP
    hotel_mcp_keywords = ['hotel', 'penginapan', 'akomodasi', 'villa', 'resort']

    # Flight keywords for MCP
    flight_mcp_keywords = ['pesawat', 'penerbangan', 'tiket', 'flight']

    # TripAdvisor specific categories
    attraction_keywords = ['atraksi', 'tempat wisata', 'objek wisata', 'destinasi', 'wisata', 'lokasi', 'lokasi wisata']
    restaurant_keywords = ['restoran', 'restaurant', 'makan', 'kuliner', 'cafe', 'tempat makan']
    review_keywords = ['review', 'ulasan', 'rating', 'penilaian', 'komentar', 'testimoni']
    photo_keywords = ['foto', 'gambar', 'picture', 'image']

    # Keywords untuk setiap jenis permintaan (lebih spesifik dulu)
    cancel_keywords = ['batal', 'cancel', 'batalkan', 'hapus pesanan', 'cancel booking', 'refund']

    # Currency/Kurs keywords - untuk search_currency_rates tool (sangat spesifik untuk menghindari konflik dengan payment)
    currency_specific_keywords = ['kurs', 'nilai tukar', 'exchange rate', 'mata uang', 'currency', 'tukar uang', 'nilai kurs']
    currency_inquiry_keywords = ['berapa kurs', 'berapa dollar', 'berapa euro', 'nilai dollar', 'nilai euro',
                                'kurs dollar', 'kurs euro', 'harga dollar', 'harga euro', 'kurs hari ini',
                                'dollar hari ini', 'euro hari ini', 'kurs terbaru', 'kurs sekarang']

    # Payment keywords - termasuk yang mengandung mata uang untuk pembayaran
    payment_keywords = ['bayar', 'payment', 'pembayaran', 'transfer', 'lunas', 'uang muka', 'cicilan',
                       'bayar dengan', 'bayar pakai', 'transfer usd', 'transfer dollar', 'transfer euro',
                       'pembayaran dollar', 'pembayaran euro', 'pembayaran usd', 'pembayaran eur']
    payment_keywords_with_boundary = [r'\bdp\b']  # Kata "dp" dengan word boundary

    # Article/News keywords - untuk search_travel_articles tool
    article_keywords = ['artikel', 'berita', 'tips', 'panduan', 'informasi', 'info', 'rekomendasi',
                       'artikel travel', 'tips travel', 'panduan travel', 'berita travel', 'info travel',
                       'artikel wisata', 'tips wisata', 'panduan wisata', 'rekomendasi wisata',
                       'ada artikel', 'cari artikel', 'carikan artikel', 'carilah artikel']

    # Kode bandara populer Indonesia (harus dideteksi sebelum payment untuk menghindari konflik dengan "dp")
    airport_codes = ['dps', 'cgk', 'sub', 'kno', 'upg', 'mlg', 'jog', 'solo', 'pdg', 'plm', 'pkn', 'btj', 'pon', 'amq']

    # Hotel sub-categories
    hotel_room_keywords = ['kamar hotel', 'tipe kamar', 'jenis kamar', 'kamar tersedia', 'cek kamar']
    hotel_facility_keywords = ['fasilitas hotel', 'amenities', 'kolam renang', 'gym', 'spa', 'wifi', 'breakfast', 'sarapan']
    hotel_search_keywords = ['cari hotel', 'carikan hotel', 'carilah hotel', 'pencarian hotel', 'mau hotel']
    hotel_keywords = ['hotel', 'menginap', 'akomodasi', 'penginapan', 'resort', 'villa',
                     'homestay', 'guest house', 'check in', 'check-in', 'malam', 'bermalam']

    # Flight sub-categories
    flight_schedule_keywords = ['jadwal pesawat', 'jam terbang', 'schedule flight', 'waktu keberangkatan', 'detail penerbangan',
                               'cari jadwal pesawat', 'carikan jadwal pesawat', 'carilah jadwal pesawat']
    flight_search_keywords = ['cari pesawat', 'carikan pesawat', 'carilah pesawat', 'pencarian pesawat', 'mau pesawat',
                             'cari penerbangan', 'carikan penerbangan', 'carilah penerbangan', 'pencarian penerbangan',
                             'cari tiket', 'carikan tiket', 'carilah tiket', 'pencarian tiket']
    flight_keywords = ['pesawat', 'penerbangan', 'tiket', 'terbang', 'bandara', 'maskapai', 'flight',
                      'garuda', 'lion air', 'citilink', 'batik air', 'sriwijaya', 'wings air',
                      'jakarta', 'surabaya', 'medan', 'makassar', 'bali', 'denpasar']

    # Tour sub-categories
    tour_detail_keywords = ['detail paket', 'itinerary', 'jadwal tour', 'rincian paket', 'detail tur']
    tour_search_keywords = ['cari tour', 'carikan tour', 'carilah tour', 'pencarian tour', 'mau tour',
                           'cari tur', 'carikan tur', 'carilah tur', 'pencarian tur', 'mau tur',
                           'cari paket', 'carikan paket', 'carilah paket', 'pencarian paket']
    tour_keywords = ['tur', 'tour', 'wisata', 'paket', 'liburan', 'jalan-jalan', 'destinasi', 'tempat wisata',
                    'pantai', 'gunung', 'candi', 'museum', 'taman', 'objek wisata', 'rekreasi']

    booking_keywords = ['pesan', 'booking', 'book', 'reservasi', 'buat pesanan', 'order', 'konfirmasi', 'proses pesanan', 'lanjutkan', 'setuju']
    history_keywords = ['riwayat', 'history', 'pesanan saya', 'booking saya', 'pemesanan saya', 'cek pesanan',
                       'status', 'invoice', 'receipt', 'bukti', 'transaksi saya', 'order saya']

    # Prioritas deteksi (paling spesifik dulu)
    # 1. DETEKSI MCP TOOLS - PRIORITAS TERTINGGI
    # Deteksi Booking.com MCP untuk hotel
    if (any(booking_keyword in message_lower for booking_keyword in booking_mcp_keywords) and
        any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
        any(hotel_keyword in message_lower for hotel_keyword in hotel_mcp_keywords)):
        return 'booking_mcp_hotel'

    # Deteksi Booking.com MCP untuk flight
    elif (any(booking_keyword in message_lower for booking_keyword in booking_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
          any(flight_keyword in message_lower for flight_keyword in flight_mcp_keywords)):
        return 'booking_mcp_flight'

    # Deteksi Airbnb MCP
    elif (any(airbnb_keyword in message_lower for airbnb_keyword in airbnb_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords)):
        return 'airbnb_mcp'

    # Deteksi TripAdvisor MCP untuk hotel
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
          any(hotel_keyword in message_lower for hotel_keyword in hotel_mcp_keywords)):
        return 'tripadvisor_mcp_hotel'

    # Deteksi TripAdvisor MCP untuk atraksi
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
          any(attraction_keyword in message_lower for attraction_keyword in attraction_keywords)):
        return 'tripadvisor_mcp_attraction'

    # Deteksi TripAdvisor MCP untuk restoran
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
          any(restaurant_keyword in message_lower for restaurant_keyword in restaurant_keywords)):
        return 'tripadvisor_mcp_restaurant'

    # Deteksi TripAdvisor MCP untuk review
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
          any(review_keyword in message_lower for review_keyword in review_keywords)):
        return 'tripadvisor_mcp_review'

    # Deteksi TripAdvisor MCP untuk foto
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords) and
          any(photo_keyword in message_lower for photo_keyword in photo_keywords)):
        return 'tripadvisor_mcp_photo'

    # Deteksi TripAdvisor MCP umum (jika hanya menyebutkan tripadvisor + mcp tanpa kategori spesifik)
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(mcp_keyword in message_lower for mcp_keyword in mcp_keywords)):
        return 'tripadvisor_mcp_general'

    # DETEKSI ALTERNATIF - Kombinasi 2-3 kata tanpa "mcp" eksplisit
    # Booking.com + hotel/flight (HANYA untuk booking.com spesifik)
    elif (any(booking_keyword in message_lower for booking_keyword in booking_mcp_keywords) and
          any(hotel_keyword in message_lower for hotel_keyword in hotel_mcp_keywords)):
        return 'booking_mcp_hotel'
    elif (any(booking_keyword in message_lower for booking_keyword in booking_mcp_keywords) and
          any(flight_keyword in message_lower for flight_keyword in flight_mcp_keywords)):
        return 'booking_mcp_flight'

    # Airbnb + hotel (deteksi 2 kata)
    elif (any(airbnb_keyword in message_lower for airbnb_keyword in airbnb_mcp_keywords) and
          any(hotel_keyword in message_lower for hotel_keyword in hotel_mcp_keywords)):
        return 'airbnb_mcp'

    # TripAdvisor + kategori (deteksi 2 kata)
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(hotel_keyword in message_lower for hotel_keyword in hotel_mcp_keywords)):
        return 'tripadvisor_mcp_hotel'
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(attraction_keyword in message_lower for attraction_keyword in attraction_keywords)):
        return 'tripadvisor_mcp_attraction'
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(restaurant_keyword in message_lower for restaurant_keyword in restaurant_keywords)):
        return 'tripadvisor_mcp_restaurant'
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(review_keyword in message_lower for review_keyword in review_keywords)):
        return 'tripadvisor_mcp_review'
    elif (any(tripadvisor_keyword in message_lower for tripadvisor_keyword in tripadvisor_mcp_keywords) and
          any(photo_keyword in message_lower for photo_keyword in photo_keywords)):
        return 'tripadvisor_mcp_photo'

    # 2. Deteksi payment terlebih dahulu (untuk menghindari konflik dengan currency)
    elif any(keyword in message_lower for keyword in payment_keywords) or any(re.search(pattern, message_lower) for pattern in payment_keywords_with_boundary):
        return 'payment'
    # 3. Deteksi currency/kurs (setelah payment untuk menghindari konflik)
    elif any(keyword in message_lower for keyword in currency_specific_keywords) or any(keyword in message_lower for keyword in currency_inquiry_keywords):
        return 'currency'
    # 4. Deteksi artikel/berita/tips travel
    elif any(keyword in message_lower for keyword in article_keywords):
        return 'article'
    # 5. Deteksi kode bandara untuk menghindari konflik dengan "dp"
    elif any(code in message_lower for code in airport_codes):
        return 'flight'
    elif any(keyword in message_lower for keyword in cancel_keywords):
        return 'cancel'
    elif any(keyword in message_lower for keyword in history_keywords):
        return 'history'
    elif any(keyword in message_lower for keyword in hotel_room_keywords):
        return 'hotel_room'
    elif any(keyword in message_lower for keyword in hotel_facility_keywords):
        return 'hotel_facility'
    elif any(keyword in message_lower for keyword in hotel_search_keywords):
        return 'hotel_search'
    elif any(keyword in message_lower for keyword in flight_schedule_keywords):
        return 'flight_schedule'
    elif any(keyword in message_lower for keyword in flight_search_keywords):
        return 'flight_search'
    elif any(keyword in message_lower for keyword in tour_detail_keywords):
        return 'tour_detail'
    elif any(keyword in message_lower for keyword in tour_search_keywords):
        return 'tour_search'
    elif any(keyword in message_lower for keyword in booking_keywords):
        return 'booking'
    elif any(keyword in message_lower for keyword in hotel_keywords):
        return 'hotel'
    elif any(keyword in message_lower for keyword in flight_keywords):
        return 'flight'
    elif any(keyword in message_lower for keyword in tour_keywords):
        return 'tour'
    else:
        return 'general'

def get_loading_message(request_type):
    """Mendapatkan pesan loading yang sesuai dengan jenis permintaan."""
    loading_messages = {
        # Kategori utama
        'hotel': 'Mencari hotel',
        'flight': 'Mencari pesawat',
        'tour': 'Mencari paket tur',
        'booking': 'Memproses pesanan',
        'history': 'Mengambil riwayat pesanan',
        'general': 'Memproses permintaan',

        # Kategori spesifik baru
        'hotel_room': 'Mencari kamar hotel',
        'hotel_facility': 'Mencari fasilitas hotel',
        'hotel_search': 'Mencari hotel',
        'flight_schedule': 'Mencari jadwal pesawat',
        'flight_search': 'Mencari pesawat',
        'tour_detail': 'Mencari detail paket tur',
        'tour_search': 'Mencari paket tur',
        'payment': 'Memproses pembayaran',
        'cancel': 'Membatalkan pesanan',

        # Kategori baru untuk customer service tools
        'currency': 'Mencari kurs',
        'article': 'Mencari artikel',

        # Kategori MCP Tools - dengan emoji jam pasir dan pesan sesuai memori
        'booking_mcp_hotel': 'Mencari hotel di booking.com',
        'booking_mcp_flight': 'Mencari pesawat di booking.com',
        'airbnb_mcp': 'Mencari hotel di airbnb',
        'tripadvisor_mcp_hotel': 'Mencari hotel di tripadvisor',
        'tripadvisor_mcp_attraction': 'Mencari atraksi di tripadvisor',
        'tripadvisor_mcp_restaurant': 'Mencari restoran di tripadvisor',
        'tripadvisor_mcp_review': 'Mencari review di tripadvisor',
        'tripadvisor_mcp_photo': 'Mencari foto di tripadvisor',
        'tripadvisor_mcp_general': 'Mencari data di tripadvisor'
    }
    return loading_messages.get(request_type, 'Memproses permintaan')

async def handle_user_message(chat_id, user_id, message_text, message_id=None):
    """Memproses pesan pengguna dan memberikan respons yang sesuai."""
    # Mencatat metrik Prometheus
    TELEGRAM_MESSAGES.labels(message_type="user_message").inc()
    ACTIVE_TELEGRAM_USERS.inc()

    start_time = time.time()

    try:
        # Cek apakah user sedang dalam proses registrasi
        registration_handled = await auth_handler.handle_registration_step(chat_id, user_id, message_text)
        if registration_handled:
            return

        # Cek apakah user sedang dalam proses login
        login_handled = await auth_handler.handle_login_step(chat_id, user_id, message_text, message_id)
        if login_handled:
            return

        # Cek apakah user sedang dalam proses konfirmasi logout
        logout_handled = await auth_handler.handle_logout_confirmation(chat_id, user_id, message_text)
        if logout_handled:
            return

        # Cek apakah user ingin resend verification email
        if message_text.lower().strip() == 'resend':
            await auth_handler.handle_resend_verification(chat_id, user_id)
            return

        # Cek natural language commands (login, register, profile, logout, help)
        natural_command_handled = await auth_handler.handle_natural_language_command(chat_id, user_id, message_text)
        if natural_command_handled:
            return

        # Cek autentikasi dan verifikasi user terlebih dahulu
        if not await auth_handler.check_user_access(chat_id, user_id):
            # User belum login atau belum verifikasi - pesan sudah dikirim oleh check_user_access
            return

        # Mendapatkan thread ID untuk pengguna ini
        thread_id = await get_thread_id(user_id)

        # Deteksi jenis permintaan untuk animasi loading yang sesuai
        request_type = detect_request_type(message_text)
        loading_base_message = get_loading_message(request_type)

        # Mengirim pesan "sedang memproses" sementara dengan animasi loading dan mengingat ID-nya
        processing_message = await bot.send_message(chat_id=chat_id, text=f"⏳ {loading_base_message}...")
        processing_message_id = processing_message.message_id

        # Memulai animasi loading di background dengan pesan yang sesuai
        animation_task = asyncio.create_task(animate_loading_with_context(
            chat_id, processing_message_id, loading_base_message
        ))

        # Memanggil API dengan pesan pengguna dan user context
        response_data = await make_api_call_with_user_context(message_text, thread_id, user_id)

        # Membatalkan animasi
        animation_task.cancel()

        # Mendapatkan status dialog dan nama agen
        dialog_state = response_data.get('dialog_state', 'supervisor')
        agent_name = agent_dict.get(dialog_state, 'Agen Supervisor')

        # Mendapatkan jawaban dari respons API
        answer = response_data.get("answer", "Saya tidak bisa memproses permintaan Anda dengan benar.")

        # Format teks dengan spasi dan pemformatan yang tepat
        answer = fix_text_formatting(answer)

        # Menghapus pesan pemrosesan
        try:
            await bot.delete_message(chat_id=chat_id, message_id=processing_message_id)
        except Exception as e:
            logger.error(f"Gagal menghapus pesan pemrosesan: {e}")

        # Format header respons dengan nama agen
        formatted_header = f"🤖 *{agent_name}*\n\n"

        # Format pesan lengkap
        full_message = formatted_header + answer

        # Mengirim pesan lengkap (tanpa streaming)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=full_message,
                parse_mode="Markdown"
            )

            # Simpan pesan dan respons ke database untuk persistensi
            # Coba Supabase RPC terlebih dahulu
            postgres_result = await postgres_client.save_chat_message(
                str(user_id),
                thread_id,
                message_text,
                answer
            )

            # Jika Supabase RPC gagal, gunakan Supabase REST API sebagai fallback
            if not postgres_result:
                await supabase_client.save_chat_message(
                    str(user_id),
                    thread_id,
                    message_text,
                    answer
                )
        except Exception as e:
            logger.error(f"Gagal mengirim pesan: {e}")
            # Mencoba tanpa markdown jika terjadi error
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🤖 {agent_name}\n\n{answer}"
                )

                # Simpan pesan dan respons ke database untuk persistensi
                # Coba Supabase RPC terlebih dahulu
                postgres_result = await postgres_client.save_chat_message(
                    str(user_id),
                    thread_id,
                    message_text,
                    answer
                )

                # Jika Supabase RPC gagal, gunakan Supabase REST API sebagai fallback
                if not postgres_result:
                    await supabase_client.save_chat_message(
                        str(user_id),
                        thread_id,
                        message_text,
                        answer
                    )
            except Exception as e2:
                logger.error(f"Gagal mengirim pesan biasa: {e2}")

    except Exception as e:
        logger.error(f"Error saat handle user message: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi."
        )
    finally:
        # Mencatat waktu respons total dan mengurangi pengguna aktif
        response_time = time.time() - start_time
        TELEGRAM_RESPONSE_TIME.labels(message_type="total").observe(response_time)
        ACTIVE_TELEGRAM_USERS.dec()

async def animate_loading_with_context(chat_id, message_id, base_message):
    """Menganimasikan pesan loading dengan konteks yang sesuai dan emoji jam pasir bergantian."""
    sand_clocks = ["⏳", "⌛"]
    dots = [".", "..", "..."]

    i = 0
    try:
        while True:
            emoji = sand_clocks[i % len(sand_clocks)]
            current_dots = dots[i % len(dots)]
            text = f"{emoji} {base_message}{current_dots}"

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text
            )
            i += 1
            await asyncio.sleep(0.5)  # Sedikit lebih cepat untuk animasi yang lebih halus
    except asyncio.CancelledError:
        # Animasi dibatalkan, yang memang diharapkan
        pass
    except Exception as e:
        logger.error(f"Error dalam animasi loading: {e}")

async def animate_loading_dots(chat_id, message_id):
    """Menganimasikan pesan loading dengan emoji jam pasir bergantian dan titik-titik beranimasi."""
    sand_clocks = ["⏳", "⌛"]
    base_message = "Sedang memproses permintaan Anda"
    dots = [".", "..", "..."]

    i = 0
    try:
        while True:
            emoji = sand_clocks[i % len(sand_clocks)]
            current_dots = dots[i % len(dots)]
            text = f"{emoji} {base_message}{current_dots}"

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text
            )
            i += 1
            await asyncio.sleep(0.5)  # Sedikit lebih cepat untuk animasi yang lebih halus
    except asyncio.CancelledError:
        # Animasi dibatalkan, yang memang diharapkan
        pass
    except Exception as e:
        logger.error(f"Error dalam animasi loading: {e}")

# Menjaga fungsi animasi asli untuk kompatibilitas mundur
async def animate_loading_message(chat_id, message_id, loading_texts):
    """Menganimasikan pesan loading dengan teks yang berbeda."""
    i = 0
    try:
        while True:
            text = loading_texts[i % len(loading_texts)]
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text
            )
            i += 1
            await asyncio.sleep(0.7)  # Animasi sedikit lebih lambat untuk keterbacaan yang lebih baik
    except asyncio.CancelledError:
        # Animasi dibatalkan, yang memang diharapkan
        pass
    except Exception as e:
        logger.error(f"Kesalahan dalam animasi loading: {e}")

def fix_text_formatting(text):
    """Memperbaiki format umum dalam teks."""
    # Lindungi URL dari pemrosesan dengan mengganti sementara
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    url_placeholders = {}

    # Ganti URL dengan placeholder
    for i, url in enumerate(urls):
        placeholder = f"__URL_PLACEHOLDER_{i}__"
        url_placeholders[placeholder] = url
        text = text.replace(url, placeholder)

    # Lindungi email addresses dari pemrosesan dengan mengganti sementara
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    email_placeholders = {}

    # Ganti email dengan placeholder
    for i, email in enumerate(emails):
        placeholder = f"__EMAIL_PLACEHOLDER_{i}__"
        email_placeholders[placeholder] = email
        text = text.replace(email, placeholder)

    # Lindungi text dengan underscore dari pemrosesan dengan mengganti sementara
    underscore_pattern = r'\b[A-Za-z0-9]+_[A-Za-z0-9_]+\b'
    underscore_texts = re.findall(underscore_pattern, text)
    underscore_placeholders = {}

    # Ganti underscore text dengan placeholder
    for i, underscore_text in enumerate(underscore_texts):
        placeholder = f"__UNDERSCORE_PLACEHOLDER_{i}__"
        underscore_placeholders[placeholder] = underscore_text
        text = text.replace(underscore_text, placeholder)

    # Memperbaiki daftar bernomor - memastikan nomor dan teks berada di baris yang sama
    text = re.sub(r'(\d+\.)\s*\n\s*([A-Za-z])', r'\1 \2', text)

    # Menambahkan spasi setelah titik, tanda tanya, dan tanda seru jika diikuti huruf
    text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)

    # Memastikan spasi yang tepat di sekitar titik pada akhir nama/gelar (seperti "Dr." atau "Tn.")
    text = re.sub(r'([A-Za-z]+\.)([A-Za-z])', r'\1 \2', text)

    # Memperbaiki format poin bullet dengan memastikan baris baru yang tepat
    text = re.sub(r'([.!?])-', r'\1\n-', text)

    # Memastikan spasi yang tepat setelah koma
    text = re.sub(r',([A-Za-z])', r', \1', text)

    # Memperbaiki daftar poin bullet - memastikan setiap poin bullet berada di baris baru tanpa ambigu
    text = re.sub(r'([.!?])(\n- )', r'\1\n\n\2', text)

    # Memperbaiki penomoran dalam daftar - memastikan format dan spasi yang tepat
    text = re.sub(r'(\d+)\.([A-Za-z])', r'\1. \2', text)

    # Menggabungkan kalimat yang terpotong antar baris (untuk spasi yang lebih baik)
    text = re.sub(r'([a-z]),\n([a-z])', r'\1, \2', text)
    text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)

    # Membersihkan koma berlebihan dengan spasi yang tepat
    text = re.sub(r',\s*,', ',', text)

    # Menghapus baris kosong berlebihan (lebih dari 2 berturut-turut)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Memperbaiki format waktu (memastikan spasi yang tepat)
    text = re.sub(r'(\d+):(\d+)([A-Za-z])', r'\1:\2 \3', text)

    # Menghapus baris dengan karakter tunggal (sering disebabkan oleh masalah formatting)
    text = re.sub(r'\n([A-Za-z])\n', r' \1 ', text)

    # Pembersihan final - mengganti beberapa spasi dengan satu spasi
    text = re.sub(r' {2,}', ' ', text)

    # Kembalikan underscore text dari placeholder
    for placeholder, underscore_text in underscore_placeholders.items():
        text = text.replace(placeholder, underscore_text)

    # Kembalikan email addresses dari placeholder
    for placeholder, email in email_placeholders.items():
        text = text.replace(placeholder, email)

    # Kembalikan URL dari placeholder
    for placeholder, url in url_placeholders.items():
        text = text.replace(placeholder, url)

    return text

def create_text_chunks(text, _=20):
    """
    Mengembalikan seluruh teks sebagai satu bagian tanpa streaming.
    Ini memastikan pesan ditampilkan secara utuh, bukan terpotong-potong.
    """
    if not text:
        return [""]

    # Mengembalikan seluruh teks sebagai satu bagian
    return [text]

async def setup_webhook():
    """Mengatur webhook untuk bot."""
    webhook_info = await bot.get_webhook_info()

    # Hapus webhook jika ada
    if webhook_info.url:
        await bot.delete_webhook()

    # Set webhook
    await bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook disetting ke {WEBHOOK_URL}")

async def load_thread_ids_from_supabase():
    """Memuat thread ID dari Supabase ke memori lokal."""
    try:
        # Coba gunakan Supabase RPC terlebih dahulu
        try:
            # Dapatkan thread ID dari Supabase RPC
            data = await postgres_client.get_all_user_thread_ids()

            if data:
                logger.info(f"Berhasil mendapatkan thread IDs via Supabase RPC")

                # Simpan ke dictionary lokal
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            user_id = item.get('user_id')
                            thread_id = item.get('thread_id')
                            if user_id and thread_id:
                                try:
                                    # Konversi user_id ke integer jika perlu
                                    user_id_int = int(user_id)
                                    user_threads[user_id_int] = thread_id
                                except ValueError:
                                    # Jika user_id bukan integer, gunakan string
                                    user_threads[user_id] = thread_id

                    logger.info(f"Berhasil memuat {len(user_threads)} thread ID dari Supabase RPC")
                    return
                else:
                    logger.info(f"Data dari Supabase RPC bukan list: {type(data)}")
                    # Lanjutkan ke Supabase REST API

        except Exception as e:
            logger.info(f"Supabase RPC error: {str(e)}, mencoba Supabase REST API")

        # Jika Supabase RPC gagal, gunakan Supabase REST API sebagai fallback
        async with httpx.AsyncClient() as client:
            try:
                # Coba gunakan RPC execute_sql
                query = """
                WITH latest_threads AS (
                    SELECT DISTINCT ON (user_id) user_id, thread_id, updated_at
                    FROM chat_history
                    WHERE platform = 'telegram'
                    ORDER BY user_id, updated_at DESC
                )
                SELECT user_id, thread_id FROM latest_threads
                """

                response = await client.post(
                    f"{supabase_client.url}/rest/v1/rpc/execute_sql",
                    headers=supabase_client.headers,
                    json={"query": query},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Berhasil mendapatkan thread IDs via RPC execute_sql")

            except Exception as e2:
                logger.info(f"RPC execute_sql error: {str(e2)}, menggunakan REST API")

                # Gunakan REST API sebagai fallback terakhir
                # Dapatkan semua user_id unik
                users_response = await client.get(
                    f"{supabase_client.url}/rest/v1/chat_history",
                    headers=supabase_client.headers,
                    params={
                        "select": "user_id",
                        "platform": "eq.telegram"
                    },
                    timeout=10.0
                )
                users_response.raise_for_status()
                users_data = users_response.json()

                # Untuk setiap user_id, dapatkan thread_id terbaru
                data = []
                unique_users = set()
                for user_item in users_data:
                    user_id = user_item.get('user_id')
                    if user_id and user_id not in unique_users:
                        unique_users.add(user_id)
                        thread_response = await client.get(
                            f"{supabase_client.url}/rest/v1/chat_history",
                            headers=supabase_client.headers,
                            params={
                                "select": "thread_id",
                                "user_id": f"eq.{user_id}",
                                "platform": "eq.telegram",
                                "order": "updated_at.desc",
                                "limit": "1"
                            },
                            timeout=10.0
                        )
                        thread_response.raise_for_status()
                        thread_data = thread_response.json()
                        if thread_data and len(thread_data) > 0:
                            data.append({
                                "user_id": user_id,
                                "thread_id": thread_data[0].get('thread_id')
                            })
                logger.info(f"Berhasil mendapatkan thread IDs via REST API")

            # Simpan ke dictionary lokal
            for item in data:
                user_id = item.get('user_id')
                thread_id = item.get('thread_id')
                if user_id and thread_id:
                    try:
                        # Konversi user_id ke integer jika perlu
                        user_id_int = int(user_id)
                        user_threads[user_id_int] = thread_id
                    except ValueError:
                        # Jika user_id bukan integer, gunakan string
                        user_threads[user_id] = thread_id

            logger.info(f"Berhasil memuat {len(user_threads)} thread ID dari Supabase")

    except Exception as e:
        logger.error(f"Error saat memuat thread ID: {str(e)}")

@app.post("/")
async def webhook(request: Request):
    """Menangani permintaan webhook dari Telegram."""
    # Dapatkan data update
    update_data = await request.json()
    update = Update.de_json(update_data, bot)

    if not update:
        return Response(status_code=200)

    # Ekstrak informasi dasar
    if update.message:
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        user_first_name = update.message.from_user.first_name

        # Periksa perintah
        if update.message.text:
            if update.message.text.startswith('/start'):
                await handle_start_command(chat_id, user_id, user_first_name)
            elif update.message.text.startswith('/register'):
                await auth_handler.handle_register_command(chat_id, user_id)
            elif update.message.text.startswith('/login'):
                await auth_handler.handle_login_command(chat_id, user_id)
            elif update.message.text.startswith('/profile'):
                await auth_handler.handle_profile_command(chat_id, user_id)
            elif update.message.text.startswith('/logout'):
                await auth_handler.handle_logout_command(chat_id, user_id)
            elif update.message.text.startswith('/verify') or update.message.text.startswith('/verifikasi'):
                await auth_handler.handle_verify_command(chat_id, user_id)
            elif update.message.text.startswith('/resend'):
                await auth_handler.handle_resend_verification(chat_id, user_id)
            elif update.message.text.startswith('/help'):
                await auth_handler.handle_help_command(chat_id, user_id)
            elif update.message.text.startswith('/cancel'):
                await handle_user_message(chat_id, user_id, update.message.text, update.message.message_id)
            elif update.message.text.startswith('/newchat'):
                await handle_newchat_command(chat_id, user_id, user_first_name)
            elif update.message.text.startswith('/deletechat'):
                await handle_deletechat_command(chat_id, user_id, user_first_name)
            else:
                await handle_user_message(chat_id, user_id, update.message.text, update.message.message_id)

    # Tangani callback query (untuk inline keyboard buttons)
    elif update.callback_query:
        callback_query = update.callback_query
        callback_data = callback_query.data

        # Handle callback untuk deletechat confirmation
        if callback_data.startswith("deletechat_"):
            await handle_deletechat_callback(callback_query)
        # Handle callback untuk help message pagination
        elif callback_data.startswith("help_page_"):
            await auth_handler.handle_help_pagination_callback(callback_query)
        # Handle callback untuk menutup help message
        elif callback_data.startswith("help_close_"):
            await auth_handler.handle_help_close_callback(callback_query)
        # Handle callback untuk page info (tidak melakukan apa-apa)
        elif callback_data == "page_info":
            await bot.answer_callback_query(callback_query.id)
        # Handle callback untuk logout confirmation (jika ada)
        elif callback_data.startswith("logout_"):
            await auth_handler.handle_logout_callback(callback_query)
        # Handle callback untuk edit profile
        elif callback_data == "edit_profile":
            await auth_handler.handle_edit_profile_callback(callback_query)
        # Handle callback untuk menutup profile
        elif callback_data == "close_profile":
            await auth_handler.handle_close_profile_callback(callback_query)
        # Handle callback untuk edit profile fields
        elif callback_data.startswith("edit_profile_"):
            await auth_handler.handle_edit_profile_field_callback(callback_query)
        # Handle callback untuk konfirmasi edit profile
        elif callback_data.startswith("edit_confirm_"):
            await auth_handler.handle_edit_confirmation_callback(callback_query)
        else:
            # Callback query tidak dikenal
            try:
                await bot.answer_callback_query(
                    callback_query.id,
                    text="❌ Perintah tidak dikenal.",
                    show_alert=True
                )
            except:
                pass

    return Response(status_code=200)

if __name__ == "__main__":
    import uvicorn

    logger.info("Memulai server webhook...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)