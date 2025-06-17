#!/usr/bin/env python3

"""
Booking.com MCP Server - Entry point
"""

import sys
import dotenv
from booking_com_mcp.server import mcp

def setup_environment():
    """Setup environment variables and validate configuration"""
    if dotenv.load_dotenv():
        print("Loaded environment variables from .env file")
    else:
        print("No .env file found or could not load it - using environment variables")

    import os
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        print("ERROR: RAPIDAPI_KEY environment variable is not set")
        print("Please set it to your RapidAPI key for Booking.com API")
        return False

    print(f"Booking.com API configuration:")
    print(f"  API Key: {'*' * (len(rapidapi_key) - 8) + rapidapi_key[-8:] if rapidapi_key else 'Not set'}")
    print(f"  Host: booking-com15.p.rapidapi.com")

    return True

def run_server():
    """Main entry point for the Booking.com MCP Server"""
    # Setup environment
    if not setup_environment():
        sys.exit(1)

    print("\nStarting Booking.com MCP Server...")
    print("Running server in standard mode...")

    # Run the server with the stdio transport
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run_server()