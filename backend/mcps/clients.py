# backend/mcp/clients.py

import os
from utils.config import get_settings

# Load configuration
config = get_settings()

# Environment variables untuk MCP clients
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", config.RAPIDAPI_KEY if hasattr(config, 'RAPIDAPI_KEY') else "")
TRIPADVISOR_API_KEY = os.getenv("TRIPADVISOR_API_KEY", config.TRIPADVISOR_API_KEY if hasattr(config, 'TRIPADVISOR_API_KEY') else "")
DATABASE_URI = os.getenv("DATABASE_URI", config.DATABASE_URI if hasattr(config, 'DATABASE_URI') else "")

# Konfigurasi untuk client-client MCP yang akan diinisialisasi
MCP_CLIENTS = {
    "booking": {
        "command": "uv",
        "args": [
            "--directory",
            "mcps/servers/booking.com",
            "run",
            "src/booking_com_mcp/main.py"
        ],
        "env": {
            "RAPIDAPI_KEY": RAPIDAPI_KEY
        },
        "transport": "stdio"
    },
    "tripadvisor": {
        "command": "uv",
        "args": [
            "--directory",
            "mcps/servers/tripadvisor",
            "run",
            "src/tripadvisor_mcp/main.py"
        ],
        "env": {
            "TRIPADVISOR_API_KEY": TRIPADVISOR_API_KEY
        },
        "transport": "stdio"
    },
    "airbnb": {
        "command": "npx",
        "args": [
            "-y",
            "@openbnb/mcp-server-airbnb",
            "--ignore-robots-txt"
        ],
        "transport": "stdio"
    },
    "supabase": {
        "command": "uv",
        "args": [
            "--directory",
            "mcps/servers/supabase",
            "run",
            "src/supabase_mcp/main.py",
            "--access-mode=unrestricted"
        ],
        "env": {
            "DATABASE_URI": DATABASE_URI
        },
        "transport": "stdio"
    },
}

# Filter out clients yang tidak memiliki API key yang diperlukan
def get_available_clients():
    """Return only clients that have required API keys configured."""
    available = {}
    
    if RAPIDAPI_KEY:
        available["booking"] = MCP_CLIENTS["booking"]
    else:
        print("⚠️  RAPIDAPI_KEY not configured, skipping Booking.com MCP")
    
    if TRIPADVISOR_API_KEY:
        available["tripadvisor"] = MCP_CLIENTS["tripadvisor"]
    else:
        print("⚠️  TRIPADVISOR_API_KEY not configured, skipping TripAdvisor MCP")
    
    # Airbnb tidak memerlukan API key
    available["airbnb"] = MCP_CLIENTS["airbnb"]

    # Supabase MCP memerlukan DATABASE_URI
    if DATABASE_URI:
        available["supabase"] = MCP_CLIENTS["supabase"]
    else:
        print("⚠️  DATABASE_URI not configured, skipping Supabase MCP")

    return available
