# BAB II
# TINJAUAN PUSTAKA

## 2.1 Multi-Agent Systems (MAS)

### 2.1.1 Definisi Multi-Agent Systems
Multi-Agent Systems (MAS) adalah sistem komputasi yang terdiri dari multiple autonomous agents yang berinteraksi dalam suatu environment untuk mencapai tujuan individual atau kolektif (Wooldridge, 2009). Setiap agent dalam MAS memiliki kemampuan untuk:
- Beroperasi secara autonomous
- Berinteraksi dengan agent lain
- Merespons perubahan environment
- Mencapai tujuan yang telah ditetapkan

### 2.1.2 Arsitektur Supervisor Agent
Supervisor agent pattern merupakan arsitektur hierarkis dimana satu agent utama (supervisor) bertanggung jawab untuk koordinasi dan delegasi tugas kepada specialized agents (Russell & Norvig, 2020). Keuntungan arsitektur ini meliputi:
- **Centralized Control**: Koordinasi terpusat untuk decision making
- **Specialization**: Setiap agent fokus pada domain expertise tertentu
- **Scalability**: Mudah menambah atau mengurangi specialized agents
- **Fault Tolerance**: Isolasi error pada level agent individual

### 2.1.3 Agent Communication dan Coordination
Komunikasi antar agent dalam MAS dapat dilakukan melalui berbagai protokol:
- **Message Passing**: Pertukaran pesan asynchronous
- **Shared Memory**: Akses ke shared state atau knowledge base
- **Event-Driven**: Komunikasi berbasis event dan notification

## 2.2 Large Language Models (LLM)

### 2.2.1 Konsep Large Language Models
Large Language Models adalah neural networks dengan parameter dalam skala besar yang dilatih pada corpus text yang massive untuk memahami dan menggenerate natural language (Brown et al., 2020). LLM modern seperti GPT-4 menunjukkan kemampuan:
- **Natural Language Understanding**: Pemahaman konteks dan semantik
- **Text Generation**: Produksi text yang coherent dan contextually relevant
- **Few-Shot Learning**: Adaptasi pada task baru dengan minimal examples
- **Multi-Modal Capabilities**: Integrasi text, image, dan data types lainnya

### 2.2.2 OpenAI GPT-4 Architecture
GPT-4 menggunakan transformer architecture dengan improvements signifikan:
- **Scale**: Parameter count dalam triliunan
- **Training Data**: Diverse dan high-quality training corpus
- **Safety Measures**: Built-in safety mechanisms dan alignment techniques
- **API Integration**: RESTful API untuk easy integration

### 2.2.3 LLM dalam Agent Systems
Integrasi LLM dalam agent systems memberikan capabilities:
- **Natural Language Interface**: User interaction menggunakan natural language
- **Context Awareness**: Mempertahankan conversation context
- **Domain Adaptation**: Specialization untuk specific domains
- **Tool Usage**: Kemampuan untuk menggunakan external tools dan APIs

## 2.3 LangGraph Framework

### 2.3.1 Konsep LangGraph
LangGraph adalah framework untuk building stateful, multi-actor applications dengan LLMs (LangChain, 2024). Framework ini menyediakan:
- **State Management**: Persistent state across conversation turns
- **Graph-Based Workflow**: Visual representation dari agent interactions
- **Checkpoint System**: Ability untuk save dan restore conversation state
- **Tool Integration**: Seamless integration dengan external tools

### 2.3.2 LangGraph Components
Komponen utama dalam LangGraph meliputi:
- **Nodes**: Individual agents atau processing units
- **Edges**: Connections dan routing logic antar nodes
- **State**: Shared state yang dapat diakses oleh semua nodes
- **Checkpointer**: Persistence layer untuk state management

### 2.3.3 Workflow Orchestration
LangGraph memungkinkan complex workflow orchestration melalui:
- **Conditional Routing**: Dynamic routing berdasarkan state atau conditions
- **Parallel Execution**: Concurrent processing untuk improved performance
- **Error Handling**: Graceful error handling dan recovery mechanisms
- **Human-in-the-Loop**: Integration points untuk human intervention

