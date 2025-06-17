import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from utils.config import get_settings
from models.auth import TokenData, SessionData
from utils.cache import redis_cache

# Konfigurasi
settings = get_settings()
SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 jam

# Security scheme untuk FastAPI
security = HTTPBearer()

logger = logging.getLogger(__name__)


class AuthUtils:
    """Utility class untuk autentikasi dan JWT"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password menggunakan bcrypt

        Args:
            password (str): Password plain text

        Returns:
            str: Hashed password
        """
        try:
            # Generate salt dan hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing password"
            )

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password dengan hash

        Args:
            plain_password (str): Password plain text
            hashed_password (str): Hashed password dari database

        Returns:
            bool: True jika password cocok
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Membuat JWT access token

        Args:
            data (Dict): Data yang akan di-encode dalam token
            expires_delta (Optional[timedelta]): Waktu kadaluarsa custom

        Returns:
            str: JWT token
        """
        try:
            to_encode = data.copy()

            # Set waktu kadaluarsa
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

            to_encode.update({
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access"
            })

            # Encode JWT
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt

        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating access token"
            )

    @staticmethod
    def verify_token(token: str) -> TokenData:
        """
        Verify dan decode JWT token

        Args:
            token (str): JWT token

        Returns:
            TokenData: Data dari token

        Raises:
            HTTPException: Jika token invalid
        """
        try:
            # Decode JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Validasi data yang diperlukan
            user_id: int = payload.get("user_id")
            email: str = payload.get("email")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")

            if user_id is None or email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Buat TokenData object
            token_data = TokenData(
                user_id=user_id,
                email=email,
                exp=exp,
                iat=iat
            )

            return token_data

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def save_user_session(user_data: Dict[str, Any], access_token: Optional[str] = None, session_duration: int = 86400) -> str:
        """
        Simpan session user ke Redis dengan format key yang konsisten

        Args:
            user_data (Dict): Data user
            access_token (Optional[str]): JWT access token
            session_duration (int): Durasi session dalam detik (default 24 jam)

        Returns:
            str: Session key
        """
        try:
            # Gunakan format key yang konsisten: agen_travel:session:user:{user_id}
            session_key = redis_cache.generate_session_key(user_data['id'])

            # Hitung waktu kadaluarsa token jika ada
            token_expires_at = None
            if access_token:
                try:
                    # Decode token untuk mendapatkan exp time
                    decoded = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
                    token_expires_at = datetime.fromtimestamp(decoded.get('exp', 0))
                except jwt.JWTError:
                    logger.warning(f"Gagal decode token untuk mendapatkan exp time")

            # Buat session data
            session_data = SessionData(
                user_id=user_data['id'],
                email=user_data['email'],
                nama=user_data['nama'],
                telepon=user_data.get('telepon'),
                alamat=user_data.get('alamat'),
                telegram_id=user_data.get('telegram_id'),
                is_verified=user_data.get('is_verified', False),
                access_token=access_token,
                token_expires_at=token_expires_at,
                login_time=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc)
            )

            # Simpan ke Redis
            await redis_cache.set(
                session_key,
                session_data.model_dump(),
                ttl=session_duration
            )

            logger.info(f"Session dengan token JWT berhasil disimpan untuk user {user_data['id']} dengan key: {session_key}")
            return session_key

        except Exception as e:
            logger.error(f"Error saving user session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error saving user session"
            )

    @staticmethod
    async def get_user_session(user_id: int) -> Optional[SessionData]:
        """
        Ambil session user dari Redis dengan format key yang konsisten

        Args:
            user_id (int): ID user

        Returns:
            Optional[SessionData]: Data session jika ada
        """
        try:
            # Gunakan format key yang konsisten: agen_travel:session:user:{user_id}
            session_key = redis_cache.generate_session_key(user_id)
            session_data = await redis_cache.get(session_key)

            if session_data:
                # Update last activity
                session_obj = SessionData(**session_data)
                session_obj.last_activity = datetime.now(timezone.utc)

                # Save updated session
                await redis_cache.set(session_key, session_obj.model_dump(), ttl=86400)

                logger.debug(f"Session ditemukan dan diperbarui untuk user {user_id} dengan key: {session_key}")
                return session_obj

            logger.debug(f"Session tidak ditemukan untuk user {user_id} dengan key: {session_key}")
            return None

        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            return None


    @staticmethod
    async def delete_user_session(user_id: int) -> bool:
        """
        Hapus session user dari Redis dengan format key yang konsisten

        Args:
            user_id (int): ID user

        Returns:
            bool: True jika berhasil
        """
        try:
            # Gunakan format key yang konsisten: agen_travel:session:user:{user_id}
            session_key = redis_cache.generate_session_key(user_id)
            result = await redis_cache.delete(session_key)
            logger.info(f"Session deleted for user {user_id} dengan key: {session_key}, result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error deleting user session: {e}")
            return False

    @staticmethod
    async def update_user_session_verification(user_id: int, is_verified: bool = True) -> bool:
        """
        Update status verifikasi di session user yang aktif

        Args:
            user_id (int): ID user
            is_verified (bool): Status verifikasi baru

        Returns:
            bool: True jika berhasil diupdate
        """
        try:
            # Ambil session yang ada
            session_data = await AuthUtils.get_user_session(user_id)

            if not session_data:
                logger.info(f"Tidak ada session aktif untuk user {user_id}, skip update verification")
                return False

            # Update status verifikasi
            session_data.is_verified = is_verified

            # Simpan kembali session yang sudah diupdate
            session_key = redis_cache.generate_session_key(user_id)
            await redis_cache.set(
                session_key,
                session_data.model_dump(),
                ttl=86400  # 24 jam
            )

            logger.info(f"Session verification status berhasil diupdate untuk user {user_id}: is_verified={is_verified}")
            return True

        except Exception as e:
            logger.error(f"Error updating user session verification: {e}")
            return False


# Dependency untuk mendapatkan current user dari token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Dependency untuk mendapatkan current user dari JWT token

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        TokenData: Data user dari token

    Raises:
        HTTPException: Jika token invalid
    """
    token = credentials.credentials
    return AuthUtils.verify_token(token)


# Dependency untuk mendapatkan current user dengan session data
async def get_current_user_with_session(current_user: TokenData = Depends(get_current_user)) -> SessionData:
    """
    Dependency untuk mendapatkan current user dengan session data

    Args:
        current_user: Token data dari get_current_user

    Returns:
        SessionData: Data session user

    Raises:
        HTTPException: Jika session tidak ditemukan
    """
    session_data = await AuthUtils.get_user_session(current_user.user_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session_data


# Dependency untuk optional authentication (tidak wajib login)
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenData]:
    """
    Dependency untuk optional authentication

    Args:
        credentials: HTTP Authorization credentials (optional)

    Returns:
        Optional[TokenData]: Data user jika ada token valid, None jika tidak
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        return AuthUtils.verify_token(token)
    except HTTPException:
        return None
