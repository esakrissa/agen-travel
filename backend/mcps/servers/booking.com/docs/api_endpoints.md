# Booking.com API Endpoints Documentation

This document provides a comprehensive overview of the Booking.com API endpoints that have been tested and are available for use in the MCP server.

## Base URL
```
https://booking-com15.p.rapidapi.com
```

## Authentication
All endpoints require RapidAPI authentication headers:
```
x-rapidapi-key: YOUR_RAPIDAPI_KEY
x-rapidapi-host: booking-com15.p.rapidapi.com
```

## Available Endpoints

## Hotels API

### 1. **Search Destinations** ✅
Search for destinations by name or keyword.

- **Endpoint**: `/api/v1/hotels/searchDestination`
- **Method**: GET
- **Parameters**:
  - `query` (required): Search term (e.g., "bali", "paris", "new york")
- **Sample Files**: `hotel_destinations.json`, `bali_destinations.json`
- **Response Data**: 
  - `dest_id`: Destination ID for further searches
  - `search_type`: Type of destination (city, region, district)
  - `hotels`: Number of available hotels
  - `coordinates`: Latitude and longitude
  - `image_url`: Destination image
  - `location hierarchy`: Country, region, city information

**Example Request**:
```bash
GET /api/v1/hotels/searchDestination?query=bali
```

### 2. **Search Hotels** ✅
Search for hotels in a specific destination with dates and guest information.

- **Endpoint**: `/api/v1/hotels/searchHotels`
- **Method**: GET
- **Parameters**:
  - `dest_id` (required): Destination ID from search destinations
  - `search_type` (required): Type of search (CITY, REGION, DISTRICT)
  - `arrival_date` (required): Check-in date (YYYY-MM-DD)
  - `departure_date` (required): Check-out date (YYYY-MM-DD)
  - `adults` (required): Number of adults
- **Sample File**: `bali_hotels.json`
- **Response Data**: 
  - Comprehensive hotel listings
  - Pricing information with discounts
  - Ratings and reviews
  - Photos and amenities
  - Booking information

**Example Request**:
```bash
GET /api/v1/hotels/searchHotels?dest_id=835&search_type=REGION&arrival_date=2025-06-19&departure_date=2025-06-21&adults=2
```

### 3. **Hotel Details** ✅
Get detailed information about a specific hotel.

- **Endpoint**: `/api/v1/hotels/getHotelDetails`
- **Method**: GET
- **Parameters**:
  - `hotel_id` (required): Hotel ID
  - `adults` (required): Number of adults
  - `arrival_date` (required): Check-in date (YYYY-MM-DD)
  - `departure_date` (required): Check-out date (YYYY-MM-DD)
  - `currency_code` (required): Currency code (USD, EUR, IDR, etc.)
  - `room_qty` (optional): Number of rooms (default: 1)
  - `units` (optional): Unit system (metric/imperial)
  - `temperature_unit` (optional): Temperature unit (c/f)
  - `languagecode` (optional): Language code (en-us, etc.)
- **Sample File**: `hotel_details_formatted.json`
- **Response Data**: 
  - Detailed hotel information
  - Comprehensive pricing breakdown
  - Facilities and amenities
  - Photo galleries
  - Room details and configurations
  - House rules and policies

**Example Request**:
```bash
GET /api/v1/hotels/getHotelDetails?hotel_id=13867039&adults=2&arrival_date=2025-06-19&departure_date=2025-06-21&currency_code=USD
```

### 4. **Room Availability** ✅
Check room availability and pricing for specific dates at a hotel.

- **Endpoint**: `/api/v1/hotels/getAvailability`
- **Method**: GET
- **Required Parameters**:
  - `hotel_id`: Hotel ID (e.g., 13867039)
  - `currency_code`: Currency code (e.g., USD, EUR, IDR)
  - `location`: Location code (e.g., US, ID) - Note: US generally provides better API compatibility
  - `min_date`: Start date in YYYY-MM-DD format
  - `max_date`: End date in YYYY-MM-DD format
- **Optional Parameters**:
  - `adults`: Number of adults (default: 2)
- **Sample File**: `room_availability.json`
- **Response Data Structure**:
  ```json
  {
    "status": true,
    "message": "Success",
    "timestamp": 1749375029211,
    "data": {
      "lengthsOfStay": [
        {"2025-06-19": 2},
        {"2025-06-20": 2},
        {"2025-06-21": 2}
      ],
      "avDates": [
        {"2025-06-19": 276.496448835754},
        {"2025-06-20": 276.496448835754},
        {"2025-06-21": 276.496448835754}
      ],
      "currency": "USD"
    }
  }
  ```
- **Data Explanation**:
  - `lengthsOfStay`: Array showing available stay durations for each date
  - `avDates`: Array showing price per night for each available date
  - `currency`: Currency code for the prices
- **Use Cases**:
  - Check room availability for specific dates
  - Get pricing calendar for a hotel
  - Determine optimal booking dates based on price variations
  - Validate date ranges before booking

**Example Request**:
```bash
GET /api/v1/hotels/getAvailability?hotel_id=13867039&currency_code=USD&location=US&min_date=2025-06-19&max_date=2025-06-21&adults=2
```

## Flights API

### 5. **Search Flight Destinations** ✅
Search for flight destinations (airports and cities) by name or keyword.