### 2.3.4 State Management dengan PostgreSQL Checkpointer
LangGraph menyediakan persistent state management melalui:
- **AsyncPostgresSaver**: PostgreSQL-based checkpointer untuk production environments
- **Connection Pooling**: Efficient database connection management
- **State Persistence**: Automatic saving dan loading conversation state
- **Fallback Mechanisms**: MemorySaver sebagai fallback untuk development

## 2.4 LangSmith Observability Platform

### 2.4.1 Konsep LangSmith
LangSmith adalah observability platform yang dirancang khusus untuk LLM applications dan agent systems (LangChain, 2024). Platform ini menyediakan:
- **Agent Tracing**: Detailed tracing untuk setiap agent invocation
- **Performance Monitoring**: Latency dan throughput metrics
- **Error Tracking**: Comprehensive error logging dan debugging
- **Conversation Analytics**: Analysis dari conversation flows dan patterns

### 2.4.2 Tracing dan Debugging
LangSmith memungkinkan deep visibility ke dalam agent behavior:
- **Execution Traces**: Step-by-step execution tracking
- **Tool Usage Analytics**: Monitoring penggunaan tools oleh agents
- **State Transitions**: Visualization dari state changes dalam workflow
- **Performance Bottlenecks**: Identification dari performance issues

### 2.4.3 Integration dengan LangGraph
LangSmith terintegrasi seamlessly dengan LangGraph untuk:
- **Automatic Tracing**: Zero-configuration tracing untuk LangGraph workflows
- **Real-time Monitoring**: Live monitoring dari agent activities
- **Historical Analysis**: Long-term analysis dari system performance
- **Debugging Support**: Interactive debugging tools untuk development

## 2.5 Microservices Architecture

### 2.5.1 Prinsip Microservices
Microservices architecture adalah pendekatan untuk mengembangkan aplikasi sebagai suite of small services yang berjalan dalam processes terpisah dan berkomunikasi melalui well-defined APIs (Newman, 2015). Karakteristik utama:
- **Service Independence**: Setiap service dapat di-develop dan deploy secara independent
- **Business Capability Focus**: Services organized around business capabilities
- **Decentralized Governance**: Independent technology choices per service
- **Failure Isolation**: Failure dalam satu service tidak mempengaruhi yang lain

### 2.5.2 Reverse Proxy dengan Traefik
Traefik adalah modern reverse proxy dan load balancer yang menyediakan:
- **Automatic Service Discovery**: Dynamic discovery dari services
- **SSL/TLS Termination**: Automatic SSL certificate management
- **Load Balancing**: Multiple load balancing algorithms
- **Middleware Support**: Rate limiting, authentication, dan monitoring
- **Dashboard**: Real-time monitoring dashboard

### 2.5.3 API Gateway Pattern
API Gateway berfungsi sebagai single entry point untuk client requests dan menyediakan:
- **Request Routing**: Routing requests ke appropriate microservices
- **Authentication & Authorization**: Centralized security enforcement
- **Rate Limiting**: Traffic control dan abuse prevention
- **Response Aggregation**: Combining responses dari multiple services

## 2.6 Database dan Storage Systems

### 2.6.1 Supabase Platform
Supabase adalah open-source Firebase alternative yang menyediakan:
- **PostgreSQL Database**: Fully managed PostgreSQL dengan real-time capabilities
- **Authentication**: Built-in user management dengan email verification
- **Storage**: File storage dengan CDN integration
- **Real-time Subscriptions**: Live data updates menggunakan WebSockets
- **Edge Functions**: Serverless functions untuk custom logic
- **Row Level Security**: Fine-grained access control

