"""
LangGraph API Entrypoint
Dedicated entrypoint for LangGraph API that avoids nest_asyncio conflicts
"""

import os
import logging
from langgraph.graph import StateGraph
from agents.state import State
from agents.base import Assistant
from langgraph.graph import START, END
from agents.route import create_entry_node
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from agents.agents import get_runnable
from models.agents import CompleteOrEscalate
from agents.prompts import customer_service_prompt, hotel_agent_prompt, flight_agent_prompt, tour_agent_prompt, supervisor_prompt
from tools.tools import (
    get_hotels,
    search_hotels_by_location,
    get_hotel_details,
    check_available_rooms,
    book_hotel_room,
    get_user_booking_history,
    get_flights,
    search_flights_by_route,
    get_flight_details,
    book_flight,
    process_hotel_payment,
    process_flight_payment,
    check_unpaid_bookings,
    get_booking_details,
    cancel_hotel_booking,
    cancel_flight_booking,
    get_tours,
    search_tours_by_destination,
    get_tour_details,
    check_tour_availability,
    book_tour,
    process_tour_payment,
    cancel_tour_booking,
    search_currency_rates,
    search_travel_articles,
    search_general_info
)
from models.agents import ToHotelAgent, ToFlightAgent, ToTourAgent, ToCustomerService, ToSupervisor
from agents.route import (
    create_tool_node_with_fallback,
    pop_dialog_state,
    RouteUpdater,
    route_to_workflow,
    route_supervisor
)
from utils.config import get_settings

# NOTE: NO nest_asyncio.apply() here - LangGraph API uses uvloop

config = get_settings()

# Setup environment variables for LangSmith tracing
os.environ["LANGSMITH_TRACING_V2"] = config.LANGSMITH_TRACING_V2
os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT
os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT

# Initialize LLM with configuration to prevent parallel tool calls
llm = ChatOpenAI(
    temperature=0,
    api_key=config.OPENAI_API_KEY,
    model=config.OPENAI_MODEL,
    model_kwargs={
        'parallel_tool_calls': False  # Disable parallel tool calls to prevent tool_call_id error
    }
)

# Import RAG tools
try:
    from rag import RAG_TOOLS
    RAG_AVAILABLE = True
    logging.info(f"RAG tools loaded: {len(RAG_TOOLS)} tools available")
except ImportError as e:
    logging.warning(f"RAG tools not available: {e}")
    RAG_TOOLS = []
    RAG_AVAILABLE = False

# Import MCP tools with lazy loading
try:
    from mcps import get_mcp_tools, _initialize_mcp_async
    MCP = get_mcp_tools()  # Get current tools (empty if not initialized)
    MCP_AVAILABLE = True
    logging.info(f"MCP module loaded: {len(MCP)} tools currently available")
except ImportError as e:
    logging.warning(f"MCP tools not available: {e}")
    MCP = []
    MCP_AVAILABLE = False
    _initialize_mcp_async = None

# Define tools for each agent
customer_service_tools = [
    get_user_booking_history, get_booking_details,
    cancel_hotel_booking, cancel_flight_booking, cancel_tour_booking,
    search_currency_rates, search_travel_articles, search_general_info
]

# Add RAG tools to customer service if available
if RAG_AVAILABLE:
    customer_service_tools.extend(RAG_TOOLS)
    logging.info(f"RAG tools added to customer service: {[t.name for t in RAG_TOOLS]}")

hotel_tools = [
    get_hotels, search_hotels_by_location, get_hotel_details, check_available_rooms,
    book_hotel_room, process_hotel_payment, check_unpaid_bookings, get_booking_details,
    cancel_hotel_booking
]

flight_tools = [
    get_flights, search_flights_by_route, get_flight_details,
    book_flight, process_flight_payment, check_unpaid_bookings, get_booking_details,
    cancel_flight_booking
]

tour_tools = [
    get_tours, search_tours_by_destination, get_tour_details, check_tour_availability,
    book_tour, process_tour_payment, check_unpaid_bookings, get_booking_details,
    cancel_tour_booking
]

supervisor_tools = [ToHotelAgent, ToFlightAgent, ToTourAgent, ToCustomerService, ToSupervisor, CompleteOrEscalate]

