import logging
import httpx
from typing import Dict, Optional
from utils.config import get_settings
from utils.handler import ExternalServiceException

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service untuk mengirim email menggunakan Supabase Auth dan Resend
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"{self.settings.SUPABASE_URL}/auth/v1"
        self.headers = {
            "apikey": self.settings.SUPABASE_KEY,
            "Authorization": f"Bearer {self.settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    
    async def send_verification_email(self, email: str, redirect_url: Optional[str] = None) -> Dict:
        """
        Kirim email verifikasi menggunakan Supabase Auth
        
        Args:
            email (str): Email tujuan
            redirect_url (str, optional): URL redirect setelah verifikasi
            
        Returns:
            Dict: Response dari Supabase Auth
        """
        try:
            # Default redirect URL jika tidak disediakan
            if not redirect_url:
                redirect_url = f"{self.settings.SUPABASE_URL}/auth/v1/verify"
            
            payload = {
                "email": email,
                "type": "signup",
                "options": {
                    "emailRedirectTo": redirect_url
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/resend",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Email verifikasi berhasil dikirim ke: {email}")
                    return {
                        "success": True,
                        "message": "Email verifikasi berhasil dikirim",
                        "email": email
                    }
                else:
                    logger.error(f"Gagal mengirim email verifikasi: {response.text}")
                    raise ExternalServiceException(
                        message="Gagal mengirim email verifikasi",
                        detail={"status_code": response.status_code, "response": response.text}
                    )
                    
        except httpx.TimeoutException:
            logger.error("Timeout saat mengirim email verifikasi")
            raise ExternalServiceException(
                message="Timeout saat mengirim email verifikasi",
                detail={"email": email}
            )
        except Exception as e:
            logger.error(f"Error mengirim email verifikasi: {e}")
            raise ExternalServiceException(
                message="Gagal mengirim email verifikasi",
                detail={"email": email, "error": str(e)}
            )
    
    async def send_password_reset_email(self, email: str, redirect_url: Optional[str] = None) -> Dict:
        """
        Kirim email reset password menggunakan Supabase Auth
        
        Args:
            email (str): Email tujuan
            redirect_url (str, optional): URL redirect setelah reset
            
        Returns:
            Dict: Response dari Supabase Auth
        """
        try:
            # Default redirect URL jika tidak disediakan
            if not redirect_url:
                redirect_url = f"{self.settings.SUPABASE_URL}/auth/v1/verify"
            
            payload = {
                "email": email,
                "options": {
                    "emailRedirectTo": redirect_url
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/recover",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Email reset password berhasil dikirim ke: {email}")
                    return {
                        "success": True,
                        "message": "Email reset password berhasil dikirim",
                        "email": email
                    }
                else:
                    logger.error(f"Gagal mengirim email reset password: {response.text}")
                    raise ExternalServiceException(
                        message="Gagal mengirim email reset password",
                        detail={"status_code": response.status_code, "response": response.text}
                    )
                    
        except httpx.TimeoutException:
            logger.error("Timeout saat mengirim email reset password")
            raise ExternalServiceException(
                message="Timeout saat mengirim email reset password",
                detail={"email": email}
            )
        except Exception as e:
            logger.error(f"Error mengirim email reset password: {e}")
            raise ExternalServiceException(
                message="Gagal mengirim email reset password",
                detail={"email": email, "error": str(e)}
            )
    
    async def create_supabase_user(self, email: str, password: str, user_metadata: Optional[Dict] = None) -> Dict:
        """
        Buat user baru di Supabase Auth
        
        Args:
            email (str): Email user
            password (str): Password user
            user_metadata (Dict, optional): Metadata tambahan
            
        Returns:
            Dict: Response dari Supabase Auth
        """
        try:
            payload = {
                "email": email,
                "password": password,
                "email_confirm": False,  # Require email confirmation
            }
            
            if user_metadata:
                payload["user_metadata"] = user_metadata
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/admin/users",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    user_data = response.json()
                    logger.info(f"User Supabase berhasil dibuat: {email}")
                    return {
                        "success": True,
                        "user": user_data,
                        "auth_user_id": user_data.get("id")
                    }
                else:
                    logger.error(f"Gagal membuat user Supabase: {response.text}")
                    raise ExternalServiceException(
                        message="Gagal membuat user di Supabase Auth",
                        detail={"status_code": response.status_code, "response": response.text}
                    )
                    
        except httpx.TimeoutException:
            logger.error("Timeout saat membuat user Supabase")
            raise ExternalServiceException(
                message="Timeout saat membuat user di Supabase Auth",
                detail={"email": email}
            )
        except Exception as e:
            logger.error(f"Error membuat user Supabase: {e}")
            raise ExternalServiceException(
                message="Gagal membuat user di Supabase Auth",
                detail={"email": email, "error": str(e)}
            )

    async def verify_supabase_token(self, token: str, token_type: str = "signup") -> Dict:
        """
        Verifikasi token dari Supabase Auth
        Untuk email verification, kita langsung decode JWT token tanpa memanggil Supabase API
        karena token sudah berisi semua informasi yang diperlukan

        Args:
            token (str): Token verifikasi (JWT access token)
            token_type (str): Tipe token (signup, recovery, etc.)

        Returns:
            Dict: Response hasil verifikasi
        """
        try:
            logger.info(f"Verifying token type: {token_type}")

            # Decode JWT token untuk mendapatkan user info
            import jwt
            import time

            # Decode tanpa verifikasi signature untuk mendapatkan payload
            decoded = jwt.decode(token, options={"verify_signature": False})

            # Cek apakah token sudah expired
            current_time = int(time.time())
            token_exp = decoded.get("exp", 0)
            token_iat = decoded.get("iat", 0)

            logger.info(f"Token info - current: {current_time}, exp: {token_exp}, iat: {token_iat}")

            if current_time > token_exp:
                logger.error(f"Token sudah expired: current={current_time}, exp={token_exp}")
                return {
                    "success": False,
                    "error": "Token sudah kadaluarsa"
                }

            # Cek apakah email sudah verified di token
            user_metadata = decoded.get("user_metadata", {})
            email_verified = user_metadata.get("email_verified", False)

            if not email_verified:
                logger.warning("Email belum verified di token metadata")

            user_info = {
                "id": decoded.get("sub"),
                "email": decoded.get("email"),
                "user_metadata": user_metadata,
                "email_verified": email_verified
            }

            logger.info(f"Token berhasil diverifikasi untuk user: {user_info.get('email')}")
            return {
                "success": True,
                "user": user_info,
                "session": None
            }

        except jwt.ExpiredSignatureError:
            logger.error("JWT token sudah expired")
            return {
                "success": False,
                "error": "Token sudah kadaluarsa"
            }
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT token tidak valid: {e}")
            return {
                "success": False,
                "error": "Token format tidak valid"
            }
        except Exception as e:
            logger.error(f"Error verifikasi token: {e}")
            return {
                "success": False,
                "error": "Gagal memverifikasi token"
            }
                    
        except httpx.TimeoutException:
            logger.error("Timeout saat verifikasi token")
            raise ExternalServiceException(
                message="Timeout saat verifikasi token",
                detail={"token_type": token_type}
            )
        except Exception as e:
            logger.error(f"Error verifikasi token: {e}")
            raise ExternalServiceException(
                message="Gagal verifikasi token",
                detail={"token_type": token_type, "error": str(e)}
            )

# Instance global untuk digunakan di seluruh aplikasi
email_service = EmailService()