### 2.6.2 PostgreSQL Connection Pooling
Untuk production environments, connection pooling sangat penting:
- **AsyncConnectionPool**: Asynchronous connection management
- **Connection Reuse**: Efficient resource utilization
- **Health Monitoring**: Connection health checks
- **Failover Support**: Automatic failover mechanisms

### 2.6.3 Redis Stack System
Redis Stack adalah comprehensive data platform yang menggabungkan Redis Server dengan Redis Insight:
- **Redis Server**: High-performance in-memory database untuk caching dan session storage
- **Redis Insight**: Modern web-based GUI untuk Redis management dan monitoring
- **Unified Container**: Single container deployment dengan kedua komponen
- **Production Ready**: Optimized untuk production workloads dengan monitoring capabilities
- **Cache**: High-performance caching layer dengan TTL support
- **Session Store**: Session management untuk web applications
- **Message Broker**: Pub/sub messaging patterns
- **Rate Limiting**: Distributed rate limiting implementation
- **Metrics Storage**: Temporary storage untuk monitoring metrics

### 2.6.4 Redis Insight Management Interface
Redis Insight menyediakan modern interface untuk Redis management:
- **Real-time Monitoring**: Live monitoring Redis performance dan memory usage
- **Key Management**: Visual interface untuk Redis key operations
- **Query Interface**: Interactive query interface untuk Redis commands
- **Performance Analytics**: Detailed analytics untuk Redis operations
- **Memory Analysis**: Memory usage patterns dan optimization insights
- **Security Integration**: Basic Authentication protection via reverse proxy

## 2.7 Retrieval-Augmented Generation (RAG) Systems

### 2.7.1 Konsep RAG
Retrieval-Augmented Generation (RAG) adalah teknik AI yang menggabungkan information retrieval dengan text generation untuk menghasilkan respons yang lebih akurat dan faktual (Lewis et al., 2020). RAG terdiri dari dua komponen utama:
- **Retrieval Component**: Mencari informasi relevan dari knowledge base menggunakan semantic search
- **Generation Component**: Menggunakan LLM untuk menghasilkan respons berdasarkan konteks yang ditemukan
- **Augmentation Process**: Memperkaya prompt LLM dengan informasi faktual dari knowledge base

### 2.7.2 Vector Databases untuk RAG
Vector databases menyediakan infrastructure untuk semantic search dalam RAG systems:
- **Embedding Storage**: Menyimpan vector representations dari dokumen
- **Similarity Search**: Efficient similarity search menggunakan vector operations
- **Scalability**: Handling jutaan dokumen dengan performa tinggi
- **Real-time Updates**: Dynamic index updates untuk fresh information

### 2.7.3 Pinecone Vector Database
Pinecone adalah fully managed vector database yang dioptimalkan untuk AI applications:
- **Managed Service**: Fully managed infrastructure tanpa operational overhead
- **High Performance**: Sub-millisecond query latency dengan high throughput
- **Scalability**: Auto-scaling berdasarkan workload demands
- **Security**: Enterprise-grade security dengan access controls
- **Integration**: Native integration dengan popular ML frameworks
- **Metadata Filtering**: Advanced filtering capabilities untuk precise retrieval

### 2.7.4 RAG Implementation Patterns
RAG dapat diimplementasikan dengan berbagai patterns:
- **Naive RAG**: Simple retrieval dan generation pipeline
- **Advanced RAG**: Enhanced dengan query rewriting dan result reranking
- **Modular RAG**: Flexible architecture dengan interchangeable components
- **Agentic RAG**: Integration dengan AI agents untuk complex workflows

### 2.7.5 RAG untuk Customer Service
RAG sangat efektif untuk customer service applications:
- **Knowledge Base Integration**: Akses ke comprehensive FAQ dan documentation
- **Consistent Responses**: Factual responses berdasarkan authoritative sources
- **Real-time Updates**: Dynamic knowledge base updates tanpa retraining
- **Context Awareness**: Understanding user queries dalam conversation context
- **Multilingual Support**: Cross-language information retrieval

