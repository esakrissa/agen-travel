from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import logging
from supabase import AsyncClient
from .handler import ExternalServiceException

# Memuat variabel environment dari file .env
load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    LANGSMITH_TRACING_V2: str
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str
    TAVILY_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_CONNECTION: str
    CORS_ORIGINS: str

    # Konfigurasi Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int
    REDIS_URL: str

    # Konfigurasi JWT
    JWT_SECRET_KEY: str

    # Konfigurasi Email Verification
    SUPABASE_AUTH_ENABLED: str
    EMAIL_VERIFICATION_REDIRECT_URL: str
    PASSWORD_RESET_REDIRECT_URL: str

    # Konfigurasi SMTP
    SMTP_HOST: str
    SMTP_PORT: str
    SMTP_USER: str
    SMTP_PASS : str
    SMTP_ADMIN_EMAIL: str
    SMTP_SENDER_NAME: str

    # Konfigurasi Base URL
    BASE_URL: str

    # Konfigurasi MCP API Keys
    RAPIDAPI_KEY: str
    TRIPADVISOR_API_KEY: str

    # Konfigurasi Database untuk Supabase MCP
    DATABASE_URI: str

    # Konfigurasi RAG
    RAG_MODEL: str
    TEMPERATURE: float
    PINECONE_API_KEY: str
    PINECONE_ENV: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Variabel global untuk menyimpan instance Supabase client
_supabase_client = None

async def get_supabase_client():
    """
    Mengembalikan instance singleton dari Supabase async client.

    Returns:
        Instance Supabase async client

    Raises:
        ExternalServiceException: Jika inisialisasi Supabase client gagal
    """
    global _supabase_client

    try:
        # Mengembalikan client yang sudah ada jika sudah diinisialisasi
        if _supabase_client is not None:
            return _supabase_client

        # Membuat client baru jika belum ada
        settings = get_settings()
        _supabase_client = AsyncClient(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        logging.error(f"Error inisialisasi Supabase client: {e}")
        raise ExternalServiceException(
            message="Gagal menginisialisasi Supabase client",
            detail={"original_error": str(e)}
        )

