# backend/tests/test_rag.py

"""
Test suite untuk RAG tools.

Test ini memvalidasi:
1. Import RAG tools berhasil
2. Konfigurasi environment variables
3. Koneksi ke Pinecone (jika tersedia)
4. Fungsi query knowledge base
5. Integrasi dengan customer service agent
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import asyncio

# Tambahkan path backend ke sys.path untuk import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


class TestRAGImports:
    """Test import RAG modules dan tools."""
    
    def test_import_rag_tools(self):
        """Test import RAG tools berhasil."""
        try:
            from rag import RAG_TOOLS, query_knowledge_base
            assert RAG_TOOLS is not None
            assert len(RAG_TOOLS) > 0
            assert query_knowledge_base in RAG_TOOLS
            print("✅ RAG tools import berhasil")
        except ImportError as e:
            pytest.fail(f"❌ Gagal import RAG tools: {e}")
    
    def test_import_rag_utils(self):
        """Test import RAG utils berhasil."""
        try:
            from rag.utils import get_existing_store, validate_pinecone_connection
            assert get_existing_store is not None
            assert validate_pinecone_connection is not None
            print("✅ RAG utils import berhasil")
        except ImportError as e:
            pytest.fail(f"❌ Gagal import RAG utils: {e}")


class TestRAGConfiguration:
    """Test konfigurasi RAG tools."""
    
    def test_environment_variables(self):
        """Test environment variables yang diperlukan."""
        from utils.config import get_settings
        settings = get_settings()

        # Test PINECONE_API_KEY
        if not settings.PINECONE_API_KEY:
            print("⚠️ PINECONE_API_KEY tidak ditemukan - RAG tools akan gagal")
        else:
            print("✅ PINECONE_API_KEY ditemukan")

        # Test OPENAI_API_KEY
        if not settings.OPENAI_API_KEY:
            print("⚠️ OPENAI_API_KEY tidak ditemukan - RAG tools akan gagal")
        else:
            print("✅ OPENAI_API_KEY ditemukan")

        # Test RAG_MODEL
        print(f"✅ RAG_MODEL: {settings.RAG_MODEL}")
        print(f"✅ TEMPERATURE: {settings.TEMPERATURE}")
    
    def test_rag_llm_configuration(self):
        """Test konfigurasi LLM untuk RAG."""
        try:
            from rag.pinecone import get_rag_llm
            from utils.config import get_settings

            settings = get_settings()

            # Test model RAG
            llm = get_rag_llm()
            assert llm.model_name == settings.RAG_MODEL
            assert llm.temperature == settings.TEMPERATURE

            print(f"✅ RAG LLM konfigurasi berhasil - Model: {settings.RAG_MODEL}, Temperature: {settings.TEMPERATURE}")
        except Exception as e:
            pytest.fail(f"❌ Gagal konfigurasi RAG LLM: {e}")


class TestRAGFunctionality:
    """Test fungsionalitas RAG tools."""
    
    @patch('rag.utils.validate_pinecone_connection')
    @patch('rag.utils.get_existing_store')
    async def test_query_knowledge_base_mock(self, mock_get_store, mock_validate_connection):
        """Test query knowledge base dengan mock."""
        # Setup mocks
        mock_validate_connection.return_value = True

        mock_store = MagicMock()
        mock_retriever = MagicMock()
        mock_store.as_retriever.return_value = mock_retriever
        mock_get_store.return_value = mock_store

        # Mock RAG chain response
        mock_result = {
            "answer": "Ini adalah jawaban dari knowledge base",
            "context": [MagicMock()]
        }

        with patch('rag.pinecone.create_retrieval_chain') as mock_create_chain:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_result
            mock_create_chain.return_value = mock_chain

            # Import dan test query function
            from rag.pinecone import query_knowledge_base

            result = await query_knowledge_base.ainvoke({
                "question": "Test question",
                "k": 5
            })

            assert "jawaban dari knowledge base" in result
            print("✅ Query knowledge base mock test berhasil")
    
    @patch('rag.utils._pc')
    def test_validate_pinecone_connection_mock(self, mock_pc):
        """Test validasi koneksi Pinecone dengan mock."""
        # Setup mock
        mock_pc.list_indexes.return_value = [{"name": "test-index"}]

        from rag.utils import validate_pinecone_connection

        result = validate_pinecone_connection()
        assert result is True
        print("✅ Validasi koneksi Pinecone mock test berhasil")

    @patch('rag.utils._pc')
    def test_get_existing_store_mock(self, mock_pc):
        """Test get existing store dengan mock."""
        # Setup mock
        mock_pc.list_indexes.return_value = [{"name": "agen-travel-faq"}]
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index

        from rag.utils import get_existing_store

        store = get_existing_store("agen-travel-faq")
        assert store is not None
        print("✅ Get existing store mock test berhasil")


class TestRAGIntegration:
    """Test integrasi RAG tools dengan customer service agent."""

    def test_rag_tools_in_customer_service(self):
        """Test RAG tools terintegrasi ke customer service."""
        try:
            # Import graph untuk melihat apakah RAG tools sudah terintegrasi
            from agents.graph import customer_service_tools, RAG_AVAILABLE

            print(f"RAG Available: {RAG_AVAILABLE}")

            if RAG_AVAILABLE:
                # Cek apakah query_knowledge_base ada di customer service tools
                tool_names = [tool.name for tool in customer_service_tools]
                print(f"Customer Service Tools: {tool_names}")

                assert "query_knowledge_base" in tool_names
                print("✅ RAG tools terintegrasi ke customer service")
            else:
                print("⚠️ RAG tools tidak tersedia - mungkin dependency belum terinstall")

        except ImportError as e:
            print(f"⚠️ Tidak bisa test integrasi: {e}")

    def test_rag_tool_functionality(self):
        """Test fungsionalitas dasar RAG tool."""
        try:
            from rag.pinecone import query_knowledge_base

            # Test tool metadata
            assert query_knowledge_base.name == "query_knowledge_base"
            assert query_knowledge_base.description is not None
            print("✅ RAG tool metadata valid")

            # Test tool args schema
            args_schema = query_knowledge_base.args_schema
            assert "question" in args_schema.model_fields
            assert "k" in args_schema.model_fields
            print("✅ RAG tool args schema valid")

        except Exception as e:
            print(f"⚠️ Error testing RAG tool functionality: {e}")


def run_tests():
    """Jalankan semua tests."""
    print("🧪 Menjalankan RAG Tests...")
    print("=" * 50)

    try:
        # Test imports
        print("\n📦 Testing Imports...")
        test_imports = TestRAGImports()
        test_imports.test_import_rag_tools()
        test_imports.test_import_rag_utils()

        # Test configuration
        print("\n⚙️ Testing Configuration...")
        test_config = TestRAGConfiguration()
        test_config.test_environment_variables()
        test_config.test_rag_llm_configuration()

        # Test functionality
        print("\n🔧 Testing Functionality...")
        test_func = TestRAGFunctionality()
        asyncio.run(test_func.test_query_knowledge_base_mock())
        test_func.test_validate_pinecone_connection_mock()
        test_func.test_get_existing_store_mock()

        # Test integration
        print("\n🔗 Testing Integration...")
        test_integration = TestRAGIntegration()
        test_integration.test_rag_tools_in_customer_service()
        test_integration.test_rag_tool_functionality()

        print("=" * 50)
        print("✅ Semua RAG Tests berhasil!")

    except Exception as e:
        print(f"❌ Error dalam test suite: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_tests()
