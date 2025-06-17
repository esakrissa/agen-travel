from agents.state import State
from models.agents import CompleteOrEscalate
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import END
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from typing import Callable, Literal, List
import logging
from utils.datetime import format_time_wita, parse_datetime, format_datetime
from utils.handler import log_exception

# Setup logger level modul
logger = logging.getLogger(__name__)

# Fungsi helper untuk routing dan Graph
class RouteUpdater:
    def __init__(self, tools, update_tool):
        self.tools = tools
        self.update_tool = update_tool

    async def route_tool_execution(self, state: State):
        try:
            route = tools_condition(state)
            if route == END:
                return END

            tool_calls = state.get("messages", [])
            if not tool_calls or len(tool_calls) == 0:
                logger.warning("Tidak ada pesan ditemukan dalam state selama routing")
                return END

            tool_calls = tool_calls[-1].tool_calls
            if not tool_calls:
                logger.warning("Tidak ada tool calls ditemukan dalam pesan terbaru")
                return END

            did_cancel = any(tc.get("name") == CompleteOrEscalate.__name__ for tc in tool_calls)
            if did_cancel:
                return "return_to_supervisor"

            safe_toolnames = [t.name for t in self.tools]
            if all(tc.get("name") in safe_toolnames for tc in tool_calls):
                return self.update_tool

            # Kasus default
            return END
        except Exception as e:
            log_exception(e)
            logger.error(f"Error dalam route_tool_execution: {str(e)}")
            return END


def create_entry_node(agent_name: str, new_dialog_state: str) -> Callable:
    async def entry_node(state: State) -> dict:
        try:
            messages = state.get("messages", [])
            if not messages or len(messages) == 0:
                logger.warning(f"Tidak ada pesan ditemukan saat membuat entry node untuk {agent_name}")
                # Mengembalikan respons valid minimal
                return {
                    "messages": [],
                    "dialog_state": new_dialog_state,
                }

            tool_calls = messages[-1].tool_calls
            if not tool_calls or len(tool_calls) == 0:
                logger.warning(f"Tidak ada tool calls ditemukan saat membuat entry node untuk {agent_name}")
                # Mengembalikan respons valid minimal
                return {
                    "messages": [],
                    "dialog_state": new_dialog_state,
                }

            # Tangani semua tool call, bukan hanya yang pertama
            entry_messages = []
            for tool_call in tool_calls:
                tool_call_id = tool_call.get("id", "unknown_id")
                entry_messages.append(
                    ToolMessage(
                        content=f"Anda adalah {agent_name} dengan DOMAIN KHUSUS. Perhatikan percakapan di atas."
                        f" WAJIB: Gunakan HANYA tool yang tersedia untuk domain Anda. DILARANG menangani permintaan di luar domain."
                        f" ESCALATE LANGSUNG: Jika user meminta sesuatu di luar domain Anda, SEGERA gunakan CompleteOrEscalate dengan alasan spesifik."
                        f" JANGAN JAWAB SENDIRI untuk permintaan di luar domain - biarkan supervisor mengarahkan ke agen yang tepat."
                        f" Fokus pada tugas dalam domain Anda hingga selesai atau user meminta hal lain yang perlu escalate.",
                        tool_call_id=tool_call_id,
                    )
                )

            return {
                "messages": entry_messages,
                "dialog_state": new_dialog_state,
            }
        except Exception as e:
            log_exception(e)
            logger.error(f"Error membuat entry node untuk {agent_name}: {str(e)}")
            # Mengembalikan respons valid minimal
            return {
                "messages": [],
                "dialog_state": new_dialog_state,
            }

    return entry_node


