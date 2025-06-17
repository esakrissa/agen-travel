#!/usr/bin/env python

import os
import logging
import sys
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import httpx

import dotenv
from mcp.server.fastmcp import FastMCP

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("tripadvisor-mcp-server")

mcp = FastMCP("Tripadvisor Content API MCP")

@dataclass
class TripadvisorConfig:
    api_key: str
    base_url: str = "https://api.content.tripadvisor.com/api/v1"

config = TripadvisorConfig(
    api_key=os.environ.get("TRIPADVISOR_API_KEY", ""),
)

async def make_api_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the Tripadvisor Content API"""
    if not config.api_key:
        raise ValueError("Tripadvisor API key is missing. Please set TRIPADVISOR_API_KEY environment variable.")

    url = f"{config.base_url}/{endpoint}"
    headers = {
        "accept": "application/json"
    }

    if params is None:
        params = {}
    params["key"] = config.api_key

    logger.info(f"Making API request to: {url} with params: {params}")

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        logger.info(f"API response status: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")

        response.raise_for_status()
        return response.json()

@mcp.tool(description="Search for locations (hotels, restaurants, attractions) on Tripadvisor")
async def tripadvisor_search_locations(
    searchQuery: str,
    language: str = "en",
    category: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    latLong: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for locations on Tripadvisor.

    Parameters:
    - searchQuery: The text to search for
    - language: Language code (default: 'en')
    - category: Optional category filter ('hotels', 'attractions', 'restaurants', 'geos')
    - phone: Optional phone number to search for
    - address: Optional address to search for
    - latLong: Optional latitude,longitude coordinates (e.g., '42.3455,-71.0983')
    """
    params = {
        "searchQuery": searchQuery,
        "language": language,
    }

    if category:
        params["category"] = category
    if phone:
        params["phone"] = phone
    if address:
        params["address"] = address
    if latLong:
        params["latLong"] = latLong

    logger.info(f"Searching for locations with query: {searchQuery}")
    try:
        result = await make_api_request("location/search", params)

        # Format the response for better readability
        if "data" in result and isinstance(result["data"], list):
            locations_count = len(result["data"])
            logger.info(f"Found {locations_count} locations for query: {searchQuery}")

            formatted_locations = []
            for location in result["data"]:
                formatted_location = {
                    "location_id": location.get("location_id"),
                    "name": location.get("name"),
                    "address": {
                        "street": location.get("address_obj", {}).get("street1", ""),
                        "street2": location.get("address_obj", {}).get("street2", ""),
                        "city": location.get("address_obj", {}).get("city", ""),
                        "country": location.get("address_obj", {}).get("country", ""),
                        "postal_code": location.get("address_obj", {}).get("postalcode", ""),
                        "full_address": location.get("address_obj", {}).get("address_string", "")
                    },
                    "coordinates": {
                        "latitude": float(location.get("latitude")) if location.get("latitude") else None,
                        "longitude": float(location.get("longitude")) if location.get("longitude") else None
                    } if location.get("latitude") and location.get("longitude") else None,
                    "distance": float(location.get("distance")) if location.get("distance") else None,
                    "bearing": location.get("bearing")
                }
                formatted_locations.append(formatted_location)

            return {
                "status": "success",
                "search_query": searchQuery,
                "total_results": len(formatted_locations),
                "locations": formatted_locations
            }
        else:
            logger.warning(f"Unexpected response format from API for query: {searchQuery}")
            return {
                "status": "error",
                "message": "No locations found or unexpected response format",
                "raw_response": result
            }
    except Exception as e:
        logger.error(f"Error in tripadvisor_search_locations: {str(e)}")
        return {
            "status": "error",
            "message": f"Error searching locations: {str(e)}"
        }

