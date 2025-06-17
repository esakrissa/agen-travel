import httpx
import logging
import sys
from typing import Dict, Any, Optional, Union
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("booking-mcp-server")

# Initialize FastMCP server
mcp = FastMCP("Booking.com MCP Server")

# Constants
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "booking-com15.p.rapidapi.com")

# Validate required environment variables
if not RAPIDAPI_KEY:
    logger.error("RAPIDAPI_KEY environment variable is not set. Please create a .env file with your API key.")
    sys.exit(1)

async def make_rapidapi_request(endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make a request to the RapidAPI with proper error handling."""
    url = f"https://{RAPIDAPI_HOST}{endpoint}"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    logger.info(f"Making API request to {endpoint} with params: {params}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            logger.info(f"API request to {endpoint} successful")
            return response.json()
        except Exception as e:
            logger.error(f"API request to {endpoint} failed: {str(e)}")
            return {"error": str(e)}

@mcp.tool()
async def booking_com_search_destinations(query: str) -> Dict[str, Any]:
    """Search for hotel destinations by name.

    Args:
        query: The destination to search for (e.g., "Paris", "New York", "Tokyo", "Bali")

    Returns:
        Dict containing destination search results with comprehensive information
    """
    logger.info(f"Searching for destinations with query: {query}")
    endpoint = "/api/v1/hotels/searchDestination"
    params = {"query": query}

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_search_destinations: {result['error']}")
        return {"error": f"Error fetching destinations: {result['error']}"}

    if "data" in result and isinstance(result["data"], list):
        destinations_count = len(result["data"])
        logger.info(f"Found {destinations_count} destinations for query: {query}")

        formatted_destinations = []
        for destination in result["data"]:
            dest_data = {
                "dest_id": destination.get('dest_id'),
                "name": destination.get('name', 'Unknown'),
                "label": destination.get('label', 'Unknown'),
                "dest_type": destination.get('dest_type', 'Unknown'),
                "search_type": destination.get('search_type', 'Unknown'),
                "country": destination.get('country', 'Unknown'),
                "region": destination.get('region', 'Unknown'),
                "city_name": destination.get('city_name', ''),
                "hotels_count": destination.get('hotels', 0),
                "coordinates": {
                    "latitude": destination.get('latitude'),
                    "longitude": destination.get('longitude')
                },
                "image_url": destination.get('image_url', ''),
                "country_code": destination.get('cc1', '')
            }
            formatted_destinations.append(dest_data)

        return {
            "status": "success",
            "query": query,
            "total_results": destinations_count,
            "destinations": formatted_destinations
        }
    else:
        logger.warning(f"Unexpected response format from API for query: {query}")
        return {"error": "Unexpected response format from the API."}

@mcp.tool()
async def booking_com_get_hotels(destination_id: str, checkin_date: str, checkout_date: str, adults: int = 2, currency_code: str = "IDR") -> Dict[str, Any]:
    """Get hotels for a specific destination with comprehensive information.

    Args:
        destination_id: The destination ID (dest_id from booking_com_search_destinations)
        checkin_date: Check-in date in YYYY-MM-DD format
        checkout_date: Check-out date in YYYY-MM-DD format
        adults: Number of adults (default: 2)
        currency_code: Currency code for pricing (default: IDR)

    Returns:
        Dict containing hotel search results with detailed information
    """
    logger.info(f"Getting hotels for destination_id: {destination_id}, checkin: {checkin_date}, checkout: {checkout_date}, adults: {adults}, currency: {currency_code}")
    endpoint = "/api/v1/hotels/searchHotels"
    params = {
        "dest_id": destination_id,
        "search_type": "CITY",
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "adults": str(adults),
        "currency_code": currency_code
    }

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_get_hotels: {result['error']}")
        return {"error": f"Error fetching hotels: {result['error']}"}

    if "data" in result and "hotels" in result["data"] and isinstance(result["data"]["hotels"], list):
        hotels_count = len(result["data"]["hotels"])
        logger.info(f"Found {hotels_count} hotels for destination: {destination_id}")
        hotels = result["data"]["hotels"]

        formatted_hotels = []
        for hotel_entry in hotels[:15]:  # Limit to 15 hotels for better performance
            if "property" in hotel_entry:
                property_data = hotel_entry["property"]

                # Extract room information from accessibility label
                room_info = "Not specified"
                accessibility_label = hotel_entry.get("accessibilityLabel", "")
                if accessibility_label:
                    import re
                    room_match = re.search(r'(Hotel room|Entire villa|Private suite|Private room|Apartment)[^\.]*', accessibility_label)
                    if room_match:
                        room_info = room_match.group(0).strip()

                # Build hotel data structure
                hotel_data = {
                    "hotel_id": property_data.get('id'),
                    "name": property_data.get('name', 'Unknown'),
                    "location": property_data.get('wishlistName', 'Unknown'),
                    "accommodation_type": room_info,
                    "rating": {
                        "score": property_data.get('reviewScore'),
                        "count": property_data.get('reviewCount'),
                        "word": property_data.get('reviewScoreWord'),
                        "stars": property_data.get('propertyClass')
                    },
                    "coordinates": {
                        "latitude": property_data.get('latitude'),
                        "longitude": property_data.get('longitude')
                    },
                    "check_in_out": {
                        "checkin": property_data.get('checkin', {}),
                        "checkout": property_data.get('checkout', {})
                    },
                    "images": {
                        "main_photo_id": property_data.get('mainPhotoId'),
                        "photo_urls": property_data.get('photoUrls', [])
                    }
                }

                # Add pricing information
                if "priceBreakdown" in property_data and "grossPrice" in property_data["priceBreakdown"]:
                    price_data = property_data["priceBreakdown"]["grossPrice"]
                    hotel_data["pricing"] = {
                        "currency": price_data.get('currency', currency_code),
                        "current_price": price_data.get('value'),
                        "formatted_price": f"{price_data.get('currency', currency_code)} {price_data.get('value', 'N/A')}"
                    }

                    # Add discount information if available
                    if "strikethroughPrice" in property_data["priceBreakdown"]:
                        original_price = property_data["priceBreakdown"]["strikethroughPrice"].get("value")
                        if original_price:
                            discount_pct = 0
                            try:
                                current = float(price_data.get('value', 0))
                                original = float(original_price)
                                if original > 0:
                                    discount_pct = round((1 - current/original) * 100)
                            except (ValueError, TypeError):
                                pass

                            hotel_data["pricing"]["original_price"] = original_price
                            hotel_data["pricing"]["discount_percentage"] = discount_pct
                else:
                    hotel_data["pricing"] = {"currency": currency_code, "current_price": None, "formatted_price": "Price not available"}

                # Add preferences if available
                if "preferences" in property_data:
                    hotel_data["preferences"] = property_data["preferences"]

                formatted_hotels.append(hotel_data)

        return {
            "status": "success",
            "search_params": {
                "destination_id": destination_id,
                "checkin_date": checkin_date,
                "checkout_date": checkout_date,
                "adults": adults,
                "currency": currency_code
            },
            "total_results": hotels_count,
            "hotels_displayed": len(formatted_hotels),
            "hotels": formatted_hotels
        }
    else:
        logger.warning(f"Unexpected response format from API for destination: {destination_id}")
        return {"error": "Unexpected response format from the API."}

@mcp.tool()
async def booking_com_get_hotel_details(hotel_id: Union[str, int], checkin_date: str, checkout_date: str, adults: int = 2, currency_code: str = "IDR") -> Dict[str, Any]:
    """Get comprehensive details for a specific hotel including facilities, photos, and policies.

    Args:
        hotel_id: The hotel ID from hotel search results
        checkin_date: Check-in date in YYYY-MM-DD format
        checkout_date: Check-out date in YYYY-MM-DD format
        adults: Number of adults (default: 2)
        currency_code: Currency code for pricing (default: IDR)

    Returns:
        Dict containing comprehensive hotel details including description, facilities, photos, and pricing
    """
    # Convert hotel_id to string to ensure compatibility
    hotel_id_str = str(hotel_id)
    logger.info(f"Getting hotel details for hotel_id: {hotel_id_str}, checkin: {checkin_date}, checkout: {checkout_date}, adults: {adults}, currency: {currency_code}")
    endpoint = "/api/v1/hotels/getHotelDetails"
    params = {
        "hotel_id": hotel_id_str,
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "adults": str(adults),
        "currency_code": currency_code,
        "room_qty": "1",
        "units": "metric",
        "temperature_unit": "c",
        "languagecode": "en-us"
    }

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_get_hotel_details: {result['error']}")
        return {"error": f"Error fetching hotel details: {result['error']}"}

    if "data" in result:
        data = result["data"]
        logger.info(f"Successfully retrieved details for hotel: {data.get('hotel_name', 'Unknown')}")

        # Build comprehensive hotel details
        hotel_details = {
            "basic_info": {
                "hotel_id": data.get('hotel_id'),
                "name": data.get('hotel_name'),
                "accommodation_type": data.get('accommodation_type_name'),
                "address": data.get('address'),
                "city": data.get('city_name_en', data.get('city')),
                "country": data.get('country_trans'),
                "zip_code": data.get('zip'),
                "coordinates": {
                    "latitude": data.get('latitude'),
                    "longitude": data.get('longitude')
                },
                "distance_to_center": data.get('distance_to_cc'),
                "timezone": data.get('timezone'),
                "url": data.get('url')
            },
            "rating_and_reviews": {
                "review_score": data.get('review_nr'),
                "total_reviews": data.get('review_nr')
            },
            "availability": {
                "available_rooms": data.get('available_rooms'),
                "max_rooms_per_reservation": data.get('max_rooms_in_reservation'),
                "is_closed": bool(data.get('is_closed', 0)),
                "soldout": bool(data.get('soldout', 0))
            },
            "dates": {
                "arrival_date": data.get('arrival_date'),
                "departure_date": data.get('departure_date')
            }
        }

        # Add pricing information
        if "product_price_breakdown" in data:
            price_data = data["product_price_breakdown"]
            hotel_details["pricing"] = {
                "currency": currency_code,
                "gross_amount": price_data.get("gross_amount", {}),
                "all_inclusive_amount": price_data.get("all_inclusive_amount", {}),
                "gross_amount_per_night": price_data.get("gross_amount_per_night", {}),
                "excluded_amount": price_data.get("excluded_amount", {}),
                "benefits": price_data.get("benefits", []),
                "charges_details": price_data.get("charges_details", {}),
                "items": price_data.get("items", [])
            }

            # Add strikethrough pricing if available
            if "strikethrough_amount" in price_data:
                hotel_details["pricing"]["original_price"] = price_data["strikethrough_amount"]
                hotel_details["pricing"]["discount_amount"] = price_data.get("discounted_amount", {})

        # Add facilities and highlights
        if "property_highlight_strip" in data:
            hotel_details["highlights"] = [
                {
                    "name": highlight.get("name"),
                    "context": highlight.get("context"),
                    "icons": [icon.get("icon") for icon in highlight.get("icon_list", [])]
                }
                for highlight in data["property_highlight_strip"]
            ]

        if "facilities_block" in data:
            facilities_data = data["facilities_block"]
            hotel_details["facilities"] = {
                "type": facilities_data.get("type"),
                "name": facilities_data.get("name"),
                "facilities": [
                    {
                        "name": facility.get("name"),
                        "icon": facility.get("icon")
                    }
                    for facility in facilities_data.get("facilities", [])
                ]
            }

        # Add top benefits
        if "top_ufi_benefits" in data:
            hotel_details["top_benefits"] = [
                {
                    "name": benefit.get("translated_name"),
                    "icon": benefit.get("icon")
                }
                for benefit in data["top_ufi_benefits"]
            ]

        # Add room information and photos
        if "rooms" in data:
            rooms_data = data["rooms"]
            hotel_details["rooms"] = {}

            for room_id, room_info in rooms_data.items():
                room_details = {
                    "room_id": room_id,
                    "highlights": [
                        {
                            "name": highlight.get("translated_name"),
                            "icon": highlight.get("icon"),
                            "id": highlight.get("id")
                        }
                        for highlight in room_info.get("highlights", [])
                    ],
                    "photos": []
                }

                # Add room photos (limit to first 5 for performance)
                if "photos" in room_info:
                    for photo in room_info["photos"][:5]:
                        room_details["photos"].append({
                            "photo_id": photo.get("photo_id"),
                            "url_original": photo.get("url_original"),
                            "url_max300": photo.get("url_max300"),
                            "url_square180": photo.get("url_square180"),
                            "ratio": photo.get("ratio")
                        })

                # Add children and beds information
                if "children_and_beds_text" in room_info:
                    children_beds = room_info["children_and_beds_text"]
                    room_details["children_and_beds"] = {
                        "allow_children": children_beds.get("allow_children"),
                        "age_intervals": children_beds.get("age_intervals", [])
                    }

                hotel_details["rooms"][room_id] = room_details

        # Add house rules and policies
        if "booking_home" in data:
            booking_home = data["booking_home"]
            hotel_details["policies"] = {
                "is_vacation_rental": bool(booking_home.get("is_vacation_rental", 0)),
                "is_single_unit_property": bool(booking_home.get("is_single_unit_property", 0)),
                "quality_class": booking_home.get("quality_class"),
                "house_rules": [
                    {
                        "title": rule.get("title"),
                        "description": rule.get("description"),
                        "type": rule.get("type"),
                        "icon": rule.get("icon")
                    }
                    for rule in booking_home.get("house_rules", [])
                ]
            }

        # Add family facilities
        if "family_facilities" in data:
            hotel_details["family_facilities"] = data["family_facilities"]

        # Add languages spoken
        if "spoken_languages" in data:
            hotel_details["languages_spoken"] = data["spoken_languages"]

        # Add important information
        if "hotel_important_information_with_codes" in data:
            hotel_details["important_information"] = [
                info.get("phrase") for info in data["hotel_important_information_with_codes"]
            ]

        return {
            "status": "success",
            "hotel_details": hotel_details
        }
    else:
        logger.warning(f"Unexpected response format from API for hotel: {hotel_id_str}")
        return {"error": "Unexpected response format from the API."}

@mcp.tool()
async def booking_com_get_room_availability(hotel_id: Union[str, int], min_date: str, max_date: str, currency_code: str = "IDR", location: str = "US", adults: int = 2) -> Dict[str, Any]:
    """Check room availability and pricing for specific dates at a hotel.

    Args:
        hotel_id: Hotel ID from hotel search results
        min_date: Start date in YYYY-MM-DD format
        max_date: End date in YYYY-MM-DD format
        currency_code: Currency code (default: IDR)
        location: Location code (default: US - use US for better API compatibility)
        adults: Number of adults (default: 2)

    Returns:
        Dict containing room availability and pricing information for each date
    """
    # Convert hotel_id to string to ensure compatibility
    hotel_id_str = str(hotel_id)
    logger.info(f"Checking room availability for hotel_id: {hotel_id_str}, dates: {min_date} to {max_date}, currency: {currency_code}")
    endpoint = "/api/v1/hotels/getAvailability"
    params = {
        "hotel_id": hotel_id_str,
        "currency_code": currency_code,
        "location": location,
        "min_date": min_date,
        "max_date": max_date,
        "adults": str(adults)
    }

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_get_room_availability: {result['error']}")
        return {"error": f"Error fetching room availability: {result['error']}"}

    # Log successful API response (without full content for cleaner logs)
    logger.info(f"API response received for hotel {hotel_id_str}, status: {result.get('status', 'unknown')}")

    # Check for different response formats
    if "data" in result:
        data = result["data"]
        logger.info(f"Successfully retrieved availability for hotel: {hotel_id_str}")

        # Check if data is empty or has no availability
        av_dates = data.get("avDates", [])
        lengths_of_stay = data.get("lengthsOfStay", [])

        if not av_dates and not lengths_of_stay:
            logger.info(f"No availability found for hotel {hotel_id_str} on dates {min_date} to {max_date}")
            return {
                "status": "success",
                "availability": {
                    "hotel_id": hotel_id_str,
                    "currency": data.get("currency", currency_code),
                    "date_range": {
                        "min_date": min_date,
                        "max_date": max_date
                    },
                    "adults": adults,
                    "availability_by_date": {},
                    "pricing_summary": {
                        "min_price": None,
                        "max_price": None,
                        "avg_price": None,
                        "total_nights": 0
                    },
                    "formatted_dates": [],
                    "message": "No rooms available for the selected dates"
                }
            }

        # Process availability data
        availability_info = {
            "hotel_id": hotel_id_str,
            "currency": data.get("currency", currency_code),
            "date_range": {
                "min_date": min_date,
                "max_date": max_date
            },
            "adults": adults,
            "availability_by_date": {},
            "pricing_summary": {
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "total_nights": 0
            }
        }

        prices = []
        for date_entry in av_dates:
            for date_str, price in date_entry.items():
                availability_info["availability_by_date"][date_str] = {
                    "price_per_night": price,
                    "currency": data.get("currency", currency_code),
                    "available": True
                }
                prices.append(price)

        # Add length of stay information
        for length_entry in lengths_of_stay:
            for date_str, length in length_entry.items():
                if date_str in availability_info["availability_by_date"]:
                    availability_info["availability_by_date"][date_str]["max_length_of_stay"] = length

        # Calculate pricing summary
        if prices:
            availability_info["pricing_summary"] = {
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": round(sum(prices) / len(prices), 2),
                "total_nights": len(prices),
                "currency": data.get("currency", currency_code)
            }

        # Add formatted pricing for easy reading
        availability_info["formatted_dates"] = []
        for date_str in sorted(availability_info["availability_by_date"].keys()):
            date_info = availability_info["availability_by_date"][date_str]
            availability_info["formatted_dates"].append({
                "date": date_str,
                "price": f"{date_info['currency']} {date_info['price_per_night']}",
                "max_stay_length": date_info.get("max_length_of_stay", "N/A")
            })

        return {
            "status": "success",
            "availability": availability_info
        }

    # Handle case where API returns success but different structure
    elif result.get("status") == True or result.get("status") == "true":
        logger.warning(f"API returned success but no 'data' field for hotel {hotel_id_str}. Full response: {result}")
        return {
            "status": "success",
            "availability": {
                "hotel_id": hotel_id_str,
                "currency": currency_code,
                "date_range": {
                    "min_date": min_date,
                    "max_date": max_date
                },
                "adults": adults,
                "availability_by_date": {},
                "pricing_summary": {
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "total_nights": 0
                },
                "formatted_dates": [],
                "message": "Hotel found but no availability data returned by API",
                "raw_response": result
            }
        }

    # Handle complete failure
    else:
        logger.warning(f"Unexpected response format from API for hotel: {hotel_id_str}. Response: {result}")
        return {
            "error": f"Unexpected response format from the API. Response: {result}"
        }

@mcp.tool()
async def booking_com_search_flight_destinations(query: str) -> Dict[str, Any]:
    """Search for flight destinations (airports and cities) by name or keyword.

    Args:
        query: Search term for flight destinations (e.g., "jakarta", "denpasar", "bali", "singapore")

    Returns:
        Dict containing flight destination search results with airports and cities
    """
    logger.info(f"Searching for flight destinations with query: {query}")
    endpoint = "/api/v1/flights/searchDestination"
    params = {"query": query}

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_search_flight_destinations: {result['error']}")
        return {"error": f"Error fetching flight destinations: {result['error']}"}

    if "data" in result and isinstance(result["data"], list):
        destinations_count = len(result["data"])
        logger.info(f"Found {destinations_count} flight destinations for query: {query}")

        formatted_destinations = []
        for destination in result["data"]:
            dest_data = {
                "id": destination.get('id'),
                "type": destination.get('type'),  # AIRPORT or CITY
                "code": destination.get('code'),
                "name": destination.get('name'),
                "city": destination.get('city'),
                "city_name": destination.get('cityName'),
                "region_name": destination.get('regionName'),
                "country": destination.get('country'),
                "country_name": destination.get('countryName'),
                "photo_uri": destination.get('photoUri', ''),
                "parent": destination.get('parent')
            }

            # Add distance to city for airports
            if destination.get('distanceToCity'):
                dest_data["distance_to_city"] = {
                    "value": destination["distanceToCity"].get("value"),
                    "unit": destination["distanceToCity"].get("unit")
                }

            formatted_destinations.append(dest_data)

        return {
            "status": "success",
            "query": query,
            "total_results": destinations_count,
            "destinations": formatted_destinations
        }
    else:
        logger.warning(f"Unexpected response format from API for query: {query}")
        return {"error": "Unexpected response format from the API."}

@mcp.tool()
async def booking_com_get_flights(from_id: str, to_id: str, depart_date: str, adults: int = 1, children: int = 0, currency_code: str = "IDR", cabin_class: str = "ECONOMY", sort: str = "BEST") -> Dict[str, Any]:
    """Search for flights between two destinations with comprehensive information.

    Args:
        from_id: Origin airport/city ID from booking_com_search_flight_destinations (e.g., "DPS.AIRPORT", "CGK.AIRPORT")
        to_id: Destination airport/city ID from booking_com_search_flight_destinations (e.g., "CGK.AIRPORT", "DPS.AIRPORT")
        depart_date: Departure date in YYYY-MM-DD format
        adults: Number of adults (default: 1)
        children: Number of children (default: 0)
        currency_code: Currency code for pricing (default: IDR)
        cabin_class: Cabin class - ECONOMY, BUSINESS, FIRST (default: ECONOMY)
        sort: Sort order - BEST, CHEAPEST, FASTEST (default: BEST)

    Returns:
        Dict containing flight search results with pricing, airlines, and booking tokens
    """
    logger.info(f"Searching flights from {from_id} to {to_id} on {depart_date}, adults: {adults}, children: {children}")
    endpoint = "/api/v1/flights/searchFlights"
    params = {
        "fromId": from_id,
        "toId": to_id,
        "departDate": depart_date,
        "adults": str(adults),
        "children": str(children),
        "currency_code": currency_code,
        "cabinClass": cabin_class,
        "sort": sort,
        "pageNo": "1"
    }

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_get_flights: {result['error']}")
        return {"error": f"Error fetching flights: {result['error']}"}

    if "data" in result:
        data = result["data"]
        logger.info(f"Successfully retrieved flight results from {from_id} to {to_id}")

        # Build flight search results
        flight_results = {
            "search_params": {
                "from_id": from_id,
                "to_id": to_id,
                "depart_date": depart_date,
                "adults": adults,
                "children": children,
                "currency_code": currency_code,
                "cabin_class": cabin_class,
                "sort": sort
            }
        }

        # Add aggregation data (summary statistics)
        if "aggregation" in data:
            aggregation = data["aggregation"]
            flight_results["summary"] = {
                "total_flights": aggregation.get("totalCount", 0),
                "filtered_count": aggregation.get("filteredTotalCount", 0),
                "duration_range": {
                    "min_hours": aggregation.get("durationMin", 0),
                    "max_hours": aggregation.get("durationMax", 0)
                },
                "price_range": {
                    "min_price": aggregation.get("minPrice", {}),
                    "currency": currency_code
                }
            }

            # Add airlines summary
            if "airlines" in aggregation:
                flight_results["available_airlines"] = [
                    {
                        "name": airline.get("name"),
                        "iata_code": airline.get("iataCode"),
                        "logo_url": airline.get("logoUrl"),
                        "flight_count": airline.get("count"),
                        "min_price": airline.get("minPrice", {})
                    }
                    for airline in aggregation["airlines"][:10]  # Limit to top 10 airlines
                ]

            # Add stops information
            if "stops" in aggregation:
                flight_results["stops_summary"] = [
                    {
                        "number_of_stops": stop.get("numberOfStops"),
                        "flight_count": stop.get("count"),
                        "min_price": stop.get("minPrice", {})
                    }
                    for stop in aggregation["stops"]
                ]

        # Add flight offers
        if "flightOffers" in data:
            flight_offers = data["flightOffers"]
            flight_results["flights"] = []

            for offer in flight_offers[:10]:  # Limit to 10 flights for performance
                flight_data = {
                    "booking_token": offer.get("token"),
                    "segments": []
                }

                # Process flight segments
                for segment in offer.get("segments", []):
                    segment_data = {
                        "departure_airport": {
                            "code": segment["departureAirport"].get("code"),
                            "name": segment["departureAirport"].get("name"),
                            "city": segment["departureAirport"].get("cityName"),
                            "country": segment["departureAirport"].get("countryName")
                        },
                        "arrival_airport": {
                            "code": segment["arrivalAirport"].get("code"),
                            "name": segment["arrivalAirport"].get("name"),
                            "city": segment["arrivalAirport"].get("cityName"),
                            "country": segment["arrivalAirport"].get("countryName")
                        },
                        "departure_time": segment.get("departureTime"),
                        "arrival_time": segment.get("arrivalTime"),
                        "total_time_seconds": segment.get("totalTime"),
                        "total_time_hours": round(segment.get("totalTime", 0) / 3600, 1) if segment.get("totalTime") else 0
                    }

                    # Add flight legs information
                    if "legs" in segment:
                        segment_data["legs"] = []
                        for leg in segment["legs"]:
                            leg_data = {
                                "flight_number": leg.get("flightInfo", {}).get("flightNumber"),
                                "cabin_class": leg.get("cabinClass"),
                                "carriers": [
                                    {
                                        "name": carrier.get("name"),
                                        "code": carrier.get("code"),
                                        "logo": carrier.get("logo")
                                    }
                                    for carrier in leg.get("carriersData", [])
                                ],
                                "duration_seconds": leg.get("totalTime"),
                                "duration_hours": round(leg.get("totalTime", 0) / 3600, 1) if leg.get("totalTime") else 0
                            }
                            segment_data["legs"].append(leg_data)

                    # Add baggage information
                    if "travellerCheckedLuggage" in segment:
                        segment_data["checked_baggage"] = [
                            {
                                "traveller_ref": luggage.get("travellerReference"),
                                "max_pieces": luggage.get("luggageAllowance", {}).get("maxPiece"),
                                "max_weight_kg": luggage.get("luggageAllowance", {}).get("maxWeightPerPiece")
                            }
                            for luggage in segment["travellerCheckedLuggage"]
                        ]

                    if "travellerCabinLuggage" in segment:
                        segment_data["cabin_baggage"] = [
                            {
                                "traveller_ref": luggage.get("travellerReference"),
                                "max_pieces": luggage.get("luggageAllowance", {}).get("maxPiece"),
                                "max_weight_kg": luggage.get("luggageAllowance", {}).get("maxWeightPerPiece"),
                                "size_restrictions": luggage.get("luggageAllowance", {}).get("sizeRestrictions", {})
                            }
                            for luggage in segment["travellerCabinLuggage"]
                        ]

                    flight_data["segments"].append(segment_data)

                # Add pricing information
                if "priceBreakdown" in offer:
                    price_breakdown = offer["priceBreakdown"]
                    flight_data["pricing"] = {
                        "total": price_breakdown.get("total", {}),
                        "base_fare": price_breakdown.get("baseFare", {}),
                        "tax": price_breakdown.get("tax", {}),
                        "fee": price_breakdown.get("fee", {}),
                        "currency": currency_code,
                        "formatted_total": f"{currency_code} {price_breakdown.get('total', {}).get('units', 0):,}"
                    }

                    # Add discount information if available
                    if price_breakdown.get("discount", {}).get("units", 0) > 0:
                        flight_data["pricing"]["discount"] = price_breakdown.get("discount", {})
                        flight_data["pricing"]["original_price"] = price_breakdown.get("totalWithoutDiscount", {})

                flight_results["flights"].append(flight_data)

        return {
            "status": "success",
            "flight_results": flight_results
        }
    else:
        logger.warning(f"Unexpected response format from API for flight search: {from_id} to {to_id}")
        return {"error": "Unexpected response format from the API."}

@mcp.tool()
async def booking_com_get_flight_details(token: str, currency_code: str = "IDR") -> Dict[str, Any]:
    """Get comprehensive details for a specific flight using booking token.

    Args:
        token: Flight booking token from booking_com_get_flights results
        currency_code: Currency code for pricing (default: IDR)

    Returns:
        Dict containing detailed flight information including pricing breakdown, baggage, and booking requirements
    """
    logger.info(f"Getting flight details for token: {token[:50]}...")
    endpoint = "/api/v1/flights/getFlightDetails"
    params = {
        "token": token,
        "currency_code": currency_code
    }

    result = await make_rapidapi_request(endpoint, params)

    if "error" in result:
        logger.error(f"Error in booking_com_get_flight_details: {result['error']}")
        return {"error": f"Error fetching flight details: {result['error']}"}

    if "data" in result:
        data = result["data"]
        logger.info(f"Successfully retrieved flight details")

        # Build comprehensive flight details
        flight_details = {
            "booking_token": data.get("token"),
            "offer_reference": data.get("offerReference"),
            "trip_type": data.get("tripType"),
            "point_of_sale": data.get("pointOfSale")
        }

        # Add flight segments with detailed information
        if "segments" in data:
            flight_details["segments"] = []
            for segment in data["segments"]:
                segment_details = {
                    "departure_airport": {
                        "code": segment["departureAirport"].get("code"),
                        "name": segment["departureAirport"].get("name"),
                        "city": segment["departureAirport"].get("cityName"),
                        "country": segment["departureAirport"].get("countryName"),
                        "province": segment["departureAirport"].get("province")
                    },
                    "arrival_airport": {
                        "code": segment["arrivalAirport"].get("code"),
                        "name": segment["arrivalAirport"].get("name"),
                        "city": segment["arrivalAirport"].get("cityName"),
                        "country": segment["arrivalAirport"].get("countryName"),
                        "province": segment["arrivalAirport"].get("province")
                    },
                    "departure_time": segment.get("departureTime"),
                    "arrival_time": segment.get("arrivalTime"),
                    "total_time_seconds": segment.get("totalTime"),
                    "total_time_hours": round(segment.get("totalTime", 0) / 3600, 1) if segment.get("totalTime") else 0,
                    "legs": []
                }

                # Add detailed leg information
                for leg in segment.get("legs", []):
                    leg_details = {
                        "departure_time": leg.get("departureTime"),
                        "arrival_time": leg.get("arrivalTime"),
                        "cabin_class": leg.get("cabinClass"),
                        "flight_info": {
                            "flight_number": leg.get("flightInfo", {}).get("flightNumber"),
                            "plane_type": leg.get("flightInfo", {}).get("planeType"),
                            "facilities": leg.get("flightInfo", {}).get("facilities", [])
                        },
                        "carriers": [
                            {
                                "name": carrier.get("name"),
                                "code": carrier.get("code"),
                                "logo": carrier.get("logo")
                            }
                            for carrier in leg.get("carriersData", [])
                        ],
                        "duration_seconds": leg.get("totalTime"),
                        "duration_hours": round(leg.get("totalTime", 0) / 3600, 1) if leg.get("totalTime") else 0,
                        "flight_stops": leg.get("flightStops", []),
                        "amenities": leg.get("amenities", [])
                    }
                    segment_details["legs"].append(leg_details)

                # Add baggage allowances
                segment_details["baggage_allowances"] = {
                    "checked_luggage": [
                        {
                            "traveller_ref": luggage.get("travellerReference"),
                            "luggage_type": luggage.get("luggageAllowance", {}).get("luggageType"),
                            "rule_type": luggage.get("luggageAllowance", {}).get("ruleType"),
                            "max_pieces": luggage.get("luggageAllowance", {}).get("maxPiece"),
                            "max_weight_kg": luggage.get("luggageAllowance", {}).get("maxWeightPerPiece"),
                            "mass_unit": luggage.get("luggageAllowance", {}).get("massUnit")
                        }
                        for luggage in segment.get("travellerCheckedLuggage", [])
                    ],
                    "cabin_luggage": [
                        {
                            "traveller_ref": luggage.get("travellerReference"),
                            "luggage_type": luggage.get("luggageAllowance", {}).get("luggageType"),
                            "max_pieces": luggage.get("luggageAllowance", {}).get("maxPiece"),
                            "max_weight_kg": luggage.get("luggageAllowance", {}).get("maxWeightPerPiece"),
                            "mass_unit": luggage.get("luggageAllowance", {}).get("massUnit"),
                            "size_restrictions": luggage.get("luggageAllowance", {}).get("sizeRestrictions", {})
                        }
                        for luggage in segment.get("travellerCabinLuggage", [])
                    ]
                }

                flight_details["segments"].append(segment_details)

        # Add comprehensive pricing breakdown
        if "priceBreakdown" in data:
            price_data = data["priceBreakdown"]
            flight_details["pricing"] = {
                "currency": currency_code,
                "total": price_data.get("total", {}),
                "base_fare": price_data.get("baseFare", {}),
                "tax": price_data.get("tax", {}),
                "fee": price_data.get("fee", {}),
                "discount": price_data.get("discount", {}),
                "total_without_discount": price_data.get("totalWithoutDiscount", {}),
                "total_rounded": price_data.get("totalRounded", {}),
                "show_price_strikethrough": price_data.get("showPriceStrikethrough", False),
                "formatted_total": f"{currency_code} {price_data.get('total', {}).get('units', 0):,}"
            }

            # Add Booking.com margin and pricing items
            if "bcomMargin" in price_data:
                flight_details["pricing"]["booking_margin"] = price_data.get("bcomMargin", {})

            if "bcomPricingItems" in price_data:
                flight_details["pricing"]["booking_deals"] = [
                    {
                        "name": item.get("name"),
                        "item_type": item.get("itemType"),
                        "amount": item.get("amount", {}),
                        "disclaimer": item.get("disclaimer")
                    }
                    for item in price_data["bcomPricingItems"]
                ]

            # Add carrier tax breakdown
            if "carrierTaxBreakdown" in price_data:
                flight_details["pricing"]["carrier_taxes"] = [
                    {
                        "carrier": tax.get("carrier", {}),
                        "avg_per_adult": tax.get("avgPerAdult", {}),
                        "avg_per_infant": tax.get("avgPerInfant", {})
                    }
                    for tax in price_data["carrierTaxBreakdown"]
                ]

        # Add traveller price breakdown
        if "travellerPrices" in data:
            flight_details["traveller_pricing"] = [
                {
                    "traveller_reference": traveller.get("travellerReference"),
                    "traveller_type": traveller.get("travellerType"),
                    "price_breakdown": traveller.get("travellerPriceBreakdown", {})
                }
                for traveller in data["travellerPrices"]
            ]

        # Add booking requirements
        flight_details["booking_requirements"] = {
            "traveller_data_required": data.get("travellerDataRequirements", []),
            "booker_data_required": data.get("bookerDataRequirement", [])
        }

        # Add travellers information
        if "travellers" in data:
            flight_details["travellers"] = [
                {
                    "reference": traveller.get("travellerReference"),
                    "type": traveller.get("type"),
                    "age": traveller.get("age")
                }
                for traveller in data["travellers"]
            ]

        # Add included products (baggage summary)
        if "includedProducts" in data:
            included_products = data["includedProducts"]
            flight_details["included_products"] = {
                "all_segments_identical": included_products.get("areAllSegmentsIdentical"),
                "baggage_summary": included_products.get("segments", [])
            }

        # Add extra products available
        if "extraProducts" in data:
            flight_details["extra_products"] = [
                {
                    "type": product.get("type"),
                    "price_breakdown": product.get("priceBreakdown", {})
                }
                for product in data["extraProducts"]
            ]

        return {
            "status": "success",
            "flight_details": flight_details
        }
    else:
        logger.warning(f"Unexpected response format from API for flight details")
        return {"error": "Unexpected response format from the API."}

if __name__ == "__main__":
    print(f"Starting Booking.com MCP Server...")
    mcp.run()