async def handle_tool_error(state) -> dict:
    """
    Menangani error tool dengan memastikan setiap tool call mendapat response.
    Berdasarkan solusi dari GitHub discussions untuk mencegah tool_call_id error.
    """
    try:
        error = state.get("error")
        if not error:
            logger.warning("Tidak ada error ditemukan dalam state selama handle_tool_error")
            return {"messages": []}

        messages_list = state.get("messages", [])
        if not messages_list or len(messages_list) == 0:
            logger.warning("Tidak ada pesan ditemukan dalam state selama handle_tool_error")
            return {"messages": []}

        # Ambil pesan terakhir yang memiliki tool_calls
        last_message = messages_list[-1]
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            logger.warning("Tidak ada tool calls ditemukan dalam pesan terbaru selama handle_tool_error")
            return {"messages": []}

        tool_calls = last_message.tool_calls

        # Pastikan semua tool call mendapatkan respons untuk mencegah tool_call_id error
        messages = []
        for tc in tool_calls:
            tool_call_id = tc.get("id")
            if not tool_call_id:
                logger.warning(f"Tool call tanpa ID ditemukan: {tc}")
                continue

            # Buat error message yang informatif
            error_content = f"Terjadi kesalahan saat menjalankan tool: {repr(error)}"
            if "tool_calls" in str(error) or "tool_call_id" in str(error):
                error_content = "Maaf, terjadi kesalahan dalam memproses permintaan. Silakan coba dengan permintaan yang lebih sederhana."

            messages.append(
                ToolMessage(
                    content=error_content,
                    tool_call_id=tool_call_id,
                )
            )

        logger.info(f"Membuat {len(messages)} tool response messages untuk menangani error")
        return {
            "messages": messages
        }
    except Exception as e:
        log_exception(e)
        logger.error(f"Error dalam handle_tool_error: {str(e)}")
        # Pastikan mengembalikan respons kosong yang valid
        return {"messages": []}


def create_tool_node_with_fallback(tools: list) -> dict:
    try:
        return ToolNode(tools).with_fallbacks(
            [RunnableLambda(handle_tool_error)], exception_key="error"
        )
    except Exception as e:
        log_exception(e)
        logger.error(f"Error membuat tool node dengan fallback: {str(e)}")
        # Mengembalikan handler default yang tidak melakukan apa-apa sebagai fallback
        return RunnableLambda(lambda x: x)


async def pop_dialog_state(state: State) -> dict:
    """Output status percakapan dan kembali ke supervisor agent.

    Hal ini memungkinkan graph secara lengkap dan eksplisit untuk melacak alur percakapan dan mendelegasikan kontrol
    ke sub graph tertentu.
    """
    try:
        messages = []
        msgs = state.get("messages", [])

        if msgs and len(msgs) > 0 and msgs[-1].tool_calls:
            # Tangani semua tool call, bukan hanya yang pertama
            for tool_call in msgs[-1].tool_calls:
                tool_call_id = tool_call.get("id", "unknown_id")
                messages.append(
                    ToolMessage(
                        content="Sub agen telah mengembalikan kontrol karena permintaan di luar domain mereka. "
                        "Sebagai supervisor, LANGSUNG route ke agen yang sesuai berdasarkan permintaan user tanpa konfirmasi ulang. "
                        "Perhatikan percakapan sebelumnya untuk memahami kebutuhan user dan arahkan ke agen yang tepat.",
                        tool_call_id=tool_call_id,
                    )
                )
        return {
            "dialog_state": "pop",
            "messages": messages,
        }
    except Exception as e:
        log_exception(e)
        logger.error(f"Error dalam pop_dialog_state: {str(e)}")
        return {
            "dialog_state": "pop",
            "messages": [],
        }

async def route_to_workflow(
    state: State,
) -> Literal[
    "supervisor",
    "customer_service",
    "hotel_agent",
    "flight_agent",
    "tour_agent",
]:
    """Jika berada dalam status yang didelegasikan, arahkan langsung ke sub agen yang sesuai."""
    try:
        dialog_state = state.get("dialog_state")
        if not dialog_state:
            return "supervisor"
        if not isinstance(dialog_state, list) or len(dialog_state) == 0:
            logger.warning(f"Format dialog_state tidak valid: {dialog_state}")
            return "supervisor"
        return dialog_state[-1]
    except Exception as e:
        log_exception(e)
        logger.error(f"Error dalam route_to_workflow: {str(e)}")
        return "supervisor"

