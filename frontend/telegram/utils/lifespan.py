"""
Lifespan events untuk FastAPI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager untuk FastAPI.
    Digunakan untuk menginisialisasi dan membersihkan sumber daya.
    """
    # Kode inisialisasi sebelum aplikasi dimulai
    yield
    # Kode pembersihan setelah aplikasi berhenti
