from fastapi import APIRouter, Depends, HTTPException, status, Header
from models.response import ResponseResponse, ResponseRequest, TruncateResponse, ChatResponse
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from agents.graph import build_graph
from utils.handler import ValidationException, DatabaseException, ExternalServiceException, log_exception
import logging
import time
import uuid
from utils.metrics import AGENT_INVOCATIONS, AGENT_RESPONSE_TIME, ACTIVE_USERS
from utils.config import get_supabase_client
import postgrest.exceptions

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

# Inisialisasi graph agen sekali pada saat modul dimuat untuk menghindari reinisialisasi pada setiap permintaan
# Tidak bisa langsung await pada level modul, jadi pakai variabel untuk menyimpan graph belum terinisialisasi
graph = None

# Fungsi async helper untuk mendapatkan graph
async def get_graph():
    global graph
    if graph is None:
        graph = await build_graph()
        logger.info('Graph percakapan berhasil dimuat')
    return graph

@router.post("/response/", response_model=ResponseResponse, tags=["Response"])
async def generate_response(request: ResponseRequest, thread_id: str = Header('550e8400-e29b-41d4-a716-446655440000', alias="X-THREAD-ID")):
    """
    # 🤖 Chat dengan AI Assistant

    **Berinteraksi dengan sistem multi-agen AI untuk perencanaan perjalanan.**

    *AI assistant dapat membantu mencari hotel, penerbangan, paket tour, dan informasi travel lainnya.*

    ## 📋 Request Body
    - **query**: Pertanyaan atau permintaan pengguna
    - **user_context**: Konteks pengguna (opsional)

    ## 🔧 Headers
    - **X-THREAD-ID**: ID thread percakapan (opsional, akan dibuat otomatis jika tidak ada)

    ## ✅ Response Success (200)
    ```json
    {
        "dialog_state": "supervisor",
        "answer": "Respons dari AI assistant..."
    }
    ```

    ## 💡 Contoh Pertanyaan
    - "Carikan hotel di Bali untuk 2 orang"
    - "Jadwal pesawat Jakarta ke Surabaya besok"
    - "Paket tur ke Yogyakarta 3 hari 2 malam"
    - "Kurs rupiah hari ini"
    """
    query = request.query
    user_context = request.user_context
    logger.info(f'Menerima query: "{query}" dengan thread_id: {thread_id}')

    # Log user context jika ada
    if user_context:
        logger.info(f'User context diterima untuk user: {user_context.get("nama", "Unknown")}')

    # Menambah penghitung pengguna aktif
    ACTIVE_USERS.inc()

    if not query:
        raise ValidationException(
            message="Query tidak boleh kosong",
            detail={"field": "query"}
        )

    try:
        # Mendapatkan graph yang terinisialisasi
        current_graph = await get_graph()

        # Menyiapkan input untuk graph agen
        inputs = [HumanMessage(content=query)]
        state = {
            'messages': inputs,
            'user_context': user_context  # Inject user context ke state
        }
        # Menggunakan recursion limit 25 sesuai preferensi user dan menambahkan error handling
        config = {"configurable": {"thread_id": thread_id, "recursion_limit": 25}}

        # Memanggil graph agen dan mengukur waktu respons dengan error handling khusus
        start_time = time.time()
        try:
            response = await current_graph.ainvoke(input=state, config=config)
        except Exception as graph_error:
            # Tangani GraphRecursionError dan tool call errors secara khusus
            if "GraphRecursionError" in str(graph_error) or "Recursion limit" in str(graph_error):
                logger.warning(f"GraphRecursionError detected: {str(graph_error)}")
                # Berikan respons fallback untuk recursion error
                return JSONResponse({
                    'dialog_state': 'supervisor',
                    'answer': 'Maaf, permintaan Anda terlalu kompleks untuk diproses saat ini. Silakan coba dengan permintaan yang lebih sederhana atau spesifik.'
                })
            elif "tool_calls" in str(graph_error) or "tool_call_id" in str(graph_error):
                logger.warning(f"Tool call error detected: {str(graph_error)}")
                # Berikan respons fallback untuk tool call error
                return JSONResponse({
                    'dialog_state': 'supervisor',
                    'answer': 'Maaf, terjadi kesalahan dalam memproses permintaan. Silakan coba lagi dengan permintaan yang berbeda.'
                })
            else:
                # Re-raise error lain untuk ditangani oleh exception handler umum
                raise graph_error

        response_time = time.time() - start_time

        logger.info('Berhasil menghasilkan respons dari graph agen')

        # Mengekstrak data respons
        dialog_states = response.get('dialog_state', [])
        dialog_state = dialog_states[-1] if dialog_states else 'supervisor'

        # Mencatat metrik Prometheus
        AGENT_INVOCATIONS.labels(agent_type=dialog_state).inc()
        AGENT_RESPONSE_TIME.labels(agent_type=dialog_state).observe(response_time)

        messages = response.get('messages', [])
        message_content = messages[-1].content if messages else ''

        # Mengembalikan respons yang diformat
        return JSONResponse({
            'dialog_state': dialog_state,
            'answer': message_content
        })
    except Exception as e:
        log_exception(e)

        # Menentukan jenis exception untuk respons error yang tepat
        if isinstance(e, (KeyError, IndexError)):
            raise DatabaseException(
                message="Error memproses respons agen",
                detail={"original_error": str(e)}
            )
        else:
            raise ExternalServiceException(
                message="Error berkomunikasi dengan sistem agen",
                detail={"original_error": str(e)}
            )
    finally:
        # Mengurangi penghitung pengguna aktif ketika permintaan selesai
        ACTIVE_USERS.dec()

