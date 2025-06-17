import os
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
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import logging
import nest_asyncio
import asyncio

from psycopg_pool import AsyncConnectionPool

# Import RAG tools
try:
    from rag import RAG_TOOLS
    RAG_AVAILABLE = True
    logging.info(f"RAG tools loaded: {len(RAG_TOOLS)} tools available")
except ImportError as e:
    logging.warning(f"RAG tools not available: {e}")
    RAG_TOOLS = []
    RAG_AVAILABLE = False

# Import MCP tools dengan lazy loading
# MCP tools yang tersedia: Booking.com, TripAdvisor, Airbnb, dan Supabase
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

config = get_settings()

# Setup environment variabel untuk LangSmith tracing
os.environ["LANGSMITH_TRACING_V2"] = config.LANGSMITH_TRACING_V2
os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT
os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT

# Inisialisasi koneksi Supabase dengan error handling
DB_URI = config.SUPABASE_CONNECTION

# Global pool variable for the whole application
pool = None

# Initialize a memory saver as default
memory = MemorySaver()

# Inisialisasi LLM dengan konfigurasi untuk mencegah parallel tool calls
# Berdasarkan solusi dari GitHub discussions untuk mengatasi tool_call_id error
llm = ChatOpenAI(temperature=0,
                 api_key=config.OPENAI_API_KEY,
                 model=config.OPENAI_MODEL,
                 model_kwargs={
                     'parallel_tool_calls': False  # Disable parallel tool calls untuk mencegah tool_call_id error
                 }
                )

async def create_agent_runnable(llm, tools, agent_prompt):
    """Fungsi helper untuk membuat agent runnable dengan konfigurasi konsisten"""
    return await get_runnable(
        llm=llm,
        tools=tools + [CompleteOrEscalate],
        agent_prompt=agent_prompt
    )

# Mendefinisikan tools untuk setiap agent
customer_service_tools = [get_user_booking_history, get_booking_details,
                         cancel_hotel_booking, cancel_flight_booking, cancel_tour_booking,
                         search_currency_rates, search_travel_articles, search_general_info]

# Tambahkan RAG tools ke customer service jika tersedia
if RAG_AVAILABLE:
    customer_service_tools.extend(RAG_TOOLS)
    logging.info(f"RAG tools added to customer service: {[t.name for t in RAG_TOOLS]}")

hotel_tools = [get_hotels, search_hotels_by_location, get_hotel_details, check_available_rooms,
               book_hotel_room, process_hotel_payment, check_unpaid_bookings, get_booking_details,
               cancel_hotel_booking]

flight_tools = [get_flights, search_flights_by_route, get_flight_details,
                book_flight, process_flight_payment, check_unpaid_bookings, get_booking_details,
                cancel_flight_booking]

tour_tools = [get_tours, search_tours_by_destination, get_tour_details, check_tour_availability,
              book_tour, process_tour_payment, check_unpaid_bookings, get_booking_details,
              cancel_tour_booking]

supervisor_tools = [ToHotelAgent, ToFlightAgent, ToTourAgent, ToCustomerService, ToSupervisor, CompleteOrEscalate]

def _update_tools_with_mcp():
    """Update tool lists with MCP tools."""
    global customer_service_tools, hotel_tools, flight_tools, tour_tools, MCP

    if MCP_AVAILABLE and MCP:
        # Filter MCP tools berdasarkan kategori
        booking_mcp_tools = [tool for tool in MCP if 'booking' in tool.name.lower()]
        tripadvisor_mcp_tools = [tool for tool in MCP if 'tripadvisor' in tool.name.lower()]
        airbnb_mcp_tools = [tool for tool in MCP if 'airbnb' in tool.name.lower()]
        supabase_mcp_tools = [tool for tool in MCP if any(keyword in tool.name.lower() for keyword in ['supabase', 'execute_sql', 'list_schemas', 'list_objects', 'get_object_details', 'explain_query', 'analyze_workload', 'analyze_query', 'analyze_db_health', 'get_top_queries'])]

        # Tambahkan ke hotel_tools (booking.com, airbnb tools, tripadvisor untuk pencarian restoran dan supabase untuk database operations)
        hotel_tools.extend(booking_mcp_tools)
        hotel_tools.extend(airbnb_mcp_tools)
        hotel_tools.extend(tripadvisor_mcp_tools)
        hotel_tools.extend(supabase_mcp_tools)

        # Tambahkan ke customer_service_tools (tripadvisor untuk review dan info, supabase untuk database query)
        customer_service_tools.extend(tripadvisor_mcp_tools)
        customer_service_tools.extend(supabase_mcp_tools)

        # Tambahkan ke flight_tools (booking.com flight tools dan supabase untuk database operations)
        flight_booking_tools = [tool for tool in booking_mcp_tools if 'flight' in tool.name.lower()]
        flight_tools.extend(flight_booking_tools)
        flight_tools.extend(supabase_mcp_tools)

        # Tambahkan ke tour_tools (tripadvisor untuk atraksi wisata dan supabase untuk database operations)
        tour_tools.extend(tripadvisor_mcp_tools)
        tour_tools.extend(supabase_mcp_tools)


        logging.info(f"MCP tools integrated: {len(booking_mcp_tools)} booking, {len(tripadvisor_mcp_tools)} tripadvisor, {len(airbnb_mcp_tools)} airbnb, {len(supabase_mcp_tools)} supabase")
        logging.info(f"Tools distribution - Hotel: {len(hotel_tools)}, Flight: {len(flight_tools)}, Customer Service: {len(customer_service_tools)}, Tour: {len(tour_tools)}")
    elif not MCP_AVAILABLE:
        # Only log if MCP module is not available, not if just not initialized yet
        logging.info("MCP module not available, using only local tools")