def _update_tools_with_mcp():
    """Update tool lists with MCP tools."""
    global customer_service_tools, hotel_tools, flight_tools, tour_tools, MCP

    if MCP_AVAILABLE and MCP:
        # Filter MCP tools by category
        booking_mcp_tools = [tool for tool in MCP if 'booking' in tool.name.lower()]
        tripadvisor_mcp_tools = [tool for tool in MCP if 'tripadvisor' in tool.name.lower()]
        airbnb_mcp_tools = [tool for tool in MCP if 'airbnb' in tool.name.lower()]
        supabase_mcp_tools = [tool for tool in MCP if any(keyword in tool.name.lower() for keyword in ['supabase', 'execute_sql', 'list_schemas', 'list_objects', 'get_object_details', 'explain_query', 'analyze_workload', 'analyze_query', 'analyze_db_health', 'get_top_queries'])]

        # Add to hotel_tools
        hotel_tools.extend(booking_mcp_tools)
        hotel_tools.extend(airbnb_mcp_tools)
        hotel_tools.extend(tripadvisor_mcp_tools)
        hotel_tools.extend(supabase_mcp_tools)

        # Add to customer_service_tools
        customer_service_tools.extend(tripadvisor_mcp_tools)
        customer_service_tools.extend(supabase_mcp_tools)

        # Add to flight_tools
        flight_booking_tools = [tool for tool in booking_mcp_tools if 'flight' in tool.name.lower()]
        flight_tools.extend(flight_booking_tools)
        flight_tools.extend(supabase_mcp_tools)

        # Add to tour_tools
        tour_tools.extend(tripadvisor_mcp_tools)
        tour_tools.extend(supabase_mcp_tools)

        logging.info(f"MCP tools integrated: {len(booking_mcp_tools)} booking, {len(tripadvisor_mcp_tools)} tripadvisor, {len(airbnb_mcp_tools)} airbnb, {len(supabase_mcp_tools)} supabase")
        logging.info(f"Tools distribution - Hotel: {len(hotel_tools)}, Flight: {len(flight_tools)}, Customer Service: {len(customer_service_tools)}, Tour: {len(tour_tools)}")

# Initial attempt to add MCP tools
_update_tools_with_mcp()

# Initialize runnables - will be initialized in build_graph()
customer_service_runnable = None
hotel_runnable = None
flight_runnable = None
tour_runnable = None
supervisor_runnable = None

async def create_agent_runnable(llm, tools, agent_prompt):
    """Helper function to create agent runnable with consistent configuration"""
    return await get_runnable(
        llm=llm,
        tools=tools + [CompleteOrEscalate],
        agent_prompt=agent_prompt
    )

async def initialize_runnables():
    """Initialize all agent runnables"""
    global customer_service_runnable, hotel_runnable, flight_runnable, tour_runnable, supervisor_runnable

    # Debug logging to see available tools
    logging.info(f"Initializing runnables with tools:")
    logging.info(f"  Customer Service tools: {len(customer_service_tools)} - {[t.name for t in customer_service_tools]}")
    logging.info(f"  Hotel tools: {len(hotel_tools)} - {[t.name for t in hotel_tools]}")
    logging.info(f"  Flight tools: {len(flight_tools)} - {[t.name for t in flight_tools]}")
    logging.info(f"  Tour tools: {len(tour_tools)} - {[t.name for t in tour_tools]}")

    customer_service_runnable = await create_agent_runnable(llm, customer_service_tools, customer_service_prompt)
    hotel_runnable = await create_agent_runnable(llm, hotel_tools, hotel_agent_prompt)
    flight_runnable = await create_agent_runnable(llm, flight_tools, flight_agent_prompt)
    tour_runnable = await create_agent_runnable(llm, tour_tools, tour_agent_prompt)
    supervisor_runnable = await create_agent_runnable(llm, supervisor_tools, supervisor_prompt)