async def route_supervisor(
    state: State,
):
    try:
        # Check if tools_condition is already an awaitable or just a regular function
        route = tools_condition(state)
        if route == END:
            return END

        msgs = state.get("messages", [])
        if not msgs or len(msgs) == 0:
            logger.warning("Tidak ada pesan ditemukan dalam state selama routing supervisor")
            return END

        tool_calls = msgs[-1].tool_calls
        if tool_calls:
            # Periksa semua tool call, bukan hanya yang pertama
            # Prioritaskan berdasarkan urutan: ToHotelAgent, ToFlightAgent, ToTourAgent, ToCustomerService, ToSupervisor
            has_hotel = False
            has_flight = False
            has_tour = False
            has_customer_service = False
            has_supervisor = False

            for tool_call in tool_calls:
                if not tool_call.get("name"):
                    continue

                tool_name = tool_call["name"]
                if tool_name == "ToHotelAgent":
                    has_hotel = True
                elif tool_name == "ToFlightAgent":
                    has_flight = True
                elif tool_name == "ToTourAgent":
                    has_tour = True
                elif tool_name == "ToCustomerService":
                    has_customer_service = True
                elif tool_name == "ToSupervisor":
                    has_supervisor = True

            # Prioritaskan routing berdasarkan urutan
            if has_hotel:
                return "hotel_agent_entrypoint"
            elif has_flight:
                return "flight_agent_entrypoint"
            elif has_tour:
                return "tour_agent_entrypoint"
            elif has_customer_service:
                return "customer_service_entrypoint"
            elif has_supervisor:
                # Jika tool ToSupervisor dipanggil, tetap di supervisor
                return END
            else:
                # Jika tool tidak dikenali, tetap di supervisor
                logger.warning(f"Tool tidak dikenali dalam tool calls")
                return END
        # Tidak ada panggilan tool berarti agen utama menangani respons secara langsung
        return END
    except Exception as e:
        log_exception(e)
        logger.error(f"Error dalam route_supervisor: {str(e)}")
        return END

# Memformat fungsi helper untuk format waktu
async def extract_time_safely(input_str: str) -> str:
    """
    Mengambil bagian waktu dari string datetime dengan aman.

    Args:
        input_str (str): String datetime

    Returns:
        str: Waktu yang diekstrak atau nilai default pada kesalahan
    """
    if not input_str:
        logger.warning("String input kosong diberikan ke extract_time_safely")
        return "00:00"

    try:
        dt = await parse_datetime(input_str)
        return await format_datetime(dt, "time")
    except Exception as e:
        log_exception(e)
        logger.error(f"Error mengambil waktu dari {input_str}: {e}")
        return "00:00"  # Default time sebagai fallback

async def format_times_with_wita(time_list: List[str]) -> List[str]:
    """
    Memformat daftar string waktu untuk mencakup zona WITA.

    Args:
        time_list (List[str]): Daftar string waktu

    Returns:
        List[str]: Daftar string waktu yang diformat dengan WITA
    """
    if not time_list:
        return []

    formatted_times = []
    for time in time_list:
        if not time:
            formatted_times.append("waktu tidak valid")
            continue

        try:
            formatted_times.append(format_time_wita(time))
        except Exception as e:
            log_exception(e)
            logger.warning(f"Error memformat waktu dengan WITA: {time}, {str(e)}")
            formatted_times.append("waktu tidak valid")
    return formatted_times

async def extract_time_from_datetime_string(datetime_str: str) -> str:
    """
    Mengambil bagian waktu dari format string datetime umum.

    Args:
        datetime_str (str): Input datetime string

    Returns:
        str: Bagian waktu yang diekstrak
    """
    if not datetime_str:
        logger.warning("String datetime kosong diberikan ke extract_time_from_datetime_string")
        return "00:00"

    try:
        if ' ' in datetime_str:
            return datetime_str.split(' ')[-1]
        elif 'T' in datetime_str:
            return datetime_str.split('T')[-1]
        return datetime_str
    except Exception as e:
        log_exception(e)
        logger.error(f"Error mengambil waktu dari string datetime {datetime_str}: {e}")
        return "00:00"  # Default time sebagai fallback