## 2.8 Model Context Protocol (MCP)

### 2.8.1 Konsep MCP
Model Context Protocol (MCP) adalah open standard yang dikembangkan oleh Anthropic untuk menghubungkan AI assistants dengan sistem eksternal tempat data berada (Anthropic, 2024). MCP berfungsi sebagai "USB-C port untuk AI applications":
- **Standardized Connection**: Protokol standar untuk koneksi AI dengan data sources
- **Real-time Data Access**: Akses langsung ke data terkini tanpa perlu API custom
- **Tool Integration**: Seamless integration external tools dengan AI agents
- **Secure Communication**: Secure communication protocols antara AI dan external systems

### 2.8.2 MCP Architecture
MCP menggunakan client-server architecture dengan komponen:
- **MCP Servers**: Expose data dan tools melalui standardized protocol
- **MCP Clients**: AI applications yang mengkonsumsi MCP services
- **Transport Layer**: Communication layer (stdio, HTTP, WebSocket)
- **Protocol Layer**: Standardized message format dan tool discovery

### 2.8.3 MCP vs Traditional API Integration
MCP menyediakan keunggulan dibanding traditional API integration:
- **Standardization**: Single protocol untuk semua integrations
- **Tool Discovery**: Automatic discovery dari available tools
- **Type Safety**: Structured tool definitions dengan validation
- **Development Speed**: Rapid integration dengan pre-built servers
- **Maintenance**: Centralized management untuk multiple data sources

### 2.8.4 MCP dalam Multi-Agent Systems
MCP sangat cocok untuk multi-agent systems karena:
- **Agent Specialization**: Different agents dapat menggunakan different MCP servers
- **Dynamic Tool Loading**: Runtime discovery dan loading MCP tools
- **Scalable Integration**: Easy addition dari new data sources
- **Consistent Interface**: Uniform interface untuk heterogeneous data sources

## 2.9 External APIs dan Integrations

### 2.7.1 Tavily Search API
Tavily adalah AI-powered search API yang menyediakan:
- **Real-time Search**: Up-to-date information retrieval
- **Content Summarization**: AI-powered content summarization
- **Source Attribution**: Reliable source tracking
- **Rate Limiting**: API usage management

### 2.7.2 Currency Exchange APIs
Untuk travel applications, currency information sangat penting:
- **Real-time Rates**: Current exchange rates
- **Historical Data**: Historical rate trends
- **Multiple Currencies**: Support untuk berbagai mata uang
- **API Reliability**: High availability dan accuracy

## 2.8 Containerization dan Orchestration

### 2.8.1 Docker Containerization
Docker menyediakan platform untuk developing, shipping, dan running applications dalam containers (Merkel, 2014). Benefits meliputi:
- **Consistency**: Consistent environment across development, testing, dan production
- **Isolation**: Application isolation dan resource management
- **Portability**: Run anywhere yang support Docker
- **Scalability**: Easy horizontal scaling
- **Multi-stage Builds**: Optimized image sizes
- **Health Checks**: Built-in container health monitoring

### 2.8.2 Docker Compose Orchestration
Docker Compose menyediakan orchestration untuk multi-container applications:
- **Service Definition**: Declarative service configuration dalam YAML
- **Network Management**: Custom networks untuk inter-container communication
- **Volume Management**: Persistent data storage dan sharing
- **Environment Variables**: Centralized configuration management
- **Dependency Management**: Service startup order dan dependencies

## 2.9 Monitoring dan Observability

### 2.9.1 Prometheus Monitoring
Prometheus adalah open-source monitoring system dengan:
- **Time Series Database**: Efficient storage untuk metrics data
- **Pull-Based Model**: Scraping metrics dari targets
- **PromQL**: Powerful query language untuk metrics analysis
- **Alerting**: Rule-based alerting system
- **Service Discovery**: Automatic target discovery
- **Exporters**: Specialized metrics collectors

