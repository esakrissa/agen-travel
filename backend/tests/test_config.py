"""
Test configuration untuk memastikan environment variables di-set dengan benar
"""
import os

def setup_test_environment():
    """Setup environment variables untuk testing"""
    
    # Redis configuration untuk testing (localhost)
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["REDIS_PASSWORD"] = "redis_server_2025"
    os.environ["REDIS_DB"] = "0"
    
    # JWT configuration
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-authentication-testing-2025"
    
    # Supabase configuration (gunakan yang sama dengan .env)
    os.environ["SUPABASE_URL"] = "http://localhost:8000"
    os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NDcwNjU2MDAsImV4cCI6MTkwNDgzMjAwMH0.MDYZwWV0zCbHzOZV-isgUcb9Ky7ONhEJ1spEFLaxxgU"
    os.environ["SUPABASE_CONNECTION"] = "postgresql://postgres:agen_travel_supabase_2025@localhost:54322/postgres"
    
    print("✅ Test environment configured:")
    print(f"   Redis: {os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}")
    print(f"   Supabase: {os.environ['SUPABASE_URL']}")
    print(f"   JWT Secret: {os.environ['JWT_SECRET_KEY'][:20]}...")


def verify_test_environment():
    """Verify bahwa semua environment variables sudah di-set"""
    required_vars = [
        "REDIS_HOST",
        "REDIS_PORT", 
        "REDIS_PASSWORD",
        "REDIS_DB",
        "JWT_SECRET_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_CONNECTION"
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in os.environ:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables are set")
    return True


if __name__ == "__main__":
    setup_test_environment()
    verify_test_environment()