- **Endpoint**: `/api/v1/flights/searchDestination`
- **Method**: GET
- **Parameters**:
  - `query` (required): Search term (e.g., "jakarta", "denpasar", "bali")
- **Sample File**: `flight_location.json`
- **Response Data**:
  - `id`: Unique identifier (format: CODE.TYPE)
  - `type`: CITY or AIRPORT
  - `code`: IATA airport/city code
  - `name`: Full name of airport or city
  - `cityName`: City name (for airports)
  - `regionName`: Region/province name
  - `country`: Country code
  - `photoUri`: Location image URL
  - `distanceToCity`: Distance from airport to city center (airports only)
  - `parent`: Parent city code (for airports)

**Example Request**:
```bash
GET /api/v1/flights/searchDestination?query=jakarta
```

**Sample Response Structure**:
```json
{
  "status": true,
  "message": "Success",
  "data": [
    {
      "id": "CGK.AIRPORT",
      "type": "AIRPORT",
      "name": "Soekarno-Hatta International Airport",
      "code": "CGK",
      "city": "JKT",
      "cityName": "Jakarta",
      "regionName": "Jakarta Province",
      "country": "ID",
      "distanceToCity": {
        "value": 20.166796001338913,
        "unit": "km"
      },
      "parent": "JKT"
    }
  ]
}
```

### 6. **Search Flights** ✅
Search for flights between two destinations with specific dates and passenger details.

- **Endpoint**: `/api/v1/flights/searchFlights`
- **Method**: GET
- **Parameters**:
  - `fromId` (required): Origin airport/city ID (e.g., "DPS.AIRPORT")
  - `toId` (required): Destination airport/city ID (e.g., "CGK.AIRPORT")
  - `departDate` (required): Departure date (YYYY-MM-DD)
  - `adults` (required): Number of adults
  - `children` (optional): Number of children (default: 0)
  - `stops` (optional): Flight stops preference (none, any)
  - `pageNo` (optional): Page number for pagination (default: 1)
  - `sort` (optional): Sort order (BEST, CHEAPEST, FASTEST)
  - `cabinClass` (optional): Cabin class (ECONOMY, BUSINESS, FIRST)
  - `currency_code` (required): Currency code (IDR, USD, EUR, etc.)
- **Sample File**: `flight_results.json`
- **Response Data**:
  - Flight listings with pricing, duration, airlines
  - Departure and arrival times
  - Aircraft information
  - Booking tokens for detailed information

**Example Request**:
```bash
GET /api/v1/flights/searchFlights?fromId=DPS.AIRPORT&toId=CGK.AIRPORT&departDate=2025-06-19&adults=1&children=0&sort=BEST&cabinClass=ECONOMY&currency_code=IDR
```

### 7. **Flight Details** ✅
Get detailed information about a specific flight using a booking token.

- **Endpoint**: `/api/v1/flights/getFlightDetails`
- **Method**: GET
- **Parameters**:
  - `token` (required): Flight booking token from search results
  - `currency_code` (required): Currency code (IDR, USD, EUR, etc.)
- **Sample File**: `flight_details.json`
- **Response Data**:
  - Detailed flight information
  - Comprehensive pricing breakdown
  - Baggage allowances
  - Seat information
  - Airline policies
  - Booking conditions

**Example Request**:
```bash
GET /api/v1/flights/getFlightDetails?token=FLIGHT_TOKEN_HERE&currency_code=IDR
```

## Key Findings

### Parameter Requirements
**Hotels:**
- All endpoints require dates in YYYY-MM-DD format
- Hotel Details & Room Availability require date parameters
- Currency code and location are required for accurate pricing
- Room Availability uses `min_date`/`max_date` instead of `arrival_date`/`departure_date`

**Flights:**
- Flight search requires origin and destination IDs from search destinations
- Departure date required in YYYY-MM-DD format
- Currency code required for pricing
- Flight details require booking token from search results

### Data Structure
**Hotels:**
- All responses use format `{status, message, timestamp, data}`
- Hotel Details provides the most comprehensive data
- Room Availability provides pricing per date with length of stay options

**Flights:**
- Flight destinations return airports and cities with hierarchical relationships
- Flight search returns booking tokens for detailed information
- Flight details provide comprehensive booking and pricing information

### Implementation Status
- All sample data available for reference (hotels + flights)
- API structure well understood for both hotels and flights
- Ready to enhance booking.com MCP tools with 7 complete endpoints (4 hotels + 3 flights)

## Sample Data Files

### Hotels
- `hotel_destinations.json` - Manhattan search results
- `bali_destinations.json` - Bali search results
- `bali_hotels.json` - Hotel search results for Bali
- `hotel_details_formatted.json` - Detailed info for Villa Shinta by JB Villas
- `room_availability.json` - Availability data for Villa Shinta
- `hotel_results.json` - Formatted sample of 2 hotels from search results

### Flights
- `flight_location.json` - Flight destinations for Denpasar and Jakarta
- `flight_results.json` - Flight search results from DPS to CGK
- `flight_details.json` - Detailed flight information with booking token

## Error Handling
- Invalid dates return validation errors
- Missing required parameters return specific error messages
- API rate limits may apply (check RapidAPI dashboard)
- Always validate response status before processing data