### 2.9.2 Grafana Visualization
Grafana menyediakan visualization platform untuk:
- **Dashboard Creation**: Interactive dashboards untuk metrics visualization
- **Data Source Integration**: Support untuk multiple data sources (Prometheus, PostgreSQL, Redis)
- **Alerting**: Visual alerting dengan notification channels
- **User Management**: Role-based access control
- **Template Variables**: Dynamic dashboard configuration
- **Annotations**: Event marking dan correlation

### 2.9.3 Application Performance Monitoring
Untuk AI agent systems, monitoring khusus diperlukan:
- **Agent Invocation Metrics**: Tracking agent calls dan performance
- **Response Time Monitoring**: Latency tracking untuk user experience
- **Error Rate Tracking**: Error monitoring dan alerting
- **Cache Performance**: Cache hit/miss ratios dan response times
- **Database Query Performance**: Query execution time dan frequency

## 2.10 Security dan Authentication

### 2.10.1 Supabase Authentication
Supabase Auth menyediakan comprehensive authentication system:
- **Email/Password Authentication**: Traditional email-based auth
- **Email Verification**: Automatic email verification workflows
- **Password Reset**: Secure password reset dengan email links
- **Social Providers**: Integration dengan OAuth providers
- **Row Level Security**: Database-level access control
- **JWT Integration**: Seamless JWT token management

### 2.10.2 SMTP Email System
SMTP (Simple Mail Transfer Protocol) untuk email delivery:
- **Email Templates**: Modern, responsive HTML templates
- **Delivery Tracking**: Monitoring email delivery success dan failures
- **Rate Limiting**: Email sending rate control
- **Template Customization**: Dynamic content injection
- **Multi-provider Support**: Fallback email providers

### 2.10.3 JWT Token Management
JSON Web Tokens (JWT) menyediakan secure token-based authentication:
- **Stateless Authentication**: No server-side session storage required
- **Claims-Based**: Embedded user information dan permissions
- **Signature Verification**: Cryptographic signature untuk integrity
- **Expiration Handling**: Built-in token expiration mechanisms
- **Refresh Token Support**: Long-term authentication management

### 2.10.4 Rate Limiting dan Security
Security measures untuk production systems:
- **API Rate Limiting**: Request rate control per user/IP
- **CORS Configuration**: Cross-origin request security
- **Input Validation**: Request data validation dan sanitization
- **Error Handling**: Secure error responses tanpa information leakage

## 2.11 Cloud Infrastructure

### 2.11.1 Google Cloud Platform (GCP)
GCP menyediakan cloud computing services meliputi:
- **Compute Engine**: Virtual machine instances dengan auto-scaling
- **Container Registry**: Docker image storage dan management
- **Cloud SQL**: Managed database services dengan backup
- **Load Balancing**: Traffic distribution dan high availability
- **Cloud Storage**: Object storage untuk static assets
- **Cloud Monitoring**: Integrated monitoring dan logging

### 2.11.2 Cloudflare Services
Cloudflare menyediakan comprehensive CDN dan security services:
- **Global CDN**: Content delivery network dengan edge locations worldwide
- **DDoS Protection**: Automatic DDoS mitigation dengan real-time threat intelligence
- **SSL/TLS**: Automatic SSL certificate management dengan modern encryption
- **Analytics**: Traffic analytics dan performance insights dengan real-time data
- **Edge Computing**: Edge functions untuk low-latency processing
- **DNS Management**: Fast dan reliable DNS services dengan global anycast

### 2.11.3 Cloudflare Tunnel Technology
Cloudflare Tunnel menyediakan secure connectivity solution:
- **Zero Trust Architecture**: Secure access tanpa exposing server IPs atau opening firewall ports
- **Encrypted Connections**: End-to-end encryption untuk all traffic
- **Global Routing**: Intelligent routing melalui Cloudflare's global network
- **Automatic Failover**: High availability dengan automatic failover mechanisms
- **Access Control**: Granular access controls dengan authentication integration
- **Performance Optimization**: Automatic performance optimization dengan edge caching

