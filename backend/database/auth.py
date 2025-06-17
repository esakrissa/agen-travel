from typing import Optional, Dict, Any
import logging
from utils.config import get_supabase_client, get_settings
from utils.auth import AuthUtils
from utils.email import email_service
from utils.handler import DatabaseException, ValidationException, NotFoundException
from models.auth import UserRegisterRequest, UserLoginRequest, UserResponse, AuthResponse, ErrorResponse
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer untuk operasi autentikasi"""

    def __init__(self):
        self._client = None

    async def _get_client(self):
        """Mendapatkan client Supabase"""
        if self._client is None:
            self._client = await get_supabase_client()
        return self._client
        
    async def _get_redis_client(self):
        """
        Mendapatkan Redis client untuk session management
        
        Returns:
            Redis Client atau None jika tidak tersedia
        """
        try:
            # Import Redis di sini untuk menghindari circular import
            from utils.redis import get_redis_client
            return await get_redis_client()
        except Exception as e:
            logger.warning(f"Error getting Redis client: {e}")
            return None

    async def register_user(self, user_data: UserRegisterRequest) -> AuthResponse:
        """
        Registrasi user baru dengan password

        Args:
            user_data (UserRegisterRequest): Data registrasi user

        Returns:
            AuthResponse: Response registrasi
        """
        try:
            logger.info(f"Registering new user: {user_data.email}")

            # Hash password
            hashed_password = AuthUtils.hash_password(user_data.password)

            # Get client
            client = await self._get_client()

            # Cek apakah email sudah terdaftar
            existing_user = await client.table('users').select('id').eq('email', user_data.email).execute()
            if existing_user.data:
                raise ValidationException(
                    message="Email sudah terdaftar",
                    detail={"email": user_data.email}
                )

            # Cek apakah telegram_id sudah terdaftar (jika diberikan)
            if user_data.telegram_id:
                existing_telegram = await client.table('users').select('id').eq('telegram_id', user_data.telegram_id).execute()
                if existing_telegram.data:
                    raise ValidationException(
                        message="Telegram ID sudah terdaftar",
                        detail={"telegram_id": user_data.telegram_id}
                    )

            settings = get_settings()
            auth_user_id = None

            # Jika Supabase Auth diaktifkan, buat user di auth.users
            if settings.SUPABASE_AUTH_ENABLED:
                try:
                    # Buat user di Supabase Auth
                    auth_result = await email_service.create_supabase_user(
                        email=user_data.email,
                        password=user_data.password,
                        user_metadata={
                            "nama": user_data.nama,
                            "telepon": user_data.telepon,
                            "alamat": user_data.alamat,
                            "telegram_id": user_data.telegram_id
                        }
                    )

                    if auth_result.get("success"):
                        auth_user_id = auth_result.get("auth_user_id")
                        logger.info(f"Supabase Auth user created: {auth_user_id}")
                    else:
                        logger.warning(f"Gagal membuat user di Supabase Auth: {auth_result}")

                except Exception as e:
                    logger.warning(f"Error creating Supabase Auth user: {e}")
                    # Lanjutkan dengan registrasi custom jika Supabase Auth gagal

            # Insert user baru langsung ke tabel
            insert_data = {
                'nama': user_data.nama,
                'email': user_data.email,
                'password': hashed_password,
                'telepon': user_data.telepon,
                'alamat': user_data.alamat,
                'telegram_id': user_data.telegram_id,
                'auth_user_id': auth_user_id,
                'is_active': True,
                'is_verified': False,
                'last_login': 'now()'  # Set last_login saat registrasi berhasil
            }

            response = await client.table('users').insert(insert_data).execute()

            if not response.data:
                raise DatabaseException(
                    message="Gagal menyimpan data user",
                    detail={"response": str(response)}
                )

            user_id = response.data[0]['id']

            # Buat record di user_profiles untuk sinkronisasi jika ada auth_user_id
            if auth_user_id:
                try:
                    await client.table('user_profiles').insert({
                        'id': auth_user_id,
                        'user_id': user_id
                    }).execute()
                except Exception as e:
                    logger.warning(f"Gagal membuat user_profiles: {e}")

            # Kirim email verifikasi via Supabase Auth
            email_sent = False
            if settings.SUPABASE_AUTH_ENABLED and auth_user_id:
                try:
                    await email_service.send_verification_email(
                        email=user_data.email,
                        redirect_url=settings.EMAIL_VERIFICATION_REDIRECT_URL
                    )
                    email_sent = True
                    logger.info(f"Email verifikasi dikirim via Supabase Auth: {user_data.email}")
                except Exception as e:
                    logger.error(f"Gagal mengirim email verifikasi: {e}")
                    # Jika gagal kirim email, tetap lanjutkan registrasi
                    # User bisa request resend verification nanti

            # Buat user response object
            user_response = UserResponse(
                id=user_id,
                nama=user_data.nama,
                email=user_data.email,
                telepon=user_data.telepon,
                alamat=user_data.alamat,
                telegram_id=user_data.telegram_id,
                is_active=True,
                is_verified=False,
                last_login=datetime.now(timezone.utc),  # Set last_login saat registrasi
                created_at=datetime.now(timezone.utc)
            )

            # Buat JWT token
            token_data = {
                "user_id": user_id,
                "email": user_data.email
            }
            access_token = AuthUtils.create_access_token(token_data)

            # Simpan session dengan access_token
            await AuthUtils.save_user_session({
                "id": user_id,
                "email": user_data.email,
                "nama": user_data.nama,
                "telepon": user_data.telepon,
                "alamat": user_data.alamat,
                "telegram_id": user_data.telegram_id,
                "auth_user_id": auth_user_id,
                "is_verified": False,
                "last_login": datetime.now(timezone.utc)  # Include last_login dalam session
            }, access_token)

            logger.info(f"User registered successfully: {user_data.email}")

            message = "Registrasi berhasil"
            if email_sent:
                message += ". Silakan cek email Anda untuk verifikasi akun."

            return AuthResponse(
                success=True,
                message=message,
                access_token=access_token,
                token_type="bearer",
                expires_in=60 * 60 * 24,  # 24 jam
                user=user_response
            )

        except (ValidationException, DatabaseException):
            raise
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise DatabaseException(
                message="Gagal melakukan registrasi",
                detail={"original_error": str(e)}
            )

    async def login_user(self, login_data: UserLoginRequest) -> AuthResponse:
        """
        Login user dengan email dan password

        Args:
            login_data (UserLoginRequest): Data login

        Returns:
            AuthResponse: Response login
        """
        try:
            logger.info(f"User login attempt: {login_data.email}")

            # Get client
            client = await self._get_client()

            # Get user data langsung dari tabel
            response = await client.table('users').select('*').eq('email', login_data.email).execute()

            if not response.data:
                raise ValidationException(
                    message="Email atau password salah",
                    detail={"email": login_data.email}
                )

            user_data = response.data[0]

            # Cek apakah user aktif
            if not user_data.get('is_active', True):
                raise ValidationException(
                    message="Akun tidak aktif",
                    detail={"email": login_data.email}
                )

            # Verify password di Python menggunakan bcrypt
            if not AuthUtils.verify_password(login_data.password, user_data['password']):
                raise ValidationException(
                    message="Email atau password salah",
                    detail={"email": login_data.email}
                )

            # Update last_login
            await client.table('users').update({'last_login': 'now()'}).eq('id', user_data['id']).execute()

            # Buat user response object
            user_response = UserResponse(
                id=user_data['id'],
                nama=user_data['nama'],
                email=user_data['email'],
                telepon=user_data.get('telepon'),
                alamat=user_data.get('alamat'),
                telegram_id=user_data.get('telegram_id'),
                is_active=True,
                is_verified=user_data.get('is_verified', False),
                last_login=datetime.now(timezone.utc),  # Set last_login saat login
                created_at=datetime.now(timezone.utc)  # Akan di-update dengan data real
            )

            # Buat JWT token
            token_data = {
                "user_id": user_data['id'],
                "email": user_data['email']
            }
            access_token = AuthUtils.create_access_token(token_data)

            # Simpan session dengan token JWT
            await AuthUtils.save_user_session(user_data, access_token)

            logger.info(f"User logged in successfully: {login_data.email}")

            return AuthResponse(
                success=True,
                message="Login berhasil",
                access_token=access_token,
                token_type="bearer",
                expires_in=60 * 60 * 24,  # 24 jam
                user=user_response
            )

        except (ValidationException, DatabaseException):
            raise
        except Exception as e:
            logger.error(f"Error logging in user: {e}")
            raise DatabaseException(
                message="Gagal melakukan login",
                detail={"original_error": str(e)}
            )

    async def get_user_by_telegram_id(self, telegram_id: str) -> Optional[UserResponse]:
        """
        Mendapatkan user berdasarkan Telegram ID

        Args:
            telegram_id (str): Telegram ID

        Returns:
            Optional[UserResponse]: Data user jika ditemukan
        """
        try:
            logger.info(f"Getting user by telegram ID: {telegram_id}")

            # Get client
            client = await self._get_client()

            # Get user data langsung dari tabel
            response = await client.table('users').select('*').eq('telegram_id', telegram_id).eq('is_active', True).execute()

            if not response.data:
                return None

            user_data = response.data[0]

            return UserResponse(
                id=user_data['id'],
                nama=user_data['nama'],
                email=user_data['email'],
                telepon=user_data.get('telepon'),
                alamat=user_data.get('alamat'),
                telegram_id=user_data.get('telegram_id'),
                is_active=True,
                is_verified=user_data.get('is_verified', False),
                last_login=user_data.get('last_login'),
                created_at=datetime.now(timezone.utc)  # Akan di-update dengan data real
            )

        except Exception as e:
            logger.error(f"Error getting user by telegram ID: {e}")
            return None

    async def link_telegram_user(self, user_id: int, telegram_id: str) -> bool:
        """
        Link user dengan Telegram ID

        Args:
            user_id (int): ID user
            telegram_id (str): Telegram ID

        Returns:
            bool: True jika berhasil
        """
        try:
            logger.info(f"Linking user {user_id} with telegram ID: {telegram_id}")

            # Get client
            client = await self._get_client()

            # Cek apakah user_id valid
            user_check = await client.table('users').select('id').eq('id', user_id).execute()
            if not user_check.data:
                raise ValidationException(
                    message="User tidak ditemukan",
                    detail={"user_id": user_id}
                )

            # Cek apakah telegram_id sudah digunakan
            telegram_check = await client.table('users').select('id').eq('telegram_id', telegram_id).neq('id', user_id).execute()
            if telegram_check.data:
                raise ValidationException(
                    message="Telegram ID sudah digunakan",
                    detail={"telegram_id": telegram_id}
                )

            # Update telegram_id
            response = await client.table('users').update({'telegram_id': telegram_id}).eq('id', user_id).execute()

            if not response.data:
                return False

            # Update session di Redis dengan telegram_id yang baru
            session_data = await AuthUtils.get_user_session(user_id)
            if session_data:
                # Update telegram_id di session
                session_data.telegram_id = telegram_id

                # Simpan kembali session yang sudah di-update dengan access_token
                await AuthUtils.save_user_session({
                    "id": session_data.user_id,
                    "email": session_data.email,
                    "nama": session_data.nama,
                    "telepon": session_data.telepon,
                    "alamat": session_data.alamat,
                    "telegram_id": telegram_id,  # telegram_id yang baru
                    "is_verified": session_data.is_verified
                }, session_data.access_token)

                logger.info(f"Updated Redis session for user {user_id} with telegram_id: {telegram_id}")

            logger.info(f"Successfully linked user {user_id} with telegram ID: {telegram_id}")
            return True

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error linking telegram user: {e}")
            return False

    async def logout_user(self, user_id: int) -> bool:
        """
        Logout user (hapus session)

        Args:
            user_id (int): ID user

        Returns:
            bool: True jika berhasil
        """
        try:
            logger.info(f"Logging out user: {user_id}")

            # Hapus session dari Redis
            success = await AuthUtils.delete_user_session(user_id)

            if success:
                logger.info(f"User {user_id} logged out successfully")

            return success

        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False

    async def resend_verification_email(self, user_id: int) -> Dict[str, Any]:
        """
        Kirim ulang email verifikasi

        Args:
            user_id (int): ID user

        Returns:
            Dict[str, Any]: Response hasil pengiriman email
        """
        try:
            logger.info(f"Resending verification email for user: {user_id}")
            settings = get_settings()

            # Get client
            client = await self._get_client()

            # Get user data
            response = await client.table('users').select('*').eq('id', user_id).execute()

            if not response.data:
                raise ValidationException(
                    message="User tidak ditemukan",
                    detail={"user_id": user_id}
                )

            user_data = response.data[0]

            # Cek apakah user sudah terverifikasi
            if user_data.get('is_verified', False):
                return {
                    "success": False,
                    "message": "Akun sudah terverifikasi"
                }

            email_sent = False
            auth_user_id = user_data.get('auth_user_id')

            # Kirim via Supabase Auth
            if settings.SUPABASE_AUTH_ENABLED and auth_user_id:
                try:
                    await email_service.send_verification_email(
                        email=user_data['email'],
                        redirect_url=settings.EMAIL_VERIFICATION_REDIRECT_URL
                    )
                    email_sent = True
                    logger.info(f"Email verifikasi dikirim ulang via Supabase Auth: {user_data['email']}")
                except Exception as e:
                    logger.error(f"Gagal mengirim email verifikasi: {e}")
            else:
                logger.warning(f"User {user_id} tidak memiliki auth_user_id, tidak bisa kirim email verifikasi")

            if email_sent:
                return {
                    "success": True,
                    "message": "Email verifikasi berhasil dikirim ulang"
                }
            else:
                return {
                    "success": False,
                    "message": "Gagal mengirim email verifikasi"
                }

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error resending verification email: {e}")
            raise DatabaseException(
                message="Gagal mengirim ulang email verifikasi",
                detail={"user_id": user_id, "error": str(e)}
            )

    async def verify_supabase_email_token(self, token: str, token_type: str = "signup") -> Dict[str, Any]:
        """
        Verifikasi email token via Supabase Auth

        Args:
            token (str): Token verifikasi
            token_type (str): Tipe token (signup, recovery)

        Returns:
            Dict[str, Any]: Response hasil verifikasi
        """
        try:
            logger.info(f"Verifying Supabase email token: {token_type}")

            # Verifikasi token via Supabase Auth
            result = await email_service.verify_supabase_token(token, token_type)

            if result.get("success"):
                # Update is_verified di tabel users jika ada user yang sesuai
                supabase_user = result.get("user")
                if supabase_user and supabase_user.get("id"):
                    try:
                        client = await self._get_client()

                        # Update database
                        update_result = await client.table('users').update({
                            'is_verified': True,
                            'updated_at': 'now()'
                        }).eq('auth_user_id', supabase_user["id"]).execute()

                        logger.info(f"User verification status updated for auth_user_id: {supabase_user['id']}")

                        # Cari user_id dari database untuk update session
                        if update_result.data:
                            user_id = update_result.data[0]['id']

                            # Update session di Redis jika ada session aktif
                            session_updated = await AuthUtils.update_user_session_verification(user_id, True)
                            if session_updated:
                                logger.info(f"Session verification status updated untuk user {user_id}")
                            else:
                                logger.info(f"Tidak ada session aktif untuk user {user_id}, skip session update")

                    except Exception as e:
                        logger.warning(f"Gagal update verification status di tabel users: {e}")

                return {
                    "success": True,
                    "message": "Email berhasil diverifikasi",
                    "user": supabase_user
                }
            else:
                return {
                    "success": False,
                    "message": result.get("error", "Token tidak valid")
                }

        except Exception as e:
            logger.error(f"Error verifying Supabase email token: {e}")
            return {
                "success": False,
                "message": "Gagal memverifikasi token"
            }

    async def send_password_reset_email(self, email: str) -> Dict[str, Any]:
        """
        Kirim email reset password

        Args:
            email (str): Email user

        Returns:
            Dict[str, Any]: Response hasil pengiriman email
        """
        try:
            logger.info(f"Sending password reset email to: {email}")
            settings = get_settings()

            # Get client
            client = await self._get_client()

            # Cek apakah email terdaftar
            response = await client.table('users').select('*').eq('email', email).execute()

            if not response.data:
                # Jangan beri tahu bahwa email tidak terdaftar untuk keamanan
                return {
                    "success": True,
                    "message": "Jika email terdaftar, link reset password akan dikirim"
                }

            user_data = response.data[0]
            user_id = user_data['id']
            auth_user_id = user_data.get('auth_user_id')

            email_sent = False

            # Kirim via Supabase Auth jika ada auth_user_id
            if settings.SUPABASE_AUTH_ENABLED and auth_user_id:
                try:
                    await email_service.send_password_reset_email(
                        email=email,
                        redirect_url=settings.PASSWORD_RESET_REDIRECT_URL
                    )
                    email_sent = True
                    logger.info(f"Password reset email sent via Supabase Auth: {email}")
                except Exception as e:
                    logger.error(f"Gagal mengirim password reset email: {e}")
            else:
                logger.warning(f"User dengan email {email} tidak memiliki auth_user_id atau Supabase Auth disabled")

            return {
                "success": True,
                "message": "Jika email terdaftar, link reset password akan dikirim"
            }

        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return {
                "success": False,
                "message": "Gagal mengirim email reset password"
            }

    async def update_user_profile_by_telegram_id(self, telegram_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update profil pengguna berdasarkan Telegram ID
        
        Args:
            telegram_id (str): ID Telegram pengguna
            profile_data (Dict): Data profil yang akan diupdate (nama, telepon, alamat)
            
        Returns:
            Dict: Response hasil update
        """
        try:
            logger.info(f"Updating profile for telegram_id: {telegram_id}")
            
            # Get client
            client = await self._get_client()
            
            # Cek apakah user dengan telegram_id ini ada
            response = await client.table('users').select('*').eq('telegram_id', telegram_id).execute()
            
            if not response.data or len(response.data) == 0:
                logger.warning(f"User with telegram_id {telegram_id} not found")
                return {
                    "success": False,
                    "message": "User tidak ditemukan",
                    "error_code": "USER_NOT_FOUND"
                }
            
            user_data = response.data[0]
            user_id = user_data['id']
            auth_user_id = user_data.get('auth_user_id')
            
            # Filter data yang akan diupdate (hanya ambil yang tidak None dan bukan "string" default)
            update_data = {}
            for field in ['nama', 'telepon', 'alamat']:
                if field in profile_data and profile_data[field] is not None and profile_data[field] != "string":
                    update_data[field] = profile_data[field]
            
            if not update_data:
                logger.warning("No data to update")
                return {
                    "success": False,
                    "message": "Tidak ada data yang diupdate",
                    "error_code": "NO_DATA_TO_UPDATE"
                }
            
            # Update data di tabel users
            update_response = await client.table('users').update(update_data).eq('id', user_id).execute()
            
            if not update_response.data:
                logger.error(f"Failed to update user profile for user_id {user_id}")
                raise DatabaseException(
                    message="Gagal memperbarui profil pengguna",
                    detail={"response": str(update_response)}
                )
            
            # Update auth.users jika ada auth_user_id
            settings = get_settings()
            if settings.SUPABASE_AUTH_ENABLED and auth_user_id:
                try:
                    # Update user metadata di Supabase Auth dengan parameter yang benar
                    await client.auth.admin.update_user_by_id(
                        auth_user_id,  # First positional argument
                        {  # Second positional argument for user metadata
                            "user_metadata": {
                                "nama": update_response.data[0].get('nama'),
                                "telepon": update_response.data[0].get('telepon'),
                                "alamat": update_response.data[0].get('alamat'),
                            }
                        }
                    )
                    logger.info(f"Supabase Auth user metadata updated for auth_user_id: {auth_user_id}")
                except Exception as e:
                    logger.warning(f"Failed to update Supabase Auth metadata: {e}")
            
            # Update session jika ada
            try:
                # Cari dan update session yang ada berdasarkan user_id
                session_id = f"agen_travel:session:user:{user_id}"
                redis_client = await self._get_redis_client()
                
                if redis_client:
                    try:
                        # Cek apakah session ada di Redis
                        session_data = await redis_client.get(session_id)
                        
                        if session_data:
                            # Parse session data
                            session_json = json.loads(session_data)
                            logger.info(f"Found Redis session for user_id: {user_id}")
                            
                            # Update field yang relevan - hanya jika field tidak kosong dan bukan string default
                            updated = False
                            for field in ['nama', 'telepon', 'alamat']:
                                value = profile_data.get(field)
                                if value is not None and value != "string":
                                    session_json[field] = value
                                    updated = True
                            
                            if updated:
                                # Get current TTL
                                ttl = await redis_client.ttl(session_id)
                                if ttl < 0:
                                    ttl = 86400  # Default 24 jam jika tidak ada TTL
                                
                                # Simpan kembali ke Redis dengan TTL yang sama
                                await redis_client.set(
                                    session_id, 
                                    json.dumps(session_json),
                                    ex=ttl  # Gunakan TTL yang ada
                                )
                                logger.info(f"Redis session updated successfully for user_id: {user_id}")
                            else:
                                logger.info(f"No changes to Redis session for user_id: {user_id}")
                        else:
                            logger.warning(f"Redis session not found for user_id: {user_id}")
                    except Exception as e:
                        logger.error(f"Error updating Redis session: {e}")
                else:
                    logger.warning("Redis client not available for session update")
                
            except Exception as e:
                logger.error(f"Failed to update session: {e}")
                # Jangan gagalkan proses jika update session gagal
            
            updated_user = update_response.data[0]
            
            logger.info(f"Profile updated successfully for telegram_id: {telegram_id}")
            
            return {
                "success": True,
                "message": "Profil berhasil diperbarui",
                "user": {
                    "id": updated_user.get('id'),
                    "nama": updated_user.get('nama'),
                    "email": updated_user.get('email'),
                    "telepon": updated_user.get('telepon'),
                    "alamat": updated_user.get('alamat'),
                    "telegram_id": updated_user.get('telegram_id'),
                    "is_verified": updated_user.get('is_verified'),
                    "is_active": updated_user.get('is_active'),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise DatabaseException(
                message="Gagal memperbarui profil pengguna",
                detail={"original_error": str(e)}
            )


# Instance global
auth_service = AuthService()
