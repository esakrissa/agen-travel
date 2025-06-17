from fastapi import APIRouter
from api.v1 import response, cache, auth, email

router = APIRouter()

# Urutan router berdasarkan prioritas tags:
# 1. Authentication - endpoint autentikasi (login, register, dll)
router.include_router(
    auth.router,
    prefix="/api/v1"
)

# 2. Email Verification - endpoint verifikasi email
router.include_router(
    email.router,
    prefix="/api/v1"
)

# 3. Response - endpoint utama untuk chat/percakapan
router.include_router(
    response.router,
    prefix="/api/v1"
)

# 4. Cache - endpoint manajemen cache
router.include_router(
    cache.router,
    prefix="/api/v1"
)

# Note: Default endpoints (health check, metrics) didefinisikan di main.py