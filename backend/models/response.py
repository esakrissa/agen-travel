from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ErrorResponse(BaseModel):
    error: str
    detail: str


class ResponseRequest(BaseModel):
    query: str = Field(..., description="Permintaan dari pengguna")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Konteks user yang sedang login")


class ResponseResponse(BaseModel):
    answer: str = Field(..., description="Response dari agen travel")
    dialog_state: str = Field(..., description="Status dialog saat ini")


class TruncateResponse(BaseModel):
    status: str = Field(..., description="Status operasi", example="success")
    message: str = Field(..., description="Pesan hasil operasi", example="Berhasil menghapus data dari tabel checkpoints dan chat_history")


class ChatResponse(BaseModel):
    status: str = Field(..., description="Status operasi", example="success")
    message: str = Field(..., description="Pesan hasil operasi")
    thread_id: Optional[str] = Field(None, description="ID chat")
    user_id: Optional[str] = Field(None, description="ID pengguna")
    details: Optional[Dict[str, Any]] = Field(None, description="Detail tambahan operasi")