#!/usr/bin/env python3
"""
Test script untuk retrieve file dari Supabase Storage
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "http://localhost:8000"
# Try with Service Role Key for full access
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NDcwNjU2MDAsImV4cCI6MTkwNDgzMjAwMH0.MDYZwWV0zCbHzOZV-isgUcb9Ky7ONhEJ1spEFLaxxgU"

def test_storage_connection():
    """Test koneksi ke Supabase Storage"""
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🔗 Testing Supabase Storage connection...")
        print(f"URL: {SUPABASE_URL}")
        
        # List all buckets
        print("\n📁 Available buckets:")
        buckets = supabase.storage.list_buckets()
        for bucket in buckets:
            print(f"  - {bucket.name} (ID: {bucket.id})")
        
        return supabase
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return None

def test_list_files(supabase: Client, bucket_name: str = "invoices"):
    """List files dalam bucket"""
    try:
        print(f"\n📄 Files in '{bucket_name}' bucket:")

        # List files in bucket
        files = supabase.storage.from_(bucket_name).list()

        # Debug: print raw response
        print(f"🔍 Raw response: {files}")
        print(f"🔍 Response type: {type(files)}")
        print(f"🔍 Response length: {len(files) if files else 'None'}")

        if not files:
            print("  No files found")
            return []

        for file in files:
            print(f"  - {file['name']} ({file.get('metadata', {}).get('size', 'unknown')} bytes)")
            print(f"    Created: {file.get('created_at', 'unknown')}")
            print(f"    Updated: {file.get('updated_at', 'unknown')}")

        return files

    except Exception as e:
        print(f"❌ Error listing files: {e}")
        print(f"🔍 Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return []

def test_get_public_url(supabase: Client, bucket_name: str, filename: str):
    """Get public URL untuk file"""
    try:
        print(f"\n🔗 Getting public URL for: {filename}")
        
        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        
        print(f"✅ Public URL: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"❌ Error getting public URL: {e}")
        return None

def test_download_file(supabase: Client, bucket_name: str, filename: str, local_path: str = None):
    """Download file dari storage"""
    try:
        print(f"\n⬇️ Downloading file: {filename}")
        
        # Download file
        file_data = supabase.storage.from_(bucket_name).download(filename)
        
        if local_path:
            # Save to local file
            with open(local_path, 'wb') as f:
                f.write(file_data)
            print(f"✅ File saved to: {local_path}")
        else:
            print(f"✅ File downloaded ({len(file_data)} bytes)")
        
        return file_data
        
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 Supabase Storage Test")
    print("=" * 50)
    
    # Test connection
    supabase = test_storage_connection()
    if not supabase:
        return
    
    # Test list files
    files = test_list_files(supabase, "invoices")
    
    if files:
        # Test dengan file pertama yang ditemukan
        first_file = files[0]['name']
        
        # Test get public URL
        public_url = test_get_public_url(supabase, "invoices", first_file)
        
        # Test download file
        download_path = f"downloaded_{first_file}"
        test_download_file(supabase, "invoices", first_file, download_path)
        
        print(f"\n✅ Test completed!")
        print(f"📁 Downloaded file: {download_path}")
        print(f"🔗 Public URL: {public_url}")
    else:
        print("\n⚠️ No files found to test with")
        print("Upload a file first via Supabase Dashboard")

if __name__ == "__main__":
    main()
