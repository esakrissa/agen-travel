import os
import logging
import asyncio
import asyncpg
import httpx
from dotenv import load_dotenv

# Load variabel environment
load_dotenv()

# Konfigurasi logging
logger = logging.getLogger(__name__)

# Variabel environment
SUPABASE_CONNECTION = os.getenv("SUPABASE_CONNECTION")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class PostgresClient:
    """Kelas untuk berinteraksi langsung dengan PostgreSQL database di Supabase."""

    def __init__(self):
        """Inisialisasi client dengan connection string PostgreSQL."""
        self.connection_string = SUPABASE_CONNECTION
        self.pool = None

        if not self.connection_string:
            logger.error("SUPABASE_CONNECTION tidak ditemukan di environment variables")

    async def get_pool(self):
        """Mendapatkan atau membuat connection pool."""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=self.connection_string,
                    min_size=1,
                    max_size=10
                )
                logger.info("Connection pool PostgreSQL berhasil dibuat")
            except Exception as e:
                logger.error(f"Error saat membuat connection pool PostgreSQL: {str(e)}")
                raise
        return self.pool

    async def close_pool(self):
        """Menutup connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Connection pool PostgreSQL berhasil ditutup")

    async def get_user_thread_id(self, user_id: str, platform: str = 'telegram') -> str:
        """
        Mendapatkan thread ID untuk user_id dari database.

        Args:
            user_id (str): ID pengguna Telegram
            platform (str): Platform chat (default: 'telegram')

        Returns:
            str: Thread ID jika ditemukan, None jika tidak
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                # Panggil fungsi get_user_thread_id langsung
                thread_id = await conn.fetchval(
                    "SELECT get_user_thread_id($1, $2)",
                    user_id,
                    platform
                )

                if thread_id:
                    logger.info(f"Thread ID untuk user {user_id}: {thread_id} via Supabase RPC")
                    return thread_id

                logger.info(f"Tidak ditemukan thread ID untuk user {user_id} via Supabase RPC")
                return None

        except Exception as e:
            logger.error(f"Error saat mendapatkan thread ID via Supabase RPC: {str(e)}")
            return None

    async def save_chat_message(self, user_id: str, thread_id: str, user_message: str, ai_message: str, platform: str = 'telegram') -> bool:
        """
        Menyimpan pesan chat ke database.

        Args:
            user_id (str): ID pengguna Telegram
            thread_id (str): Thread ID percakapan
            user_message (str): Pesan dari pengguna
            ai_message (str): Respons dari AI
            platform (str): Platform chat (default: 'telegram')

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                # Panggil fungsi save_chat_message langsung
                result = await conn.fetchval(
                    "SELECT save_chat_message($1, $2, $3, $4, $5)",
                    user_id,
                    thread_id,
                    user_message,
                    ai_message,
                    platform
                )

                logger.info(f"Pesan chat berhasil disimpan untuk thread {thread_id} via Supabase RPC")
                return True

        except Exception as e:
            logger.error(f"Error saat menyimpan pesan chat via Supabase RPC: {str(e)}")
            return False

    async def get_all_user_thread_ids(self, platform: str = 'telegram') -> list:
        """
        Mendapatkan thread ID terbaru untuk semua pengguna.

        Args:
            platform (str): Platform chat (default: 'telegram')

        Returns:
            list: List dictionary dengan user_id dan thread_id
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                # Panggil fungsi get_all_user_thread_ids langsung
                try:
                    result = await conn.fetchval(
                        "SELECT get_all_user_thread_ids($1)",
                        platform
                    )

                    if result:
                        logger.info(f"Berhasil mendapatkan thread IDs via Supabase RPC")
                        # Pastikan hasil adalah list, bukan string
                        if isinstance(result, str):
                            import json
                            try:
                                parsed_result = json.loads(result)
                                return parsed_result
                            except json.JSONDecodeError:
                                logger.error(f"Error parsing JSON result: {result}")
                                # Lanjutkan ke query SQL langsung
                        else:
                            return result
                except Exception as e:
                    logger.error(f"Error saat memanggil fungsi get_all_user_thread_ids: {str(e)}")
                    # Lanjutkan ke query SQL langsung

                # Jika fungsi tidak tersedia atau gagal, gunakan query SQL langsung
                query = """
                WITH latest_threads AS (
                    SELECT DISTINCT ON (user_id) user_id, thread_id, updated_at
                    FROM chat_history
                    WHERE platform = $1
                    ORDER BY user_id, updated_at DESC
                )
                SELECT json_agg(json_build_object('user_id', user_id, 'thread_id', thread_id))
                FROM latest_threads
                """

                result = await conn.fetchval(query, platform)

                if result:
                    logger.info(f"Berhasil mendapatkan thread IDs via Supabase SQL query")
                    return result

                return []

        except Exception as e:
            logger.error(f"Error saat mendapatkan thread IDs via Supabase RPC: {str(e)}")
            return []