@router.post("/truncate/", response_model=TruncateResponse, tags=["Response"], response_model_exclude_none=True, response_model_exclude_unset=True)
async def truncate_history():
    """
    # 🗑️ Hapus Semua Riwayat Chat

    **Menghapus seluruh data percakapan dari sistem.**

    *Operasi ini akan menghapus semua checkpoints dan chat history. Tidak dapat dibatalkan!*

    ## ⚠️ Peringatan
    - **Operasi permanen**: Data tidak dapat dikembalikan
    - **Mempengaruhi semua user**: Menghapus seluruh riwayat sistem
    - **Gunakan dengan hati-hati**: Hanya untuk maintenance atau reset sistem

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Berhasil menghapus data dari tabel checkpoints dan chat_history",
        "details": {
            "checkpoints_deleted": 150,
            "chat_history_deleted": 300
        }
    }
    ```

    ## 🎯 Kegunaan
    - Maintenance sistem
    - Reset development environment
    - Cleanup data testing
    """
    logger.info('Menghapus data dari tabel checkpoints dan chat_history')

    try:
        # Mendapatkan klien Supabase
        client = await get_supabase_client()

        # Mencoba panggilan rpc
        response = await client.rpc('truncate_chat_data').execute()

        # Memproses hasil
        result = response.data

        # Jika hasilnya adalah array dengan satu item (dari fungsi yang telah diperbarui)
        if isinstance(result, list) and len(result) > 0:
            result_data = result[0]
            logger.info(f"Berhasil menghapus data: {result_data.get('rows_deleted', {})}")

            return JSONResponse({
                'status': 'success',
                'message': 'Berhasil menghapus data dari tabel checkpoints dan chat_history',
                'details': result_data.get('rows_deleted', {})
            })

        # Respons default jika format tidak sesuai ekspektasi
        return JSONResponse({
            'status': 'success',
            'message': 'Berhasil menghapus data dari tabel checkpoints dan chat_history'
        })

    except Exception as e:
        log_exception(e)
        # Jika operasi sebenarnya berhasil tapi kita mendapat error dari klien
        if "status': 'success'" in str(e):
            return JSONResponse({
                'status': 'success',
                'message': 'Berhasil menghapus data dari tabel checkpoints dan chat_history'
            })
        # Error
        raise DatabaseException(
            message="Error saat menghapus data dari tables",
            detail={"original_error": str(e)}
        )


