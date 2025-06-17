# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-12-26

### Added
- Initial release of Booking.com MCP server
- Search destinations functionality
- Get hotels for specific destinations
- Environment variable support for API keys
- Comprehensive error handling
- Rich hotel information including pricing, ratings, and photos

### Features
- **search_destinations**: Search for destinations by name
- **get_hotels**: Get hotel listings for specific destinations with dates
- Support for check-in/check-out dates
- Configurable number of adults
- Detailed hotel information including:
  - Room details and types
  - Pricing and discounts
  - Ratings and reviews
  - Photos
  - Check-in/check-out times
  - Star ratings
  - Location coordinates

### Technical
- Built with FastMCP framework
- Uses RapidAPI Booking.com API
- Async/await support
- Comprehensive logging
- Environment variable configuration
- Test suite with pytest
- Type hints throughout codebase

## [Unreleased]

### Planned
- Hotel availability checking
- Price comparison features
- Advanced filtering options
- Booking functionality (if API supports)
- Rate limiting and caching
- Enhanced error messages
