# backend/mcps/__init__.py

import logging

logger = logging.getLogger(__name__)

# Global variables untuk MCP tools
MCP = []
MCP_INITIALIZED = False


# Lazy initialization untuk menghindari event loop conflicts
async def _initialize_mcp_async():
    global MCP, MCP_INITIALIZED
    if not MCP_INITIALIZED:
        try:
            logger.info("→ menginisialisasi MCP servers…")
            from .manager import initialize_mcp_tools

            MCP = await initialize_mcp_tools()
            MCP_INITIALIZED = True
            logger.info(f"→ memuat {len(MCP)} MCP tools: {[t.name for t in MCP]}")
        except Exception as e:
            logger.warning(f"→ inisialisasi MCP gagal: {e}")
            logger.info("→ melanjutkan tanpa MCP tools")
            MCP = []
            MCP_INITIALIZED = False
    return MCP

# Sync wrapper untuk lazy loading
def get_mcp_tools():
    """Get MCP tools with lazy initialization."""
    global MCP, MCP_INITIALIZED
    if not MCP_INITIALIZED:
        # Return empty list if not initialized yet
        # Will be initialized when first async call is made
        return []
    return MCP

# Initialize empty MCP list
MCP = []
MCP_INITIALIZED = False


# Cleanup function untuk graceful shutdown
async def cleanup_mcp():
    """Cleanup MCP connections saat shutdown."""
    try:
        from .manager import cleanup_mcp as manager_cleanup
        await manager_cleanup()
        logger.info("MCP cleanup berhasil")
    except Exception as e:
        logger.error(f"Error saat MCP cleanup: {e}")