# Initial attempt to add MCP tools (will be empty if not initialized yet)
_update_tools_with_mcp()

# Inisialisasi runnables - akan diinisialisasi di build_graph()
customer_service_runnable = None
hotel_runnable = None
flight_runnable = None
tour_runnable = None
supervisor_runnable = None

# Apply nest_asyncio untuk kompatibilitas
nest_asyncio.apply()

async def initialize_runnables():
    """Initialize all agent runnables"""
    global customer_service_runnable, hotel_runnable, flight_runnable, tour_runnable, supervisor_runnable

    # Debug logging untuk melihat tools yang tersedia
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
    # Validasi bahwa runnables sudah diinisialisasi
    if not all([supervisor_runnable, customer_service_runnable, hotel_runnable, flight_runnable, tour_runnable]):
        raise ValueError("Agent runnables must be initialized before creating graph builder")

    builder = StateGraph(State)

    builder.add_node("supervisor", Assistant(supervisor_runnable))

    # Entry points untuk setiap agen
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

    # Agen nodes
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

    # Routing dari START
    builder.add_conditional_edges(START, route_to_workflow)

    # Routing dari supervisor
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

async def initialize_pool():
    """Inisialisasi pool koneksi database untuk aplikasi"""
    global pool
    if pool is None:
        # Membuat pool dengan open=False untuk mencegah pembukaan otomatis di konstruktor
        pool = AsyncConnectionPool(DB_URI, min_size=1, max_size=10, open=False,
                                  kwargs={"autocommit": True})
        # Membuka pool secara eksplisit
        await pool.open()
        return pool
    return pool

async def build_graph():
    """
    Membangun graph agen secara asynchronous.

    Returns:
        StateGraph: Graph agen yang telah dikompilasi
    """
    global memory, pool

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

    # Inisialisasi PostgreSQL connection pool dan checkpointer
    try:
        # Get or initialize the pool
        pool = await initialize_pool()

        # Membuat PostgreSQL checkpointer dengan connection pool
        memory = AsyncPostgresSaver(pool)

        # Setup PostgreSQL database schema
        await memory.setup()
        logging.info("PostgreSQL schema telah diinisialisasi")

        # Buat graph builder
        builder = create_graph_builder()

        try:
            # StateGraph.compile() tidak mendukung async secara langsung,
            # tapi tetap menggunakan fungsi async untuk konsistensi
            graph = builder.compile(checkpointer=memory)
            return graph
        except Exception as e:
            logging.error(f"Error kompilasi graph: {e}")
            # Fallback ke memory checkpointer jika kompilasi gagal
            fallback_memory = MemorySaver()
            return builder.compile(checkpointer=fallback_memory)
    except Exception as e:
        logging.error(f"Error setup PostgreSQL: {e}")
        # Fallback ke memory checkpointer jika setup gagal
        memory = MemorySaver()
        logging.warning("Menggunakan checkpoint in-memory sebagai fallback")

        # Buat graph builder dengan memory saver
        builder = create_graph_builder()
        return builder.compile(checkpointer=memory)

# Function to close the pool when the application shuts down
async def close_pool():
    global pool
    if pool is not None:
        await pool.close()
        logging.info("Database pool closed")

    # Cleanup MCP connections
    if MCP_AVAILABLE:
        try:
            from mcp import cleanup_mcp
            await cleanup_mcp()
            logging.info("MCP connections cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up MCP connections: {e}")