class SupabaseClient:
    """Kelas untuk berinteraksi dengan Supabase API."""

    def __init__(self):
        """Inisialisasi client dengan URL dan API key Supabase."""
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        if not self.url or not self.key:
            logger.error("SUPABASE_URL atau SUPABASE_KEY tidak ditemukan di environment variables")

    async def get_thread_id(self, user_id: str, platform: str = 'telegram') -> str:
        """
        Mendapatkan thread ID untuk user_id dari Supabase.

        Args:
            user_id (str): ID pengguna Telegram
            platform (str): Platform chat (default: 'telegram')

        Returns:
            str: Thread ID jika ditemukan, None jika tidak
        """
        try:
            # Coba gunakan RPC get_user_thread_id
            async with httpx.AsyncClient() as client:
                try:
                    # Panggil fungsi RPC get_user_thread_id
                    response = await client.post(
                        f"{self.url}/rest/rpc/get_user_thread_id",
                        headers=self.headers,
                        json={
                            "p_user_id": str(user_id),
                            "p_platform": platform
                        },
                        timeout=10.0
                    )

                    response.raise_for_status()
                    thread_id = response.json()

                    if thread_id:
                        logger.info(f"Thread ID untuk user {user_id}: {thread_id}")
                        return thread_id

                    logger.info(f"Tidak ditemukan thread ID untuk user {user_id} via RPC")
                    return None

                except httpx.HTTPStatusError as e:
                    # Jika RPC gagal, gunakan REST API sebagai fallback
                    logger.info(f"RPC get_user_thread_id error: {e.response.status_code}, menggunakan REST API")

                    response = await client.get(
                        f"{self.url}/rest/v1/chat_history",
                        headers=self.headers,
                        params={
                            "user_id": f"eq.{user_id}",
                            "platform": f"eq.{platform}",
                            "select": "thread_id",
                            "order": "updated_at.desc",
                            "limit": "1"
                        },
                        timeout=10.0
                    )

                    response.raise_for_status()
                    data = response.json()

                    if data and len(data) > 0:
                        thread_id = data[0].get('thread_id')
                        logger.info(f"Thread ID untuk user {user_id}: {thread_id}")
                        return thread_id

                    logger.info(f"Tidak ditemukan thread ID untuk user {user_id}")
                    return None

        except Exception as e:
            logger.error(f"Error saat mendapatkan thread ID: {str(e)}")

        return None

    async def save_thread_id(self, user_id: str, thread_id: str, platform: str = 'telegram') -> bool:
        """
        Menyimpan thread ID untuk user_id ke Supabase.

        Args:
            user_id (str): ID pengguna Telegram
            thread_id (str): Thread ID yang akan disimpan
            platform (str): Platform chat (default: 'telegram')

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            # Selalu buat entri baru untuk menyimpan thread_id
            # Ini memungkinkan kita untuk menyimpan beberapa pesan untuk satu pengguna
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/rest/v1/chat_history",
                    headers=self.headers,
                    json={
                        "user_id": str(user_id),
                        "thread_id": thread_id,
                        "platform": platform,
                        "user_message": "thread_id_mapping",
                        "ai_message": "thread_id_mapping",
                        "created_at": "now()",
                        "updated_at": "now()"
                    },
                    timeout=10.0
                )

                response.raise_for_status()
                logger.info(f"Thread ID {thread_id} berhasil disimpan untuk user {user_id}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error saat menyimpan thread ID: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error saat menyimpan thread ID: {str(e)}")

        return False

    async def save_chat_message(self, user_id: str, thread_id: str, user_message: str, ai_message: str, platform: str = 'telegram') -> bool:
        """
        Menyimpan pesan chat ke Supabase.

        Args:
            user_id (str): ID pengguna Telegram
            thread_id (str): Thread ID percakapan
            user_message (str): Pesan dari pengguna
            ai_message (str): Respons dari AI
            platform (str): Platform chat (default: 'telegram')

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            async with httpx.AsyncClient() as client:
                try:
                    # Panggil fungsi RPC save_chat_message
                    response = await client.post(
                        f"{self.url}/rest/rpc/save_chat_message",
                        headers=self.headers,
                        json={
                            "p_user_id": str(user_id),
                            "p_thread_id": thread_id,
                            "p_user_message": user_message,
                            "p_ai_message": ai_message,
                            "p_platform": platform
                        },
                        timeout=10.0
                    )

                    response.raise_for_status()
                    logger.info(f"Pesan chat berhasil disimpan untuk thread {thread_id} via RPC")
                    return True

                except httpx.HTTPStatusError as e:
                    # Jika RPC gagal, gunakan REST API sebagai fallback
                    logger.info(f"RPC save_chat_message error: {e.response.status_code}, menggunakan REST API")

                    # Insert pesan chat langsung ke tabel
                    response = await client.post(
                        f"{self.url}/rest/v1/chat_history",
                        headers=self.headers,
                        json={
                            "user_id": str(user_id),
                            "thread_id": thread_id,
                            "user_message": user_message,
                            "ai_message": ai_message,
                            "platform": platform,
                            "created_at": "now()",
                            "updated_at": "now()"
                        },
                        timeout=10.0
                    )

                    response.raise_for_status()
                    logger.info(f"Pesan chat berhasil disimpan untuk thread {thread_id} via REST API")
                    return True

        except Exception as e:
            logger.error(f"Error saat menyimpan pesan chat: {str(e)}")

        return False

# Singleton instances
postgres_client = PostgresClient()
supabase_client = SupabaseClient()
