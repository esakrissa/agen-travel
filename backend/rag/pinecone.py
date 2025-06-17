# backend/rag/pinecone.py

"""
Tools untuk Retrieval-Augmented Generation menggunakan Pinecone vector database.

Module ini menyediakan tools untuk melakukan query terhadap knowledge base
dan FAQ yang tersimpan di Pinecone index "agen-travel-faq".
"""

import logging
from typing import Optional

from langchain_core.tools import tool
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI

from .utils import get_existing_store, validate_pinecone_connection
from utils.config import get_settings

logger = logging.getLogger(__name__)

# Dapatkan konfigurasi dari settings
settings = get_settings()


def get_rag_llm() -> ChatOpenAI:
    """
    Dapatkan LLM instance untuk RAG.

    Returns:
        ChatOpenAI instance yang dikonfigurasi untuk RAG
    """
    return ChatOpenAI(
        model=settings.RAG_MODEL,
        temperature=settings.TEMPERATURE,
        api_key=settings.OPENAI_API_KEY
    )


# System prompt untuk RAG (sesuai dengan rag_references)
_SYSTEM_PROMPT = (
    "Jawab **hanya** menggunakan konteks di bawah ini. "
    "Jika konteks tidak menjawab pertanyaan, balas 'Maaf, saya tidak menemukan informasi tersebut dalam knowledge base kami. Silakan hubungi customer service untuk bantuan lebih lanjut.'\n\n"
    "Konteks:\n{context}"
)

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", "{input}")
])


@tool
async def query_knowledge_base(question: str, k: int = 5) -> str:
    """
    Mencari informasi dari knowledge base dan FAQ agen travel.

    Tool ini melakukan pencarian semantik di Pinecone index "agen-travel-faq"
    dan menggunakan LLM untuk menghasilkan jawaban berdasarkan konteks yang ditemukan.

    Args:
        question: Pertanyaan dalam bahasa natural tentang layanan travel, FAQ, atau kebijakan
        k: Jumlah dokumen yang akan diambil untuk konteks (default: 5, max: 20)

    Returns:
        String jawaban berdasarkan knowledge base atau pesan jika informasi tidak ditemukan

    Example:
        >>> query_knowledge_base("Bagaimana cara membatalkan booking hotel?")
        "Untuk membatalkan booking hotel, Anda dapat..."

        >>> query_knowledge_base("Apa kebijakan refund untuk penerbangan?", k=10)
        "Kebijakan refund untuk penerbangan adalah..."
    """
    try:
        # Validasi input
        if not question or len(question.strip()) == 0:
            return "Pertanyaan tidak boleh kosong. Silakan ajukan pertanyaan yang spesifik."
            
        # Batasi jumlah dokumen yang diambil
        k = max(1, min(k, 20))
        
        # Validasi koneksi Pinecone
        if not validate_pinecone_connection():
            return "Maaf, terjadi masalah koneksi ke knowledge base. Silakan coba lagi nanti atau hubungi customer service."
            
        # Dapatkan vector store untuk index yang sudah ada
        store = get_existing_store("agen-travel-faq")
        
        if not store:
            return "Maaf, knowledge base tidak tersedia saat ini. Silakan hubungi customer service untuk bantuan."
            
        # Setup retriever dengan konfigurasi yang optimal (sesuai rag_references)
        retriever = store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 20,  # Gunakan k=20 seperti di rag_references
                "score_threshold": 0.15  # Threshold untuk relevansi
            }
        )

        # Dapatkan LLM untuk RAG
        llm = get_rag_llm()

        logger.info(f"Menggunakan model {settings.RAG_MODEL} untuk query: {question[:50]}...")

        # Buat chain untuk menggabungkan dokumen (sesuai rag_references)
        combine_docs_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=_PROMPT
        )

        # Buat retrieval chain
        rag_chain = create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=combine_docs_chain,
        )

        # Jalankan query
        result = rag_chain.invoke({"input": question})
        
        # Ekstrak jawaban
        answer = result.get("answer", "")
        
        # Dapatkan dokumen sumber untuk logging
        source_docs = result.get("context", [])
        
        if source_docs:
            logger.info(f"Query berhasil dengan {len(source_docs)} dokumen relevan ditemukan")
        else:
            logger.warning(f"Tidak ada dokumen relevan ditemukan untuk query: {question}")
            
        # Return jawaban atau pesan default jika kosong
        if answer and answer.strip():
            return answer.strip()
        else:
            return "Maaf, saya tidak menemukan informasi tersebut dalam knowledge base kami. Silakan hubungi customer service untuk bantuan lebih lanjut."
            
    except Exception as e:
        logger.exception(f"Error saat melakukan query knowledge base: {e}")
        return f"Maaf, terjadi kesalahan saat mencari informasi. Silakan coba lagi atau hubungi customer service. Error: {str(e)}"
