#!/usr/bin/env python

import os
import logging
import sys
import asyncio

from supabase_mcp.server import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    database_uri = os.getenv("DATABASE_URI")
    if not database_uri:
        logger.error("DATABASE_URI environment variable is not set")
        sys.exit(1)
    
    logger.info("Supabase MCP Server starting...")
    logger.info(f"Using Python {sys.version}")
    
    # Set environment variable for database connection
    os.environ["DATABASE_URI"] = database_uri
    
    # Run the main function
    asyncio.run(main()) 