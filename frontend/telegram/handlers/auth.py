from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from typing import Dict, Any, List, Optional
import logging
import re
import json
import asyncio
from utils.auth import auth_client
from utils.keyboard import create_keyboard_from_list, create_confirmation_keyboard

logger = logging.getLogger(__name__)

class AuthHandler:
    """Handler untuk autentikasi dan manajemen user di Telegram bot"""

    def __init__(self, bot: Bot):
        self.bot = bot
        # Dictionary untuk menyimpan user session sementara
        self.user_sessions = {}
        # Dictionary untuk menyimpan registration state
        self.registration_states = {}
        # Dictionary untuk menyimpan login state
        self.login_states = {}
        # Dictionary untuk menyimpan logout confirmation state
        self.logout_confirmation_states = {}
        # Dictionary untuk tracking flow aktif user (booking, chat, dll)
        self.user_active_flows = {}

        # Kata kunci untuk deteksi natural language commands
        self.command_keywords = {
            'login': [
                'login', 'masuk', 'sign in', 'log in', 'mau login', 'ingin login',
                'saya mau login', 'saya ingin login', 'mau masuk', 'ingin masuk',
                'saya mau masuk', 'saya ingin masuk', 'aku mau login', 'aku ingin login'
            ],
            'register': [
                'register', 'daftar', 'registrasi', 'sign up', 'signup', 'mau daftar',
                'ingin daftar', 'saya mau daftar', 'saya ingin daftar', 'mau registrasi',
                'ingin registrasi', 'saya mau registrasi', 'saya ingin registrasi',
                'buat akun', 'mau buat akun', 'ingin buat akun', 'aku mau daftar', 'aku ingin daftar'
            ],
            'profile': [
                'profile', 'profil', 'akun saya', 'data saya', 'info saya',
                'lihat profil', 'lihat akun', 'cek profil', 'cek akun'
            ],
            'logout': [
                'logout', 'keluar', 'log out', 'sign out', 'mau logout', 'ingin logout',
                'saya mau logout', 'saya ingin logout', 'mau keluar', 'ingin keluar',
                'saya mau keluar', 'saya ingin keluar'
            ],
            'verify': [
                'verify'
            ],
            'resend': [
                'resend'
            ],
            'greeting': [
                'halo', 'hi', 'hai', 'osa', 'salam', 'om swastyastu',
                'selamat pagi', 'selamat siang', 'selamat sore', 'selamat malam'
            ],
            'help': [
                'help', 'bantuan', 'panduan', 'tutorial', 'petunjuk', 'instruksi',
                'mau bantuan', 'butuh bantuan', 'perlu bantuan', 'minta bantuan',
                'start', 'mulai', 'fitur apa', 'menu bantuan', 'cara pakai',
                'cara menggunakan', 'gimana pakai', 'bagaimana menggunakan'
            ],
            'newchat': [
                'new chat', 'newchat', 'chat baru', 'percakapan baru', 'mulai chat baru',
                'start new chat', 'buat chat baru', 'mau chat baru', 'ingin chat baru',
                'saya mau chat baru', 'saya ingin chat baru', 'mulai percakapan baru'
            ],
            'deletechat': [
                'delete chat', 'deletechat', 'hapus chat', 'hapus percakapan',
                'hapus riwayat', 'clear chat', 'bersihkan chat', 'reset chat',
                'mau hapus chat', 'ingin hapus chat', 'saya mau hapus chat'
            ]
        }

    def detect_command_from_text(self, message_text: str) -> Optional[str]:
        """
        Deteksi command dari natural language text

        Args:
            message_text (str): Pesan dari user

        Returns:
            Optional[str]: Command yang terdeteksi atau None
        """
        message_lower = message_text.lower().strip()

        # Cek setiap kategori command
        for command, keywords in self.command_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return command

        return None

    def is_user_in_active_flow(self, user_id: int) -> bool:
        """
        Cek apakah user sedang dalam flow aktif (registrasi, login, booking, dll)

        Args:
            user_id (int): Telegram user ID

        Returns:
            bool: True jika user sedang dalam flow aktif
        """
        # Cek flow registrasi
        if user_id in self.registration_states:
            return True

        # Cek flow login
        if user_id in self.login_states:
            return True

        # Cek flow logout confirmation
        if user_id in self.logout_confirmation_states:
            return True

        # Cek flow aktif lainnya (booking, chat dengan agen, dll)
        if user_id in self.user_active_flows:
            return True

        return False

    def is_greeting_message(self, message_text: str) -> bool:
        """
        Cek apakah pesan adalah salam pembuka dengan deteksi yang lebih ketat

        Args:
            message_text (str): Pesan dari user

        Returns:
            bool: True jika pesan adalah salam pembuka
        """
        message_lower = message_text.lower().strip()

        # Untuk kata pendek, hanya deteksi jika itu satu-satunya kata
        short_greetings = ['hi', 'hai', 'halo', 'osa']
        if message_lower in short_greetings:
            return True

        # Untuk salam panjang, cek jika ada di 3 kata pertama
        long_greetings = ['selamat pagi', 'selamat siang', 'selamat sore', 'selamat malam', 'om swastyastu']
        words = message_lower.split()
        first_three_words = ' '.join(words[:3])

        for greeting in long_greetings:
            if greeting in first_three_words:
                return True

        # Cek kata 'salam' di awal pesan
        if words and words[0] == 'salam':
            return True

        return False

    async def handle_natural_language_command(self, chat_id: int, user_id: int, message_text: str) -> bool:
        """
        Handle natural language command detection berdasarkan kata kunci
        """
        try:
            # Check for edit profile input first (higher priority)
            if hasattr(self, 'edit_profile_states') and user_id in self.edit_profile_states:
                return await self.handle_edit_profile_input(chat_id, user_id, message_text)
                
            # Deteksi greeting (sapaan) terlebih dahulu
            if self.is_greeting_message(message_text):
                await self.handle_greeting_command(chat_id, user_id)
                return True
                
            # Deteksi natural language command berdasarkan kata kunci
            detected_command = self.detect_command_from_text(message_text)
            if not detected_command:
                return False  # Bukan natural language command
                
            # Handle command yang terdeteksi
            if detected_command == 'login':
                await self.handle_login_command(chat_id, user_id)
                return True
            elif detected_command == 'register':
                await self.handle_register_command(chat_id, user_id)
                return True
            elif detected_command == 'profile':
                await self.handle_profile_command(chat_id, user_id)
                return True
            elif detected_command == 'logout':
                await self.handle_logout_command(chat_id, user_id)
                return True
            elif detected_command == 'verify':
                await self.handle_verify_command(chat_id, user_id)
                return True
            elif detected_command == 'resend':
                await self.handle_resend_verification(chat_id, user_id)
                return True
            elif detected_command == 'help':
                await self.handle_help_command(chat_id, user_id)
                return True
            elif detected_command == 'newchat':
                # Import fungsi dari bot.py
                from bot import handle_newchat_command
                # Dapatkan user first name dari session atau default
                user_session = self.user_sessions.get(user_id, {})
                user_data = user_session.get("user_data", {})
                user_first_name = user_data.get("nama", "User")
                await handle_newchat_command(chat_id, user_id, user_first_name)
                return True
                
            return False  # Default fallback
            
        except Exception as e:
            logger.error(f"Error saat handle natural language command: {e}")
            return False

    async def handle_greeting_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle greeting messages dengan animasi loading
        """
        try:
            # Kirim loading message dengan animasi
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text="⏳ Memulai percakapan..."
            )

            # Import fungsi animasi dari bot.py
            from bot import animate_loading_with_context

            # Mulai animasi loading
            animation_task = asyncio.create_task(animate_loading_with_context(
                chat_id, loading_msg.message_id, "Memulai percakapan"
            ))

            # Biarkan animasi berjalan selama 1.5 detik untuk UX yang baik
            await asyncio.sleep(1.5)

            # Stop animasi
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass

            # Hapus loading message
            await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

            # Cek status authentication
            is_authenticated = await self.is_user_authenticated(user_id)

            if is_authenticated:
                # User sudah login
                session = self.user_sessions.get(user_id, {})
                user_data = session.get("user_data", {})
                nama = user_data.get("nama", "User")

                greeting_message = (
                    f"👋 Halo {nama}! Selamat datang kembali!\n\n"
                    f"Ada yang bisa saya bantu untuk perjalanan Anda hari ini? ✈️😊"
                )
            else:
                # User belum login
                greeting_message = (
                    "👋 Halo! Selamat datang di Travel Agent Bot!\n\n"
                    "🔐 Untuk menggunakan layanan kami, silakan:\n"
                    "📝 /register - Registrasi akun baru\n"
                    "🔑 /login - Login dengan akun\n\n"
                    "Setelah login, Anda bisa langsung chat dengan Agen Travel AI!"
                )

            await self.bot.send_message(
                chat_id=chat_id,
                text=greeting_message,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error saat handle greeting command: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="👋 Halo! Ada yang bisa saya bantu?"
            )

    async def handle_help_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle help command - tampilkan menu bantuan
        """
        try:
            # Cek status authentication
            is_authenticated = await self.is_user_authenticated(user_id)

            if is_authenticated:
                # User sudah login - kirim help dengan paginasi
                session = self.user_sessions.get(user_id, {})
                user_data = session.get("user_data", {})
                nama = user_data.get("nama", "User")

                await self.send_paginated_help_message(chat_id, user_id, nama, is_authenticated=True)
            else:
                # User belum login - kirim help dengan paginasi
                await self.send_paginated_help_message(chat_id, user_id, "User", is_authenticated=False)

            # help_message sudah tidak digunakan karena menggunakan paginasi
            pass

        except Exception as e:
            logger.error(f"Error saat handle help command: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat menampilkan bantuan."
            )

    async def send_paginated_help_message(self, chat_id, user_id, nama, is_authenticated=True, page=1):
        """Mengirim help message dengan paginasi."""
        try:
            if is_authenticated:
                # Data halaman untuk user yang sudah login
                help_pages = [
                    {
                        "title": f"📖 *Panduan Agen Travel AI*",
                        "content": (
                            f"👋 Halo {nama}!\n\n"
                            f"_Proyek Tugas Akhir Sistem Multi-Agen Travel_\n\n"
                            "🤖 *Agen Travel AI siap membantu:*\n"
                            "🏨 Hotel • ✈️ Penerbangan • 🏝️ Tur • 📞 Support\n\n"
                            "💬 *Coba fitur dengan ketik:*\n"
                            "• \"Carikan hotel di Ubud tanggal 25 Juni\"\n"
                            "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                            "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\""
                        )
                    },
                    {
                        "title": f"📖 *Panduan Agen Travel AI*",
                        "content": (
                            "_Daftar layanan dan fitur yang tersedia_\n\n"
                            "🔍 *Pencarian & Pemesanan:*\n"
                            "🏠 *Hotel* - Data hotel di database\n"
                            "🛫 *Penerbangan* - Data penerbangan di database\n"
                            "🏝️ *Paket Tur* - Data paket tur di database\n\n"
                            "🚀 *Fitur Plus - MCP Tools:*\n\n"
                            "🗓️ *Booking.com*\n"
                            "• \"Gunakan Booking.com untuk hotel di Ubud\"\n"
                            "• \"Cari penerbangan dengan Booking.com\"\n\n"
                            "🏠 *Airbnb*\n"
                            "• \"Pakai Airbnb untuk villa di Ubud\"\n"
                            "• \"Cari homestay dengan Airbnb\"\n\n"
                            "🦉 *TripAdvisor*\n"
                            "• \"Review hotel dengan TripAdvisor\"\n"
                            "• \"Atraksi wisata di TripAdvisor\"\n\n"
                            "🌐 *Web Search*\n"
                            "• \"Berapa kurs USD hari ini?\"\n"
                            "• \"Artikel tips wisata Bali\""
                        )
                    },
                    {
                        "title": f"📖 *Panduan Agen Travel AI*",
                        "content": (
                            "_Daftar perintah yang tersedia dan tips_\n\n"
                            "⚙️ *Perintah & Tips:*\n\n"
                            "👤 `/profile` - Lihat & edit profil Anda\n"
                            "💬 `/newchat` - Mulai percakapan baru\n"
                            "🗑️ `/deletechat` - Hapus riwayat percakapan\n"
                            "✅ `/verify` - Verifikasi email\n"
                            "🚪 `/logout` - Keluar dari akun\n\n"
                            "🎯 *Pro Tips:*\n"
                            "• Sebutkan \"MCP\" untuk data real-time\n"
                            "• Sertakan tanggal untuk hasil akurat\n"
                            "• Gunakan bahasa sehari-hari\n"
                            "• Contoh: \"Carikan hotel di Ubud untuk 30 Juni 2 orang\"\n"
                            "• Contoh: \"Berapa kurs USD hari ini?\"\n\n"
                            "📖 Gunakan `/help` untuk bantuan dan panduan lengkap fitur"
                        )
                    }
                ]
            else:
                # Data halaman untuk user yang belum login
                help_pages = [
                    {
                        "title": "📖 *Panduan Agen Travel AI*",
                        "content": (
                            "_Cara memulai menggunakan layanan_\n\n"
                            "🔐 *Mulai sekarang:*\n"
                            "📝 /register - Daftar akun baru\n"
                            "🔑 /login - Masuk dengan akun\n\n"
                            "🤖 *Layanan tersedia:*\n"
                            "🏨 Hotel • ✈️ Penerbangan • 🏝️ Tur • 📞 Support\n\n"
                            "💬 *Setelah login, coba ketik:*\n"
                            "• \"Carikan hotel di Ubud tanggal 25 Juni\"\n"
                            "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                            "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\""
                        )
                    },
                    {
                        "title": "📖 *Panduan Agen Travel AI*",
                        "content": (
                            "_Fitur-fitur yang tersedia setelah login_\n\n"
                            "🔍 *Pencarian & Pemesanan:*\n"
                            "🏠 *Hotel* - Data hotel di database\n"
                            "🛫 *Penerbangan* - Data penerbangan di database\n"
                            "🏝️ *Paket Tur* - Data paket tur di database\n\n"
                            "🚀 *Fitur Plus - MCP Tools:*\n\n"
                            "🗓️ *Booking.com* - Data hotel real-time\n"
                            "🏠 *Airbnb* - Villa & homestay unik\n"
                            "🦉 *TripAdvisor* - Review & rating terkini\n"
                            "🌐 *Web Search* - Kurs USD & artikel travel\n\n"
                            "💬 *Contoh percakapan setelah login:*\n"
                            "• \"Carikan hotel di Bali untuk 30 Juni\"\n"
                            "• \"Cari penerbangan Denpasar-Jakarta\"\n"
                            "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n"
                            "• \"Berapa kurs USD hari ini?\"\n"
                            "• \"Gunakan Booking.com untuk hotel di Ubud\""
                        )
                    },
                    {
                        "title": "📖  *Panduan Agen Travel AI*",
                        "content": (
                            "_Cara registrasi dan verifikasi_\n\n"
                            "🎯 *Cara memulai:*\n\n"
                            "1️⃣ Ketik `/register` untuk membuat akun\n"
                            "2️⃣ Verifikasi email Anda\n"
                            "3️⃣ Mulai chat dengan agen AI\n\n"
                            "💡 *Tips:*\n"
                            "• Gunakan bahasa sehari-hari\n"
                            "• Sertakan tanggal untuk hasil akurat\n"
                            "• Kami siap membantu 24/7!\n\n"
                            "📖 `/help` untuk panduan dan fitur lengkap"
                        )
                    }
                ]

            # Validasi halaman
            if page < 1 or page > len(help_pages):
                page = 1

            current_page = help_pages[page - 1]

            # Buat keyboard navigasi dengan format baru: < > di atas, halaman di bawah
            keyboard = []

            # Baris 1: Navigation buttons
            nav_buttons = []
            # Previous button (circular)
            prev_page = len(help_pages) if page == 1 else page - 1
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"help_page_{prev_page}_{user_id}"))

            # Next button (circular)
            next_page = 1 if page == len(help_pages) else page + 1
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"help_page_{next_page}_{user_id}"))

            keyboard.append(nav_buttons)

            # Baris 2: Page indicator
            page_indicator = f"{page}/{len(help_pages)}"
            keyboard.append([InlineKeyboardButton(page_indicator, callback_data="page_info")])

            # Baris 3: Tombol tutup
            keyboard.append([InlineKeyboardButton("Tutup", callback_data=f"help_close_{user_id}")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Format pesan
            message_text = f"{current_page['title']}\n\n{current_page['content']}"

            await self.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending paginated help message: {e}")
            # Fallback ke pesan sederhana
            fallback_message = f"👋 Halo {nama}! Gunakan /start untuk memulai atau /register untuk membuat akun."
            await self.bot.send_message(chat_id=chat_id, text=fallback_message)

    async def handle_help_pagination_callback(self, callback_query):
        """Menangani callback untuk paginasi help message."""
        try:
            chat_id = callback_query.message.chat.id
            user_id = callback_query.from_user.id
            callback_data = callback_query.data

            # Parse callback data: help_page_{page}_{user_id}
            parts = callback_data.split("_")
            if len(parts) >= 3:
                page = int(parts[2])
                target_user_id = int(parts[3]) if len(parts) > 3 else user_id

                # Cek autentikasi user
                is_authenticated = await self.is_user_authenticated(target_user_id)

                if is_authenticated:
                    session = self.user_sessions.get(target_user_id, {})
                    user_data = session.get("user_data", {})
                    nama = user_data.get("nama", callback_query.from_user.first_name)
                else:
                    nama = callback_query.from_user.first_name

                # Data halaman berdasarkan status autentikasi
                if is_authenticated:
                    help_pages = [
                        {
                            "title": f"📖  *Panduan Agen Travel AI*",
                            "content": (
                                f"👋 Halo {nama}!\n\n"
                                f"_Proyek Tugas Akhir Sistem Multi-Agen Travel_\n\n"
                                "🤖 *Agen Travel AI siap membantu:*\n"
                                "🏨 Hotel • ✈️ Penerbangan • 🏝️ Tur • 📞 Support\n\n"
                                "💬 *Coba fitur dengan ketik:*\n"
                                "• \"Carikan hotel di Ubud tanggal 25 Juni\"\n"
                                "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                                "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\""
                            )
                        },
                        {
                            "title": f"📖 *Panduan Agen Travel AI*",
                            "content": (
                                "_Layanan dan fitur yang tersedia_\n\n"
                                "🔍 *Pencarian & Pemesanan:*\n"
                                "🏨  *Hotel* - Data hotel di database\n"
                                "🛫 *Penerbangan* - Data penerbangan di database\n"
                                "🏝️ *Paket Tur* - Data paket tur di database\n\n"
                                "🚀 *Fitur Plus - MCP Tools:*\n\n"
                                "🗓️ *Booking.com*\n"
                                "• \"Gunakan Booking.com untuk hotel di Ubud\"\n"
                                "• \"Cari penerbangan dengan Booking.com\"\n\n"
                                "🏠 *Airbnb*\n"
                                "• \"Pakai Airbnb untuk villa di Ubud\"\n"
                                "• \"Cari homestay dengan Airbnb\"\n\n"
                                "🦉 *TripAdvisor*\n"
                                "• \"Review hotel dengan TripAdvisor\"\n"
                                "• \"Atraksi wisata di TripAdvisor\"\n\n"
                                "🌐 *Web Search*\n"
                                "• \"Berapa kurs USD hari ini?\"\n"
                                "• \"Artikel tips wisata Bali\""
                            )
                        },
                        {
                            "title": f"📖 *Panduan Agen Travel AI*",
                            "content": (
                                "_Daftar perintah yang tersedia dan tips_\n\n"
                                "⚙️ *Perintah & Tips:*\n\n"
                                "👤 `/profile` - Lihat & edit profil Anda\n"
                                "💬 `/newchat` - Mulai percakapan baru\n"
                                "🗑️ `/deletechat` - Hapus riwayat percakapan\n"
                                "✅ `/verify` - Verifikasi email\n"
                                "🚪 `/logout` - Keluar dari akun\n\n"
                                "🎯 *Pro Tips:*\n"
                                "• Sebutkan \"MCP\" untuk data real-time\n"
                                "• Sertakan tanggal untuk hasil akurat\n"
                                "• Gunakan bahasa sehari-hari\n"
                                "• Contoh: \"Carikan hotel di Ubud untuk 30 Juni 2 orang\"\n"
                                "• Contoh: \"Berapa kurs USD hari ini?\"\n\n"
                                "📖 Gunakan `/help` untuk bantuan dan panduan lengkap"
                            )
                        }
                    ]
                else:
                    help_pages = [
                        {
                            "title": "📖 *Panduan Agen Travel AI*",
                            "content": (
                                "_Cara memulai menggunakan layanan_\n\n"
                                "🔐 *Mulai sekarang:*\n"
                                "📝 /register - Daftar akun baru\n"
                                "🔑 /login - Masuk dengan akun\n\n"
                                "🤖 *Layanan tersedia:*\n"
                                "🏨 Hotel • ✈️ Penerbangan • 🏝️ Tur • 📞 Support\n\n"
                                "💬 *Setelah login, coba ketik:*\n"
                                "• \"Carikan hotel di Ubud tanggal 25 Juni\"\n"
                                "• \"Penerbangan Denpasar-Jakarta tanggal 26 Juni\"\n"
                                "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\""
                            )
                        },
                        {
                            "title": "📖 *Panduan Agen Travel AI*",
                            "content": (
                                "_Fitur-fitur yang tersedia setelah login_\n\n"
                                "🔍 *Pencarian & Pemesanan:*\n"
                                "🏨 *Hotel* - Data hotel di database\n"
                                "🛫 *Penerbangan* - Data penerbangan di database\n"
                                "🏝️ *Paket Tur* - Data paket tur di database\n\n"
                                "🚀 *Fitur Plus - MCP Tools:*\n\n"
                                "🗓️ *Booking.com* - Data hotel real-time\n"
                                "🏠 *Airbnb* - Villa & homestay unik\n"
                                "🦉 *TripAdvisor* - Review & rating terkini\n"
                                "🌐 *Web Search* - Kurs USD & artikel travel\n\n"
                                "💬 *Contoh percakapan setelah login:*\n"
                                "• \"Carikan hotel di Bali untuk 30 Juni\"\n"
                                "• \"Cari penerbangan Jakarta-Denpasar\"\n"
                                "• \"Paket tur Kintamani tanggal 27 Juni 2 orang\"\n"
                                "• \"Berapa kurs USD hari ini?\"\n"
                                "• \"Gunakan Booking.com untuk hotel di Ubud\""
                            )
                        },
                        {
                            "title": "📖 *Panduan Agen Travel AI*",
                            "content": (
                                "_Cara registrasi dan verifikasi_\n\n"
                                "🎯 *Cara memulai:*\n\n"
                                "1️⃣ Ketik `/register` untuk membuat akun\n"
                                "2️⃣ Verifikasi email Anda\n"
                                "3️⃣ Mulai chat dengan agen AI\n\n"
                                "💡 *Tips:*\n"
                                "• Gunakan bahasa sehari-hari\n"
                                "• Sertakan tanggal untuk hasil akurat\n"
                                "• Sebutkan \"MCP\" untuk fitur plus\n"
                                "📖 `/help` untuk panduan lengkap"
                            )
                        }
                    ]

                # Validasi halaman
                if page < 1 or page > len(help_pages):
                    page = 1

                current_page = help_pages[page - 1]

                # Buat keyboard navigasi dengan format baru: < > di atas, halaman di bawah
                keyboard = []

                # Baris 1: Navigation buttons
                nav_buttons = []
                # Previous button (circular)
                prev_page = len(help_pages) if page == 1 else page - 1
                nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"help_page_{prev_page}_{target_user_id}"))

                # Next button (circular)
                next_page = 1 if page == len(help_pages) else page + 1
                nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"help_page_{next_page}_{target_user_id}"))

                keyboard.append(nav_buttons)

                # Baris 2: Page indicator
                page_indicator = f"{page}/{len(help_pages)}"
                keyboard.append([InlineKeyboardButton(page_indicator, callback_data="page_info")])

                # Baris 3: Tombol tutup
                keyboard.append([InlineKeyboardButton("Tutup", callback_data=f"help_close_{target_user_id}")])

                reply_markup = InlineKeyboardMarkup(keyboard)

                # Format pesan
                message_text = f"{current_page['title']}\n\n{current_page['content']}"

                # Edit pesan yang ada
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id,
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )

            # Jawab callback query
            await self.bot.answer_callback_query(callback_query.id)

        except Exception as e:
            logger.error(f"Error handling help pagination callback: {e}")
            try:
                await self.bot.answer_callback_query(
                    callback_query.id,
                    text="❌ Terjadi kesalahan saat navigasi.",
                    show_alert=True
                )
            except:
                pass

    async def handle_help_close_callback(self, callback_query):
        """Menangani callback untuk menutup help message."""
        try:
            chat_id = callback_query.message.chat.id
            user_id = callback_query.from_user.id
            callback_data = callback_query.data

            # Parse callback data: help_close_{user_id}
            parts = callback_data.split("_")
            if len(parts) >= 3:
                target_user_id = int(parts[2]) if len(parts) > 2 else user_id

                # Verifikasi bahwa user yang menekan tombol adalah pemilik help message
                if user_id == target_user_id:
                    # Hapus pesan help
                    await self.bot.delete_message(
                        chat_id=chat_id,
                        message_id=callback_query.message.message_id
                    )

                    # Kirim pesan konfirmasi singkat yang akan hilang otomatis
                    confirmation_msg = await self.bot.send_message(
                        chat_id=chat_id,
                        text="✅ Pesan bantuan ditutup"
                    )

                    # Hapus pesan konfirmasi setelah 2 detik
                    import asyncio
                    asyncio.create_task(self._delete_message_after_delay(chat_id, confirmation_msg.message_id, 2))
                else:
                    # User bukan pemilik, tampilkan peringatan
                    await self.bot.answer_callback_query(
                        callback_query.id,
                        text="❌ Anda tidak dapat menutup pesan bantuan orang lain.",
                        show_alert=True
                    )
                    return

            # Jawab callback query
            await self.bot.answer_callback_query(callback_query.id)

        except Exception as e:
            logger.error(f"Error handling help close callback: {e}")
            try:
                await self.bot.answer_callback_query(
                    callback_query.id,
                    text="❌ Terjadi kesalahan saat menutup bantuan.",
                    show_alert=True
                )
            except:
                pass

    async def _delete_message_after_delay(self, chat_id, message_id, delay_seconds):
        """Helper function untuk menghapus pesan setelah delay tertentu."""
        import asyncio
        try:
            await asyncio.sleep(delay_seconds)
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.debug(f"Gagal menghapus pesan konfirmasi: {e}")



    async def handle_register_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle command /register - memulai proses registrasi step-by-step
        """
        try:
            # Cek apakah user sudah login
            if await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Anda sudah terdaftar dan login. Gunakan /profile untuk melihat profil Anda."
                )
                return

            # Mulai proses registrasi
            self.registration_states[user_id] = {
                "step": "nama",
                "data": {}
            }

            welcome_message = (
                "📝 *Selamat datang di proses registrasi!*\n\n"
                "Saya akan membantu Anda mendaftar step by step.\n"
                "Anda bisa ketik /cancel kapan saja untuk membatalkan.\n\n"
                "👤 *Langkah 1/5*\n"
                "Silakan masukkan *nama lengkap* Anda:"
            )

            await self.bot.send_message(
                chat_id=chat_id,
                text=welcome_message,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error saat handle register command: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat memulai registrasi. Silakan coba lagi."
            )

    async def handle_registration_step(self, chat_id: int, user_id: int, message_text: str) -> bool:
        """
        Handle step-by-step registration process

        Returns:
            bool: True jika pesan diproses sebagai bagian registrasi, False jika bukan
        """
        # Cek apakah user sedang dalam proses registrasi
        if user_id not in self.registration_states:
            return False

        try:
            state = self.registration_states[user_id]
            step = state["step"]
            data = state["data"]

            # Handle cancel command
            if message_text.lower() in ['/cancel', 'cancel', 'batal']:
                del self.registration_states[user_id]
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Registrasi dibatalkan. Ketik /register untuk memulai lagi."
                )
                return True

            # Process each step
            if step == "nama":
                if len(message_text.strip()) < 2:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Nama harus minimal 2 karakter. Silakan masukkan nama lengkap Anda:"
                    )
                    return True

                data["nama"] = message_text.strip()
                state["step"] = "email"

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ Nama: {data['nama']}\n\n"
                        "📧 *Langkah 2/5*\n"
                        "Silakan masukkan *alamat email* Anda:"
                    ),
                    parse_mode="Markdown"
                )

            elif step == "email":
                # Validasi email sederhana
                if "@" not in message_text or "." not in message_text:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Format email tidak valid. Silakan masukkan email yang benar (contoh: nama@email.com):"
                    )
                    return True

                data["email"] = message_text.strip().lower()
                state["step"] = "password"

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ Email: {data['email']}\n\n"
                        "🔒 *Langkah 3/5*\n"
                        "Silakan buat *password* Anda (minimal 6 karakter):"
                    ),
                    parse_mode="Markdown"
                )

            elif step == "password":
                if len(message_text) < 6:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Password harus minimal 6 karakter. Silakan masukkan password yang lebih kuat:"
                    )
                    return True

                data["password"] = message_text
                state["step"] = "telepon"

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "✅ Password berhasil dibuat\n\n"
                        "📱 *Langkah 4/5*\n"
                        "Silakan masukkan *nomor telepon* Anda (atau ketik 'skip' untuk melewati):"
                    ),
                    parse_mode="Markdown"
                )

            elif step == "telepon":
                if message_text.lower() == 'skip':
                    data["telepon"] = None
                else:
                    # Validasi nomor telepon sederhana
                    cleaned_phone = ''.join(filter(str.isdigit, message_text))
                    if len(cleaned_phone) < 10:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text="❌ Nomor telepon harus minimal 10 digit. Silakan masukkan nomor yang benar (atau 'skip'):"
                        )
                        return True
                    data["telepon"] = message_text.strip()

                state["step"] = "alamat"

                telepon_text = data["telepon"] if data["telepon"] else "Dilewati"
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ Telepon: {telepon_text}\n\n"
                        "🏠 *Langkah 5/5*\n"
                        "Silakan masukkan *alamat* Anda (atau ketik 'skip' untuk melewati):"
                    ),
                    parse_mode="Markdown"
                )

            elif step == "alamat":
                if message_text.lower() == 'skip':
                    data["alamat"] = None
                else:
                    data["alamat"] = message_text.strip()

                # Proses registrasi
                await self._process_registration(chat_id, user_id, data)

            return True

        except Exception as e:
            logger.error(f"Error saat handle registration step: {e}")
            # Cleanup state on error
            if user_id in self.registration_states:
                del self.registration_states[user_id]
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat registrasi. Silakan ketik /register untuk memulai lagi."
            )
            return True

    async def _process_registration(self, chat_id: int, user_id: int, data: Dict[str, Any]) -> None:
        """
        Process final registration with collected data
        """
        try:
            # Tampilkan ringkasan data
            alamat_text = data["alamat"] if data["alamat"] else "Tidak diisi"
            telepon_text = data["telepon"] if data["telepon"] else "Tidak diisi"

            summary_message = (
                "📋 *Ringkasan Data Registrasi*\n\n"
                f"👤 Nama: {data['nama']}\n"
                f"📧 Email: {data['email']}\n"
                f"📱 Telepon: {telepon_text}\n"
                f"🏠 Alamat: {alamat_text}"
            )

            await self.bot.send_message(
                chat_id=chat_id,
                text=summary_message,
                parse_mode="Markdown"
            )

            # Kirim loading message dengan animasi untuk proses registrasi (di bawah ringkasan)
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text="⏳ Sedang memproses registrasi..."
            )

            # Import fungsi animasi dari bot.py
            import asyncio
            from bot import animate_loading_with_context

            # Mulai animasi loading untuk registrasi
            animation_task = asyncio.create_task(animate_loading_with_context(
                chat_id, loading_msg.message_id, "Sedang memproses registrasi"
            ))

            try:
                # Registrasi ke backend
                result = await auth_client.register_user(
                    nama=data["nama"],
                    email=data["email"],
                    password=data["password"],
                    telepon=data["telepon"],
                    alamat=data["alamat"],
                    telegram_id=str(user_id)
                )

                # Biarkan animasi berjalan minimal 2 detik untuk UX yang baik
                await asyncio.sleep(2)

            finally:
                # Stop animasi registrasi
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass

                # Hapus pesan loading registrasi saja (biarkan ringkasan tetap ada)
                await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

            # Cleanup registration state
            if user_id in self.registration_states:
                del self.registration_states[user_id]

            if result.get("success"):
                # Registrasi berhasil
                user_data = result.get("user", {})
                access_token = result.get("access_token")

                # Simpan session
                self.user_sessions[user_id] = {
                    "authenticated": True,
                    "user_data": user_data,
                    "access_token": access_token
                }

                # Pesan gabungan: Registrasi berhasil + Email verifikasi dikirim
                success_message = (
                    f"🎉 *Registrasi berhasil!*\n\n"
                    f"Selamat datang, {data['nama']}!\n"
                    f"📧 Email: {data['email']}\n"
                    f"📱 Telegram ID: {user_id}\n\n"
                    f"Akun Anda telah berhasil dibuat.\n\n"
                    f"📬 *Email Verifikasi Dikirim!*\n\n"
                    f"Email verifikasi telah dikirim ke:\n"
                    f"📧 {data['email']}\n\n"
                    f"⚠️ Anda perlu verifikasi email sebelum dapat menggunakan layanan kami.\n"
                    f"💡 Gunakan /verify untuk cek status verifikasi."
                )

                success_msg = await self.bot.send_message(
                    chat_id=chat_id,
                    text=success_message,
                    parse_mode="Markdown"
                )

                # Callback effect di background - edit pesan success setelah 30 detik
                async def callback_edit():
                    await asyncio.sleep(30)
                    final_success_message = (
                        f"🎉 *Registrasi berhasil!*\n\n"
                        f"📬 *Email Verifikasi Dikirim!*"
                    )
                    try:
                        await self.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=success_msg.message_id,
                            text=final_success_message,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.warning(f"Gagal mengedit pesan success: {e}")

                # Jalankan callback edit di background tanpa menunggu
                asyncio.create_task(callback_edit())

                logger.info(f"User {user_id} berhasil registrasi dengan email {data['email']}")

            else:
                # Registrasi gagal
                error_message = result.get("message", "Registrasi gagal")
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"❌ *Registrasi gagal!*\n\n"
                        f"{error_message}\n\n"
                        f"Silakan ketik /register untuk mencoba lagi."
                    ),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error saat process registration: {e}")
            # Cleanup state on error
            if user_id in self.registration_states:
                del self.registration_states[user_id]
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat memproses registrasi. Silakan ketik /register untuk mencoba lagi."
            )
    

    
    async def handle_profile_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle command /profile - lihat profil user
        """
        try:
            # Cek apakah user sudah login (menggunakan Redis check)
            if not await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "❌ Anda belum login.\n\n"
                        "Gunakan /register untuk registrasi atau /login untuk masuk."
                    )
                )
                return

            # Ambil session setelah Redis check (sudah di-restore jika ada)
            session = self.user_sessions.get(user_id, {})
            user_data = session.get("user_data", {})

            # Format last_login jika ada
            last_login_text = "Belum tersedia"
            if user_data.get('last_login'):
                try:
                    from datetime import datetime
                    import pytz

                    # Parse last_login (bisa berupa string ISO atau datetime object)
                    last_login = user_data.get('last_login')
                    if isinstance(last_login, str):
                        # Parse ISO string, handle berbagai format
                        if last_login.endswith('Z'):
                            last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                        elif '+' in last_login or last_login.endswith('00:00'):
                            last_login_dt = datetime.fromisoformat(last_login)
                        else:
                            # Assume UTC jika tidak ada timezone info
                            last_login_dt = datetime.fromisoformat(last_login).replace(tzinfo=pytz.UTC)
                    else:
                        last_login_dt = last_login

                    # Convert ke timezone Indonesia (WITA - Asia/Makassar)
                    wita_tz = pytz.timezone('Asia/Makassar')
                    last_login_wita = last_login_dt.astimezone(wita_tz)

                    # Format tanggal yang user-friendly dalam Bahasa Indonesia
                    months_id = {
                        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
                    }

                    day = last_login_wita.day
                    month = months_id[last_login_wita.month]
                    year = last_login_wita.year
                    time = last_login_wita.strftime("%H:%M")

                    last_login_text = f"{day} {month} {year}, {time} WITA"

                except Exception as e:
                    logger.warning(f"Error formatting last_login: {e}")
                    last_login_text = "Format tidak valid"

            profile_message = (
                f"👤 *Profil Anda*\n\n"
                f"📛 Nama: {user_data.get('nama', 'N/A')}\n"
                f"📧 Email: {user_data.get('email', 'N/A')}\n"
                f"📱 Telepon: {user_data.get('telepon', 'Belum diisi')}\n"
                f"🏠 Alamat: {user_data.get('alamat', 'Belum diisi')}\n"
                f"🆔 Telegram ID: {user_data.get('telegram_id', 'N/A')}\n"
                f"🕐 Login Terakhir: {last_login_text}\n"
                f"✅ Status: {'Terverifikasi' if user_data.get('is_verified') else 'Belum terverifikasi'}\n\n"
                f"🚪 /logout - Keluar dari akun"
            )
            
            # Buat inline keyboard untuk edit profile dan close message
            keyboard = [
                [
                    InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile"),
                    InlineKeyboardButton("❌ Tutup", callback_data="close_profile")
                ]
            ]
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=profile_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error saat handle edit profile callback: {e}")
            await self.bot.answer_callback_query(callback_query.id, text="Terjadi kesalahan")
    
    async def handle_edit_profile_field_callback(self, callback_query):
        """
        Handle callback untuk edit field profile tertentu
        """
        try:
            chat_id = callback_query.message.chat_id
            message_id = callback_query.message.message_id
            user_id = callback_query.from_user.id
            data = callback_query.data
            
            # Answer the callback query
            await self.bot.answer_callback_query(callback_query.id)
            
            # Inisialisasi state untuk edit profile jika belum ada
            if not hasattr(self, 'edit_profile_states'):
                self.edit_profile_states = {}
            
            if data == "edit_profile_cancel":
                # Hapus pesan pemilihan field
                await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Edit profil dibatalkan."
                )
                
                # Hapus state jika ada
                if user_id in self.edit_profile_states:
                    del self.edit_profile_states[user_id]
                    
                return
            
            # Ambil field yang akan diedit
            field = data.replace("edit_profile_", "")
            
            # Set state untuk mengingat field yang sedang diedit
            self.edit_profile_states[user_id] = {
                "field": field,
                "chat_id": chat_id,
                "message_id": message_id,
                "step": "input"  # Track langkah edit: input -> confirm -> save
            }
            
            field_labels = {
                "nama": "Nama",
                "telepon": "Telepon",
                "alamat": "Alamat"
            }
            
            # Hapus pesan pemilihan field
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Kirim pesan untuk meminta input field baru
            prompt_message = await self.bot.send_message(
                chat_id=chat_id,
                text=f"✏️ *Edit {field_labels[field]}*\n\nSilakan masukkan {field_labels[field].lower()} baru Anda:",
                parse_mode="Markdown"
            )
            
            # Simpan message_id prompt untuk dihapus nantinya
            self.edit_profile_states[user_id]["prompt_message_id"] = prompt_message.message_id
            
        except Exception as e:
            logger.error(f"Error saat handle edit profile field callback: {e}")
            await self.bot.answer_callback_query(callback_query.id, text="Terjadi kesalahan")
    
    async def handle_edit_profile_input(self, chat_id: int, user_id: int, input_text: str) -> bool:
        """
        Handle input dari user untuk edit profile
        """
        # Cek apakah user sedang dalam mode edit profile
        if not hasattr(self, 'edit_profile_states') or user_id not in self.edit_profile_states:
            return False
        
        try:
            # Ambil state
            state = self.edit_profile_states[user_id]
            field = state["field"]
            step = state.get("step", "input")
            
            # Field labels untuk tampilan yang lebih baik
            field_labels = {
                "nama": "Nama",
                "telepon": "Telepon",
                "alamat": "Alamat"
            }
            
            # Jika tahap input pertama, tampilkan konfirmasi
            if step == "input":
                # Simpan nilai input untuk digunakan nanti
                self.edit_profile_states[user_id]["new_value"] = input_text
                self.edit_profile_states[user_id]["step"] = "confirm"
                
                # Hapus pesan prompt sebelumnya
                if "prompt_message_id" in state:
                    try:
                        await self.bot.delete_message(chat_id=chat_id, message_id=state["prompt_message_id"])
                    except Exception:
                        pass
                
                # Tampilkan konfirmasi dengan nilai baru
                confirm_message = (
                    f"✏️ *Edit {field_labels[field]}*\n\n"
                    f"Nilai baru: {input_text}\n\n"
                    f"Apakah Anda yakin ingin mengubah {field_labels[field].lower()} Anda?"
                )
                
                # Buat keyboard konfirmasi
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Ya", callback_data="edit_confirm_yes"),
                        InlineKeyboardButton("❌ Tidak", callback_data="edit_confirm_no")
                    ]
                ]
                
                # Kirim pesan konfirmasi
                confirm_msg = await self.bot.send_message(
                    chat_id=chat_id,
                    text=confirm_message,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Simpan message_id konfirmasi
                self.edit_profile_states[user_id]["confirm_message_id"] = confirm_msg.message_id
                
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error saat handle edit profile input: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat memproses input."
            )
            
            # Bersihkan state
            if user_id in self.edit_profile_states:
                del self.edit_profile_states[user_id]
                
            return True
    
    async def handle_edit_confirmation_callback(self, callback_query):
        """
        Handle callback untuk konfirmasi perubahan profile
        """
        try:
            chat_id = callback_query.message.chat_id
            message_id = callback_query.message.message_id
            user_id = callback_query.from_user.id
            data = callback_query.data
            
            # Answer the callback query
            await self.bot.answer_callback_query(callback_query.id)
            
            # Cek apakah user masih dalam mode edit profile
            if not hasattr(self, 'edit_profile_states') or user_id not in self.edit_profile_states:
                await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Sesi edit telah berakhir."
                )
                return
            
            # Ambil state
            state = self.edit_profile_states[user_id]
            field = state.get("field")
            new_value = state.get("new_value", "")
            
            # Hapus pesan konfirmasi terlebih dahulu
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Proses berdasarkan pilihan user
            if data == "edit_confirm_yes":
                # Proses update profile
                await self.save_profile_changes(chat_id, user_id, field, new_value)
            else:
                # Kirim pesan batal
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Perubahan dibatalkan."
                )
                
                # Bersihkan state
                del self.edit_profile_states[user_id]
                
        except Exception as e:
            logger.error(f"Error saat handle edit confirmation callback: {e}")
            await self.bot.answer_callback_query(callback_query.id, text="Terjadi kesalahan")
            
    async def save_profile_changes(self, chat_id: int, user_id: int, field: str, new_value: str):
        """
        Menyimpan perubahan profile ke database
        """
        try:
            # Kirim loading message
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text=f"⏳ Menyimpan {field} baru..."
            )
            
            try:
                # Update profile menggunakan auth_client dengan telegram_id
                result = await auth_client.update_user_profile(
                    telegram_id=str(user_id),
                    **{field: new_value}
                )
                
                # Update session lokal
                if result.get("success"):
                    if user_id in self.user_sessions and "user_data" in self.user_sessions[user_id]:
                        self.user_sessions[user_id]["user_data"][field] = new_value
                    
                    # Success message
                    await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ {field.capitalize()} berhasil diperbarui!"
                    )
                    
                    # Tunjukkan profil yang sudah diupdate
                    await self.handle_profile_command(chat_id, user_id)
                else:
                    # Error message
                    await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ Gagal memperbarui {field}: {result.get('message', 'Terjadi kesalahan')}"
                    )
            except Exception as e:
                # Error message
                await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Terjadi kesalahan saat memperbarui profil: {str(e)}"
                )
            
            # Bersihkan state
            if user_id in self.edit_profile_states:
                del self.edit_profile_states[user_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat save profile changes: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat menyimpan perubahan."
            )
            
            # Bersihkan state
            if user_id in self.edit_profile_states:
                del self.edit_profile_states[user_id]
                
            return True
                
    async def handle_verify_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle command /verify - cek dan refresh status verifikasi email
        """
        try:
            # Cek apakah user sudah login
            if not await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "❌ Anda belum login.\n\n"
                        "Gunakan /register untuk registrasi atau /login untuk masuk."
                    )
                )
                return

            # Kirim loading message dengan animasi
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text="⏳ Mengecek status verifikasi..."
            )

            # Import fungsi animasi dari bot.py
            import asyncio
            from bot import animate_loading_with_context

            # Mulai animasi loading
            animation_task = asyncio.create_task(animate_loading_with_context(
                chat_id, loading_msg.message_id, "Mengecek status verifikasi"
            ))

            try:
                # Refresh status verifikasi dari database
                refresh_result = await auth_client.refresh_verification_status(str(user_id))

                # Biarkan animasi berjalan minimal 1.5 detik untuk UX yang lebih baik
                await asyncio.sleep(1.5)

            finally:
                # Stop animasi
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass

                # Hapus loading message
                await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

            if refresh_result.get("success"):
                user_data = refresh_result.get("user", {})
                is_verified = refresh_result.get("is_verified", False)

                # Update session lokal juga
                if user_id in self.user_sessions:
                    self.user_sessions[user_id]["user_data"]["is_verified"] = is_verified

                if is_verified:
                    # User sudah terverifikasi
                    # Pesan 1: Email terverifikasi
                    success_message = (
                        "✅ *Email Terverifikasi!*\n\n"
                        f"🎉 Selamat! Email Anda sudah terverifikasi.\n"
                        f"📧 Email: {user_data.get('email', 'N/A')}"
                    )

                    success_msg = await self.bot.send_message(
                        chat_id=chat_id,
                        text=success_message,
                        parse_mode="Markdown"
                    )

                    # Callback effect di background - edit pesan 1 setelah 3 detik
                    async def callback_edit():
                        await asyncio.sleep(3)
                        final_success_message = "✅ *Email Terverifikasi!*"
                        try:
                            await self.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=success_msg.message_id,
                                text=final_success_message,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.warning(f"Gagal mengedit pesan success: {e}")

                    # Jalankan callback edit di background tanpa menunggu
                    asyncio.create_task(callback_edit())

                    # Pesan 2: Pembuka yang ramah
                    welcome_message = (
                        "Ada yang bisa saya bantu untuk perjalanan Anda hari ini? ✈️😊"
                    )

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=welcome_message
                    )
                else:
                    # User belum terverifikasi
                    pending_message = (
                        "⚠️ *Email Belum Terverifikasi*\n\n"
                        f"📧 Email: {user_data.get('email', 'N/A')}\n"
                        f"❌ Status: Belum terverifikasi\n\n"
                        f"📬 Silakan cek email Anda dan klik link verifikasi.\n\n"
                        f"💡 Belum menerima email? Gunakan /resend untuk kirim ulang."
                    )

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=pending_message,
                        parse_mode="Markdown"
                    )
            else:
                # Error saat refresh
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Gagal mengecek status verifikasi. Silakan coba lagi."
                )

        except Exception as e:
            logger.error(f"Error saat handle verify command: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat mengecek verifikasi. Silakan coba lagi."
            )

    async def handle_resend_verification(self, chat_id: int, user_id: int) -> None:
        """
        Handle resend verification email
        """
        try:
            # Cek apakah user sudah login
            if not await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "❌ Anda belum login.\n\n"
                        "Gunakan /register untuk registrasi atau /login untuk masuk."
                    )
                )
                return

            # Ambil data user
            session = self.user_sessions.get(user_id, {})
            user_data = session.get("user_data", {})

            # Cek apakah user sudah terverifikasi
            if user_data.get("is_verified", False):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Email Anda sudah terverifikasi. Tidak perlu kirim ulang."
                )
                return

            # Kirim loading message dengan animasi
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text="⏳ Mengirim ulang email verifikasi..."
            )

            # Import fungsi animasi dari bot.py
            import asyncio
            from bot import animate_loading_with_context

            # Mulai animasi loading
            animation_task = asyncio.create_task(animate_loading_with_context(
                chat_id, loading_msg.message_id, "Mengirim ulang email verifikasi"
            ))

            # Ambil access token dari session
            access_token = session.get("access_token")

            if not access_token:
                # Hapus loading message
                await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Token akses tidak ditemukan. Silakan login ulang."
                )
                return

            # Ambil user_id dari session
            user_data = session.get("user_data", {})
            user_db_id = user_data.get("id")

            if not user_db_id:
                # Hapus loading message
                await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Data user tidak lengkap. Silakan login ulang."
                )
                return

            # Jalankan API call dan animasi secara bersamaan untuk UX yang lebih baik
            try:
                # Kirim ulang email verifikasi via backend
                resend_result = await auth_client.resend_verification_email(access_token, user_db_id)

                # Biarkan animasi berjalan minimal 2 detik untuk pengalaman yang lebih baik
                await asyncio.sleep(2)

            finally:
                # Stop animasi
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass

            # Hapus loading message
            await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

            if resend_result.get("success"):
                # Berhasil kirim ulang
                success_message = (
                    "✅ *Email Verifikasi Dikirim Ulang!*\n\n"
                    f"📬 Email verifikasi telah dikirim ulang ke:\n"
                    f"📧 {user_data.get('email', 'N/A')}\n\n"
                    f"⏰ Silakan tunggu beberapa menit dan cek email Anda.\n"
                    f"📁 Jangan lupa cek folder spam/junk.\n\n"
                    f"💡 Setelah klik link verifikasi, gunakan /verify untuk refresh status."
                )

                success_msg = await self.bot.send_message(
                    chat_id=chat_id,
                    text=success_message,
                    parse_mode="Markdown"
                )

                # Callback effect di background - edit pesan success setelah 3 detik
                async def callback_edit():
                    await asyncio.sleep(3)
                    final_success_message = "✅ *Email Verifikasi Dikirim Ulang!*"
                    try:
                        await self.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=success_msg.message_id,
                            text=final_success_message,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.warning(f"Gagal mengedit pesan success: {e}")

                # Jalankan callback edit di background tanpa menunggu
                asyncio.create_task(callback_edit())
            else:
                # Gagal kirim ulang
                error_message = resend_result.get("message", "Gagal mengirim email")

                fail_message = (
                    "❌ *Gagal Kirim Ulang Email*\n\n"
                    f"📧 Email: {user_data.get('email', 'N/A')}\n"
                    f"⚠️ Error: {error_message}\n\n"
                    f"💡 Silakan coba lagi nanti atau hubungi customer service."
                )

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=fail_message,
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error saat handle resend verification: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat kirim ulang email. Silakan coba lagi."
            )

    async def handle_logout_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle command /logout - logout user dengan konfirmasi menggunakan inline keyboard
        """
        try:
            # Cek apakah user sudah login
            if not await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="ℹ️ Anda belum login."
                )
                return

            # Ambil data user untuk personalisasi pesan
            session = self.user_sessions.get(user_id, {})
            user_data = session.get("user_data", {})
            user_name = user_data.get("nama", "User")

            logger.info(f"Logout confirmation requested for user {user_id}")

            # Buat inline keyboard untuk konfirmasi
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ya, Logout", callback_data=f"logout_confirm_{user_id}"),
                    InlineKeyboardButton("❌ Batal", callback_data=f"logout_cancel_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            confirmation_message = (
                f"🚪 *Konfirmasi Logout*\n\n"
                f"Halo {user_name}, apakah Anda yakin ingin keluar dari sistem?\n\n"
                f"💡 Tips: Setelah logout, Anda perlu login kembali untuk menggunakan layanan kami.\n\n"
                f"Silakan pilih:"
            )

            await self.bot.send_message(
                chat_id=chat_id,
                text=confirmation_message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error saat handle logout command: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat memproses logout."
            )

    async def handle_logout_confirmation(self, chat_id: int, user_id: int, message_text: str) -> bool:
        """
        Handle konfirmasi logout dari user (fallback untuk text confirmation)
        Sekarang logout menggunakan inline keyboard, tapi ini tetap ada untuk kompatibilitas

        Returns:
            bool: True jika pesan diproses sebagai konfirmasi logout, False jika bukan
        """
        # Sekarang logout menggunakan inline keyboard, jadi tidak ada state confirmation
        # Fungsi ini tetap ada untuk kompatibilitas jika ada yang masih menggunakan text
        # Suppress unused parameter warnings
        _ = chat_id, user_id, message_text
        return False

    async def _process_logout(self, chat_id: int, user_id: int) -> None:
        """
        Proses logout setelah konfirmasi
        """
        try:
            # Ambil data user untuk personalisasi pesan
            session = self.user_sessions.get(user_id, {})
            user_data = session.get("user_data", {})
            user_name = user_data.get("nama", "User")
            access_token = session.get("access_token")

            # Kirim loading message
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text="⏳ Memproses logout..."
            )

            # Logout dari backend (hapus session Redis)
            if access_token:
                try:
                    logout_result = await auth_client.logout_user(access_token)
                    if logout_result.get("success"):
                        logger.info(f"Successfully logged out user {user_id} from backend")
                    else:
                        logger.warning(f"Backend logout failed for user {user_id}: {logout_result.get('message', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Error calling backend logout for user {user_id}: {e}")

            # Hapus session lokal
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

            # Hapus loading message
            await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

            # Kirim pesan logout berhasil
            await self.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"👋 *Logout berhasil!*\n\n"
                    f"Sampai jumpa {user_name}! Anda telah keluar dari sistem.\n\n"
                    f"🔑 Gunakan /login untuk masuk kembali\n"
                    f"📝 Gunakan /register untuk membuat akun baru\n\n"
                    f"Terima kasih telah menggunakan layanan Agen Travel AI! 🙏"
                ),
                parse_mode="Markdown"
            )

            logger.info(f"User {user_id} ({user_name}) berhasil logout")

        except Exception as e:
            logger.error(f"Error saat process logout: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat logout. Silakan coba lagi."
            )

    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan session user
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            Optional[Dict]: Session data atau None jika tidak ada
        """
        return self.user_sessions.get(user_id)
    
    async def is_user_authenticated(self, user_id: int) -> bool:
        """
        Cek apakah user sudah terauthentikasi
        Mengecek Redis terlebih dahulu, kemudian memory lokal

        Args:
            user_id (int): Telegram user ID

        Returns:
            bool: True jika user sudah login
        """
        try:
            # Cek session di Redis terlebih dahulu
            session_result = await auth_client.check_user_session_by_telegram_id(str(user_id))

            if session_result.get("success") and session_result.get("session_found"):
                # Session ditemukan di Redis, restore ke memory lokal
                user_data = session_result.get("user", {})
                access_token = session_result.get("access_token")

                # Simpan ke memory lokal untuk performa
                self.user_sessions[user_id] = {
                    "authenticated": True,
                    "user_data": user_data,
                    "access_token": access_token
                }

                logger.info(f"Session restored dari Redis untuk user {user_id}")
                return True

            # Jika tidak ada di Redis, cek memory lokal
            session = self.user_sessions.get(user_id)
            return session and session.get("authenticated", False)

        except Exception as e:
            logger.error(f"Error saat cek authentication: {e}")
            # Fallback ke memory lokal jika ada error
            session = self.user_sessions.get(user_id)
            return session and session.get("authenticated", False)

    async def is_user_verified(self, user_id: int) -> bool:
        """
        Cek apakah user sudah terverifikasi email

        Args:
            user_id (int): Telegram user ID

        Returns:
            bool: True jika user sudah terverifikasi
        """
        try:
            # Pastikan user sudah authenticated dulu
            if not await self.is_user_authenticated(user_id):
                return False

            # Ambil data user dari session
            session = self.user_sessions.get(user_id, {})
            user_data = session.get("user_data", {})

            return user_data.get("is_verified", False)

        except Exception as e:
            logger.error(f"Error saat cek verification status: {e}")
            return False

    async def check_user_access(self, chat_id: int, user_id: int) -> bool:
        """
        Cek apakah user memiliki akses penuh (authenticated + verified)
        Jika belum, kirim pesan yang sesuai

        Args:
            chat_id (int): Chat ID
            user_id (int): Telegram user ID

        Returns:
            bool: True jika user memiliki akses penuh
        """
        try:
            # Cek authentication
            if not await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "🔐 *Anda belum login!*\n\n"
                        "Untuk menggunakan layanan kami, silakan:\n"
                        "📝 /register - Registrasi akun baru\n"
                        "🔑 /login - Login dengan akun yang sudah ada\n\n"
                        "Setelah login, Anda dapat menikmati semua layanan kami."
                    ),
                    parse_mode="Markdown"
                )
                return False

            # Cek verification
            if not await self.is_user_verified(user_id):
                session = self.user_sessions.get(user_id, {})
                user_data = session.get("user_data", {})
                email = user_data.get("email", "N/A")

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "⚠️ *Email Belum Terverifikasi*\n\n"
                        f"📧 Email: {email}\n"
                        f"❌ Status: Belum terverifikasi\n\n"
                        f"📬 Silakan cek email Anda dan klik link verifikasi untuk mengaktifkan akun.\n\n"
                        f"💡 Gunakan /verify untuk cek status atau /resend untuk kirim ulang email."
                    ),
                    parse_mode="Markdown"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error saat check user access: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat mengecek akses. Silakan coba lagi."
            )
            return False

    async def handle_login_command(self, chat_id: int, user_id: int) -> None:
        """
        Handle command /login - memulai proses login step-by-step
        """
        try:
            # Cek apakah user sudah login
            if await self.is_user_authenticated(user_id):
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Anda sudah login. Gunakan /profile untuk melihat profil Anda."
                )
                return

            # Mulai proses login
            self.login_states[user_id] = {
                "step": "email",
                "data": {},
                "password_attempts": 0  # Track jumlah percobaan password
            }

            login_message = (
                "🔑 *Login ke Akun Anda*\n\n"
                "Silakan login dengan akun yang sudah ada.\n"
                "Anda bisa ketik /cancel kapan saja untuk membatalkan.\n\n"
                "📧 *Langkah 1/2*\n"
                "Silakan masukkan *email* Anda:"
            )

            await self.bot.send_message(
                chat_id=chat_id,
                text=login_message,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error saat handle login command: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat memulai login. Silakan coba lagi."
            )

    async def handle_login_step(self, chat_id: int, user_id: int, message_text: str, message_id: int = None) -> bool:
        """
        Handle step-by-step login process

        Returns:
            bool: True jika pesan diproses sebagai bagian login, False jika bukan
        """
        # Cek apakah user sedang dalam proses login
        if user_id not in self.login_states:
            return False

        try:
            state = self.login_states[user_id]
            step = state["step"]
            data = state["data"]

            # Handle cancel command
            if message_text.lower() in ['/cancel', 'cancel', 'batal']:
                # Hapus pesan password jika ada untuk keamanan
                password_message_id = state.get("password_message_id")
                if password_message_id:
                    try:
                        await self.bot.delete_message(chat_id=chat_id, message_id=password_message_id)
                        logger.info(f"Password message {password_message_id} dihapus karena login dibatalkan")
                    except Exception as e:
                        logger.warning(f"Gagal menghapus pesan password saat cancel: {e}")

                del self.login_states[user_id]
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Login dibatalkan dan pesan password telah dihapus untuk keamanan. Ketik /login untuk mencoba lagi."
                )
                return True

            # Process each step
            if step == "email":
                # Validasi email sederhana
                if "@" not in message_text or "." not in message_text:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Format email tidak valid. Silakan masukkan email yang benar:"
                    )
                    return True

                data["email"] = message_text.strip().lower()
                state["step"] = "password"

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ Email: {data['email']}\n\n"
                        "🔒 *Langkah 2/2*\n"
                        "Silakan masukkan *password* Anda:"
                    ),
                    parse_mode="Markdown"
                )

            elif step == "password":
                data["password"] = message_text
                # Simpan message_id dari pesan password untuk dihapus nanti jika login berhasil
                if message_id:
                    state["password_message_id"] = message_id
                    logger.info(f"Password message_id {message_id} disimpan untuk user {user_id}")

                # Proses login dengan tracking attempts
                await self._process_login(chat_id, user_id, data, state)

            return True

        except Exception as e:
            logger.error(f"Error saat handle login step: {e}")
            # Hapus pesan password jika ada untuk keamanan
            if user_id in self.login_states:
                state = self.login_states[user_id]
                password_message_id = state.get("password_message_id")
                if password_message_id:
                    try:
                        await self.bot.delete_message(chat_id=chat_id, message_id=password_message_id)
                        logger.info(f"Password message {password_message_id} dihapus karena error")
                    except Exception as e2:
                        logger.warning(f"Gagal menghapus pesan password saat error: {e2}")

                # Cleanup state on error
                del self.login_states[user_id]

            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat login dan pesan password telah dihapus untuk keamanan. Silakan ketik /login untuk mencoba lagi."
            )
            return True

    async def _process_login(self, chat_id: int, user_id: int, data: Dict[str, Any], state: Dict[str, Any]) -> None:
        """
        Process login with collected credentials and handle password attempts
        """
        try:
            # Kirim loading message
            loading_msg = await self.bot.send_message(
                chat_id=chat_id,
                text="⏳ Memverifikasi kredensial Anda..."
            )

            # Login ke backend
            result = await auth_client.login_user(
                email=data["email"],
                password=data["password"]
            )

            # Hapus loading message
            await self.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)

            if result.get("success"):
                # Login berhasil - hapus pesan password untuk keamanan
                password_message_id = state.get("password_message_id")
                logger.info(f"Login berhasil untuk user {user_id}, password_message_id: {password_message_id}")

                if password_message_id:
                    try:
                        await self.bot.delete_message(chat_id=chat_id, message_id=password_message_id)
                        logger.info(f"✅ Password message {password_message_id} berhasil dihapus untuk keamanan user {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Gagal menghapus pesan password {password_message_id}: {e}")
                else:
                    logger.warning(f"⚠️ Password message_id tidak ditemukan untuk user {user_id}")

                # Cleanup login state
                if user_id in self.login_states:
                    del self.login_states[user_id]

                user_data = result.get("user", {})
                access_token = result.get("access_token")

                # Link telegram account jika belum
                if not user_data.get("telegram_id"):
                    link_result = await auth_client.link_telegram_account(
                        access_token=access_token,
                        telegram_id=str(user_id)
                    )
                    if link_result.get("success"):
                        user_data["telegram_id"] = str(user_id)
                        logger.info(f"Successfully linked telegram_id {user_id} to user account")

                # Simpan session
                self.user_sessions[user_id] = {
                    "authenticated": True,
                    "user_data": user_data,
                    "access_token": access_token
                }

                # Pesan 1: Login berhasil (dengan detail lengkap)
                initial_success_message = (
                    f"✅ *Login berhasil!*\n\n"
                    f"Selamat datang kembali, {user_data.get('nama', 'User')}!\n"
                    f"📧 Email: {data['email']}\n"
                    f"📱 Telegram ID: {user_id}\n\n"
                    f"🔒 *Keamanan:* Pesan password Anda telah dihapus otomatis dari chat.\n\n"
                    f"Akun Anda sudah terhubung dengan Telegram."
                )

                success_msg = await self.bot.send_message(
                    chat_id=chat_id,
                    text=initial_success_message,
                    parse_mode="Markdown"
                )

                # Delay kecil untuk transisi yang lebih smooth (500ms)
                await asyncio.sleep(0.5)

                # Pesan 2: Pembuka yang ramah
                welcome_message = (
                    "Ada yang bisa saya bantu untuk perjalanan Anda hari ini? ✈️😊"
                )

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_message
                )

                # Callback effect di background - edit pesan 1 setelah 10 detik
                async def callback_edit():
                    await asyncio.sleep(5)
                    final_success_message = "✅ *Login berhasil!*"
                    try:
                        await self.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=success_msg.message_id,
                            text=final_success_message,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.warning(f"Gagal mengedit pesan login success: {e}")

                # Jalankan callback edit di background tanpa menunggu
                asyncio.create_task(callback_edit())

                logger.info(f"User {user_id} berhasil login dengan email {data['email']}")

            else:
                # Login gagal - handle password attempts
                state["password_attempts"] += 1
                max_attempts = 3
                remaining_attempts = max_attempts - state["password_attempts"]

                error_message = result.get("message", "Password salah")

                if state["password_attempts"] >= max_attempts:
                    # Sudah 3 kali salah, hapus pesan password untuk keamanan
                    password_message_id = state.get("password_message_id")
                    if password_message_id:
                        try:
                            await self.bot.delete_message(chat_id=chat_id, message_id=password_message_id)
                            logger.info(f"Password message {password_message_id} dihapus setelah 3 kali gagal login")
                        except Exception as e:
                            logger.warning(f"Gagal menghapus pesan password setelah gagal login: {e}")

                    # Cleanup state
                    if user_id in self.login_states:
                        del self.login_states[user_id]

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"❌ *Login gagal!*\n\n"
                            f"Anda sudah mencoba {max_attempts} kali dengan password yang salah.\n"
                            f"Untuk keamanan, proses login dihentikan dan pesan password telah dihapus.\n\n"
                            f"Silakan ketik /login untuk mencoba lagi atau /register untuk membuat akun baru."
                        ),
                        parse_mode="Markdown"
                    )
                else:
                    # Masih ada kesempatan, minta password lagi
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"❌ *Password salah!*\n\n"
                            f"{error_message}\n\n"
                            f"🔒 Sisa kesempatan: *{remaining_attempts} kali*\n"
                            f"Silakan masukkan password yang benar:"
                        ),
                        parse_mode="Markdown"
                    )

        except Exception as e:
            logger.error(f"Error saat process login: {e}")
            # Hapus pesan password jika ada untuk keamanan
            password_message_id = state.get("password_message_id")
            if password_message_id:
                try:
                    await self.bot.delete_message(chat_id=chat_id, message_id=password_message_id)
                    logger.info(f"Password message {password_message_id} dihapus karena error dalam process login")
                except Exception as e2:
                    logger.warning(f"Gagal menghapus pesan password saat error process login: {e2}")

            # Cleanup state on error
            if user_id in self.login_states:
                del self.login_states[user_id]
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Terjadi kesalahan saat memproses login dan pesan password telah dihapus untuk keamanan. Silakan ketik /login untuk mencoba lagi."
            )

    async def handle_logout_callback(self, callback_query):
        """Menangani callback dari tombol konfirmasi logout."""
        try:
            chat_id = callback_query.message.chat.id
            user_id = callback_query.from_user.id
            callback_data = callback_query.data

            # Ambil nama user dari session untuk personalisasi
            session = self.user_sessions.get(user_id, {})
            user_data = session.get("user_data", {})
            user_name = user_data.get("nama", "User")

            if callback_data.startswith("logout_confirm_"):
                # User mengkonfirmasi logout
                # Hapus pesan konfirmasi
                await self.bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)

                # Jalankan proses logout
                await self._process_logout(chat_id, user_id)

            elif callback_data.startswith("logout_cancel_"):
                # User membatalkan logout
                # Edit pesan konfirmasi menjadi pesan pembatalan
                cancel_message = (
                    f"✅ *Logout Dibatalkan*\n\n"
                    f"Baik {user_name}, Anda tetap login di sistem.\n\n"
                    f"Ada yang bisa saya bantu untuk perjalanan Anda hari ini? ✈️😊"
                )

                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id,
                    text=cancel_message,
                    parse_mode="Markdown"
                )

            # Jawab callback query untuk menghilangkan loading di tombol
            await self.bot.answer_callback_query(callback_query.id)

        except Exception as e:
            logger.error(f"Error saat menangani callback logout: {e}")
            try:
                await self.bot.answer_callback_query(
                    callback_query.id,
                    text="❌ Terjadi kesalahan. Silakan coba lagi.",
                    show_alert=True
                )
            except:
                pass

    async def handle_edit_profile_callback(self, callback_query):
        """
        Handle callback untuk tombol edit profile
        """
        try:
            chat_id = callback_query.message.chat_id
            user_id = callback_query.from_user.id
            
            # Answer the callback query
            await self.bot.answer_callback_query(callback_query.id)
            
            # Inisialisasi state untuk edit profile jika belum ada
            if not hasattr(self, 'edit_profile_states'):
                self.edit_profile_states = {}
                
            # Buat keyboard untuk memilih field yang akan diedit
            keyboard = [
                [InlineKeyboardButton("📛 Edit Nama", callback_data="edit_profile_nama")],
                [InlineKeyboardButton("📱 Edit Telepon", callback_data="edit_profile_telepon")],
                [InlineKeyboardButton("🏠 Edit Alamat", callback_data="edit_profile_alamat")],
                [InlineKeyboardButton("❌ Batal", callback_data="edit_profile_cancel")]
            ]
            
            await self.bot.send_message(
                chat_id=chat_id,
                text="✏️ *Edit Profil*\n\nPilih data yang ingin Anda edit:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error saat handle edit profile callback: {e}")
            await self.bot.answer_callback_query(callback_query.id, text="Terjadi kesalahan")

    async def handle_close_profile_callback(self, callback_query):
        """
        Handle callback untuk tombol tutup pada profile
        """
        try:
            chat_id = callback_query.message.chat_id
            message_id = callback_query.message.message_id
            user_id = callback_query.from_user.id

            # Delete the message
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Answer the callback query
            await self.bot.answer_callback_query(callback_query.id, text="Profil ditutup")
            
        except Exception as e:
            logger.error(f"Error saat handle close profile callback: {e}")
            await self.bot.answer_callback_query(callback_query.id, text="Terjadi kesalahan")