@router.delete("/chat/{thread_id}", response_model=ChatResponse, tags=["Chat"])
async def delete_chat(thread_id: str):
    """
    # 🗂️ Hapus Chat Tertentu

    **Menghapus percakapan spesifik berdasarkan thread ID.**

    *Operasi ini akan menghapus semua data terkait chat termasuk checkpoints dan history.*

    ## 🔧 Path Parameters
    - **thread_id**: ID unik thread percakapan yang akan dihapus

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Berhasil menghapus chat 550e8400-e29b-41d4-a716-446655440000",
        "thread_id": "550e8400-e29b-41d4-a716-446655440000",
        "details": {
            "checkpoints_deleted": 5,
            "messages_deleted": 12
        }
    }
    ```

    ## 🎯 Kegunaan
    - Hapus percakapan yang tidak diperlukan
    - Cleanup chat history pengguna
    - Manajemen storage database

    ## ⚠️ Catatan
    - Operasi permanen dan tidak dapat dibatalkan
    - Hanya mempengaruhi thread yang ditentukan
    """
    logger.info(f'Menghapus chat: {thread_id}')

    try:
        # Mendapatkan klien Supabase
        client = await get_supabase_client()

        # Mencoba panggilan rpc delete_chat
        response = await client.rpc('delete_chat', {'p_thread_id': thread_id}).execute()

        # Memproses hasil - sekarang berupa array dari table function
        result = response.data
        result_data = result[0] if result and len(result) > 0 else {}

        logger.info(f"Berhasil menghapus chat {thread_id}: {result_data}")

        return JSONResponse({
            'status': 'success',
            'message': f'Berhasil menghapus chat {thread_id}',
            'thread_id': thread_id,
            'details': result_data
        })

    except Exception as e:
        log_exception(e)
        raise DatabaseException(
            message=f"Error saat menghapus chat {thread_id}",
            detail={"original_error": str(e)}
        )


@router.post("/chat/{user_id}", response_model=ChatResponse, tags=["Chat"])
async def create_new_chat(user_id: str, platform: str = "telegram"):
    """
    # 💬 Buat Chat Baru

    **Membuat thread percakapan baru untuk pengguna.**

    *Setiap chat memiliki thread ID unik untuk melacak konteks percakapan.*

    ## 🔧 Path Parameters
    - **user_id**: ID pengguna yang akan membuat chat

    ## 🔧 Query Parameters
    - **platform**: Platform asal chat (`telegram`, `web`, `mobile`) - default: `telegram`

    ## ✅ Response Success (200)
    ```json
    {
        "status": "success",
        "message": "Berhasil membuat chat baru",
        "thread_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "123",
        "details": {
            "platform": "telegram",
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
    ```

    ## 🎯 Kegunaan
    - Inisialisasi percakapan baru
    - Tracking konteks per user
    - Isolasi percakapan antar platform

    ## 💡 Tips
    - Simpan thread_id untuk percakapan selanjutnya
    - Gunakan platform yang sesuai untuk analytics
    """
    # Generate thread ID baru
    new_thread_id = str(uuid.uuid4())

    logger.info(f'Membuat chat baru untuk user {user_id}: {new_thread_id}')

    try:
        # Mendapatkan klien Supabase
        client = await get_supabase_client()

        # Mencoba panggilan rpc create_new_chat
        response = await client.rpc('create_new_chat', {
            'p_user_id': user_id,
            'p_new_thread_id': new_thread_id,
            'p_platform': platform
        }).execute()

        # Memproses hasil - sekarang berupa array dari table function
        result = response.data
        result_data = result[0] if result and len(result) > 0 else {}

        logger.info(f"Berhasil membuat chat baru untuk user {user_id}: {new_thread_id}")

        return JSONResponse({
            'status': 'success',
            'message': f'Berhasil membuat chat baru',
            'thread_id': new_thread_id,
            'user_id': user_id,
            'details': result_data
        })

    except Exception as e:
        log_exception(e)
        raise DatabaseException(
            message=f"Error saat membuat chat baru untuk user {user_id}",
            detail={"original_error": str(e)}
        )