### 2.11.4 Tunnel vs Traditional Networking
Cloudflare Tunnel advantages over traditional networking:
- **Security**: No inbound firewall rules required, reducing attack surface
- **Simplicity**: No complex networking configuration atau port forwarding
- **Reliability**: Built-in redundancy dengan global infrastructure
- **Performance**: Optimized routing melalui Cloudflare's network
- **Scalability**: Automatic scaling tanpa infrastructure changes
- **Monitoring**: Built-in analytics dan monitoring capabilities

## 2.12 Frontend Technologies

### 2.12.1 Telegram Bot API
Telegram Bot API menyediakan platform untuk bot development:
- **Webhook Support**: Real-time message processing
- **Rich Media**: Support untuk images, documents, dan interactive elements
- **Inline Keyboards**: Interactive button interfaces
- **Message Formatting**: Markdown dan HTML formatting support
- **File Handling**: Upload dan download file capabilities

### 2.12.2 Next.js Web Framework
Next.js adalah React framework untuk production applications:
- **Server-Side Rendering**: Improved SEO dan performance
- **API Routes**: Built-in API endpoint creation
- **Static Generation**: Pre-built pages untuk fast loading
- **TypeScript Support**: Type-safe development
- **Automatic Code Splitting**: Optimized bundle sizes

## 2.15 Research Gap dan Kontribusi

Berdasarkan tinjauan pustaka, research gap yang diidentifikasi meliputi:
1. **Limited Integration**: Kurangnya framework terintegrasi untuk LLM-based multi-agent systems dalam travel domain dengan supervisor pattern
2. **Scalability Challenges**: Minimnya research tentang scalable deployment untuk AI agent systems dengan production-ready infrastructure
3. **Real-world Implementation**: Gap antara theoretical frameworks dan practical implementation dengan modern technology stack
4. **Observability Gap**: Kurangnya comprehensive monitoring dan tracing untuk multi-agent AI systems
5. **Performance Optimization**: Limited research tentang caching strategies dan optimization untuk AI agent systems
6. **RAG Integration Gap**: Kurangnya research tentang RAG integration dalam multi-agent systems untuk enhanced knowledge retrieval
7. **MCP Adoption**: Limited implementation dari Model Context Protocol dalam production multi-agent systems
8. **Real-time Data Integration**: Gap dalam integrating real-time external data sources dengan AI agents

Kontribusi penelitian ini adalah:
1. **Comprehensive Architecture**: End-to-end architecture untuk AI-powered travel booking system dengan supervisor pattern menggunakan LangGraph
2. **Practical Implementation**: Real-world implementation menggunakan modern technology stack (FastAPI, Supabase, Redis Stack, Docker, Traefik)
3. **Performance Optimization**: Integrated caching dengan Redis Stack, database connection pooling, dan monitoring untuk production-ready system
4. **Observability Framework**: Implementation LangSmith untuk AI agent tracing dan Prometheus/Grafana untuk infrastructure monitoring
5. **Multi-Interface Support**: Dual interface implementation (Telegram Bot dan Web UI) untuk maximum accessibility
6. **Security Implementation**: Comprehensive security dengan Supabase Auth, JWT tokens, rate limiting, dan email verification
7. **Deployment Strategy**: Production-ready deployment dengan Docker containerization, reverse proxy, dan cloud infrastructure
8. **RAG Implementation**: Integration Pinecone vector database untuk enhanced knowledge retrieval dalam customer service
9. **MCP Integration**: Implementation Model Context Protocol untuk real-time external data integration (Booking.com, TripAdvisor, Airbnb)
10. **Advanced Monitoring**: Redis Insight integration untuk comprehensive caching monitoring dan management
11. **Secure Public Access**: Cloudflare Tunnel implementation untuk zero-trust public access tanpa firewall configuration
