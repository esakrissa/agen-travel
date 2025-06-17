#!/usr/bin/env python3
"""
Script untuk testing MCP integration di agen-travel.
"""

import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mcp_manager():
    """Test MCP Manager initialization dan tool loading."""
    try:
        from mcps.manager import MCPManager, initialize_mcp_tools
        
        logger.info("Testing MCP Manager...")
        
        # Test singleton pattern
        manager1 = MCPManager()
        manager2 = MCPManager()
        assert manager1 is manager2, "MCPManager should be singleton"
        logger.info("✓ Singleton pattern working")
        
        # Test tool initialization
        tools = await initialize_mcp_tools()
        logger.info(f"✓ Loaded {len(tools)} MCP tools")
        
        # List available tools
        if tools:
            logger.info("Available MCP tools:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description[:100]}...")
        else:
            logger.warning("No MCP tools loaded - check API keys and server configuration")
        
        return tools
        
    except Exception as e:
        logger.error(f"Error testing MCP Manager: {e}")
        return []

async def test_mcp_tools(tools):
    """Test individual MCP tools."""
    if not tools:
        logger.warning("No tools to test")
        return
    
    logger.info("Testing individual MCP tools...")
    
    # Test Booking.com tools
    booking_tools = [t for t in tools if 'booking' in t.name.lower()]
    if booking_tools:
        logger.info(f"Found {len(booking_tools)} Booking.com tools")
        
        # Test destination search
        search_tool = next((t for t in booking_tools if 'search_destinations' in t.name), None)
        if search_tool:
            try:
                logger.info("Testing Booking.com destination search...")
                result = await search_tool.ainvoke({"query": "Bali"})
                logger.info(f"✓ Booking.com search result: {type(result)}")
            except Exception as e:
                logger.error(f"✗ Booking.com search failed: {e}")
    
    # Test TripAdvisor tools
    tripadvisor_tools = [t for t in tools if 'tripadvisor' in t.name.lower()]
    if tripadvisor_tools:
        logger.info(f"Found {len(tripadvisor_tools)} TripAdvisor tools")
        
        # Test location search
        search_tool = next((t for t in tripadvisor_tools if 'search_locations' in t.name), None)
        if search_tool:
            try:
                logger.info("Testing TripAdvisor location search...")
                result = await search_tool.ainvoke({"searchQuery": "Bali hotels"})
                logger.info(f"✓ TripAdvisor search result: {type(result)}")
            except Exception as e:
                logger.error(f"✗ TripAdvisor search failed: {e}")
    
    # Test Airbnb tools
    airbnb_tools = [t for t in tools if 'airbnb' in t.name.lower()]
    if airbnb_tools:
        logger.info(f"Found {len(airbnb_tools)} Airbnb tools")

async def test_graph_integration():
    """Test MCP integration dengan graph agen-travel."""
    try:
        logger.info("Testing graph integration...")
        
        # Import graph components
        from agents.graph import MCP_AVAILABLE, MCP
        
        if MCP_AVAILABLE:
            logger.info(f"✓ MCP available in graph with {len(MCP)} tools")
            
            # Test tool categorization
            booking_tools = [t for t in MCP if 'booking' in t.name.lower()]
            tripadvisor_tools = [t for t in MCP if 'tripadvisor' in t.name.lower()]
            airbnb_tools = [t for t in MCP if 'airbnb' in t.name.lower()]
            
            logger.info(f"Tool distribution:")
            logger.info(f"  - Booking.com: {len(booking_tools)} tools")
            logger.info(f"  - TripAdvisor: {len(tripadvisor_tools)} tools")
            logger.info(f"  - Airbnb: {len(airbnb_tools)} tools")
            
        else:
            logger.warning("✗ MCP not available in graph")
            
    except Exception as e:
        logger.error(f"Error testing graph integration: {e}")

async def test_cleanup():
    """Test MCP cleanup functionality."""
    try:
        logger.info("Testing MCP cleanup...")
        
        from mcps import cleanup_mcp
        await cleanup_mcp()
        
        logger.info("✓ MCP cleanup successful")
        
    except Exception as e:
        logger.error(f"Error testing cleanup: {e}")

async def main():
    """Main test function."""
    logger.info("Starting MCP integration tests...")
    
    # Test 1: MCP Manager
    tools = await test_mcp_manager()
    
    # Test 2: Individual tools
    await test_mcp_tools(tools)
    
    # Test 3: Graph integration
    await test_graph_integration()
    
    # Test 4: Cleanup
    await test_cleanup()
    
    logger.info("MCP integration tests completed!")

if __name__ == "__main__":
    # Ensure we're in the right directory
    if not os.path.exists("backend"):
        logger.error("Please run this script from the agen-travel root directory")
        sys.exit(1)
    
    # Add backend to Python path
    sys.path.insert(0, "backend")
    
    # Run tests
    asyncio.run(main())
