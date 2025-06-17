#!/usr/bin/env python3

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from booking_com_mcp.server import mcp, search_destinations, get_hotels, make_rapidapi_request


class TestBookingComMCP:
    """Test suite for Booking.com MCP server"""

    @pytest.fixture
    def mock_rapidapi_response(self):
        """Mock response from RapidAPI"""
        return {
            "data": [
                {
                    "name": "Paris",
                    "dest_type": "city",
                    "city_ufi": "20088325",
                    "region": "Ile-de-France",
                    "country": "France",
                    "latitude": 48.8566,
                    "longitude": 2.3522
                }
            ]
        }

    @pytest.fixture
    def mock_hotels_response(self):
        """Mock hotels response from RapidAPI"""
        return {
            "data": {
                "hotels": [
                    {
                        "property": {
                            "name": "Hotel Test",
                            "wishlistName": "Paris Center",
                            "reviewScore": 8.5,
                            "reviewCount": 1234,
                            "reviewScoreWord": "Very Good",
                            "priceBreakdown": {
                                "grossPrice": {
                                    "currency": "EUR",
                                    "value": 150
                                }
                            },
                            "latitude": 48.8566,
                            "longitude": 2.3522,
                            "propertyClass": 4,
                            "photoUrls": ["https://example.com/photo.jpg"]
                        },
                        "accessibilityLabel": "Hotel room for 2 adults"
                    }
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_search_destinations_success(self, mock_rapidapi_response):
        """Test successful destination search"""
        with patch('booking_com_mcp.server.make_rapidapi_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_rapidapi_response
            
            result = await search_destinations("Paris")
            
            assert "Paris" in result
            assert "city" in result
            assert "France" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_destinations_error(self):
        """Test destination search with API error"""
        with patch('booking_com_mcp.server.make_rapidapi_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"error": "API Error"}
            
            result = await search_destinations("InvalidCity")
            
            assert "Error fetching destinations" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hotels_success(self, mock_hotels_response):
        """Test successful hotel search"""
        with patch('booking_com_mcp.server.make_rapidapi_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_hotels_response
            
            result = await get_hotels("20088325", "2024-12-01", "2024-12-03", 2)
            
            assert "Hotel Test" in result
            assert "Paris Center" in result
            assert "8.5" in result
            assert "EUR150" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hotels_error(self):
        """Test hotel search with API error"""
        with patch('booking_com_mcp.server.make_rapidapi_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"error": "API Error"}
            
            result = await get_hotels("invalid", "2024-12-01", "2024-12-03", 2)
            
            assert "Error fetching hotels" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_rapidapi_request_success(self):
        """Test successful API request"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await make_rapidapi_request("/test", {"param": "value"})
            
            assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_make_rapidapi_request_error(self):
        """Test API request with error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            result = await make_rapidapi_request("/test", {"param": "value"})
            
            assert "error" in result
            assert "Network error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])
