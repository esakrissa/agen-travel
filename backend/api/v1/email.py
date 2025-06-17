from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging
import os
from database.auth import auth_service
from utils.handler import DatabaseException, ValidationException
from utils.auth import get_current_user_with_session
from models.auth import SessionData
from utils.config import get_settings

logger = logging.getLogger(__name__)

# Inisialisasi settings untuk mendapatkan BASE_URL
settings = get_settings()

router = APIRouter(prefix="/email", tags=["Email Verification"])

class ResendVerificationRequest(BaseModel):
    """Request model untuk resend verification email"""
    user_id: int

class PasswordResetRequest(BaseModel):
    """Request model untuk password reset"""
    email: EmailStr

class VerifyTokenRequest(BaseModel):
    """Request model untuk verify token"""
    token: str
    token_type: str = "signup"

class VerifyTokenResponse(BaseModel):
    """Response model untuk token verification"""
    success: bool
    message: str
    user_id: str = None
    email: str = None
    nama: str = None

@router.post("/resend-verification", response_model=Dict[str, Any])
async def resend_verification_email(
    request: ResendVerificationRequest,
    current_user: SessionData = Depends(get_current_user_with_session)
):
    """
    # 📧 Kirim Ulang Email Verifikasi

    **Mengirim ulang email verifikasi ke alamat email pengguna.**

    *Endpoint ini memerlukan autentikasi dan hanya bisa digunakan untuk akun sendiri.*

    ## 🔒 Authorization Required
    - **Bearer Token**: JWT token dari login

    ## 📋 Request Body
    - **user_id**: ID pengguna (harus sama dengan pengguna yang login)

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Email verifikasi berhasil dikirim"
    }
    ```

    ## ❌ Response Error
    - **403**: Tidak diizinkan mengirim email untuk user lain
    - **400**: Email sudah terverifikasi atau error lainnya
    """
    try:
        # Pastikan user hanya bisa resend untuk dirinya sendiri
        if current_user.user_id != request.user_id:
            raise HTTPException(
                status_code=403,
                detail="Tidak diizinkan mengirim email verifikasi untuk user lain"
            )
        
        result = await auth_service.resend_verification_email(request.user_id)
        
        if result["success"]:
            logger.info(f"Email verifikasi berhasil dikirim ulang untuk user: {request.user_id}")
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except ValidationException as e:
        logger.warning(f"Validation error resending verification email: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        logger.error(f"Database error resending verification email: {e.message}")
        raise HTTPException(status_code=500, detail="Gagal mengirim ulang email verifikasi")
    except Exception as e:
        logger.error(f"Unexpected error resending verification email: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan sistem")

@router.get("/verify-email")
async def verify_email(
    token: str = Query(None, description="Token verifikasi email"),
    type: str = Query("signup", description="Tipe token (signup, recovery)")
):
    """
    # ✉️ Verifikasi Email dari Link

    **Memverifikasi email pengguna menggunakan token dari link email.**

    *Endpoint ini dipanggil otomatis ketika pengguna mengklik link verifikasi di email.*

    ## 🔧 Query Parameters
    - **token**: Token verifikasi dari email (opsional)
    - **type**: Tipe token - `signup` untuk verifikasi email, `recovery` untuk reset password

    ## ✅ Response Success (302)
    - Redirect ke halaman sukses jika verifikasi berhasil
    - Redirect ke halaman error jika token tidak valid

    ## 🔄 Redirect Behavior
    - **Dengan token**: Proses verifikasi langsung
    - **Tanpa token**: Redirect ke halaman pemroses fragment

    ## 💡 Penggunaan
    - Link otomatis dari email verifikasi
    - Callback dari Supabase Auth
    - Tidak perlu dipanggil manual
    """
    try:
        # Jika ada token di query parameter, proses langsung
        if token:
            result = await auth_service.verify_supabase_email_token(token, type)

            if result["success"]:
                logger.info(f"Email berhasil diverifikasi: {type}")
                return RedirectResponse(
                    url=f"{settings.BASE_URL}/static/redirect.html?status=success",
                    status_code=302
                )
            else:
                logger.warning(f"Gagal verifikasi email token: {result['message']}")
                return RedirectResponse(
                    url=f"{settings.BASE_URL}/static/redirect.html?status=error&message={result['message']}",
                    status_code=302
                )
        else:
            # Jika tidak ada token di query parameter, redirect ke halaman yang bisa memproses fragment
            logger.info("No token in query parameter, redirecting to fragment processor")
            return RedirectResponse(
                url=f"{settings.BASE_URL}/static/redirect.html",
                status_code=302
            )

    except Exception as e:
        logger.error(f"Unexpected error verifying email: {e}")
        return RedirectResponse(
            url=f"{settings.BASE_URL}/static/redirect.html?status=error&message=Terjadi kesalahan sistem",
            status_code=302
        )

@router.post("/verify-email-api", response_model=VerifyTokenResponse)
async def verify_email_api(request: VerifyTokenRequest):
    """
    # 🔗 Verifikasi Email via API

    **Endpoint API untuk verifikasi email secara programmatic.**

    *Berguna untuk testing, mobile app, atau integrasi dengan sistem lain.*

    ## 📋 Request Body
    - **token**: Token verifikasi dari email
    - **token_type**: Tipe token (`signup` atau `recovery`)

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Email berhasil diverifikasi",
        "user_id": "123",
        "email": "wayanbagus@gmail.com",
        "nama": "Wayan Bagus"
    }
    ```

    ## ❌ Response Error
    - Token tidak valid atau expired
    - Token sudah digunakan sebelumnya

    ## 🎯 Kegunaan
    - Testing verifikasi email
    - Mobile app integration
    - Custom verification flow
    """
    try:
        result = await auth_service.verify_supabase_email_token(request.token, request.token_type)

        if result["success"]:
            logger.info(f"Email berhasil diverifikasi via API: {request.token_type}")
            user_data = result.get("user", {})
            return VerifyTokenResponse(
                success=True,
                message=result["message"],
                user_id=user_data.get("id"),
                email=user_data.get("email"),
                nama=user_data.get("user_metadata", {}).get("nama")
            )
        else:
            logger.warning(f"Gagal verifikasi email token via API: {result['message']}")
            return VerifyTokenResponse(
                success=False,
                message=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Unexpected error verifying email via API: {e}")
        return VerifyTokenResponse(
            success=False,
            message="Terjadi kesalahan sistem"
        )

@router.post("/forgot-password", response_model=Dict[str, Any])
async def forgot_password(request: PasswordResetRequest):
    """
    # 🔑 Lupa Password

    **Mengirim email reset password ke alamat email pengguna.**

    *Endpoint ini akan mengirim link reset password jika email terdaftar di sistem.*

    ## 📋 Request Body
    - **email**: Alamat email yang terdaftar

    ## ✅ Response Success (200)
    ```json
    {
        "success": true,
        "message": "Jika email terdaftar, link reset password akan dikirim"
    }
    ```

    ## 🔒 Keamanan
    - Selalu return success untuk mencegah email enumeration
    - Link reset hanya valid untuk waktu terbatas
    - Hanya email terdaftar yang akan menerima link

    ## 📧 Email yang Dikirim
    - Link reset password yang aman
    - Instruksi cara reset password
    - Peringatan keamanan
    """
    try:
        result = await auth_service.send_password_reset_email(request.email)
        
        logger.info(f"Password reset email request untuk: {request.email}")
        
        # Selalu return success untuk keamanan (tidak membocorkan info email terdaftar atau tidak)
        return {
            "success": True,
            "message": result["message"]
        }
            
    except Exception as e:
        logger.error(f"Unexpected error sending password reset email: {e}")
        return {
            "success": True,
            "message": "Jika email terdaftar, link reset password akan dikirim"
        }

@router.get("/reset-password")
async def reset_password_callback(
    token: str = Query(..., description="Token reset password"),
    type: str = Query("recovery", description="Tipe token")
):
    """
    # 🔄 Callback Reset Password

    **Endpoint callback untuk reset password dari link email.**

    *Dipanggil otomatis ketika pengguna mengklik link reset password di email.*

    ## 🔧 Query Parameters
    - **token**: Token reset password dari email
    - **type**: Tipe token - default: `recovery`

    ## ✅ Response Success (302)
    - Redirect ke halaman reset password jika token valid
    - Redirect ke halaman error jika token tidak valid

    ## 🔄 Redirect Behavior
    - **Token valid**: Redirect ke form reset password
    - **Token invalid/expired**: Redirect ke halaman error

    ## 💡 Penggunaan
    - Callback otomatis dari email reset password
    - Tidak perlu dipanggil manual
    - Bagian dari flow reset password

    ## 🔒 Keamanan
    - Token hanya valid sekali pakai
    - Expired setelah waktu tertentu
    - Validasi ketat dari Supabase Auth
    """
    try:
        # Verifikasi token terlebih dahulu
        result = await auth_service.verify_supabase_email_token(token, type)
        
        if result["success"]:
            logger.info(f"Password reset token valid")
            # Redirect ke halaman reset password dengan token
            return RedirectResponse(
                url=f"{settings.BASE_URL}/auth/reset-password?token={token}&status=valid",
                status_code=302
            )
        else:
            logger.warning(f"Invalid password reset token: {result.get('message', 'Token tidak valid')}")
            # Redirect ke halaman error
            return RedirectResponse(
                url=f"{settings.BASE_URL}/auth/reset-password?status=error&message=Token tidak valid atau sudah kadaluarsa",
                status_code=302
            )
            
    except Exception as e:
        logger.error(f"Unexpected error in password reset callback: {e}")
        return RedirectResponse(
            url=f"{settings.BASE_URL}/auth/reset-password?status=error&message=Terjadi kesalahan sistem",
            status_code=302
        )

@router.get("/templates/verification")
async def get_verification_template():
    """
    # 📧 Template Email Verifikasi

    **Menyediakan template HTML untuk email verifikasi.**

    *Template ini digunakan oleh Supabase GoTrue untuk mengirim email verifikasi yang custom.*

    ## ✅ Response Success (200)
    - Content-Type: `text/html`
    - Template HTML yang sudah di-styling

    ## 🎨 Template Features
    - Design responsif untuk mobile dan desktop
    - Branding sesuai aplikasi travel
    - Call-to-action button yang jelas
    - Informasi keamanan dan support

    ## 🔧 Penggunaan
    - Otomatis dipanggil oleh Supabase Auth
    - Tidak perlu dipanggil manual
    - Bagian dari konfigurasi email custom

    ## ❌ Response Error (404)
    - Template file tidak ditemukan
    """
    try:
        template_path = os.path.join("static", "templates", "email-verification.html")

        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail="Template tidak ditemukan")

        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        return HTMLResponse(content=template_content, media_type="text/html")

    except Exception as e:
        logger.error(f"Error serving verification template: {e}")
        raise HTTPException(status_code=500, detail="Gagal memuat template")

@router.get("/templates/password-reset")
async def get_password_reset_template():
    """
    # 🔑 Template Email Reset Password

    **Menyediakan template HTML untuk email reset password.**

    *Template ini digunakan oleh Supabase GoTrue untuk mengirim email reset password yang custom.*

    ## ✅ Response Success (200)
    - Content-Type: `text/html`
    - Template HTML yang sudah di-styling

    ## 🎨 Template Features
    - Design konsisten dengan template verifikasi
    - Instruksi reset password yang jelas
    - Peringatan keamanan
    - Link bantuan dan support

    ## 🔧 Penggunaan
    - Otomatis dipanggil oleh Supabase Auth
    - Triggered saat forgot password
    - Bagian dari flow reset password

    ## ❌ Response Error (404)
    - Template file tidak ditemukan
    """
    try:
        template_path = os.path.join("static", "templates", "password-reset.html")

        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail="Template tidak ditemukan")

        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        return HTMLResponse(content=template_content, media_type="text/html")

    except Exception as e:
        logger.error(f"Error serving password reset template: {e}")
        raise HTTPException(status_code=500, detail="Gagal memuat template")

@router.get("/health")
async def health_check():
    """Health check endpoint untuk email verification service"""
    return {
        "status": "healthy",
        "service": "email_verification",
        "message": "Email verification service berjalan normal"
    }