@mcp.tool(description="Search for locations near a specific latitude/longitude")
async def tripadvisor_search_nearby_locations(
    latitude: float,
    longitude: float,
    language: str = "en",
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for locations near a specific latitude/longitude.

    Parameters:
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    - language: Language code (default: 'en')
    - category: Optional category filter ('hotels', 'attractions', 'restaurants')
    """
    params = {
        "latLong": f"{latitude},{longitude}",
        "language": language,
    }

    if category:
        params["category"] = category

    try:
        result = await make_api_request("location/search", params)

        # Format the response for better readability
        if "data" in result and isinstance(result["data"], list):
            formatted_locations = []
            for location in result["data"]:
                formatted_location = {
                    "location_id": location.get("location_id"),
                    "name": location.get("name"),
                    "address": {
                        "street": location.get("address_obj", {}).get("street1", ""),
                        "street2": location.get("address_obj", {}).get("street2", ""),
                        "city": location.get("address_obj", {}).get("city", ""),
                        "country": location.get("address_obj", {}).get("country", ""),
                        "postal_code": location.get("address_obj", {}).get("postalcode", ""),
                        "full_address": location.get("address_obj", {}).get("address_string", "")
                    },
                    "coordinates": {
                        "latitude": float(location.get("latitude")) if location.get("latitude") else None,
                        "longitude": float(location.get("longitude")) if location.get("longitude") else None
                    } if location.get("latitude") and location.get("longitude") else None,
                    "distance": float(location.get("distance")) if location.get("distance") else None,
                    "bearing": location.get("bearing")
                }
                formatted_locations.append(formatted_location)

            return {
                "status": "success",
                "search_coordinates": {"latitude": latitude, "longitude": longitude},
                "total_results": len(formatted_locations),
                "locations": formatted_locations
            }
        else:
            return {
                "status": "error",
                "message": "No locations found or unexpected response format",
                "raw_response": result
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching nearby locations: {str(e)}"
        }

@mcp.tool(description="Get detailed information about a specific location")
async def tripadvisor_get_location_details(
    locationId: Union[str, int],
    language: str = "en",
) -> Dict[str, Any]:
    """
    Get detailed information about a specific location (hotel, restaurant, or attraction).

    Parameters:
    - locationId: Tripadvisor location ID (can be string or integer)
    - language: Language code (default: 'en')
    """
    params = {
        "language": language,
    }

    # Convert locationId to string to ensure compatibility
    location_id_str = str(locationId)

    try:
        result = await make_api_request(f"location/{location_id_str}/details", params)

        # Format the response for better readability
        if result:
            formatted_details = {
                "location_id": result.get("location_id"),
                "name": result.get("name"),
                "description": result.get("description"),
                "web_url": result.get("web_url"),
                "category": {
                    "name": result.get("category", {}).get("name"),
                    "localized_name": result.get("category", {}).get("localized_name")
                } if result.get("category") else None,
                "subcategory": [
                    {
                        "name": sub.get("name"),
                        "localized_name": sub.get("localized_name")
                    }
                    for sub in result.get("subcategory", [])
                ] if result.get("subcategory") else [],
                "address": {
                    "street": result.get("address_obj", {}).get("street1", ""),
                    "street2": result.get("address_obj", {}).get("street2", ""),
                    "city": result.get("address_obj", {}).get("city", ""),
                    "state": result.get("address_obj", {}).get("state", ""),
                    "country": result.get("address_obj", {}).get("country", ""),
                    "postal_code": result.get("address_obj", {}).get("postalcode", ""),
                    "full_address": result.get("address_obj", {}).get("address_string", "")
                } if result.get("address_obj") else None,
                "coordinates": {
                    "latitude": float(result.get("latitude")) if result.get("latitude") else None,
                    "longitude": float(result.get("longitude")) if result.get("longitude") else None
                } if result.get("latitude") and result.get("longitude") else None,
                "rating": {
                    "rating": result.get("rating"),
                    "num_reviews": result.get("num_reviews"),
                    "review_rating_count": result.get("review_rating_count")
                } if result.get("rating") else None,
                "ranking": {
                    "ranking": result.get("ranking"),
                    "ranking_category": result.get("ranking_category"),
                    "ranking_string": result.get("ranking_string")
                } if result.get("ranking") else None,
                "awards": result.get("awards", []),
                "location_string": result.get("location_string"),
                "photo": {
                    "images": result.get("photo", {}).get("images", {}),
                    "caption": result.get("photo", {}).get("caption")
                } if result.get("photo") else None,
                "api_detail_url": result.get("api_detail_url"),
                "write_review": result.get("write_review"),
                "ancestors": [
                    {
                        "level": ancestor.get("level"),
                        "name": ancestor.get("name"),
                        "location_id": ancestor.get("location_id")
                    }
                    for ancestor in result.get("ancestors", [])
                ] if result.get("ancestors") else [],
                "timezone": result.get("timezone"),
                "phone": result.get("phone"),
                "website": result.get("website"),
                "email": result.get("email"),
                "price_level": result.get("price_level"),
                "hours": result.get("hours"),
                "cuisine": result.get("cuisine", []),
                "dietary_restrictions": result.get("dietary_restrictions", []),
                "see_all_photos": result.get("see_all_photos"),
                "neighborhood_info": result.get("neighborhood_info", [])
            }

            return {
                "status": "success",
                "location_details": formatted_details
            }
        else:
            return {
                "status": "error",
                "message": "No location details found",
                "raw_response": result
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting location details: {str(e)}"
        }

@mcp.tool(description="Get reviews for a specific location")
async def tripadvisor_get_location_reviews(
    locationId: Union[str, int],
    language: str = "en",
) -> Dict[str, Any]:
    """
    Get the most recent reviews for a specific location.

    Parameters:
    - locationId: Tripadvisor location ID (can be string or integer)
    - language: Language code (default: 'en', use 'en' instead of 'id' to avoid conflicts)
    """
    params = {
        "language": language,
    }

    # Convert locationId to string to ensure compatibility
    location_id_str = str(locationId)

    logger.info(f"Getting reviews for location ID: {location_id_str} with language: {language}")
    try:
        result = await make_api_request(f"location/{location_id_str}/reviews", params)

        # Format the response for better readability
        if "data" in result and isinstance(result["data"], list):
            formatted_reviews = []
            for review in result["data"]:
                formatted_review = {
                    "id": review.get("id"),
                    "lang": review.get("lang"),
                    "url": review.get("url"),
                    "location_id": review.get("location_id"),
                    "published_date": review.get("published_date"),
                    "rating": review.get("rating"),
                    "helpful_votes": review.get("helpful_votes"),
                    "rating_image_url": review.get("rating_image_url"),
                    "title": review.get("title"),
                    "text": review.get("text"),
                    "trip_type": review.get("trip_type"),
                    "travel_date": review.get("travel_date"),
                    "user": {
                        "username": review.get("user", {}).get("username"),
                        "user_location": {
                            "name": review.get("user", {}).get("user_location", {}).get("name"),
                            "id": review.get("user", {}).get("user_location", {}).get("id")
                        } if review.get("user", {}).get("user_location") else None,
                        "avatar": {
                            "thumbnail": review.get("user", {}).get("avatar", {}).get("thumbnail"),
                            "small": review.get("user", {}).get("avatar", {}).get("small"),
                            "medium": review.get("user", {}).get("avatar", {}).get("medium"),
                            "large": review.get("user", {}).get("avatar", {}).get("large"),
                            "original": review.get("user", {}).get("avatar", {}).get("original")
                        } if review.get("user", {}).get("avatar") else None
                    } if review.get("user") else None,
                    "subratings": {
                        str(key): {
                            "name": subrating.get("name"),
                            "rating_image_url": subrating.get("rating_image_url"),
                            "value": subrating.get("value"),
                            "localized_name": subrating.get("localized_name")
                        }
                        for key, subrating in review.get("subratings", {}).items()
                    } if review.get("subratings") else {},
                    "machine_translated": review.get("machine_translated", False),
                    "machine_translatable": review.get("machine_translatable", False)
                }
                formatted_reviews.append(formatted_review)

            return {
                "status": "success",
                "location_id": location_id_str,
                "total_reviews": len(formatted_reviews),
                "reviews": formatted_reviews
            }
        else:
            return {
                "status": "error",
                "message": "No reviews found or unexpected response format",
                "raw_response": result
            }
    except Exception as e:
        logger.error(f"Error in tripadvisor_get_location_reviews for location {location_id_str}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting location reviews: {str(e)}",
            "location_id": location_id_str,
            "language": language
        }

@mcp.tool(description="Get photos for a specific location")
async def tripadvisor_get_location_photos(
    locationId: Union[str, int],
    language: str = "en",
) -> Dict[str, Any]:
    """
    Get high-quality photos for a specific location.

    Parameters:
    - locationId: Tripadvisor location ID (can be string or integer)
    - language: Language code (default: 'en')
    """
    params = {
        "language": language,
    }

    # Convert locationId to string to ensure compatibility
    location_id_str = str(locationId)

    try:
        result = await make_api_request(f"location/{location_id_str}/photos", params)

        # Format the response for better readability
        if "data" in result and isinstance(result["data"], list):
            formatted_photos = []
            for photo in result["data"]:
                formatted_photo = {
                    "id": photo.get("id"),
                    "is_blessed": photo.get("is_blessed"),
                    "caption": photo.get("caption"),
                    "published_date": photo.get("published_date"),
                    "images": {
                        "thumbnail": {
                            "height": photo.get("images", {}).get("thumbnail", {}).get("height"),
                            "width": photo.get("images", {}).get("thumbnail", {}).get("width"),
                            "url": photo.get("images", {}).get("thumbnail", {}).get("url")
                        } if photo.get("images", {}).get("thumbnail") else None,
                        "small": {
                            "height": photo.get("images", {}).get("small", {}).get("height"),
                            "width": photo.get("images", {}).get("small", {}).get("width"),
                            "url": photo.get("images", {}).get("small", {}).get("url")
                        } if photo.get("images", {}).get("small") else None,
                        "medium": {
                            "height": photo.get("images", {}).get("medium", {}).get("height"),
                            "width": photo.get("images", {}).get("medium", {}).get("width"),
                            "url": photo.get("images", {}).get("medium", {}).get("url")
                        } if photo.get("images", {}).get("medium") else None,
                        "large": {
                            "height": photo.get("images", {}).get("large", {}).get("height"),
                            "width": photo.get("images", {}).get("large", {}).get("width"),
                            "url": photo.get("images", {}).get("large", {}).get("url")
                        } if photo.get("images", {}).get("large") else None,
                        "original": {
                            "height": photo.get("images", {}).get("original", {}).get("height"),
                            "width": photo.get("images", {}).get("original", {}).get("width"),
                            "url": photo.get("images", {}).get("original", {}).get("url")
                        } if photo.get("images", {}).get("original") else None
                    } if photo.get("images") else None,
                    "album": photo.get("album"),
                    "source": {
                        "name": photo.get("source", {}).get("name"),
                        "localized_name": photo.get("source", {}).get("localized_name")
                    } if photo.get("source") else None,
                    "user": {
                        "username": photo.get("user", {}).get("username"),
                        "user_location": {
                            "name": photo.get("user", {}).get("user_location", {}).get("name"),
                            "id": photo.get("user", {}).get("user_location", {}).get("id")
                        } if photo.get("user", {}).get("user_location") else None
                    } if photo.get("user") else None
                }
                formatted_photos.append(formatted_photo)

            return {
                "status": "success",
                "location_id": location_id_str,
                "total_photos": len(formatted_photos),
                "photos": formatted_photos
            }
        else:
            return {
                "status": "error",
                "message": "No photos found or unexpected response format",
                "raw_response": result
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting location photos: {str(e)}"
        }

if __name__ == "__main__":
    print(f"Starting Tripadvisor MCP Server...")
    mcp.run()