def create_graph_builder():
    """
    Helper function to create and configure the graph builder

    Returns:
        StateGraph: Configured but not compiled graph builder
    """
    # Validate that runnables are initialized
    if not all([supervisor_runnable, customer_service_runnable, hotel_runnable, flight_runnable, tour_runnable]):
        raise ValueError("Agent runnables must be initialized before creating graph builder")

    builder = StateGraph(State)

    builder.add_node("supervisor", Assistant(supervisor_runnable))

    # Entry points for each agent
    builder.add_node(
        "customer_service_entrypoint",
        create_entry_node("Customer Service", "customer_service"),
    )
    builder.add_node(
        "hotel_agent_entrypoint",
        create_entry_node("Hotel Agent", "hotel_agent"),
    )
    builder.add_node(
        "flight_agent_entrypoint",
        create_entry_node("Flight Agent", "flight_agent"),
    )
    builder.add_node(
        "tour_agent_entrypoint",
        create_entry_node("Tour Agent", "tour_agent"),
    )

    # Agent nodes
    builder.add_node("customer_service", Assistant(customer_service_runnable))
    builder.add_node("hotel_agent", Assistant(hotel_runnable))
    builder.add_node("flight_agent", Assistant(flight_runnable))
    builder.add_node("tour_agent", Assistant(tour_runnable))

    # Tool nodes
    builder.add_node(
        "customer_service_tools",
        create_tool_node_with_fallback(customer_service_tools),
    )
    builder.add_node(
        "hotel_agent_tools",
        create_tool_node_with_fallback(hotel_tools),
    )
    builder.add_node(
        "flight_agent_tools",
        create_tool_node_with_fallback(flight_tools),
    )
    builder.add_node(
        "tour_agent_tools",
        create_tool_node_with_fallback(tour_tools),
    )

    builder.add_node("return_to_supervisor", pop_dialog_state)

    # Routing from START
    builder.add_conditional_edges(START, route_to_workflow)

    # Routing from supervisor
    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        [
            "customer_service_entrypoint",
            "hotel_agent_entrypoint",
            "flight_agent_entrypoint",
            "tour_agent_entrypoint",
            END,
        ],
    )

    # Customer service flow
    builder.add_edge("customer_service_entrypoint", "customer_service")
    builder.add_edge("customer_service_tools", "customer_service")
    builder.add_conditional_edges(
        "customer_service",
        RouteUpdater(customer_service_tools, "customer_service_tools").route_tool_execution,
        ["customer_service_tools", "return_to_supervisor", END],
    )

    # Hotel agent flow
    builder.add_edge("hotel_agent_entrypoint", "hotel_agent")
    builder.add_edge("hotel_agent_tools", "hotel_agent")
    builder.add_conditional_edges(
        "hotel_agent",
        RouteUpdater(hotel_tools, "hotel_agent_tools").route_tool_execution,
        ["hotel_agent_tools", "return_to_supervisor", END],
    )

    # Flight agent flow
    builder.add_edge("flight_agent_entrypoint", "flight_agent")
    builder.add_edge("flight_agent_tools", "flight_agent")
    builder.add_conditional_edges(
        "flight_agent",
        RouteUpdater(flight_tools, "flight_agent_tools").route_tool_execution,
        ["flight_agent_tools", "return_to_supervisor", END],
    )

    # Tour agent flow
    builder.add_edge("tour_agent_entrypoint", "tour_agent")
    builder.add_edge("tour_agent_tools", "tour_agent")
    builder.add_conditional_edges(
        "tour_agent",
        RouteUpdater(tour_tools, "tour_agent_tools").route_tool_execution,
        ["tour_agent_tools", "return_to_supervisor", END],
    )

    # Return to supervisor
    builder.add_edge("return_to_supervisor", "supervisor")

    return builder

async def build_graph():
    """
    Build the agent graph asynchronously for LangGraph API.
    Uses MemorySaver instead of PostgreSQL to avoid database setup complexity.

    Returns:
        StateGraph: Compiled agent graph
    """
    # Initialize MCP tools if available
    global MCP
    if MCP_AVAILABLE and len(MCP) == 0:
        try:
            logging.info("→ Initializing MCP tools...")
            from mcps import _initialize_mcp_async
            MCP = await _initialize_mcp_async()
            logging.info(f"→ MCP tools initialized: {len(MCP)} tools available")

            # Update tool lists with MCP tools
            _update_tools_with_mcp()

        except Exception as e:
            logging.warning(f"→ Failed to initialize MCP tools: {e}")

    # Initialize runnables AFTER MCP tools are loaded
    await initialize_runnables()
    logging.info("→ Agent runnables initialized with updated tool lists")

    # Use MemorySaver for simplicity in LangGraph API environment
    memory = MemorySaver()
    logging.info("Using MemorySaver for checkpointing")

    # Create graph builder
    builder = create_graph_builder()

    # Compile and return the graph
    graph = builder.compile(checkpointer=memory)
    logging.info("Graph compiled successfully for LangGraph API")
    return graph
