# BAB III
# METODOLOGI PENELITIAN

## 3.1 Metodologi Pengembangan Sistem

### 3.1.1 Pendekatan Pengembangan
Penelitian ini menggunakan pendekatan **Agile Development** dengan metodologi **Scrum** yang diadaptasi untuk research context. Pemilihan metodologi ini didasarkan pada:
- **Iterative Development**: Memungkinkan continuous improvement dan adaptation
- **Rapid Prototyping**: Quick validation dari concepts dan implementations
- **Flexibility**: Adaptasi terhadap changing requirements dan discoveries
- **Risk Mitigation**: Early identification dan resolution dari technical challenges

### 3.1.2 Tahapan Pengembangan
Pengembangan sistem dilakukan dalam 5 sprint utama:

**Sprint 1: Architecture Design & Foundation**
- Desain arsitektur multi-agent system
- Setup development environment
- Database schema design
- Core infrastructure setup

**Sprint 2: Agent Implementation**
- Supervisor agent development
- Specialized agents (hotel, flight, tour, customer service)
- LangGraph workflow implementation
- Agent communication protocols

**Sprint 3: Integration & Services**
- Database integration (Supabase)
- Authentication system (SMTP email)
- Caching implementation (Redis)
- API development (FastAPI)

**Sprint 4: User Interfaces**
- Telegram Bot development
- Web UI implementation
- User experience optimization
- Testing dan debugging

**Sprint 5: Deployment & Monitoring**
- Docker containerization
- Cloud deployment (GCP)
- Monitoring setup (Grafana/Prometheus)
- Performance optimization

## 3.2 Arsitektur Sistem

### 3.2.1 High-Level Architecture
Sistem menggunakan **layered architecture** dengan separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│              (Telegram Bot, Web UI)                     │
├─────────────────────────────────────────────────────────┤
│                    Application Layer                     │
│                   (FastAPI Endpoints)                   │
├─────────────────────────────────────────────────────────┤
│                      Agent Layer                        │
│            (LangGraph Multi-Agent System)               │
├─────────────────────────────────────────────────────────┤
│                     Service Layer                       │
│              (Business Logic, Tools)                    │
├─────────────────────────────────────────────────────────┤
│                      Data Layer                         │
│            (Supabase, Redis, External APIs)             │
└─────────────────────────────────────────────────────────┘
```

### 3.2.2 Multi-Agent Architecture
Arsitektur agent menggunakan **Supervisor Pattern** dengan komponen:

**Supervisor Agent**
- Central coordinator untuk semua user interactions
- Routing decisions berdasarkan user intent
- Context management across conversations
- Error handling dan escalation

**Specialized Agents**
- **Hotel Agent**: Hotel search, booking, dan management
- **Flight Agent**: Flight search, booking, dan management  
- **Tour Agent**: Tour package search, booking, dan management
- **Customer Service Agent**: Booking history, support, general inquiries

### 3.2.3 Technology Stack

**Backend Technologies:**
- **Python 3.13**: Core programming language dengan async support
- **FastAPI**: Web framework untuk RESTful APIs dengan automatic documentation
- **LangGraph**: Multi-agent workflow orchestration dengan state management
- **LangSmith**: AI agent tracing dan observability platform
- **OpenAI GPT-4.1-mini**: Large Language Model untuk natural language processing
- **OpenAI GPT-4.1**: Specialized model untuk RAG dengan temperature 0.0
- **Supabase**: Database, authentication, dan real-time capabilities
- **Redis Stack**: Caching, session management, dan monitoring dengan Redis Insight
- **Pinecone**: Vector database untuk RAG knowledge base dan semantic search
- **Model Context Protocol (MCP)**: Standardized protocol untuk external data integration
- **Prometheus**: Metrics collection dan time-series database
- **Grafana**: Monitoring dashboards dan alerting

**Frontend Technologies:**
- **Telegram Bot API**: Primary user interface
- **Next.js**: Web UI framework
- **React**: UI component library
- **TypeScript**: Type-safe JavaScript

**Infrastructure Technologies:**
- **Docker**: Containerization dengan multi-stage builds
- **Docker Compose**: Multi-container orchestration dengan service dependencies
- **Traefik**: Reverse proxy, load balancer, dan SSL termination
- **Cloudflare Tunnel**: Secure public access dengan zero-trust architecture
- **Google Cloud Platform**: Cloud hosting dengan auto-scaling
- **PostgreSQL**: Primary database dengan connection pooling
- **External APIs**: Tavily search API, currency exchange APIs
- **MCP Servers**: Booking.com, TripAdvisor, Airbnb, Supabase MCP integrations

## 3.3 Desain Database

### 3.3.1 Database Schema
Database menggunakan **PostgreSQL** melalui Supabase dengan schema:

**Core Tables:**
- `users`: User management dan authentication
- `hotels`: Hotel information dan availability
- `flights`: Flight schedules dan pricing
- `tours`: Tour packages dan itineraries

**Booking Tables:**
- `hotel_bookings`: Hotel reservation records
- `flight_bookings`: Flight reservation records  
- `tour_bookings`: Tour package reservations

**System Tables:**
- `user_profiles`: Extended user information dan preferences
- `chat_history`: Conversation logs dengan agent context
- `user_sessions`: Session management dengan Redis integration
- `system_metrics`: Performance monitoring data

### 3.3.2 Data Relationships
Database menggunakan **normalized design** dengan foreign key relationships:
- One-to-Many: Users → Bookings
- Many-to-One: Bookings → Hotels/Flights/Tours
- One-to-Many: Users → Sessions

## 3.4 Agent Design dan Implementation

### 3.4.1 Agent State Management
Setiap agent memiliki **state structure** yang konsisten:

```python
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    dialog_state: Annotated[list[str], update_dialog_stack]
    user_context: Optional[Dict[str, Any]]
