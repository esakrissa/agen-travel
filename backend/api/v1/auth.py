from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from models.auth import (
    UserRegisterRequest, UserLoginRequest, AuthResponse, ErrorResponse,
    LinkTelegramRequest, TelegramAuthRequest,
    SessionData, UserProfileUpdateRequest
)
from database.auth import auth_service
from utils.auth import get_current_user_with_session, AuthUtils
from utils.handler import ValidationException, DatabaseException, log_exception
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, responses={400: {"model": ErrorResponse}})
async def register_user(user_data: UserRegisterRequest):
    """
    # 🔐 Registrasi Pengguna Baru

    **Membuat akun pengguna baru dengan email dan password.**

    *Endpoint ini akan mengirimkan email verifikasi setelah registrasi berhasil.*

    ## 📋 Request Body
    - **email**: Email valid pengguna
    - **password**: Password minimal 8 karakter
    - **nama**: Nama lengkap pengguna

    ## ✅ Response Success (201)
    ```json
    {
        "success": true,
        "message": "Registrasi berhasil",
        "user": {...},
        "access_token": "jwt_token"
    }
    ```

    ## ❌ Response Error (400)
    - Email sudah terdaftar
    - Password tidak memenuhi kriteria
    - Data tidak valid
    """
    try:
        logger.info(f"Registration request for email: {user_data.email}")

        result = await auth_service.register_user(user_data)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result.model_dump(mode='json')
        )

    except ValidationException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="VALIDATION_ERROR",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except DatabaseException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="DATABASE_ERROR",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )


@router.post("/login", response_model=AuthResponse, responses={400: {"model": ErrorResponse}})
async def login_user(login_data: UserLoginRequest):
    """
    # 🔑 Login Pengguna

    **Autentikasi pengguna dengan email dan password.**

    *Menghasilkan JWT token untuk akses ke endpoint yang memerlukan autentikasi.*

    ## 📋 Request Body
    - **email**: Email terdaftar
    - **password**: Password pengguna

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Login berhasil",
        "user": {...},
        "access_token": "jwt_token"
    }
    ```

    ## ❌ Response Error (401)
    - Email atau password salah
    - Akun belum diverifikasi
    """
    try:
        logger.info(f"Login request for email: {login_data.email}")

        result = await auth_service.login_user(login_data)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(mode='json')
        )

    except ValidationException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="AUTHENTICATION_FAILED",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except DatabaseException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="DATABASE_ERROR",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )


@router.post("/logout")
async def logout_user(current_user: SessionData = Depends(get_current_user_with_session)):
    """
    # 🚪 Logout Pengguna

    **Menghapus session pengguna dan membatalkan akses token.**

    *Endpoint ini memerlukan autentikasi dengan Bearer token.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Logout berhasil"
    }
    ```
    """
    try:
        logger.info(f"Logout request for user: {current_user.user_id}")

        success = await auth_service.logout_user(current_user.user_id)

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Logout berhasil"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    success=False,
                    error="Gagal melakukan logout",
                    error_code="LOGOUT_FAILED"
                ).model_dump(mode='json')
            )

    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )


@router.get("/me", response_model=SessionData)
async def get_current_user_info(current_user: SessionData = Depends(get_current_user_with_session)):
    """
    # 👤 Informasi Pengguna Saat Ini

    **Mendapatkan detail profil pengguna yang sedang login.**

    *Endpoint ini memerlukan autentikasi dengan Bearer token.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## ✅ Response Success (200)
    ```json
    {
        "user_id": 123,
        "email": "wayanbagus@gmail.com",
        "nama": "Wayan Bagus",
        "email_verified": true,
        "telegram_id": "123456789"
    }
    ```
    """
    try:
        logger.info(f"Get user info request for user: {current_user.user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=current_user.model_dump(mode='json')
        )

    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )


@router.post("/telegram/link")
async def link_telegram_account(
    link_data: LinkTelegramRequest,
    current_user: SessionData = Depends(get_current_user_with_session)
):
    """
    # 📱 Link Akun dengan Telegram

    **Menghubungkan akun pengguna dengan Telegram user ID.**

    *Setelah di-link, pengguna dapat mengakses layanan melalui bot Telegram.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## 📋 Request Body
    - **telegram_id**: ID pengguna Telegram (string)

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Akun berhasil di-link dengan Telegram"
    }
    ```

    ## ❌ Response Error
    - **400**: Telegram ID sudah digunakan atau tidak valid
    - **401**: Token tidak valid
    """
    try:
        logger.info(f"Link telegram request for user {current_user.user_id} with telegram ID: {link_data.telegram_id}")

        success = await auth_service.link_telegram_user(
            current_user.user_id,
            link_data.telegram_id
        )

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Akun berhasil di-link dengan Telegram"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    success=False,
                    error="Gagal melakukan link dengan Telegram",
                    error_code="LINK_FAILED"
                ).model_dump(mode='json')
            )

    except ValidationException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="VALIDATION_ERROR",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )


@router.post("/telegram/session-check")
async def check_telegram_session(request: TelegramAuthRequest):
    """
    # 🔍 Cek Session Telegram

    **Memeriksa status session pengguna berdasarkan Telegram ID.**

    *Endpoint ini digunakan oleh bot Telegram untuk mengecek apakah pengguna sudah login.*

    ## 📋 Request Body
    - **telegram_id**: ID pengguna Telegram (string)

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "session_found": true,
        "message": "Session aktif ditemukan",
        "user": {
            "id": 123,
            "email": "wayanbagus@gmail.com",
            "nama": "Wayan Bagus"
        },
        "access_token": "jwt_token"
    }
    ```

    ## 📱 Untuk Bot Telegram
    - Cek otomatis saat pengguna berinteraksi
    - Validasi token yang tersimpan
    - Cleanup session yang expired
    """
    try:
        logger.info(f"Session check request for telegram_id: {request.telegram_id}")

        # Cari user berdasarkan telegram_id
        user = await auth_service.get_user_by_telegram_id(request.telegram_id)

        if not user:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "session_found": False,
                    "message": "User tidak ditemukan"
                }
            )

        # Cek session di Redis
        session_data = await AuthUtils.get_user_session(user.id)

        if session_data:
            # Validasi apakah token masih valid
            if session_data.access_token:
                try:
                    # Verify token
                    AuthUtils.verify_token(session_data.access_token)

                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "success": True,
                            "session_found": True,
                            "message": "Session aktif ditemukan",
                            "user": user.model_dump(mode='json'),
                            "access_token": session_data.access_token
                        }
                    )
                except:
                    # Token expired atau invalid, hapus session
                    await AuthUtils.delete_user_session(user.id)
                    logger.info(f"Expired session deleted for user {user.id}")

                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "success": True,
                            "session_found": False,
                            "message": "Session expired dan telah dihapus"
                        }
                    )
            else:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "success": True,
                        "session_found": False,
                        "message": "Session tidak memiliki token"
                    }
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "session_found": False,
                    "message": "Session tidak ditemukan"
                }
            )

    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )


