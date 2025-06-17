# backend/rag/utils.py

"""
Utility functions untuk RAG dengan Pinecone vector database.

Module ini menyediakan fungsi-fungsi helper untuk:
- Koneksi ke Pinecone index yang sudah ada
- Setup embeddings untuk query
- Manajemen Pinecone vector store
"""

import logging
from typing import Optional

from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from utils.config import get_settings

# Variabel global
logger = logging.getLogger(__name__)

# Dapatkan konfigurasi dari settings
settings = get_settings()

# Validasi environment variables
if not settings.PINECONE_API_KEY:
    logger.error("PINECONE_API_KEY tidak ditemukan di environment variables")
    raise ValueError("PINECONE_API_KEY harus diset untuk menggunakan RAG tools")

# Inisialisasi Pinecone client
_pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Konfigurasi embeddings
_EMBED = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.OPENAI_API_KEY
)


def get_existing_store(index_name: str) -> Optional[PineconeVectorStore]:
    """
    Dapatkan PineconeVectorStore untuk index yang sudah ada.
    
    Fungsi ini akan:
    1. Cek apakah index sudah ada
    2. Return PineconeVectorStore instance jika ada
    3. Return None jika index tidak ditemukan
    
    Args:
        index_name: Nama index yang sudah ada
        
    Returns:
        PineconeVectorStore instance jika index ada, None jika tidak ada
        
    Raises:
        Exception: Jika terjadi error saat mengakses Pinecone
    """
    try:
        # Cek apakah index ada
        existing_indexes = [idx["name"] for idx in _pc.list_indexes()]
        
        if index_name not in existing_indexes:
            logger.warning(f"Index '{index_name}' tidak ditemukan. Index yang tersedia: {existing_indexes}")
            return None
            
        logger.info(f"Menggunakan index Pinecone yang sudah ada: {index_name}")
        
        # Return PineconeVectorStore untuk index yang sudah ada
        return PineconeVectorStore(
            index=_pc.Index(index_name),
            embedding=_EMBED,
            text_key="page_content",
        )
        
    except Exception as e:
        logger.error(f"Error saat mengakses Pinecone index '{index_name}': {e}")
        raise


def validate_pinecone_connection() -> bool:
    """
    Validasi koneksi ke Pinecone.
    
    Returns:
        bool: True jika koneksi berhasil, False jika gagal
    """
    try:
        # Test koneksi dengan list indexes
        indexes = _pc.list_indexes()
        logger.info(f"Koneksi Pinecone berhasil. Index yang tersedia: {[idx['name'] for idx in indexes]}")
        return True
    except Exception as e:
        logger.error(f"Gagal terkoneksi ke Pinecone: {e}")
        return False


def get_available_indexes() -> list:
    """
    Dapatkan daftar index yang tersedia di Pinecone.
    
    Returns:
        list: Daftar nama index yang tersedia
    """
    try:
        indexes = _pc.list_indexes()
        return [idx["name"] for idx in indexes]
    except Exception as e:
        logger.error(f"Error saat mengambil daftar index: {e}")
        return []
