# 🌴 Arsitektur Agen Travel Berbasis AI dengan Implementasi LangGraph dan Model Context Protocol (MCP)

Sistem multi-agen untuk pemesanan hotel, penerbangan, dan paket tur menggunakan **Ekosistem LangChain** khususnya **LangGraph** dan **LangSmith** dengan **OpenAI GPT-4.1-mini** sebagai model AI utama. Pengguna dapat berinteraksi dalam bahasa alami untuk mencari informasi, memeriksa ketersediaan, dan melakukan pemesanan dengan mengingat konteks percakapan melalui **Telegram Bot** (@agen_travel_bot) atau interface web (Web UI).

> 🎓 **Proyek Tugas Akhir Sarjana Teknologi Informasi**
> Sistem ini dikembangkan sebagai persyaratan kelulusan program Sarjana Teknologi Informasi Universitas Udayana dengan fokus pada implementasi AI Multi-Agent System, Microservices Architecture, dan Modern DevOps Practices.

## 🏗️ Arsitektur Enterprise & Infrastructure

### 🔄 Reverse Proxy & Load Balancing dengan Traefik
Sistem menggunakan **Traefik v3.4** sebagai reverse proxy dan load balancer modern dengan fitur:

**🎯 Core Features:**
- **Auto-Discovery**: Deteksi otomatis container Docker dengan label-based routing
- **Dynamic Configuration**: Konfigurasi routing yang dapat berubah secara real-time
- **Health Checks**: Monitoring kesehatan service dengan automatic failover
- **Load Balancing**: Distribusi traffic dengan sticky sessions
- **Rate Limiting**: Pembatasan request untuk mencegah abuse dan DDoS
- **SSL/TLS Termination**: Siap untuk HTTPS dengan Let's Encrypt integration
- **Dashboard Monitoring**: Web interface untuk monitoring routing dan metrics

**🔧 Configuration Structure:**
```yaml
# Static Configuration (traefik.yml)
- Entry Points: HTTP (80), HTTPS (443), Dashboard (8080)
- Providers: Docker auto-discovery + File-based routing
- Metrics: Prometheus integration untuk monitoring

# Dynamic Configuration (dynamic/*.yml)
- backend.yml: API routing dengan CORS, rate limiting, dan Basic Auth untuk docs
- telegram.yml: Webhook routing dengan security headers
- monitoring.yml: Grafana & Prometheus dengan subdomain routing
- supabase.yml: Database dashboard dengan subdomain routing
- redis.yml: Redis Insight dengan subdomain routing dan Basic Authentication
- dashboard.yml: Traefik dashboard dengan subdomain routing
- middlewares.yml: Reusable middleware definitions (CORS, Auth, Security)
```

**🔀 Routing Logic:**
```yaml
# Path-based routing (main domain)
agen-travel.live/api/*     → backend:2025
agen-travel.live/webhook/* → telegram-bot:8444
agen-travel.live/health    → backend:2025/health
agen-travel.live/docs      → backend:2025/api/docs (Basic Auth)

# Subdomain routing (admin services)
traefik.agen-travel.live   → traefik:8080 (Basic Auth)
redis.agen-travel.live     → redis-stack:8001 (Basic Auth)
grafana.agen-travel.live   → grafana:3000 (Built-in Auth)
prometheus.agen-travel.live → prometheus:9090 (Basic Auth)
supabase.agen-travel.live  → supabase-studio:54323 (Basic Auth)
```

**🛡️ Security Features:**
- **Basic Authentication**: Protected admin interfaces (Traefik, Prometheus, Redis Insight, Supabase)
- **CORS Configuration**: Cross-origin request handling
- **Security Headers**: XSS protection, content type sniffing prevention
- **Rate Limiting**: Per-service rate limiting dengan burst handling
- **Multi-layer Security**: Authentication di level reverse proxy tanpa mengganggu fungsionalitas

### 🌐 Cloudflare Tunnel Integration
Implementasi **Cloudflare Tunnel** untuk secure public access tanpa port forwarding:

**🔐 Zero Trust Architecture:**
- **Domain**: `agen-travel.live` dengan SSL/TLS otomatis
- **Zero Trust Security**: Akses aman tanpa membuka port firewall
- **Global CDN**: Performa optimal dengan edge locations worldwide
- **DDoS Protection**: Perlindungan otomatis dari serangan DDoS
- **Analytics**: Real-time traffic analytics dan security insights

**🌍 Global Routing Configuration:**
```yaml
# .cloudflared/config.yml
ingress:
  # ===== SUBDOMAIN ROUTING =====
  # Monitoring & Admin Services menggunakan subdomain
  - hostname: traefik.agen-travel.live    # Traefik Dashboard
    service: http://localhost:80
  - hostname: redis.agen-travel.live      # Redis Insight
    service: http://localhost:80
  - hostname: grafana.agen-travel.live    # Grafana Dashboard
    service: http://localhost:80
  - hostname: prometheus.agen-travel.live # Prometheus Metrics
    service: http://localhost:80
  - hostname: supabase.agen-travel.live   # Supabase Studio
    service: http://localhost:80

  # ===== PATH-BASED ROUTING =====
  # Main domain menggunakan path-based routing
  - hostname: agen-travel.live
    path: /api/*          # Backend API
  - hostname: agen-travel.live
    path: /webhook/*      # Telegram Webhook
  - hostname: agen-travel.live
    path: /health         # Health Check
  - hostname: agen-travel.live
    path: /docs           # API Documentation
  - hostname: agen-travel.live
    service: http://localhost:80  # Default routing
```

**📊 Benefits:**
- **No Port Forwarding**: Secure access tanpa membuka ports
- **Automatic SSL**: Certificate management otomatis
- **Global Performance**: Edge caching dan optimization
- **Security**: Built-in DDoS protection dan WAF
- **Reliability**: 99.9% uptime dengan global infrastructure

