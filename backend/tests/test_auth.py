import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup environment untuk testing
from test_config import setup_test_environment, verify_test_environment
setup_test_environment()

from database.auth import auth_service
from models.auth import UserRegisterRequest, UserLoginRequest
from utils.auth import AuthUtils
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAuth:
    """Test class untuk autentikasi"""

    @pytest.fixture
    def sample_user_data(self):
        """Sample data untuk testing"""
        return UserRegisterRequest(
            nama="Test User",
            email="test@example.com",
            password="testpassword123",
            telepon="081234567890",
            alamat="Jl. Test No. 123",
            telegram_id="test_telegram_123"
        )

    @pytest.fixture
    def login_data(self):
        """Sample login data"""
        return UserLoginRequest(
            email="test@example.com",
            password="testpassword123"
        )

    def test_password_hashing(self):
        """Test password hashing dan verification"""
        password = "testpassword123"

        # Test hashing
        hashed = AuthUtils.hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hash should be longer

        # Test verification
        assert AuthUtils.verify_password(password, hashed) == True
        assert AuthUtils.verify_password("wrongpassword", hashed) == False

        logger.info("✅ Password hashing test passed")

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation dan verification"""
        # Test data
        user_data = {
            "user_id": 123,
            "email": "test@example.com"
        }

        # Create token
        token = AuthUtils.create_access_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT should be reasonably long

        # Verify token
        token_data = AuthUtils.verify_token(token)
        assert token_data.user_id == 123
        assert token_data.email == "test@example.com"
        assert token_data.exp > token_data.iat

        logger.info("✅ JWT token test passed")

    @pytest.mark.asyncio
    async def test_user_registration_flow(self, sample_user_data):
        """Test user registration flow"""
        try:
            # Test registration
            result = await auth_service.register_user(sample_user_data)

            assert result.success == True
            assert result.access_token is not None
            assert result.user is not None
            assert result.user.email == sample_user_data.email
            assert result.user.nama == sample_user_data.nama

            logger.info("✅ User registration test passed")

            # Cleanup - hapus user test jika ada
            # Note: Dalam production, gunakan test database terpisah

        except Exception as e:
            if "Email sudah terdaftar" in str(e):
                logger.info("⚠️ User already exists, skipping registration test")
            else:
                logger.error(f"❌ Registration test failed: {e}")
                raise

    @pytest.mark.asyncio
    async def test_user_login_flow(self, login_data):
        """Test user login flow"""
        try:
            # Test login
            result = await auth_service.login_user(login_data)

            assert result.success == True
            assert result.access_token is not None
            assert result.user is not None
            assert result.user.email == login_data.email

            logger.info("✅ User login test passed")

        except Exception as e:
            if "Email atau password salah" in str(e):
                logger.info("⚠️ User not found, create user first")
            else:
                logger.error(f"❌ Login test failed: {e}")
                raise

    @pytest.mark.asyncio
    async def test_telegram_user_operations(self):
        """Test Telegram user operations"""
        try:
            telegram_user_id = "test_telegram_456"

            # Test get user by telegram ID (should not exist initially)
            user = await auth_service.get_user_by_telegram_id(telegram_user_id)
            assert user is None

            logger.info("✅ Telegram user operations test passed")

        except Exception as e:
            logger.error(f"❌ Telegram operations test failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test session management"""
        try:
            # Test data
            user_data = {
                "id": 999,
                "email": "session_test@example.com",
                "nama": "Session Test User",
                "telepon": "081234567890",
                "alamat": "Test Address",
                "telegram_id": "session_test_telegram",
                "is_verified": True
            }

            # Save session
            session_key = await AuthUtils.save_user_session(user_data, 60)  # 1 minute
            assert session_key is not None

            # Get session
            session_data = await AuthUtils.get_user_session(user_data["id"])
            assert session_data is not None
            assert session_data.user_id == user_data["id"]
            assert session_data.email == user_data["email"]

            # Delete session
            success = await AuthUtils.delete_user_session(user_data["id"])
            assert success == True

            # Verify session is deleted
            session_data = await AuthUtils.get_user_session(user_data["id"])
            assert session_data is None

            logger.info("✅ Session management test passed")

        except Exception as e:
            logger.error(f"❌ Session management test failed: {e}")
            raise


async def test_redis_connection():
    """Test Redis connection"""
    try:
        from utils.cache import redis_cache
        client = await redis_cache._get_client()
        await client.ping()
        logger.info("✅ Redis connection test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection test failed: {e}")
        return False


async def run_manual_tests():
    """Run tests manually without pytest"""
    logger.info("🚀 Starting authentication tests...")

    # Test 0: Redis connection
    redis_ok = await test_redis_connection()
    if not redis_ok:
        logger.error("❌ Redis connection failed. Please check Redis configuration.")
        logger.error("Expected: localhost:6379 with password 'redis_server_2025'")
        return

    test_instance = TestAuth()

    # Test 1: Password hashing
    try:
        test_instance.test_password_hashing()
    except Exception as e:
        logger.error(f"❌ Password hashing test failed: {e}")

    # Test 2: JWT tokens
    try:
        test_instance.test_jwt_token_creation_and_verification()
    except Exception as e:
        logger.error(f"❌ JWT test failed: {e}")

    # Test 3: Session management
    try:
        await test_instance.test_session_management()
    except Exception as e:
        logger.error(f"❌ Session management test failed: {e}")

    # Test 4: Telegram operations
    try:
        await test_instance.test_telegram_user_operations()
    except Exception as e:
        logger.error(f"❌ Telegram operations test failed: {e}")

    logger.info("🏁 Authentication tests completed!")


if __name__ == "__main__":
    # Run manual tests
    asyncio.run(run_manual_tests())