@router.get("/verify-token")
async def verify_token(current_user: SessionData = Depends(get_current_user_with_session)):
    """
    # ✅ Verifikasi JWT Token

    **Memverifikasi validitas JWT token dan mengembalikan informasi pengguna.**

    *Endpoint ini berguna untuk validasi token di aplikasi frontend atau mobile.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token yang akan diverifikasi

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Token valid",
        "user": {
            "user_id": 123,
            "email": "wayanbagus@gmail.com",
            "nama": "Wayan Bagus",
            "email_verified": true
        }
    }
    ```

    ## ❌ Response Error (401)
    - Token expired atau tidak valid
    - Token tidak ditemukan di header
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Token valid",
                "user": current_user.model_dump(mode='json')
            }
        )

    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                success=False,
                error="Token tidak valid",
                error_code="INVALID_TOKEN"
            ).model_dump(mode='json')
        )


@router.post("/refresh-verification")
async def refresh_verification_status(request: TelegramAuthRequest):
    """
    # 🔄 Refresh Status Verifikasi

    **Refresh status verifikasi user berdasarkan Telegram ID dan sync dengan database.**

    *Endpoint ini berguna untuk Telegram bot mengecek status verifikasi terbaru setelah user melakukan verifikasi email.*

    ## 📋 Request Body
    - **telegram_id**: ID pengguna Telegram (string)

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "is_verified": true,
        "message": "Status verifikasi berhasil diperbarui",
        "user": {
            "id": 123,
            "email": "wayanbagus@gmail.com",
            "nama": "Wayan Bagus",
            "is_verified": true
        }
    }
    ```

    ## 📱 Untuk Bot Telegram
    - Cek status verifikasi terbaru dari database
    - Update session jika status berubah
    - Return status terbaru untuk bot
    """
    try:
        logger.info(f"Refresh verification status request for telegram_id: {request.telegram_id}")

        # Cari user berdasarkan telegram_id
        user = await auth_service.get_user_by_telegram_id(request.telegram_id)

        if not user:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": False,
                    "message": "User tidak ditemukan"
                }
            )

        # Update session verification status jika ada session aktif
        session_updated = await AuthUtils.update_user_session_verification(user.id, user.is_verified)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "is_verified": user.is_verified,
                "message": "Status verifikasi berhasil diperbarui" if session_updated else "Status verifikasi dicek",
                "user": user.model_dump(mode='json')
            }
        )

    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Gagal refresh status verifikasi",
                error_code="REFRESH_VERIFICATION_ERROR"
            ).model_dump(mode='json')
        )


@router.post("/users/update-profile", response_model=AuthResponse, responses={400: {"model": ErrorResponse}})
async def update_profile(request: UserProfileUpdateRequest):
    """
    # 👤 Update Profil Pengguna

    **Update profil pengguna berdasarkan Telegram ID.**

    *Endpoint ini tidak memerlukan autentikasi JWT dan digunakan khusus untuk update via Telegram Bot.*

    ## 📋 Request Body
    - **telegram_id**: ID Telegram pengguna (wajib)
    - **nama**: Nama lengkap pengguna (opsional)
    - **telepon**: Nomor telepon pengguna (opsional)
    - **alamat**: Alamat lengkap pengguna (opsional)

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Profil berhasil diperbarui",
        "user": {
            "id": 1,
            "nama": "Nama Baru",
            "telepon": "081234567890",
            "alamat": "Alamat Baru",
            ...
        }
    }
    ```

    ## ❌ Response Error (400)
    - User tidak ditemukan
    - Data tidak valid
    - Tidak ada data yang diupdate
    """
    try:
        logger.info(f"Update profile request for telegram_id: {request.telegram_id}")
        
        # Extract the profile data
        profile_data = {}
        if request.nama is not None:
            profile_data["nama"] = request.nama
        if request.telepon is not None:
            profile_data["telepon"] = request.telepon
        if request.alamat is not None:
            profile_data["alamat"] = request.alamat
            
        # Call the service
        result = await auth_service.update_user_profile_by_telegram_id(
            telegram_id=request.telegram_id,
            profile_data=profile_data
        )
        
        if not result.get("success"):
            error_code = result.get("error_code", "VALIDATION_ERROR")
            status_code = status.HTTP_400_BAD_REQUEST if error_code == "USER_NOT_FOUND" else status.HTTP_400_BAD_REQUEST
            
            return JSONResponse(
                status_code=status_code,
                content=ErrorResponse(
                    success=False,
                    error=result.get("message", "Gagal memperbarui profil"),
                    error_code=error_code
                ).model_dump(mode='json')
            )
            
        # Return successful response without UserResponse conversion
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": result.get("message", "Profil berhasil diperbarui"),
                "user": result.get("user", {})
            }
        )
    
    except ValidationException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="VALIDATION_ERROR",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except DatabaseException as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=e.message,
                error_code="DATABASE_ERROR",
                detail=e.detail
            ).model_dump(mode='json')
        )
    except Exception as e:
        log_exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Terjadi kesalahan internal server",
                error_code="INTERNAL_ERROR"
            ).model_dump(mode='json')
        )
