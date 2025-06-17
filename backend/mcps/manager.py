# backend/mcp/manager.py

import logging
import asyncio
from typing import Dict, List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import StructuredTool, Tool
from .clients import get_available_clients

logger = logging.getLogger(__name__)


class MCPManager:
    """Manager untuk Model Context Protocol servers."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Pastikan pola singleton untuk manager."""
        if cls._instance is None:
            cls._instance = super(MCPManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict] = None):
        """Inisialisasi MCP Manager."""
        if getattr(self, "_initialized", False):
            return

        self._config = config or get_available_clients()
        self.client = None
        self._tools: List[Tool] = []
        self._initialized = True
        self._loop = None  # Simpan referensi ke event loop

        logger.debug(f"MCPManager diinisialisasi dengan {len(self._config)} servers")

    async def connect(self) -> None:
        """Inisialisasi dan koneksi ke semua MCP servers yang dikonfigurasi."""
        if self.client is not None:
            logger.info("MCP client sudah terkoneksi, melewati")
            return

        try:
            logger.info(f"Menghubungkan ke {len(self._config)} MCP servers...")
            # Dapatkan event loop saat ini atau buat yang baru
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            # Buat client menggunakan pola API baru
            self.client = MultiServerMCPClient(self._config)

            # Dapatkan tools langsung dari client (API baru)
            raw_tools = await self.client.get_tools()

            # Konversi tools untuk memastikan mereka memiliki implementasi sync dan async
            self._tools = self.prepare_tools(raw_tools)

            logger.info(
                f"Berhasil terkoneksi, memuat {len(self._tools)} tools: {[t.name for t in self._tools]}"
            )
        except Exception as e:
            logger.error(f"Gagal terkoneksi ke MCP servers: {e}")
            self.client = None
            self._tools = []
            raise

    async def disconnect(self) -> None:
        """Putuskan koneksi dengan baik dari semua MCP servers."""
        if not self.client:
            logger.info("Tidak ada MCP client untuk diputus")
            return

        logger.info("Memutuskan koneksi dari MCP servers...")
        self.client = None  # Bersihkan referensi terlebih dahulu
        self._tools = []
        logger.info("Berhasil memutuskan koneksi dari MCP servers")

    def get_tools(self) -> List[Tool]:
        """Ambil semua tools yang tersedia dari MCP servers yang terkoneksi."""
        if not self.client:
            logger.warning("Tidak ada MCP client yang terkoneksi")
            return []

        return self._tools

    def prepare_tools(self, raw_tools: List[Tool]) -> List[Tool]:
        """
        Adaptasi MCP tools untuk bekerja dengan LangGraph dengan memastikan async tools dibungkus dengan benar.
        """
        prepared_tools = []

        for tool in raw_tools:
            if isinstance(tool, StructuredTool):
                # Pastikan tool memiliki implementasi sync yang mendelegasikan ke async
                if tool.coroutine and not tool.func:
                    # Buat sync wrapper yang menjalankan fungsi async dalam loop
                    async_func = tool.coroutine

                    def create_sync_wrapper(async_fn):
                        def sync_wrapper(*args, **kwargs):
                            try:
                                # Coba dapatkan loop yang sedang berjalan
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Jika loop sedang berjalan, buat task baru
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(asyncio.run, async_fn(*args, **kwargs))
                                        return future.result()
                                else:
                                    # Jika loop tidak berjalan, jalankan langsung
                                    return loop.run_until_complete(async_fn(*args, **kwargs))
                            except RuntimeError:
                                # Jika tidak ada loop, buat yang baru
                                return asyncio.run(async_fn(*args, **kwargs))
                        return sync_wrapper

                    # Set fungsi sync sebagai wrapper
                    tool.func = create_sync_wrapper(async_func)

                prepared_tools.append(tool)
            else:
                # Tool biasa, tambahkan langsung
                prepared_tools.append(tool)

        return prepared_tools


# Instance singleton global
mcp_manager = MCPManager()


async def initialize_mcp_tools() -> List[Tool]:
    """Inisialisasi koneksi MCP dan kembalikan tools yang tersedia."""
    await mcp_manager.connect()
    return mcp_manager.get_tools()


async def cleanup_mcp() -> None:
    """Bersihkan koneksi MCP."""
    await mcp_manager.disconnect()
