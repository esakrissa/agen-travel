# backend/rag/__init__.py

"""
Package untuk Retrieval-Augmented Generation (RAG) menggunakan Pinecone.

Package ini menyediakan tools untuk melakukan query terhadap knowledge base 
yang tersimpan di Pinecone vector database untuk customer service agent.

Modules:
    - pinecone: Tools untuk querying dokumen di Pinecone
    - utils: Utility functions untuk koneksi dan manajemen Pinecone

Tools yang tersedia:
    - query_knowledge_base: Melakukan query terhadap index Pinecone untuk mendapatkan jawaban

Example:
    >>> from backend.rag import RAG_TOOLS
    >>> # RAG_TOOLS berisi list tools yang dapat digunakan oleh customer service agent
    >>> print([tool.name for tool in RAG_TOOLS])
    ['query_knowledge_base']
"""

from .pinecone import query_knowledge_base

# List tools RAG yang tersedia untuk customer service agent
RAG_TOOLS = [
    query_knowledge_base,
]

__all__ = ["RAG_TOOLS", "query_knowledge_base"]
