# Hotels MCP Server

A Model Context Protocol (MCP) server that allows LLMs to search for hotels and destinations using the Booking.com API. It also provides functionality for flight search.

## Features

- Search for destinations by name (hotels and flights)
- Get hotel listings for specific destinations with dates
- View detailed hotel information including rooms, amenities, and policies
- Search for flights between destinations
- Get detailed flight information
- Rich hotel information including:
  - Room details and types
  - Pricing and discounts
  - Ratings and reviews
  - Photos
  - Check-in/check-out times
  - Star ratings

## API Integration

This MCP server uses the [Booking.com API](https://rapidapi.com/apidojo/api/booking-com/) via RapidAPI. You'll need:

1. A RapidAPI account
2. Subscribe to the Booking.com API
3. Get your API key

The implementation uses several endpoints:
- `/api/v1/hotels/searchDestination`: Search for hotel destinations
- `/api/v1/hotels/searchHotels`: Get hotels for a destination
- `/api/v1/hotels/getHotelDetails`: Get detailed information about a specific hotel
- `/api/v1/hotels/getRoomList`: Get room availability for a hotel
- `/api/v1/flights/searchDestination`: Search for flight destinations
- `/api/v1/flights/searchFlights`: Search for flights between destinations
- `/api/v1/flights/getFlightDetails`: Get detailed information about a specific flight

## Setup and Installation

### Prerequisites

- Python 3.11+
- MCP SDK (`pip install mcp`)
- httpx (`pip install httpx`)
- python-dotenv (`pip install python-dotenv`)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/username/hotels_mcp_server.git
   cd hotels_mcp_server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your RapidAPI credentials:
   - Copy `.env.example` to `.env`
   - Add your RapidAPI key from [Booking.com API on RapidAPI](https://rapidapi.com/tipsters/api/booking-com) to the `.env` file

### Running the Server

Run the server with:

```bash
python main.py
```

The server uses stdio transport by default for compatibility with MCP clients like Cursor.

## Using with MCP Clients

### Cursor

1. Edit `~/.cursor/mcp.json`:
   ```json
   {
     "hotels": {
       "command": "python",
       "args": [
         "/path/to/hotels_mcp_server/main.py"
       ]
     }
   }
   ```

2. Restart Cursor

3. Use natural language to search for hotels in Cursor:
   - "Find hotels in Paris for next week"
   - "What are the best-rated hotels in Tokyo?"

### MCP Inspector

Test your server with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python main.py
```

This opens an interactive UI where you can:
- View available tools
- Send test requests
- See server responses

## Available Tools

1. `booking_com_search_destinations`: Search for hotel destinations by name
   - Parameter: `query` - Destination name (e.g., "Paris", "New York")

2. `booking_com_get_hotels`: Get hotels for a destination
   - Parameters:
     - `destination_id`: Destination ID from search_destinations
     - `checkin_date`: Check-in date (YYYY-MM-DD)
     - `checkout_date`: Check-out date (YYYY-MM-DD)
     - `adults`: Number of adults (default: 2)
     - `currency_code`: Currency code for pricing (default: "IDR")

3. `booking_com_get_hotel_details`: Get comprehensive details for a specific hotel
   - Parameters:
     - `hotel_id`: Hotel ID from hotel search results
     - `checkin_date`: Check-in date (YYYY-MM-DD)
     - `checkout_date`: Check-out date (YYYY-MM-DD)
     - `adults`: Number of adults (default: 2)
     - `currency_code`: Currency code for pricing (default: "IDR")

4. `booking_com_get_room_availability`: Get room availability for a hotel
   - Parameters:
     - `hotel_id`: Hotel ID from hotel search results
     - `min_date`: Start date for availability search (YYYY-MM-DD)
     - `max_date`: End date for availability search (YYYY-MM-DD)
     - `currency_code`: Currency code for pricing (default: "IDR")
     - `location`: Location code (default: "ID")
     - `adults`: Number of adults (default: 2)

5. `booking_com_search_flight_destinations`: Search for flight destinations
   - Parameter: `query` - Destination name (e.g., "Paris", "New York")

6. `booking_com_get_flights`: Search for flights between destinations
   - Parameters:
     - `from_id`: Origin airport/city ID from flight_search_destinations
     - `to_id`: Destination airport/city ID from flight_search_destinations
     - `depart_date`: Departure date (YYYY-MM-DD)
     - `adults`: Number of adults (default: 1)
     - `children`: Number of children (default: 0)
     - `currency_code`: Currency code for pricing (default: "IDR")
     - `cabin_class`: Cabin class (default: "ECONOMY", options: "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST")
     - `sort`: Sorting method (default: "BEST", options: "BEST", "CHEAPEST", "FASTEST", "DEPARTURE_TIME", "ARRIVAL_TIME")

7. `booking_com_get_flight_details`: Get detailed information about a specific flight
   - Parameters:
     - `token`: Flight token from get_flights result
     - `currency_code`: Currency code for pricing (default: "IDR")

## Code Structure

- `main.py`: The entry point for the server
- `booking_com_mcp/`: The core MCP implementation
  - `__init__.py`: Package initialization
  - `server.py`: MCP server implementation with tool definitions

## License

MIT © Esa Krissa 2025