```

### 3.4.2 Agent Communication Protocol
Agents berkomunikasi menggunakan **message passing** dengan:
- **Structured Messages**: Consistent message format
- **Tool Calls**: Function calling untuk external services
- **State Updates**: Shared state modifications
- **Error Propagation**: Graceful error handling

### 3.4.3 Tool Integration
Setiap agent dilengkapi dengan **specialized tools**:

**Hotel Agent Tools:**
- `get_hotels`: Retrieve all available hotels
- `search_hotels_by_location`: Location-based hotel search
- `get_hotel_details`: Detailed hotel information
- `check_available_rooms`: Room availability checking
- `book_hotel_room`: Hotel reservation processing
- `process_hotel_payment`: Payment processing untuk hotel bookings
- `cancel_hotel_booking`: Hotel booking cancellation

**Flight Agent Tools:**
- `get_flights`: Retrieve all available flights
- `search_flights_by_route`: Route-based flight search
- `get_flight_details`: Detailed flight information
- `book_flight`: Flight reservation processing
- `process_flight_payment`: Payment processing untuk flight bookings
- `cancel_flight_booking`: Flight booking cancellation

**Tour Agent Tools:**
- `get_tours`: Retrieve all available tour packages
- `search_tours_by_destination`: Destination-based tour search
- `get_tour_details`: Detailed tour package information
- `check_tour_availability`: Tour availability checking
- `book_tour`: Tour package reservation
- `process_tour_payment`: Payment processing untuk tour bookings
- `cancel_tour_booking`: Tour booking cancellation

**Customer Service Tools:**
- `get_user_booking_history`: User booking history retrieval
- `get_booking_details`: Detailed booking information
- `query_knowledge_base`: RAG-powered knowledge base search menggunakan Pinecone
- `search_currency_rates`: Real-time currency exchange rates
- `search_travel_articles`: Travel-related information search
- `search_general_info`: General information search via Tavily API

**Supervisor Tools:**
- `ToHotelAgent`: Route to hotel agent
- `ToFlightAgent`: Route to flight agent
- `ToTourAgent`: Route to tour agent
- `ToCustomerService`: Route to customer service agent
- `CompleteOrEscalate`: Complete conversation atau escalate to human

## 3.5 RAG (Retrieval-Augmented Generation) Implementation

### 3.5.1 RAG Architecture Design
RAG system diimplementasikan untuk meningkatkan customer service capabilities:
- **Knowledge Base**: Pinecone vector database dengan index 'agen-travel-faq'
- **Embedding Model**: OpenAI text-embedding-3-small untuk vector generation
- **Retrieval Strategy**: Similarity search dengan score threshold 0.15
- **Generation Model**: OpenAI GPT-4.1 dengan temperature 0.0 untuk consistent responses

### 3.5.2 Pinecone Integration
Vector database configuration untuk optimal performance:
- **Index Configuration**: Optimized untuk travel domain knowledge
- **Semantic Search**: Context-aware information retrieval
- **Real-time Updates**: Dynamic knowledge base updates
- **Scalability**: Handle large knowledge bases dengan sub-millisecond latency

### 3.5.3 RAG Workflow
RAG implementation mengikuti workflow:
1. **Query Processing**: User query preprocessing dan embedding generation
2. **Vector Search**: Semantic search dalam Pinecone index
3. **Context Retrieval**: Relevant documents retrieval berdasarkan similarity
4. **Response Generation**: LLM response generation dengan retrieved context
5. **Answer Validation**: Response validation dan fallback mechanisms

## 3.6 Model Context Protocol (MCP) Integration

### 3.6.1 MCP Architecture
MCP implementation untuk real-time external data integration:
- **MCP Servers**: Booking.com, TripAdvisor, Airbnb, Supabase servers
- **Client Management**: Centralized MCP client dengan connection pooling
- **Tool Discovery**: Automatic tool discovery dan registration
- **Error Handling**: Graceful degradation ketika MCP servers unavailable

### 3.6.2 MCP Server Configuration
Individual MCP server configurations:
- **Booking.com MCP**: Hotel dan flight data via RapidAPI
- **TripAdvisor MCP**: Reviews, ratings, dan attraction information
- **Airbnb MCP**: Property listings dan availability data
- **Supabase MCP**: Database operations dan analytics

### 3.6.3 MCP Tool Distribution
Tools didistribusikan ke agents berdasarkan specialization:
- **Hotel Agent**: Booking.com + Airbnb + Supabase MCP tools
- **Flight Agent**: Booking.com MCP tools untuk flight data
- **Tour Agent**: TripAdvisor MCP tools untuk attractions dan reviews
- **Customer Service**: TripAdvisor MCP tools untuk comprehensive information

## 3.7 Authentication dan Security

### 3.5.1 Supabase Authentication
Sistem menggunakan **Supabase Auth** dengan:
- **Email/Password Authentication**: Traditional authentication flow
- **Email Verification**: Automatic email verification untuk new users
- **Password Reset**: Secure password reset via email links
- **Row Level Security**: Database-level access control
- **JWT Integration**: Seamless token management

### 3.5.2 SMTP Email System
Email delivery menggunakan **SMTP integration** dengan:
- **Modern Templates**: Responsive HTML email templates
- **Multiple Providers**: Fallback email providers untuk reliability
- **Delivery Tracking**: Email delivery status monitoring
- **Rate Limiting**: Email sending rate control

### 3.5.3 Session Management
Session management menggunakan **JWT tokens** dengan:
- **Stateless Design**: No server-side session storage required
- **Redis Caching**: Token validation caching untuk performance
- **Expiration Handling**: Automatic token refresh mechanisms
- **Security Headers**: CORS, rate limiting, dan security middleware

### 3.5.4 Security Measures
Additional security implementations:
- **Input Validation**: Request data validation dan sanitization
- **Rate Limiting**: API rate limiting per user/IP
- **Error Handling**: Secure error responses tanpa information leakage
- **HTTPS Enforcement**: SSL/TLS encryption untuk all communications

## 3.8 Caching Strategy dengan Redis Stack

### 3.8.1 Redis Stack Implementation
Caching strategy menggunakan **Redis Stack** dengan integrated monitoring:

**Redis Server Components:**
- Database query results caching
- API response caching dengan TTL
- User session data management
- Rate limiting implementation

**Redis Insight Integration:**
- Real-time monitoring Redis performance
- Memory usage analytics dan optimization
- Key management dengan visual interface
- Query performance analysis

**Application Level Caching:**
- Database query results
- External API responses
- User session data
- Authentication tokens

**Agent Level Caching:**
- Conversation context
- Tool execution results
- User preferences
- MCP tool responses

### 3.8.2 Cache Invalidation Strategy
Cache invalidation menggunakan **TTL-based expiration** dengan:
- **Dynamic TTL**: Different expiration times per data type
- **Event-Based Invalidation**: Cache clearing pada data updates
- **Memory Management**: Automatic cleanup untuk memory optimization
- **Redis Insight Monitoring**: Visual monitoring cache performance dan hit rates

### 3.8.3 Redis Stack Security
Security implementation untuk Redis Stack:
- **Basic Authentication**: HTTP Basic Auth protection via Traefik
- **Network Isolation**: Container network isolation
- **Access Control**: Subdomain-based access control
- **Monitoring**: Secure monitoring interface dengan authentication

## 3.7 Monitoring dan Observability

### 3.7.1 LangSmith AI Observability
LangSmith integration untuk AI agent monitoring:
- **Agent Tracing**: Detailed execution traces untuk setiap agent
- **Performance Analytics**: Latency dan throughput metrics untuk LLM calls
- **Error Tracking**: Comprehensive error logging dan debugging
- **Conversation Analytics**: Analysis dari conversation flows dan patterns
- **Tool Usage Monitoring**: Tracking penggunaan tools oleh agents

### 3.7.2 Prometheus Metrics Collection
Infrastructure dan application monitoring:
- **Application Metrics**: Request rates, response times, error rates
- **Agent Metrics**: Agent invocations, tool usage, conversation flows
- **Infrastructure Metrics**: CPU, memory, disk usage, network traffic
- **Database Metrics**: Query performance, connection pool status
- **Cache Metrics**: Redis hit/miss ratios, response times
- **Business Metrics**: Booking rates, user engagement, conversion rates

### 3.7.3 Grafana Visualization
Comprehensive dashboards untuk:
- **System Health**: Infrastructure monitoring dengan alerting
- **Application Performance**: API performance metrics dan SLA tracking
- **Agent Analytics**: Agent usage patterns dan performance
- **Business Intelligence**: Booking trends, user behavior, revenue metrics
- **Error Monitoring**: Error rates, failure patterns, debugging insights

### 3.7.4 Alerting Strategy
Proactive monitoring dengan:
- **Threshold-Based Alerts**: CPU, memory, response time thresholds
- **Anomaly Detection**: Unusual patterns dalam agent behavior
- **Business Alerts**: Booking failure rates, payment issues
- **Infrastructure Alerts**: Service downtime, database connectivity

## 3.8 Deployment Strategy

### 3.8.1 Containerization
Deployment menggunakan **Docker containers** dengan:
- **Multi-Stage Builds**: Optimized container images
- **Service Isolation**: Separate containers per service
- **Resource Limits**: Memory dan CPU constraints
- **Health Checks**: Container health monitoring

### 3.8.2 Orchestration
Container orchestration menggunakan **Docker Compose** dengan:
- **Service Dependencies**: Proper startup ordering
- **Network Isolation**: Secure inter-service communication
- **Volume Management**: Persistent data storage
- **Environment Configuration**: Centralized configuration management

### 3.8.3 Cloud Deployment
Production deployment pada **Google Cloud Platform**:
- **Compute Engine**: VM instances untuk application hosting
- **Load Balancing**: Traffic distribution
- **Auto Scaling**: Dynamic resource allocation
- **Backup Strategy**: Automated backup procedures

## 3.9 Testing Strategy

### 3.9.1 Testing Levels
Testing dilakukan pada multiple levels:
- **Unit Testing**: Individual component testing
- **Integration Testing**: Service integration testing
- **Agent Testing**: Multi-agent workflow testing
- **End-to-End Testing**: Complete user journey testing

### 3.9.2 Performance Testing
Performance evaluation meliputi:
- **Load Testing**: System behavior under normal load
- **Stress Testing**: System limits dan breaking points
- **Agent Response Time**: LLM response performance
- **Database Performance**: Query optimization validation

## 3.10 Evaluation Metrics

### 3.10.1 Technical Metrics
- **Response Time**: Average API response time < 2 seconds
- **Availability**: System uptime > 99.5%
- **Throughput**: Concurrent user handling capacity
- **Error Rate**: Error rate < 1%

### 3.10.2 Functional Metrics
- **Agent Accuracy**: Correct intent recognition > 95%
- **Booking Success Rate**: Successful booking completion > 90%
- **User Satisfaction**: Positive user feedback > 85%
- **Conversation Completion**: Task completion rate > 80%

## 3.11 Research Methodology Framework

### 3.11.1 Data Collection Methods
- **System Logs**: Automated logging untuk performance analysis
- **User Interactions**: Conversation data untuk agent improvement
- **Performance Metrics**: Real-time monitoring data
- **Error Tracking**: Exception dan error pattern analysis

### 3.11.2 Analysis Techniques
- **Quantitative Analysis**: Statistical analysis dari performance metrics
- **Qualitative Analysis**: User feedback dan conversation quality assessment
- **Comparative Analysis**: Benchmarking dengan existing solutions
- **Trend Analysis**: Performance trends over time