**🔄 Routing Strategy:**
- **Production**: Menggunakan subdomain untuk admin services (traefik.agen-travel.live, redis.agen-travel.live, dll.)
- **Development**: Menggunakan subdomain localhost (traefik.localhost, redis.localhost, dll.)
- **Main Services**: Path-based routing pada domain utama (/api/*, /webhook/*, /health)
- **Security**: Admin interfaces dilindungi Basic Authentication di level Traefik

### 🔐 Authentication & Security
Sistem autentikasi berlapis dengan **Supabase Auth** dan **Basic Authentication**:

**🔑 User Authentication Features:**
- **JWT-based Authentication**: Secure token-based authentication dengan RS256
- **Email Verification**: Verifikasi email otomatis dengan Supabase Auth
- **Password Reset**: Reset password via email dengan secure tokens
- **Session Management**: Redis-based session storage dengan automatic expiry
- **Multi-platform Support**: Konsisten di Telegram Bot dan Web UI
- **Role-based Access**: User roles dan permissions management

**🛡️ Admin Interface Security:**
- **Basic Authentication**: Proteksi dashboard admin dengan HTTP Basic Auth
- **API Documentation Protection**: Swagger/ReDoc docs diamankan dengan Basic Auth
- **Service-specific Credentials**: Setiap service memiliki kredensial terpisah
- **Non-intrusive Security**: Autentikasi di level reverse proxy tanpa mengubah aplikasi
- **Secure Password Storage**: Password di-hash dengan bcrypt dalam file .htpasswd

**📧 Email Verification Flow:**
```mermaid
graph LR
    A[User Register] --> B[Create Supabase User]
    B --> C[Send Verification Email]
    C --> D[User Clicks Link]
    D --> E[Verify Token]
    E --> F[Update User Status]
    F --> G[Redirect to Success Page]
```

**🔄 Session Management:**
- **Redis Storage**: Session data disimpan di Redis dengan TTL
- **Automatic Refresh**: Token refresh otomatis sebelum expiry
- **Cross-platform Sync**: Session sync antara Web UI dan Telegram
- **Secure Logout**: Proper session cleanup dan token invalidation

**🛡️ Security Measures:**
- **Password Hashing**: Bcrypt hashing dengan salt
- **Rate Limiting**: Login attempt limiting untuk brute force protection
- **CORS Protection**: Configured CORS untuk secure cross-origin requests
- **Environment Isolation**: Sensitive data di environment variables

### 🗄️ Redis Stack Integration
Sistem menggunakan **Redis Stack** yang menggabungkan Redis Server dan Redis Insight:

**📊 Redis Stack Components:**
- **Redis Server**: High-performance in-memory database untuk caching dan session storage
- **Redis Insight**: Modern web-based GUI untuk Redis management dan monitoring
- **Unified Container**: Single container deployment dengan kedua komponen
- **Production Ready**: Optimized untuk production workloads

**🔐 Redis Insight Security:**
- **Basic Authentication**: Protected dengan HTTP Basic Auth via Traefik
- **Subdomain Access**: Akses melalui `redis.localhost` atau `redis.agen-travel.live`
- **Non-intrusive**: Tidak menggunakan Redis ACL untuk menjaga kesederhanaan
- **Full Functionality**: Semua fitur Redis Insight tetap berfungsi normal
- **Secure Credentials**: Lihat file `traefik/config/.htpasswd-redis` untuk kredensial

**⚡ Redis Features:**
- **Session Storage**: JWT session management dengan automatic expiry
- **Caching Layer**: Application-level caching untuk performance optimization
- **Real-time Data**: WebSocket connection state management
- **Metrics Storage**: Temporary metrics storage untuk monitoring
- **Background Jobs**: Queue management untuk asynchronous tasks

### 🤖 Model AI & Development Tools
- **LLM Model**: OpenAI GPT-4.1-mini - Model AI terbaru yang efisien dengan kemampuan reasoning yang kuat dan cost-effective untuk aplikasi production
- **RAG Model**: OpenAI GPT-4.1 - Model khusus untuk Retrieval-Augmented Generation dengan temperature 0.0 untuk konsistensi jawaban
- **Development Environment**:
  - **Code Editor**: Cursor AI dan VSCode untuk remote development
  - **Remote Development**: SSH connection ke GCP VM untuk server development
  - **AI Coding Assistant**: Augment Code dengan Claude Sonnet 4 untuk intelligent code assistance
  - **Runtime**: Python 3.13 dalam Docker containers

### 🧠 RAG (Retrieval-Augmented Generation) untuk Customer Service

Sistem menggunakan **RAG** untuk meningkatkan kualitas layanan customer service dengan mengintegrasikan knowledge base dan FAQ yang tersimpan di **Pinecone Vector Database**.

#### 🔍 Apa itu RAG?
**Retrieval-Augmented Generation (RAG)** adalah teknik AI yang menggabungkan:
- **Retrieval**: Pencarian informasi relevan dari knowledge base menggunakan semantic search
- **Generation**: Menghasilkan jawaban yang akurat berdasarkan konteks yang ditemukan
- **Augmentation**: Memperkaya respons AI dengan informasi faktual dan terkini

#### 📊 Pinecone Vector Database
**Pinecone** adalah vector database yang digunakan untuk menyimpan dan mencari knowledge base:

**🔧 Konfigurasi Pinecone:**
- **Index Name**: `agen-travel-faq` - Index yang berisi knowledge base dan FAQ
- **Embedding Model**: `text-embedding-3-small` - Model OpenAI untuk mengkonversi teks ke vector
- **Search Type**: `similarity_score_threshold` - Pencarian berdasarkan similarity score
- **Score Threshold**: `0.15` - Minimum threshold untuk relevansi dokumen
- **Max Documents**: `20` - Maksimum dokumen yang diambil per query

**💡 Keunggulan Pinecone:**
- **Semantic Search**: Pencarian berdasarkan makna, bukan hanya keyword matching
- **Real-time Updates**: Index dapat diupdate secara real-time
- **Scalability**: Dapat menangani jutaan dokumen dengan performa tinggi
- **Cloud-native**: Fully managed service tanpa perlu maintenance infrastructure

#### ⚙️ Konfigurasi RAG
**Model & Parameter:**
```bash
# Model khusus untuk RAG
RAG_MODEL=gpt-4.1          # Model OpenAI GPT-4.1 untuk konsistensi tinggi
TEMPERATURE=0.0            # Temperature 0.0 untuk jawaban yang konsisten dan faktual

# Pinecone Configuration
PINECONE_API_KEY=your_key  # API key untuk akses Pinecone
PINECONE_ENV=us-east-1-aws # Environment region Pinecone
```

**🎯 Mengapa Temperature 0.0?**
- **Konsistensi**: Jawaban yang sama untuk pertanyaan yang sama
- **Faktual**: Mengurangi halusinasi dan jawaban yang tidak akurat
- **Reliability**: Cocok untuk customer service yang membutuhkan informasi tepat

#### 🔧 Integrasi dengan Customer Service Agent
RAG terintegrasi langsung dengan **Customer Service Agent** melalui tool `query_knowledge_base`:

**📋 Kapan RAG Digunakan:**
- Pertanyaan tentang kebijakan perusahaan (pembatalan, refund, perubahan booking)
- FAQ umum tentang layanan travel
- Prosedur dan panduan penggunaan layanan
- Informasi umum tentang destinasi wisata
- Troubleshooting dan bantuan teknis
- Syarat dan ketentuan layanan

**🛠️ Tool Implementation:**
```python
@tool
async def query_knowledge_base(question: str, k: int = 5) -> str:
    """
    Mencari informasi dari knowledge base dan FAQ agen travel.

    Args:
        question: Pertanyaan dalam bahasa natural
        k: Jumlah dokumen yang diambil (default: 5, max: 20)

    Returns:
        String jawaban berdasarkan knowledge base
    """
```

**🔄 Alur Kerja RAG:**
1. **Input**: User mengajukan pertanyaan ke customer service
2. **Embedding**: Pertanyaan dikonversi ke vector menggunakan OpenAI embeddings
3. **Retrieval**: Pencarian semantic di Pinecone index `agen-travel-faq`
4. **Context**: Dokumen relevan diambil berdasarkan similarity score
5. **Generation**: GPT-4.1 menghasilkan jawaban berdasarkan konteks
6. **Output**: Jawaban yang akurat dan faktual diberikan ke user

**⚡ Performance & Reliability:**
- **Caching**: Hasil query di-cache untuk performa optimal
- **Fallback**: Jika knowledge base tidak tersedia, sistem fallback ke web search
- **Error Handling**: Graceful error handling dengan pesan informatif
- **Logging**: Comprehensive logging untuk monitoring dan debugging

### 🔌 Model Context Protocol (MCP) untuk Integrasi Real-time

Sistem menggunakan **Model Context Protocol (MCP)** untuk mengintegrasikan data real-time dari platform travel eksternal, memberikan akses langsung ke informasi terkini dari Booking.com, TripAdvisor, Airbnb, dan database internal.

#### 🔍 Apa itu Model Context Protocol (MCP)?
**Model Context Protocol (MCP)** adalah standar terbuka yang dikembangkan oleh Anthropic untuk menghubungkan AI assistant dengan sistem eksternal tempat data berada. MCP berfungsi seperti "USB-C port untuk aplikasi AI" - menyediakan cara standar untuk menghubungkan model AI dengan berbagai sumber data dan tools.

**🎯 Konsep Utama MCP:**
- **Standardized Connection**: Protokol standar untuk koneksi AI dengan data sources
- **Real-time Data Access**: Akses langsung ke data terkini tanpa perlu API custom
- **Tool Integration**: Integrasi tools eksternal dengan AI agents
- **Secure Communication**: Komunikasi aman antara AI dan sistem eksternal

#### 💡 Keunggulan MCP
**🚀 Untuk Pengembangan:**
- **Simplified Integration**: Satu protokol untuk semua integrasi eksternal
- **Reduced Complexity**: Tidak perlu membangun connector custom untuk setiap service
- **Standardized Interface**: Interface yang konsisten untuk semua data sources
- **Rapid Development**: Pengembangan lebih cepat dengan pre-built MCP servers

**⚡ Untuk Performa:**
- **Real-time Data**: Data selalu fresh dan up-to-date dari sumber asli
- **Direct Access**: Akses langsung tanpa middleware tambahan
- **Efficient Communication**: Protokol yang dioptimalkan untuk komunikasi AI-data
- **Scalable Architecture**: Mudah menambah data sources baru

**🔒 Untuk Keamanan:**
- **Controlled Access**: Akses terkontrol ke data sensitif
- **Authentication**: Built-in authentication mechanisms
- **Isolation**: Setiap MCP server terisolasi dan independen
- **Audit Trail**: Logging lengkap untuk semua akses data

#### 🏗️ Arsitektur MCP dalam Proyek
**📊 MCP Servers yang Terintegrasi:**

1. **🏨 Booking.com MCP Server**
   - **Purpose**: Data hotel dan penerbangan real-time dari Booking.com
   - **API**: RapidAPI Booking.com API
   - **Transport**: stdio
   - **Authentication**: RAPIDAPI_KEY

2. **🌟 TripAdvisor MCP Server**
   - **Purpose**: Review, rating, dan informasi atraksi wisata
   - **API**: TripAdvisor Content API
   - **Transport**: stdio
   - **Authentication**: TRIPADVISOR_API_KEY

3. **🏠 Airbnb MCP Server**
   - **Purpose**: Data properti Airbnb dan villa
   - **API**: Web scraping dengan respect robots.txt
   - **Transport**: stdio
   - **Authentication**: Tidak diperlukan

4. **🗄️ Supabase MCP Server**
   - **Purpose**: Database operations dan analytics
   - **API**: Direct PostgreSQL connection
   - **Transport**: stdio
   - **Authentication**: DATABASE_URI

#### ⚙️ Konfigurasi MCP
**Environment Variables:**
```bash
# MCP API Keys
RAPIDAPI_KEY=your_rapidapi_key          # Untuk Booking.com MCP
TRIPADVISOR_API_KEY=your_tripadvisor_key # Untuk TripAdvisor MCP
DATABASE_URI=postgresql://...            # Untuk Supabase MCP
# Airbnb MCP tidak memerlukan API key
```

**🔧 MCP Client Configuration:**
```python
MCP_CLIENTS = {
    "booking": {
        "command": "uv",
        "args": ["--directory", "mcps/servers/booking.com", "run", "src/booking_com_mcp/main.py"],
        "env": {"RAPIDAPI_KEY": RAPIDAPI_KEY},
        "transport": "stdio"
    },
    "tripadvisor": {
        "command": "uv",
        "args": ["--directory", "mcps/servers/tripadvisor", "run", "src/tripadvisor_mcp/main.py"],
        "env": {"TRIPADVISOR_API_KEY": TRIPADVISOR_API_KEY},
        "transport": "stdio"
    },
    "airbnb": {
        "command": "npx",
        "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
        "transport": "stdio"
    },
    "supabase": {
        "command": "uv",
        "args": ["--directory", "mcps/servers/supabase", "run", "src/supabase_mcp/main.py"],
        "env": {"DATABASE_URI": DATABASE_URI},
        "transport": "stdio"
    }
}
```

#### 🛠️ MCP Tools Distribution per Agent
**🏨 Hotel Agent MCP Tools:**
- **Booking.com Tools**:
  - `booking_com_search_destinations` - Cari destinasi hotel
  - `booking_com_get_hotels` - Dapatkan daftar hotel untuk destinasi
  - `booking_com_get_hotel_details` - Detail lengkap hotel termasuk fasilitas
  - `booking_com_get_room_availability` - Ketersediaan kamar real-time
- **Airbnb Tools**:
  - `airbnb_search` - Cari properti Airbnb berdasarkan lokasi
  - `airbnb_listing_details` - Detail lengkap properti Airbnb
- **Supabase Tools**:
  - `execute_sql` - Eksekusi query database untuk operasi hotel
  - `analyze_db_health` - Monitoring kesehatan database

**✈️ Flight Agent MCP Tools:**
- **Booking.com Tools**:
  - `booking_com_search_flight_destinations` - Cari destinasi penerbangan
  - `booking_com_get_flights` - Pencarian penerbangan antar destinasi
  - `booking_com_get_flight_details` - Detail lengkap penerbangan

**🏝️ Tour Agent MCP Tools:**
- **TripAdvisor Tools**:
  - `search_locations` - Cari lokasi wisata, restoran, atraksi
  - `search_nearby_locations` - Cari tempat wisata terdekat
  - `get_location_details` - Detail lengkap lokasi wisata
  - `get_location_reviews` - Review dan rating dari traveler
  - `get_location_photos` - Foto-foto lokasi wisata

**📞 Customer Service MCP Tools:**
- **TripAdvisor Tools**: Akses ke semua tools TripAdvisor untuk memberikan informasi review dan rating
- **RAG Tools**: Kombinasi dengan knowledge base untuk FAQ

#### 🔄 Alur Kerja MCP Integration
1. **Initialization**: MCP servers diinisialisasi saat startup aplikasi
2. **Tool Registration**: Tools dari setiap MCP server didaftarkan ke agent yang sesuai
3. **Request Processing**: Ketika user meminta data real-time, agent menggunakan MCP tools
4. **Data Retrieval**: MCP server mengambil data dari API eksternal
5. **Response Processing**: Data diproses dan dikembalikan ke user dalam format yang user-friendly

**🔧 Lazy Loading & Error Handling:**
- **Lazy Initialization**: MCP tools dimuat hanya ketika diperlukan
- **Graceful Degradation**: Jika MCP server tidak tersedia, sistem tetap berjalan dengan tools lokal
- **Automatic Retry**: Retry mechanism untuk koneksi yang gagal
- **Comprehensive Logging**: Logging lengkap untuk debugging dan monitoring

**📊 MCP vs Traditional API Integration:**
| Aspek | Traditional API | MCP Integration |
|-------|----------------|-----------------|
| **Setup Complexity** | Custom untuk setiap API | Standardized protocol |
| **Maintenance** | Manual untuk setiap service | Centralized management |
| **Error Handling** | Custom per API | Unified error handling |
| **Tool Discovery** | Manual registration | Automatic discovery |
| **Development Speed** | Slow (custom code) | Fast (pre-built servers) |
| **Scalability** | Limited | Highly scalable |

**💡 Contoh Penggunaan MCP:**
```
User: "Cari hotel di Bali dengan rating tinggi dari TripAdvisor"
→ Hotel Agent menggunakan:
  1. booking_com_search_destinations("Bali")
  2. booking_com_get_hotels(destination_id, dates)
  3. search_locations("hotels Bali") dari TripAdvisor
  4. get_location_reviews(hotel_ids) untuk rating

User: "Bandingkan villa Airbnb di Ubud dengan hotel Booking.com"
→ Hotel Agent menggunakan:
  1. airbnb_search("Ubud villa")
  2. booking_com_get_hotels("Ubud")
  3. Perbandingan data dari kedua sumber
```

### 📱 Telegram Bot Integration
Sistem terintegrasi dengan Telegram Bot yang memungkinkan pengguna berinteraksi langsung melalui chat:
- **Bot Name**: Agen Travel
- **Bot Username**: @agen_travel_bot
- **Bot ID**: agen_travel_bot
- **Webhook Integration**: Real-time message processing dengan Cloudflare Tunnel

#### 🤖 Available Bot Commands
Bot menyediakan command-command berikut untuk memudahkan interaksi:

| Command | Deskripsi |
|---------|-----------|
| `/start` | Mulai percakapan dengan agen travel |
| `/register` | Registrasi akun baru |
| `/login` | Login ke akun yang sudah ada |
| `/profile` | Lihat profil pengguna |
| `/newchat` | Mulai percakapan baru |
| `/deletechat` | Hapus riwayat percakapan |
| `/help` | Tampilkan bantuan dan informasi bot |
| `/logout` | Logout dari akun |

**💡 Tips Penggunaan:**
- Gunakan `/start` untuk memulai interaksi pertama kali
- Setelah login, Anda dapat langsung mengetik permintaan dalam bahasa natural
- Gunakan `/newchat` untuk memulai sesi percakapan baru
- Command `/help` memberikan panduan lengkap penggunaan bot

## 📊 Diagram Arsitektur Multi-Agen

### Diagram Utama - Alur Multi-Agen
```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
    'primaryColor': '#e4e1f5',
    'primaryTextColor': '#5a5a5a',
    'primaryBorderColor': '#b6a4e3',
    'lineColor': '#b6a4e3',
    'secondaryColor': '#f0f0f0',
    'tertiaryColor': '#f0f0f0'
    }}}%%
graph TD
    %% Define nodes
    START([_start_])
    END([_end_])

    supervisor[supervisor]

    hotel_agent_entrypoint[hotel_agent_entrypoint]
    hotel_agent[hotel_agent]
    hotel_agent_tools[hotel_agent_tools]

    flight_agent_entrypoint[flight_agent_entrypoint]
    flight_agent[flight_agent]
    flight_agent_tools[flight_agent_tools]

    tour_agent_entrypoint[tour_agent_entrypoint]
    tour_agent[tour_agent]
    tour_agent_tools[tour_agent_tools]

    customer_service_entrypoint[customer_service_entrypoint]
    customer_service[customer_service]
    customer_service_tools[customer_service_tools]

    return_to_supervisor[return_to_supervisor]

    %% Connections
    START -.-> supervisor
    START -.-> hotel_agent
    START -.-> flight_agent
    START -.-> tour_agent
    START -.-> customer_service

    supervisor -.-> hotel_agent_entrypoint
    supervisor -.-> flight_agent_entrypoint
    supervisor -.-> tour_agent_entrypoint
    supervisor -.-> customer_service_entrypoint
    supervisor -.-> END

    hotel_agent_entrypoint --> hotel_agent
    hotel_agent --> hotel_agent_tools
    hotel_agent -.-> return_to_supervisor
    hotel_agent_tools --> hotel_agent
    hotel_agent -.-> END

    flight_agent_entrypoint --> flight_agent
    flight_agent --> flight_agent_tools
    flight_agent -.-> return_to_supervisor
    flight_agent_tools --> flight_agent
    flight_agent -.-> END

    tour_agent_entrypoint --> tour_agent
    tour_agent --> tour_agent_tools
    tour_agent -.-> return_to_supervisor
    tour_agent_tools --> tour_agent
    tour_agent -.-> END

    customer_service_entrypoint --> customer_service
    customer_service --> customer_service_tools
    customer_service -.-> return_to_supervisor
    customer_service_tools --> customer_service
    customer_service -.-> END

    return_to_supervisor --> supervisor

    %% Styling classes
    classDef supervisor fill:#f9f,stroke:#333,stroke-width:2px;
    classDef agent fill:#fcf,stroke:#333,stroke-width:1px;
    classDef tool fill:#bbf,stroke:#333,stroke-width:1px;
    classDef user fill:#dfd,stroke:#333,stroke-width:2px;
    classDef flow fill:none,stroke:#999,stroke-width:1px,stroke-dasharray: 5 5;
    classDef start_end fill:#f9f,stroke:#333,stroke-width:2px,shape:circle;

    %% Apply styling
    class supervisor supervisor;
    class hotel_agent,flight_agent,tour_agent,customer_service agent;
    class hotel_agent_tools,flight_agent_tools,tour_agent_tools,customer_service_tools tool;
    class hotel_agent_entrypoint,flight_agent_entrypoint,tour_agent_entrypoint,customer_service_entrypoint,return_to_supervisor flow;
    class START,END start_end;
```

<details>
<summary>📋 Lihat Diagram Tools dan Routing</summary>

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
    'primaryColor': '#e4e1f5',
    'primaryTextColor': '#5a5a5a',
    'primaryBorderColor': '#b6a4e3',
    'lineColor': '#b6a4e3',
    'secondaryColor': '#f0f0f0',
    'tertiaryColor': '#f0f0f0'
    }}}%%
graph TD
    %% Define nodes
    START([_start_])
    END([_end_])

    supervisor[supervisor]

    hotel_agent_entrypoint[hotel_agent_entrypoint]
    hotel_agent[hotel_agent]
    hotel_agent_tools[hotel_agent_tools]

    flight_agent_entrypoint[flight_agent_entrypoint]
    flight_agent[flight_agent]
    flight_agent_tools[flight_agent_tools]

    tour_agent_entrypoint[tour_agent_entrypoint]
    tour_agent[tour_agent]
    tour_agent_tools[tour_agent_tools]

    customer_service_entrypoint[customer_service_entrypoint]
    customer_service[customer_service]
    customer_service_tools[customer_service_tools]

    return_to_supervisor[return_to_supervisor]

    %% Hotel Tools Definition
    subgraph HotelTools[Hotel Tool Functions]
        search_hotels_destination[search_hotels_destination]
        get_hotel_details[get_hotel_details]
        boook_hotel_room[boook_hotel_room]
    end

    %% Flight Tools Definition
    subgraph FlightTools[Flight Tool Functions]
        search_flights_route[search_flights_route]
        get_flight_details[get_flight_details]
        book_flight[book_flight]
    end

    %% Tour Tools Definition
    subgraph TourTools[Tour Tool Functions]
        search_tours_by_destination[search_tours_by_destination]
        get_tour_details[get_tour_details]
        book_tour[book_tour]
    end

    %% Customer Service Tools Definition
    subgraph CustomerServiceTools[Customer Service Tool Functions]
        get_user_booking_history[get_user_booking_history]
        get_booking_details[get_booking_details]
    end

    %% Connections
    START -.-> supervisor
    START -.-> hotel_agent
    START -.-> flight_agent
    START -.-> tour_agent
    START -.-> customer_service

    supervisor -.-> hotel_agent_entrypoint
    supervisor -.-> flight_agent_entrypoint
    supervisor -.-> tour_agent_entrypoint
    supervisor -.-> customer_service_entrypoint
    supervisor -.-> END

    hotel_agent_entrypoint --> hotel_agent
    hotel_agent --> hotel_agent_tools
    hotel_agent -.-> return_to_supervisor
    hotel_agent_tools --> hotel_agent
    hotel_agent -.-> END

    flight_agent_entrypoint --> flight_agent
    flight_agent --> flight_agent_tools
    flight_agent -.-> return_to_supervisor
    flight_agent_tools --> flight_agent
    flight_agent -.-> END

    tour_agent_entrypoint --> tour_agent
    tour_agent --> tour_agent_tools
    tour_agent -.-> return_to_supervisor
    tour_agent_tools --> tour_agent
    tour_agent -.-> END

    customer_service_entrypoint --> customer_service
    customer_service --> customer_service_tools
    customer_service -.-> return_to_supervisor
    customer_service_tools --> customer_service
    customer_service -.-> END

    return_to_supervisor --> supervisor

    %% Tool connections
    hotel_agent_tools --- HotelTools
    flight_agent_tools --- FlightTools
    tour_agent_tools --- TourTools
    customer_service_tools --- CustomerServiceTools

    %% Styling classes
    classDef supervisor fill:#f9f,stroke:#333,stroke-width:2px;
    classDef agent fill:#fcf,stroke:#333,stroke-width:1px;
    classDef tool fill:#bbf,stroke:#333,stroke-width:1px;
    classDef user fill:#dfd,stroke:#333,stroke-width:2px;
    classDef flow fill:none,stroke:#999,stroke-width:1px,stroke-dasharray: 5 5;
    classDef start_end fill:#f9f,stroke:#333,stroke-width:2px;

    %% Apply styling
    class supervisor supervisor;
    class hotel_agent,flight_agent,tour_agent,customer_service agent;
    class hotel_agent_tools,flight_agent_tools,tour_agent_tools,customer_service_tools tool;
    class search_hotels_destination,boook_hotel_room,get_hotel_details tool;
    class search_flights_route,book_flight,get_flight_details tool;
    class get_tours,search_tours_by_destination,get_tour_details,check_tour_availability,book_tour,process_tour_payment,cancel_tour_booking tool;
    class get_user_booking_history,get_booking_details tool;
    class hotel_agent_entrypoint,flight_agent_entrypoint,tour_agent_entrypoint,customer_service_entrypoint,return_to_supervisor flow;
    class HotelTools,FlightTools,TourTools,CustomerServiceTools flow;
    class START,END start_end;
```

</details>

<details>
<summary>🔧 Lihat Diagram Detail Implementasi</summary>

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
    'primaryColor': '#e4e1f5',
    'primaryTextColor': '#5a5a5a',
    'primaryBorderColor': '#b6a4e3',
    'lineColor': '#b6a4e3',
    'secondaryColor': '#f0f0f0',
    'tertiaryColor': '#f0f0f0'
    }}}%%
graph TD

    %% Main nodes
    START([Start])
    supervisor[Supervisor Agent]

    %% Agent paths - separated for clarity
    subgraph CustomerServicePath[Customer Service Path]
        customer_service_entrypoint[Customer Service Entry Node]
        customer_service[Customer Service]
        customer_service_tools[Customer Service Tools]
    end

    subgraph TourPath[Tour Path]
        tour_agent_entrypoint[Tour Agent Entry Node]
        tour_agent[Tour Agent]
        tour_agent_tools[Tour Tools]
    end

    subgraph FlightPath[Flight Path]
        flight_agent_entrypoint[Flight Agent Entry Node]
        flight_agent[Flight Agent]
        flight_agent_tools[Flight Tools]
    end

    subgraph HotelPath[Hotel Path]
        hotel_agent_entrypoint[Hotel Agent Entry Node]
        hotel_agent[Hotel Agent]
        hotel_agent_tools[Hotel Tools]
    end

    %% Positioned at bottom of diagram
    return_to_supervisor[Return to Supervisor]
    END([End])

    %% Main flow connections
    START -->|route_to_workflow| supervisor

    %% Supervisor routing
    supervisor -->|ToHotelAgent| hotel_agent_entrypoint
    supervisor -->|ToFlightAgent| flight_agent_entrypoint
    supervisor -->|ToTourAgent| tour_agent_entrypoint
    supervisor -->|ToCustomerService| customer_service_entrypoint
    supervisor -->|CompleteOrEscalate/ToSupervisor| END

    %% Hotel path flow
    hotel_agent_entrypoint -->|Entry Node Message| hotel_agent
    hotel_agent -->|tool_condition route| hotel_agent_tools
    hotel_agent -.->|CompleteOrEscalate| return_to_supervisor
    hotel_agent_tools -->|Tool Response| hotel_agent
    hotel_agent -.->|END condition| END

    %% Flight path flow
    flight_agent_entrypoint -->|Entry Node Message| flight_agent
    flight_agent -->|tool_condition route| flight_agent_tools
    flight_agent -.->|CompleteOrEscalate| return_to_supervisor
    flight_agent_tools -->|Tool Response| flight_agent
    flight_agent -.->|END condition| END

    %% Tour path flow
    tour_agent_entrypoint -->|Entry Node Message| tour_agent
    tour_agent -->|tool_condition route| tour_agent_tools
    tour_agent -.->|CompleteOrEscalate| return_to_supervisor
    tour_agent_tools -->|Tool Response| tour_agent
    tour_agent -.->|END condition| END

    %% Customer Service path flow
    customer_service_entrypoint -->|Entry Node Message| customer_service
    customer_service -->|tool_condition route| customer_service_tools
    customer_service -.->|CompleteOrEscalate| return_to_supervisor
    customer_service_tools -->|Tool Response| customer_service
    customer_service -.->|END condition| END

    %% Return path
    return_to_supervisor -->|Pop Dialog State| supervisor

    %% Styling classes
    classDef supervisor fill:#f9f,stroke:#333,stroke-width:2px;
    classDef agent fill:#fcf,stroke:#333,stroke-width:1px;
    classDef tool fill:#bbf,stroke:#333,stroke-width:1px;
    classDef user fill:#dfd,stroke:#333,stroke-width:2px;
    classDef flow fill:none,stroke:#999,stroke-width:1px,stroke-dasharray: 5 5;
    classDef start_end fill:#f9f,stroke:#333,stroke-width:2px,shape:circle;

    %% Apply styles
    class START,END start_end
    class supervisor supervisor
    class hotel_agent,flight_agent,tour_agent,customer_service agent
    class hotel_agent_entrypoint,flight_agent_entrypoint,tour_agent_entrypoint,customer_service_entrypoint flow
    class hotel_agent_tools,flight_agent_tools,tour_agent_tools,customer_service_tools tool
    class return_to_supervisor,HotelPath,FlightPath,TourPath,CustomerServicePath flow
```

</details>

## 🔑 Fitur Utama

### 🎯 Core Features
- **Interaksi Bahasa Alami**: Pengguna dapat mencari hotel, penerbangan, paket tur, memeriksa ketersediaan, dan melakukan pemesanan dengan bahasa alami
- **Sistem Multi-Agen**: 5 agen AI spesialis untuk menangani berbagai layanan travel
- **Kesadaran Konteks**: Sistem mempertahankan konteks percakapan per sesi dengan Supabase persistence
- **Authentication System**: Registrasi, login, dan verifikasi email terintegrasi
- **Real-time Communication**: WebSocket dan webhook untuk komunikasi real-time

### 🌐 Multi-Interface Access
- 📱 **Telegram Bot**: Chat interface untuk mobile users dengan webhook integration
- 🌐 **Web UI**: Modern chat interface berbasis Next.js untuk desktop
- 🛠️ **LangGraph Studio**: Development dan debugging interface untuk agen
- 📊 **Admin Dashboard**: Monitoring dan management interface

### 🔧 Infrastructure & DevOps
- **Reverse Proxy**: Traefik untuk load balancing dan routing
- **Secure Tunneling**: Cloudflare Tunnel untuk public access
- **API Documentation**: Swagger/ReDoc dengan Basic Authentication protection
- **Monitoring Stack**: Grafana, Prometheus, dan custom metrics
- **Microservices Architecture**: Arsitektur terdistribusi dengan Docker containers
- **CI/CD Ready**: Deployment automation dengan GCP integration
- **AI-Powered Development**: Dikembangkan dengan Cursor AI dan Augment Code assistance

## 🏗️ Arsitektur Sistem

### 🔄 Infrastructure Layer
- **Reverse Proxy**: Traefik v3.4 untuk load balancing, routing, dan SSL termination
- **Secure Tunneling**: Cloudflare Tunnel untuk public access dengan domain `agen-travel.live`
- **Container Orchestration**: Docker Compose untuk multi-service deployment
- **Networking**: Custom Docker networks untuk service isolation dan communication

### 🖥️ Application Layer
- **Frontend Services**:
  - **Web UI**: Modern chat interface berbasis Next.js dengan TypeScript
  - **Telegram Bot**: Python-based bot dengan webhook integration
- **Backend Services**:
  - **FastAPI Backend**: API Gateway dengan endpoint terstruktur, middleware CORS, dan error handling
  - **Authentication Service**: JWT-based auth dengan Supabase integration
  - **Email Service**: Verifikasi email dan notifikasi dengan Supabase Auth

### 🤖 AI Agent Layer (LangGraph)
- **Agen Supervisor (supervisor)**: Agen utama yang mengarahkan permintaan pengguna ke sub agen
- **Agen Customer Service (customer_service)**: Menangani pengecekan riwayat pemesanan dan detail booking
- **Agen Hotel (hotel_agent)**: Pencarian informasi dan pemesanan hotel
- **Agen Pesawat (flight_agent)**: Pencarian informasi dan pemesanan penerbangan
- **Agen Tur (tour_agent)**: Pencarian informasi dan pemesanan paket wisata

### 💾 Data Layer
- **Primary Database**: Supabase PostgreSQL untuk data persistence
- **Cache Layer**: Redis Stack (Redis Server + Redis Insight) untuk session management dan caching
- **Vector Database**: Pinecone untuk RAG knowledge base dan semantic search
- **Storage**: Supabase Storage untuk file uploads dan static assets
- **Checkpoint Storage**: LangGraph state persistence di Supabase
- **Redis Insight**: Web-based Redis management interface dengan Basic Authentication

### 📊 Monitoring & Observability
- **Application Monitoring**: LangSmith untuk AI agent tracing dan evaluation
- **Infrastructure Monitoring**: Prometheus untuk metrics collection
- **Visualization**: Grafana dashboards untuk real-time monitoring
- **System Metrics**: Node Exporter dan Redis Exporter untuk system health

## 🧩 Alur Multi-Agen di LangGraph

Workflow berbasis **LangGraph** meliputi:

### Peran Agen dan Tools

#### Agen Supervisor (supervisor)
Berperan sebagai agen utama dan router, bertanggung jawab untuk:
- Interaksi awal pengguna
- Mengarahkan permintaan ke sub agen
- Menangani pertanyaan umum dan koordinasi antar agen

**Tools:**
- ToHotelAgent - Mengarahkan ke agen hotel
- ToFlightAgent - Mengarahkan ke agen pesawat
- ToTourAgent - Mengarahkan ke agen tur
- ToCustomerService - Mengarahkan ke agen customer service
- ToSupervisor - Mengarahkan kembali ke agen supervisor
- CompleteOrEscalate - Menyelesaikan percakapan atau meneruskan ke agen lain

#### Agen Customer Service (customer_service)
Menangani layanan pelanggan, riwayat pemesanan, dan FAQ dengan dukungan RAG dan MCP:

**Local Tools:**
- get_user_booking_history - Mendapatkan riwayat pemesanan pengguna
- get_booking_details - Mendapatkan detail pemesanan spesifik
- cancel_hotel_booking, cancel_flight_booking, cancel_tour_booking - Pembatalan pemesanan
- search_currency_rates - Informasi nilai tukar mata uang
- search_travel_articles - Artikel dan tips travel
- search_general_info - Informasi umum menggunakan web search

**🧠 RAG Tools:**
- **query_knowledge_base** - Mencari informasi dari knowledge base dan FAQ

**🔌 MCP Tools (Real-time Data):**
- **TripAdvisor MCP**: Akses ke semua tools TripAdvisor untuk memberikan review dan rating terkini

#### Agen Hotel (hotel_agent)
Sub-agen untuk semua layanan hotel dengan integrasi MCP real-time:

**Local Tools:**
- get_hotels - Menampilkan semua hotel yang tersedia
- search_hotels_by_location - Mencari hotel berdasarkan lokasi
- get_hotel_details - Mendapatkan detail hotel
- check_available_rooms - Memeriksa ketersediaan kamar hotel
- book_hotel_room - Melakukan pemesanan hotel
- process_hotel_payment - Memproses pembayaran hotel
- check_unpaid_bookings - Memeriksa pemesanan yang belum dibayar
- cancel_hotel_booking - Membatalkan pemesanan hotel

**🔌 MCP Tools (Real-time Data):**
- **Booking.com MCP**: booking_com_search_destinations, booking_com_get_hotels, booking_com_get_hotel_details, booking_com_get_room_availability
- **Airbnb MCP**: airbnb_search, airbnb_listing_details
- **Supabase MCP**: execute_sql, analyze_db_health untuk database operations

#### Agen Pesawat (flight_agent)
Sub-agen untuk semua layanan penerbangan dengan integrasi MCP real-time:

**Local Tools:**
- get_flights - Menampilkan penerbangan yang tersedia
- search_flights_by_route - Mencari penerbangan berdasarkan rute
- get_flight_details - Mendapatkan detail penerbangan
- book_flight - Melakukan pemesanan penerbangan
- process_flight_payment - Memproses pembayaran penerbangan
- check_unpaid_bookings - Memeriksa pemesanan yang belum dibayar
- cancel_flight_booking - Membatalkan pemesanan penerbangan

**🔌 MCP Tools (Real-time Data):**
- **Booking.com MCP**: booking_com_search_flight_destinations, booking_com_get_flights, booking_com_get_flight_details

#### Agen Tur (tour_agent)
Sub-agen untuk semua layanan paket wisata dengan integrasi MCP real-time:

**Local Tools:**
- get_tours - Menampilkan paket tur yang tersedia
- search_tours_by_destination - Mencari tur berdasarkan destinasi
- get_tour_details - Mendapatkan detail paket tur
- check_tour_availability - Memeriksa ketersediaan tur
- book_tour - Melakukan pemesanan tur
- process_tour_payment - Memproses pembayaran tur
- check_unpaid_bookings - Memeriksa pemesanan yang belum dibayar
- cancel_tour_booking - Membatalkan pemesanan tur

**🔌 MCP Tools (Real-time Data):**
- **TripAdvisor MCP**: search_locations, search_nearby_locations, get_location_details, get_location_reviews, get_location_photos

### Struktur Alur
- **State Management**: Setiap agen mempertahankan konteks percakapan
- **Conditional Routing**: Menentukan agen mana yang harus menangani setiap permintaan pengguna
- **Tool Execution**: Alat khusus dijalankan berdasarkan kebutuhan pengguna
- **Manajemen Konteks & Sesi**: Mengelola alur sesi dan penghentian percakapan
- **Asynchronous Processing**: Pemrosesan asinkron untuk performa optimal

## 📂 Struktur Proyek

```bash
agen-travel/
├── arsitektur/                    # 📊 Diagram arsitektur sistem
│   ├── diagram.mmd               # Diagram utama arsitektur multi-agen
│   ├── diagram-tools.mmd         # Diagram tools dan routing
│   ├── diagram-details.mmd       # Diagram detail implementasi
│   └── *.png                     # Export diagram dalam format PNG
├── backend/                      # 🚀 Backend FastAPI dengan LangGraph
│   ├── agents/                   # 🤖 Definisi agen dan manajemen state
│   │   ├── agents.py            # Konfigurasi runnable agen
│   │   ├── graph.py             # Definisi alur LangGraph
│   │   ├── base.py              # Kelas agen dasar
│   │   ├── state.py             # Manajemen state percakapan
│   │   ├── prompts.py           # Prompt sistem untuk setiap agen
│   │   └── route.py             # Routing dan helper functions
│   ├── api/                     # 🌐 Endpoint API
│   │   ├── router.py            # API router untuk FastAPI
│   │   └── v1/                  # API versi 1
│   │       ├── response.py      # Endpoint percakapan
│   │       ├── auth.py          # Endpoint autentikasi
│   │       ├── email.py         # Endpoint verifikasi email
│   │       └── cache.py         # Endpoint manajemen cache
│   ├── database/                # 💾 Konfigurasi database
│   │   ├── engine.py            # Engine untuk akses database
│   │   ├── services.py          # Service layer untuk database
│   │   ├── auth.py              # Service autentikasi
│   │   └── sql/                 # SQL scripts
│   │       ├── agen_travel.sql  # Schema database
│   │       └── data_agen_travel.sql # Data sample
│   ├── models/                  # 📋 Model data
│   │   ├── agents.py            # Model untuk agen dan routing
│   │   ├── response.py          # Model untuk percakapan
│   │   ├── auth.py              # Model autentikasi
│   │   └── tools.py             # Model untuk tools
│   ├── rag/                     # 🧠 RAG (Retrieval-Augmented Generation)
│   │   ├── __init__.py          # RAG tools export
│   │   ├── pinecone.py          # Pinecone vector database integration
│   │   └── utils.py             # RAG utility functions
│   ├── mcps/                    # 🔌 Model Context Protocol (MCP)
│   │   ├── __init__.py          # MCP tools initialization
│   │   ├── manager.py           # MCP manager dan connection handling
│   │   ├── clients.py           # MCP client configurations
│   │   └── servers/             # MCP servers
│   │       ├── booking.com/     # Booking.com MCP server
│   │       ├── tripadvisor/     # TripAdvisor MCP server
│   │       ├── airbnb/          # Airbnb MCP server
│   │       └── supabase/        # Supabase MCP server
│   ├── tools/                   # 🔧 Implementasi tools
│   │   └── tools.py             # Semua tools agen (hotel, flight, tour, dll.)
│   ├── utils/                   # ⚙️ Utilitas dan konfigurasi
│   │   ├── config.py            # Pengaturan konfigurasi
│   │   ├── datetime.py          # Utilitas tanggal dan waktu
│   │   ├── handler.py           # Handler untuk event dan error
│   │   ├── validation.py        # Validasi input dan data
│   │   ├── middleware.py        # Middleware untuk FastAPI
│   │   ├── metrics.py           # Metrics untuk monitoring
│   │   ├── prometheus.py        # Prometheus integration
│   │   ├── instrumentator.py    # Instrumentasi monitoring
│   │   ├── email.py             # Service email dan verifikasi
│   │   ├── auth.py              # Utilitas autentikasi JWT
│   │   └── redis.py             # Redis client dan session management
│   ├── static/                  # 📁 Static files
│   │   └── redirect.html        # Halaman redirect verifikasi email
│   ├── tests/                   # 🧪 Unit tests
│   ├── main.py                  # Entry point aplikasi FastAPI
│   ├── .env                     # Variabel environment backend
│   ├── langgraph.json           # Konfigurasi LangGraph
│   ├── Dockerfile               # Konfigurasi Docker
│   └── requirements.txt         # Dependensi Python backend
├── frontend/                    # 🖥️ Frontend applications
│   ├── webui/                   # 🌐 Chat UI modern berbasis Next.js
│   │   ├── src/                 # Source code aplikasi Next.js
│   │   ├── package.json         # Dependencies Node.js
│   │   ├── next.config.mjs      # Konfigurasi Next.js
│   │   └── langgraph.json       # Konfigurasi LangGraph client
│   └── telegram/                # 📱 Bot Telegram
│       ├── bot.py               # Implementasi bot Telegram
│       ├── .env                 # Variabel environment telegram
│       ├── Dockerfile           # Konfigurasi Docker
│       └── requirements.txt     # Dependensi Python telegram
├── traefik/                     # 🔄 Reverse Proxy & Load Balancer
│   ├── traefik.yml              # Konfigurasi static Traefik
│   ├── dynamic/                 # Konfigurasi dynamic routing
│   │   ├── backend.yml          # Routing untuk backend API
│   │   ├── telegram.yml         # Routing untuk Telegram webhook
│   │   ├── monitoring.yml       # Routing untuk Grafana & Prometheus
│   │   ├── supabase.yml         # Routing untuk Supabase dashboard
│   │   ├── redis.yml            # Routing untuk Redis Insight dengan Basic Auth
│   │   ├── dashboard.yml        # Routing untuk Traefik dashboard
│   │   └── middlewares.yml      # Middleware definitions
│   └── config/                  # Konfigurasi sensitif
│       ├── .env                 # Environment variables
│       ├── .htpasswd            # Basic auth credentials
│       └── .htpasswd-*          # Service-specific auth files
├── supabase/                    # 🗄️ Database Supabase
│   ├── agen-travel/             # Proyek Supabase lokal
│   │   ├── docker-compose.yml   # Konfigurasi Supabase
│   │   └── .env                 # Environment Supabase
│   └── supabase/                # Repository Supabase official
├── grafana/                     # 📊 Monitoring dashboard
│   ├── dashboards/              # Konfigurasi Dashboard
│   └── datasources/             # Konfigurasi Data sources
├── prometheus/                  # 📈 Metrics collection
│   └── prometheus.yml           # Konfigurasi Prometheus
├── scripts/                     # 🚀 Deployment dan utility scripts
│   ├── gcp.sh                   # Script manajemen VM GCP
│   ├── vm.sh                    # Script kontrol VM (start/stop)
│   ├── cloudflare.sh            # Script Cloudflare Tunnel management
│   └── ngrok.sh                 # Script ngrok untuk webhook (legacy)
├── .cloudflared/                # ☁️ Cloudflare Tunnel configuration
│   ├── config.yml               # Konfigurasi tunnel routing
│   └── tunnel.log               # Log file tunnel
├── docker-compose.yml           # 🐳 Orchestrasi semua services
├── .env                         # 🔐 Environment variables global
├── .gitignore                   # File git ignore
├── plan.md                      # 📋 Rencana pengembangan
└── requirements.txt             # Dependensi Python root
```

## 🚀 Instalasi dan Setup

### Prasyarat
- Docker dan Docker Compose
- Git
- ngrok (untuk webhook Telegram)
- GCP CLI (untuk deployment)
- Telegram Bot Token (dari BotFather)
- OpenAI API Key

### 🤖 Setup Telegram Bot

Sebelum menjalankan aplikasi, Anda perlu membuat Telegram Bot:

1. **Buka Telegram dan cari @BotFather**
2. **Mulai chat dengan BotFather dan buat bot baru**:
   ```
   /start
   /newbot
   ```
3. **Masukkan nama bot**: `Agen Travel`
4. **Masukkan username bot**: `agen_travel_bot` (atau username unik lainnya)
5. **Simpan Bot Token** yang diberikan BotFather (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

6. **Konfigurasi Bot (Opsional)**:
   ```
   /setdescription - Set deskripsi bot
   /setabouttext - Set teks about
   /setuserpic - Upload foto profil bot
   ```

7. **Set Bot Commands** untuk user experience yang lebih baik:
   ```
   /setcommands

   Kemudian masukkan commands berikut:
   start - Mulai percakapan dengan agen travel
   new_chat - Buat percakapan baru
   delete_chat - Hapus riwayat percakapan
   cancel - Batalkan operasi saat ini
   ```

**Contoh Bot Token**: `7617976401:AAH54HligRbQLO0mnb7Q8De6ThKUZdgXA2Q`

> ⚠️ **Penting**: Jangan pernah share Bot Token Anda secara publik. Simpan dengan aman di file `.env`

### Clone Repository
```bash
git clone https://github.com/esakrissa/agen-travel-ai.git
cd agen-travel
```

## 🔧 Menjalankan Proyek

### 1️⃣ Setup Supabase Database

Pertama, setup database Supabase lokal:

```bash
# Clone repository Supabase official
cd supabase
git clone https://github.com/supabase/supabase.git

# Buat proyek agen-travel
cd agen-travel
cp .env.example .env

# Edit .env dan set:
# - POSTGRES_PASSWORD=your_secure_password
# - ANON_KEY=your_anon_key
# - JWT_SECRET=your_jwt_secret
# - DASHBOARD_PASSWORD=your_dashboard_password

# Pull dan jalankan Supabase
docker compose pull
docker compose up -d
```

Supabase akan tersedia di:
- Dashboard: `http://localhost:54323`
- Database: `postgresql://postgres:your_secure_password@localhost:54322/postgres`
- API: `http://localhost:8000`

### 2️⃣ Setup Cloudflare Tunnel untuk Public Access

#### Prerequisites
```bash
# Install Cloudflare CLI (jika belum ada)
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

#### Setup Tunnel
```bash
# Login ke Cloudflare (hanya sekali)
cloudflared tunnel login

# Jalankan tunnel menggunakan script
./scripts/cloudflare.sh start
```

#### 🌐 Domain & Routing Configuration
Domain `agen-travel.live` sudah dikonfigurasi dengan routing lengkap:

**🔗 Public Endpoints (Main Domain):**
- **API Backend**: `https://agen-travel.live/api/*`
- **Telegram Webhook**: `https://agen-travel.live/webhook/*`
- **Health Check**: `https://agen-travel.live/health`
- **API Documentation**: `https://agen-travel.live/docs` (Basic Auth required)

**📊 Monitoring & Admin (Subdomain Access):**
- **Traefik Dashboard**: `https://traefik.agen-travel.live` (Basic Auth required)
- **Redis Insight**: `https://redis.agen-travel.live` (Basic Auth required)
- **Grafana Dashboard**: `https://grafana.agen-travel.live` (Built-in login)
- **Prometheus Metrics**: `https://prometheus.agen-travel.live` (Basic Auth required)
- **Supabase Studio**: `https://supabase.agen-travel.live` (Basic Auth required)

#### 🔧 Script Cloudflare Management
Script `./scripts/cloudflare.sh` menyediakan comprehensive tunnel management:

**📋 Available Commands:**
```bash
# Menjalankan tunnel di background
./scripts/cloudflare.sh start

# Memeriksa status tunnel dan koneksi
./scripts/cloudflare.sh status

# Menghentikan tunnel
./scripts/cloudflare.sh stop

# Melihat log tunnel secara real-time
./scripts/cloudflare.sh logs
```

**🔍 Script Features:**
- **Background Execution**: Tunnel berjalan di background dengan nohup
- **Process Management**: Automatic process detection dan management
- **Logging**: Comprehensive logging ke `.cloudflared/tunnel.log`
- **Status Monitoring**: Real-time status checking dengan tunnel info
- **Error Handling**: Graceful error handling dan user feedback

**📁 File Structure:**
```bash
.cloudflared/
├── config.yml          # Tunnel configuration dengan routing rules
├── tunnel.log           # Log file untuk debugging
└── cert.pem            # Cloudflare certificate (auto-generated)
```

**🚀 Automatic Setup:**
Script akan otomatis:
1. Memeriksa apakah tunnel sudah berjalan
2. Validasi konfigurasi file
3. Menjalankan tunnel dengan logging
4. Memberikan feedback status dan URL access
5. Menyimpan PID untuk management

**💡 Usage Tips:**
- Jalankan `start` setelah semua services Docker aktif
- Gunakan `status` untuk monitoring koneksi
- Check `logs` jika ada masalah koneksi
- `stop` akan gracefully terminate tunnel process

### 3️⃣ Build dan Jalankan dengan Docker Compose

```bash
# Build semua services
docker compose build

# Jalankan semua services
docker compose up -d

# Melihat status services
docker compose ps

# Melihat logs
docker compose logs -f
```

#### 🌐 Services & Access Points

**🔄 Via Traefik Reverse Proxy (Recommended):**

*Main Domain Services (Path-based routing):*
- **Backend API**: `http://localhost/api/*`
- **API Documentation**: `http://localhost/api/docs` (Basic Auth required)
- **Telegram Webhook**: `http://localhost/webhook/*`
- **Health Check**: `http://localhost/health`

*Admin Services (Subdomain routing):*
- **Traefik Dashboard**: `http://traefik.localhost` (Basic Auth required)
- **Grafana**: `http://grafana.localhost` (Built-in login)
- **Prometheus**: `http://prometheus.localhost` (Basic Auth required)
- **Supabase Studio**: `http://supabase.localhost` (Basic Auth required)
- **Redis Insight**: `http://redis.localhost` (Basic Auth required)

**🔗 Direct Access (Development):**
- **Node Exporter**: `http://localhost:9100`
- **Redis**: `localhost:6379` (untuk database clients)

**📊 Monitoring & Health:**
- **Health Check**: `http://localhost/health`
- **Metrics**: `http://localhost/metrics`
- **API Docs**: `http://localhost/api/docs` (Basic Auth required)

#### 🌐 Konfigurasi Subdomain untuk Development

Untuk mengakses layanan melalui subdomain, Anda perlu menambahkan konfigurasi ke file `/etc/hosts`:

**Di macOS/Linux:**
```bash
# Edit file hosts dengan editor favorit
sudo nano /etc/hosts

# Atau menggunakan vim
sudo vim /etc/hosts
```

**Di Windows:**
```bash
# Buka Command Prompt sebagai Administrator, lalu:
notepad C:\Windows\System32\drivers\etc\hosts
```

**Tambahkan baris berikut di akhir file `/etc/hosts`:**
```bash
# Agen Travel - Subdomain Configuration (Development)
127.0.0.1 redis.localhost
127.0.0.1 grafana.localhost
127.0.0.1 prometheus.localhost
127.0.0.1 supabase.localhost
127.0.0.1 traefik.localhost
```

**💡 Development vs Production Routing:**
- **Development**: Menggunakan `.localhost` subdomain (redis.localhost, grafana.localhost, dll.)
- **Production**: Menggunakan `.agen-travel.live` subdomain (redis.agen-travel.live, grafana.agen-travel.live, dll.)
- **Traefik Configuration**: Otomatis mendeteksi dan routing ke service yang tepat berdasarkan hostname

**Setelah menyimpan file, restart browser dan akses layanan:**
- ✅ **Redis Insight**: `http://redis.localhost` (Basic Auth required)
- ✅ **Grafana**: `http://grafana.localhost` (Built-in login)
- ✅ **Prometheus**: `http://prometheus.localhost` (Basic Auth required)
- ✅ **Supabase Studio**: `http://supabase.localhost` (Basic Auth required)
- ✅ **Traefik Dashboard**: `http://traefik.localhost` (Basic Auth required)

**💡 Tips:**
- Tidak perlu restart Docker services setelah edit `/etc/hosts`
- Jika subdomain tidak bisa diakses, coba clear browser cache
- Untuk production, gunakan DNS record yang sebenarnya

### 4️⃣ LangGraph Studio untuk Development

Untuk development dan debugging agen dengan interface visual:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Buat virtual environment
python -m venv .venv

# Install dependensi Python
uv pip install -r requirements.txt

# Install LangGraph CLI
uv pip install -U "langgraph-cli[inmem]"

# Jalankan LangGraph Studio
cd backend
langgraph dev
```

LangGraph Studio akan tersedia di `http://localhost:2024` dengan:
- **Graph ID**: `agen_travel`
- **Visual Interface**: Interface grafis untuk testing agen
- **Real-time Debugging**: Monitor alur eksekusi agen secara real-time
- **State Inspection**: Melihat state management antar agen

### 5️⃣ Web UI Development Interface

Untuk development dengan interface web yang terhubung langsung ke LangGraph API:

```bash
cd frontend/webui
npm install
npm run dev
```

Web UI akan tersedia di `http://localhost:3000` dan akan terhubung ke:
- **LangGraph API**: `http://localhost:2024` (ketika menjalankan `langgraph dev`)
- **Agent ID**: `agen_travel`
- **Real-time Chat**: Interface chat langsung dengan multi-agent system

### 6️⃣ Menggunakan Telegram Bot

Setelah setup selesai, pengguna dapat berinteraksi dengan sistem melalui Telegram:

1. **Cari bot di Telegram**: `@agen_travel_bot`
2. **Mulai percakapan**: Ketik `/start`
3. **Gunakan commands**:
   - `/start` - Mulai percakapan
   - `/register` - Registrasi baru
   - `/login` - Login akun
   - `/profile` - Lihat profil
   - `/newchat` - Percakapan baru
   - `/deletechat` - Hapus percakapan
   - `/help` - Bantuan
   - `/logout` - Logout akun

4. **Contoh percakapan**:
   ```
   User: Halo, saya ingin mencari hotel di Ubud
   Bot: 🏨 Halo! Saya akan membantu Anda mencari hotel di Ubud...

   User: Saya butuh kamar untuk 2 orang tanggal 25 Desember
   Bot: ✅ Berikut hotel yang tersedia di Ubud untuk 2 tamu...

   User: Bagaimana cara membatalkan booking hotel?
   Bot: 🧠 Berdasarkan knowledge base kami, untuk membatalkan booking hotel...
   ```

5. **Fitur Bot**:
   - 💬 Chat natural language processing
   - 🔄 Context awareness antar pesan
   - 📱 Mobile-friendly interface
   - ⚡ Real-time responses via webhook
   - 🎯 Multi-agent routing otomatis
   - 🧠 **RAG-powered FAQ** - Jawaban akurat dari knowledge base

6. **Contoh Pertanyaan RAG**:
   ```
   User: "Apa kebijakan refund untuk penerbangan?"
   User: "Bagaimana cara mengubah tanggal booking?"
   User: "Berapa lama proses pembayaran?"
   User: "Syarat dan ketentuan pemesanan apa saja?"
   User: "Panduan menggunakan aplikasi"
   ```

7. **Contoh Pertanyaan MCP**:
   ```
   User: "Gunakan Booking.com untuk cari hotel di Bali"
   User: "Pakai TripAdvisor untuk lihat review restoran di Ubud"
   User: "Cari villa Airbnb di Seminyak untuk 4 orang"
   User: "Bandingkan hotel Booking.com dengan Airbnb di Canggu"
   User: "Gunakan data real-time untuk penerbangan Jakarta-Bali"
   ```

## 🔍 Monitoring dan Debugging

### 🎯 LangSmith Integration
Proyek ini terintegrasi dengan LangSmith untuk monitoring aktivitas agen dan eksekusi workflow:

```bash
# backend/.env
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=agen-travel
LANGSMITH_TRACING_V2=true
```

**Fitur LangSmith:**
- **Agent Tracing**: Monitor eksekusi setiap agen secara real-time
- **Performance Analytics**: Analisis performa dan latency
- **Error Tracking**: Pelacakan error dan debugging
- **Conversation Flow**: Visualisasi alur percakapan multi-agen

### 📊 Prometheus & Grafana Stack
Sistem monitoring real-time dengan metrics collection lengkap:

**🔧 Prometheus Configuration:**
- **Metrics Collection**: Mengumpulkan metrics dari semua services
- **Service Discovery**: Auto-discovery Docker containers
- **Alerting Rules**: Konfigurasi alert untuk anomali sistem
- **Data Retention**: 15 hari storage untuk historical analysis

**📈 Grafana Dashboards:**
- **Application Metrics Dashboard**: API performance, response times, error rates
- **System Monitoring Dashboard**: CPU, memory, disk, network usage
- **Telegram Bot Dashboard**: Bot metrics, message volume, user activity
- **Agen Travel Dashboard**: Agent performance, conversation analytics
- **Redis Dashboard**: Cache hit rates, memory usage, connection stats
- **Traefik Dashboard**: Request routing, load balancing metrics

**🔍 Monitoring Components:**
- **Node Exporter**: System metrics dari server host
- **Redis Exporter**: Redis performance dan memory metrics
- **Redis Insight**: Web-based Redis monitoring dengan real-time analytics
- **Custom Metrics**: Application-specific metrics dari FastAPI
- **Health Checks**: Automated service health monitoring

## 🔐 Basic Authentication Credentials

Sistem menggunakan Basic Authentication untuk mengamankan dashboard admin. Berikut adalah kredensial untuk setiap service:

### 🔑 Service Credentials

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **Traefik Dashboard** | `http://traefik.localhost` | `admin` | `[lihat .htpasswd]` |
| **API Documentation** | `http://localhost/api/docs` | `admin` | `[lihat .htpasswd-api]` |
| **Redis Insight** | `http://redis.localhost` | `admin` | `[lihat .htpasswd-redis]` |
| **Prometheus** | `http://prometheus.localhost` | `admin` | `[lihat .htpasswd-prometheus]` |
| **Supabase Studio** | `http://supabase.localhost` | `admin` | `[lihat .htpasswd-supabase]` |
| **Grafana** | `http://grafana.localhost` | `admin` | `[built-in login]` |

### 🛡️ Security Implementation

**🔧 Implementation Details:**
- **HTTP Basic Authentication**: Implemented di level Traefik reverse proxy
- **Service Isolation**: Setiap service memiliki file `.htpasswd` terpisah
- **Non-intrusive**: Tidak mengubah konfigurasi aplikasi asli
- **Bcrypt Hashing**: Password di-hash dengan bcrypt untuk keamanan
- **Middleware Based**: Menggunakan Traefik middleware untuk authentication

**📁 Authentication Files:**
```bash
traefik/config/
├── .htpasswd              # Traefik Dashboard
├── .htpasswd-api          # API Documentation (Swagger/ReDoc)
├── .htpasswd-redis        # Redis Insight
├── .htpasswd-prometheus   # Prometheus
├── .htpasswd-supabase     # Supabase Studio
└── .env                   # Environment variables
```

**🔄 Changing Credentials:**
```bash
# Generate new password hash
htpasswd -nbB username newpassword

# Or using openssl
echo "username:$(openssl passwd -1 newpassword)"

# Update respective .htpasswd file
echo "newuser:$2y$10$..." > traefik/config/.htpasswd-[service]

# Restart Traefik to apply changes
docker-compose restart traefik
```

**💡 Security Notes:**
- Kredensial disimpan dalam file `.htpasswd` yang tidak di-commit ke repository
- Untuk production, gunakan password yang lebih kuat dan unik
- Pertimbangkan menggunakan OAuth/OIDC untuk production environment
- File `.htpasswd` sudah di-gitignore untuk keamanan
- Ganti semua default password sebelum deployment production

## 🔧 Troubleshooting & Best Practices

### 🚨 Common Issues & Solutions

#### 🐳 Docker Issues
```bash
# Service tidak bisa start
docker compose logs [service-name]
docker compose restart [service-name]

# Port conflicts
docker compose down
sudo netstat -tulpn | grep :[port]
sudo kill -9 [pid]

# Volume permission issues
sudo chown -R $USER:$USER ./volumes/
docker compose down && docker compose up -d
```

#### 🌐 Network & Connectivity
```bash
# Traefik routing issues
curl -H "Host: localhost" http://localhost/health
docker compose logs traefik

# Cloudflare tunnel issues
./scripts/cloudflare.sh status
./scripts/cloudflare.sh logs
cloudflared tunnel info agen-travel

# DNS resolution issues
nslookup agen-travel.live
dig agen-travel.live

# Subdomain access issues (development)
# Pastikan /etc/hosts sudah dikonfigurasi dengan benar
cat /etc/hosts | grep localhost
ping redis.localhost
ping grafana.localhost

# Clear browser cache jika subdomain tidak bisa diakses
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete
# Safari: Cmd+Option+E
```

#### 🔐 Authentication Issues
```bash
# JWT token issues
redis-cli -a $REDIS_PASSWORD
KEYS "session:*"
GET "session:[user_id]"

# Email verification issues
docker compose logs backend
curl http://localhost/api/v1/email/verify-email?token=[token]

# Supabase connection issues
docker compose logs supabase-db
psql -h localhost -p 54322 -U postgres -d postgres
```

#### 🧠 RAG & Pinecone Issues
```bash
# Test Pinecone connection
python -c "
from backend.rag.utils import validate_pinecone_connection, get_available_indexes
print('Connection:', validate_pinecone_connection())
print('Indexes:', get_available_indexes())
"

# Test RAG functionality
python -c "
import asyncio
from backend.rag.pinecone import query_knowledge_base
result = asyncio.run(query_knowledge_base('test query'))
print('RAG Result:', result)
"

# Check RAG environment variables
echo "RAG_MODEL: $RAG_MODEL"
echo "TEMPERATURE: $TEMPERATURE"
echo "PINECONE_API_KEY: ${PINECONE_API_KEY:0:10}..."

# Debug RAG integration in customer service
docker compose logs backend | grep -i "rag\|pinecone\|knowledge"
```

#### 🔌 MCP (Model Context Protocol) Issues
```bash
# Test MCP connections
python -c "
import asyncio
from backend.mcps.manager import initialize_mcp_tools
tools = asyncio.run(initialize_mcp_tools())
print(f'MCP Tools: {len(tools)}')
for tool in tools:
    print(f'  - {tool.name}')
"

# Check MCP environment variables
echo "RAPIDAPI_KEY: ${RAPIDAPI_KEY:0:10}..."
echo "TRIPADVISOR_API_KEY: ${TRIPADVISOR_API_KEY:0:10}..."
echo "DATABASE_URI: ${DATABASE_URI:0:30}..."

# Test individual MCP servers
# Booking.com MCP
cd backend/mcps/servers/booking.com
uv run src/booking_com_mcp/main.py

# TripAdvisor MCP
cd backend/mcps/servers/tripadvisor
uv run src/tripadvisor_mcp/main.py

# Airbnb MCP (requires Node.js)
npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt

# Supabase MCP
cd backend/mcps/servers/supabase
uv run src/supabase_mcp/main.py

# Debug MCP integration in agents
docker compose logs backend | grep -i "mcp\|booking\|tripadvisor\|airbnb"

# Check MCP tool distribution
python -c "
from backend.agents.graph import MCP_AVAILABLE, MCP
print(f'MCP Available: {MCP_AVAILABLE}')
print(f'MCP Tools: {len(MCP)}')
"
```

### 💡 Development Tips

#### 🛠️ Local Development
```bash
# Hot reload untuk development
docker compose -f docker-compose.dev.yml up

# Debug mode dengan logs
docker compose logs -f backend
docker compose logs -f telegram-bot

# Database access untuk debugging
docker exec -it supabase-db psql -U postgres -d postgres
docker exec -it redis redis-cli -a $REDIS_PASSWORD
```

#### 🧪 Testing
```bash
# API testing
curl -X POST http://localhost/api/v1/response/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test"}'

# Testing RAG functionality
curl -X POST http://localhost/api/v1/response/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Bagaimana cara membatalkan booking hotel?", "user_id": "test"}'

# Testing MCP functionality
curl -X POST http://localhost/api/v1/response/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Gunakan Booking.com untuk cari hotel di Bali", "user_id": "test"}'

curl -X POST http://localhost/api/v1/response/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Pakai TripAdvisor untuk lihat review hotel terbaik di Ubud", "user_id": "test"}'

# API Documentation (dengan Basic Auth)
curl -u admin:password http://localhost/api/docs
curl -u admin:password http://localhost/api/redoc
curl -u admin:password http://localhost/api/openapi.json

# Health checks (tanpa auth)
curl http://localhost/health
curl https://agen-travel.live/health

# Monitoring endpoints
curl http://localhost/metrics
curl http://prometheus.localhost/api/v1/query?query=up
```

## 🌐 Production Deployment

### 🚀 Google Cloud Platform Deployment

#### `gcp.sh` - Comprehensive VM Management
Script untuk mengelola VM instance di Google Cloud Platform dengan automation:

```bash
# Membuat VM instance baru dengan firewall rules
./scripts/gcp.sh create

# Memeriksa status VM dan resources
./scripts/gcp.sh status

# Setup SSH untuk VSCode Remote Development
./scripts/gcp.sh setup-ssh

# Menghapus VM dan semua resources
./scripts/gcp.sh delete
```

**🖥️ VM Specifications:**
- **Project**: travel-agency-448103
- **Zone**: asia-southeast2-a (Jakarta) - Low latency untuk Indonesia
- **Machine Type**: e2-standard-16 (16 vCPUs, 64GB RAM)
- **OS**: Ubuntu 24.04 LTS dengan Docker pre-installed
- **Disk**: 46GB SSD dengan automatic backup
- **Network**: Premium tier dengan global load balancing

**🔥 Firewall Configuration:**
```bash
# HTTP/HTTPS Traffic
80, 443          # Web traffic via Cloudflare
8080             # Traefik dashboard

# Application Ports
2025             # Backend API
8444             # Telegram webhook

# Monitoring Ports
9090, 9100       # Prometheus & Node Exporter
2027             # Grafana dashboard

# Database Ports
54322            # Supabase PostgreSQL
6379             # Redis
```

#### `vm.sh` - VM Lifecycle Management
Script untuk kontrol VM dengan cost optimization:

```bash
# Menghidupkan VM (auto-start services)
./scripts/vm.sh start

# Mematikan VM (graceful shutdown)
./scripts/vm.sh stop

# Cek status VM dan billing
./scripts/vm.sh status

# Restart VM dengan health checks
./scripts/vm.sh restart
```

**💰 Cost Optimization:**
- **Automatic Shutdown**: VM otomatis shutdown di malam hari
- **Preemptible Instances**: Option untuk development environment
- **Resource Monitoring**: Alert jika usage tinggi
- **Scheduled Scaling**: Auto-scaling berdasarkan traffic pattern

### 🚀 Production Deployment Steps

#### 1️⃣ Infrastructure Setup
```bash
# Buat VM Instance dengan automated setup
./scripts/gcp.sh create

# Verify VM status dan network connectivity
./scripts/gcp.sh status
```

#### 2️⃣ Remote Development Setup
```bash
# Setup SSH untuk VSCode Remote Development
./scripts/gcp.sh setup-ssh

# Connect via SSH
ssh agen-travel  # Menggunakan SSH config yang sudah disetup
```

#### 3️⃣ Environment Preparation
```bash
# Update system dan install dependencies
sudo apt update && sudo apt upgrade -y

# Install Docker dengan official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose V2
sudo apt install docker-compose-plugin -y

# Install Cloudflare CLI
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Verify installations
docker --version
docker compose version
cloudflared --version
```

#### 4️⃣ Application Deployment
```bash
# Clone repository
git clone https://github.com/esakrissa/agen-travel-ai.git
cd agen-travel

# Setup environment variables
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/telegram/.env.example frontend/telegram/.env
cp traefik/config/.env.example traefik/config/.env

# Edit environment files dengan production values
nano .env
nano backend/.env
nano frontend/telegram/.env
nano traefik/config/.env
```

#### 5️⃣ Database Setup
```bash
# Setup Supabase local instance
cd supabase/agen-travel
cp .env.example .env
nano .env  # Configure database credentials

# Start Supabase services
docker compose up -d

# Verify database connectivity
docker compose logs supabase-db
```

#### 6️⃣ Secure Tunnel Setup
```bash
# Login ke Cloudflare (one-time setup)
cloudflared tunnel login

# Start Cloudflare Tunnel
cd ~/agen-travel
./scripts/cloudflare.sh start

# Verify tunnel status
./scripts/cloudflare.sh status
```

#### 7️⃣ Application Launch
```bash
# Build all services
docker compose build

# Start all services in production mode
docker compose up -d

# Verify all services are running
docker compose ps

# Check service health
curl http://localhost/health
curl https://agen-travel.live/health
```

#### 8️⃣ Monitoring Setup
```bash
# Access monitoring dashboards via subdomain routing
echo "=== Main Domain Services ==="
echo "API Documentation: https://agen-travel.live/docs (Basic Auth required)"
echo "Health Check: https://agen-travel.live/health (No auth required)"
echo ""
echo "=== Admin Services (Subdomain) ==="
echo "Grafana: https://grafana.agen-travel.live (Built-in login)"
echo "Prometheus: https://prometheus.agen-travel.live (Basic Auth required)"
echo "Traefik: https://traefik.agen-travel.live (Basic Auth required)"
echo "Redis Insight: https://redis.agen-travel.live (Basic Auth required)"
echo "Supabase Studio: https://supabase.agen-travel.live (Basic Auth required)"

# Setup alerts dan notifications
# Configure Grafana alerts untuk production monitoring
```

## ⚙️ Konfigurasi Environment

### 🔧 Backend Configuration (.env)
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini

# LangSmith Configuration
LANGSMITH_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=agen-travel

# Supabase Configuration
SUPABASE_URL=http://kong:8000  # Internal Docker network
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_CONNECTION=postgresql://postgres:password@supabase-db:5432/postgres

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Email Configuration
EMAIL_VERIFICATION_REDIRECT_URL=http://localhost/api/v1/email/verify-email
SUPABASE_AUTH_ENABLED=true

# External APIs
TAVILY_API_KEY=your_tavily_api_key

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://agen-travel.live
```

### 📱 Telegram Bot Configuration (.env)
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
WEBHOOK_URL=https://agen-travel.live/webhook/  # Cloudflare Tunnel URL
PORT=8444

# API Gateway
API_URL=http://backend:2025/api/v1/response/  # Internal Docker network

# Supabase Configuration
SUPABASE_URL=http://kong:8000
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_CONNECTION=postgresql://postgres:password@supabase-db:5432/postgres
```

### 🗄️ Supabase Configuration (.env)
```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=54322
POSTGRES_DB=postgres

# JWT Configuration
JWT_SECRET=your_jwt_secret
ANON_KEY=your_anon_key
SERVICE_ROLE_KEY=your_service_role_key

# Dashboard
DASHBOARD_PASSWORD=your_dashboard_password

# Email Configuration (Supabase Auth)
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=your_resend_api_key
```

### 🔄 Traefik Configuration (.env)
```bash
# Dashboard Credentials
TRAEFIK_DASHBOARD_USER=admin
TRAEFIK_DASHBOARD_PASSWORD=your_traefik_password

# Monitoring Credentials
GRAFANA_ADMIN_PASSWORD=your_grafana_password
PROMETHEUS_ADMIN_PASSWORD=your_prometheus_password

# Rate Limiting
RATE_LIMIT_API=100
RATE_LIMIT_WEBHOOK=10
RATE_LIMIT_DASHBOARD=30
```

### 🌐 Global Configuration (.env)
```bash
# Redis Configuration
REDIS_PASSWORD=your_redis_password

# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# Supabase Keys (shared across services)
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_DB_PASSWORD=your_supabase_db_password
```

## 🏗️ Arsitektur Microservices

Sistem menggunakan arsitektur microservices modern dengan Docker containers dan orchestration:

### 🔄 Infrastructure Services
- **Traefik**: Reverse proxy, load balancer, dan SSL termination
- **Cloudflare Tunnel**: Secure public access dengan zero-trust networking
- **Redis**: Session management, caching, dan message queuing
- **Supabase Stack**: PostgreSQL database dengan real-time features

### 🚀 Application Services
- **Backend Service**: FastAPI dengan LangGraph multi-agent system
- **Telegram Bot Service**: Python bot dengan webhook integration
- **Web UI Service**: Next.js frontend dengan TypeScript
- **Authentication Service**: JWT-based auth dengan email verification

### 📊 Monitoring & Observability Services
- **Prometheus**: Time-series metrics database dengan service discovery
- **Grafana**: Visualization dashboards dengan alerting
- **Node Exporter**: System metrics collection
- **Redis Exporter**: Redis performance monitoring
- **LangSmith**: AI agent tracing dan evaluation

### 🤖 Multi-Agent Supervisor Architecture
- **Supervisor Pattern**: Agen utama mengkoordinasi sub agen dengan intelligent routing
- **Specialized Agents**: Hotel, Flight, Tour, Customer Service agents dengan domain expertise
- **State Management**: Distributed state dengan Supabase PostgreSQL untuk persistence
- **Tool Routing**: Dynamic routing berdasarkan user intent dan context
- **Memory Persistence**: Checkpoint dan conversation history dengan Redis caching

### 🔗 Integration & Communication
- **LangChain Tools**: Custom tools untuk setiap domain (hotel, flight, tour)
- **LangGraph Workflow**: State machine untuk multi-agent coordination
- **Async Processing**: Non-blocking operations dengan asyncio untuk performa optimal
- **Context Awareness**: Persistent conversation context per session
- **Real-time Communication**: WebSocket dan webhook untuk instant messaging
- **API Gateway Pattern**: Centralized routing dengan middleware dan authentication

## 🌱 Roadmap Pengembangan

### 🎯 Phase 1: Core Enhancement (Q1 2025)
- ✅ **Traefik Integration**: Reverse proxy dan load balancing
- ✅ **Cloudflare Tunnel**: Secure public access dengan domain
- ✅ **Authentication System**: JWT-based auth dengan email verification
- ✅ **Redis Integration**: Session management dan caching
- 🔄 **Payment System**: Invoice generation dan payment processing

### 🚀 Phase 2: Advanced Features (Q2 2025)
- 📱 **Mobile App**: React Native app untuk iOS dan Android
- 🌍 **Multi-language Support**: Internationalization dengan i18n
- 🔗 **Real-time APIs**: Integrasi dengan API hotel dan penerbangan real-time
- 🤖 **AI Recommendations**: Machine learning untuk personalized recommendations
- 📊 **Advanced Analytics**: User behavior analysis dan business intelligence

### 🔮 Phase 3: Enterprise Features (Q3-Q4 2025)
- 🏢 **Multi-tenant Architecture**: Support untuk multiple travel agencies
- 🔐 **Advanced Security**: OAuth2, RBAC, dan audit logging
- 📈 **Scalability**: Kubernetes deployment dan auto-scaling
- 🌐 **Global Deployment**: Multi-region deployment dengan CDN
- 🤝 **Partner Integration**: API marketplace untuk travel partners
- 📱 **Progressive Web App**: PWA dengan offline capabilities

## 💻 Tech Stack

### 🚀 Backend Technologies
- **FastAPI**: Modern Python web framework dengan automatic API documentation
- **LangGraph**: Multi-agent workflow orchestration dengan state management
- **LangChain**: LLM application framework dengan tool integration
- **OpenAI GPT-4.1-mini**: Large Language Model - efisien dan cost-effective
- **Supabase**: PostgreSQL database dengan real-time features dan auth
- **Redis**: In-memory data store untuk caching dan session management
- **Uvicorn**: High-performance ASGI server
- **Python 3.13**: Latest Python runtime dalam Docker containers

### 🖥️ Frontend Technologies
- **Next.js 14**: React framework dengan App Router dan TypeScript
- **Telegram Bot API**: Chat interface dengan webhook integration
- **TypeScript**: Type-safe JavaScript untuk better development experience
- **Tailwind CSS**: Utility-first CSS framework untuk styling
- **React**: Modern UI library dengan hooks dan context

### 🔧 Development Tools
- **Code Editors**:
  - **Cursor AI**: AI-powered code editor dengan intelligent suggestions
  - **VSCode**: Remote development via SSH ke GCP VM
- **AI Coding Assistant**:
  - **Augment Code**: Advanced coding assistant dengan Claude Sonnet 4
  - **GitHub Copilot**: AI pair programming untuk code completion
- **Version Control**: Git dengan GitHub integration dan automated workflows

### 🏗️ Infrastructure & DevOps
- **Containerization**:
  - **Docker**: Container platform dengan multi-stage builds
  - **Docker Compose**: Multi-container orchestration untuk development
- **Reverse Proxy & Load Balancing**:
  - **Traefik v3.4**: Modern reverse proxy dengan auto-discovery
  - **Cloudflare Tunnel**: Secure public access dengan zero-trust networking
- **Cloud Platform**:
  - **Google Cloud Platform**: VM instances dengan automated deployment
  - **Cloudflare**: CDN, DNS, dan security services
- **Networking**:
  - **Custom Docker Networks**: Service isolation dan communication
  - **SSL/TLS**: Automatic certificate management

### 📊 Monitoring & Observability
- **Application Monitoring**:
  - **LangSmith**: LLM application monitoring dan tracing
  - **Custom Metrics**: FastAPI metrics dengan Prometheus integration
- **Infrastructure Monitoring**:
  - **Prometheus**: Time-series metrics database dengan alerting
  - **Grafana**: Visualization dashboards dengan real-time monitoring
  - **Node Exporter**: System metrics collection
  - **Redis Exporter**: Redis performance monitoring
- **Logging & Debugging**:
  - **Structured Logging**: JSON-formatted logs untuk better analysis
  - **Health Checks**: Automated service health monitoring
  - **Error Tracking**: Comprehensive error handling dan reporting

### 🔐 Security & Authentication
- **Authentication**:
  - **JWT**: JSON Web Tokens untuk stateless authentication
  - **Supabase Auth**: Email verification dan password reset
  - **Redis Sessions**: Secure session management
- **Security**:
  - **CORS**: Cross-Origin Resource Sharing configuration
  - **Rate Limiting**: API rate limiting untuk abuse prevention
  - **Basic Auth**: Protected admin interfaces
  - **Environment Variables**: Secure configuration management

## 🎓 Academic Context

Proyek ini dikembangkan sebagai **Tugas Akhir Sarjana Teknologi Informasi** dengan fokus pada:

### 📚 Aspek Akademis
- **Multi-Agent Systems**: Implementasi sistem multi-agen dengan LangGraph
- **Microservices Architecture**: Arsitektur terdistribusi dengan Docker containers
- **AI/ML Integration**: Penggunaan Large Language Models untuk natural language processing
- **DevOps Practices**: CI/CD, monitoring, dan deployment automation
- **Software Engineering**: Clean code, testing, dan documentation

### 🎯 Learning Outcomes
- **System Design**: Merancang arsitektur sistem yang scalable dan maintainable
- **AI Implementation**: Mengintegrasikan AI/ML dalam aplikasi real-world
- **Modern Development**: Menggunakan tools dan practices modern dalam software development
- **Problem Solving**: Menyelesaikan masalah kompleks dengan pendekatan sistematis
- **Documentation**: Membuat dokumentasi teknis yang komprehensif

### 🏆 Technical Achievements
- ✅ **Multi-Agent Coordination**: Implementasi supervisor pattern untuk koordinasi agen
- ✅ **Real-time Communication**: WebSocket dan webhook integration
- ✅ **Authentication System**: JWT-based auth dengan email verification
- ✅ **Monitoring Stack**: Comprehensive monitoring dengan Grafana dan Prometheus
- ✅ **Infrastructure as Code**: Docker Compose dan automated deployment
- ✅ **Security Implementation**: Rate limiting, CORS, dan secure configuration
- ✅ **Performance Optimization**: Caching, load balancing, dan async processing

---

## 📄 Lisensi

MIT License

Copyright (c) 2025 Agen Travel AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 👨‍💻 Author

> **Nama**: I Wayan Darmika Esa Krissayoga
> **NIM**: 1705551076
> **Program Studi**: Sarjana Teknologi Informasi
> **Universitas**: Universitas Udayana
> **Tahun**: 2025

**Contact**:
- 📧 Email: [esakrissa.wayan@gmail.com]
- 💼 LinkedIn: [linkedin.com/in/esakrissa]
- 🐙 GitHub: [github.com/esakrissa]

---

*Proyek ini dikembangkan dengan ❤️ menggunakan AI-powered development tools dan modern software engineering practices.*