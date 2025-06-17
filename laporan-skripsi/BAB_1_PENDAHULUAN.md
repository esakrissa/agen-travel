# BAB I
# PENDAHULUAN

## 1.1 Latar Belakang

Industri pariwisata telah mengalami transformasi digital yang signifikan dalam dekade terakhir. Dengan meningkatnya kebutuhan akan layanan travel yang efisien dan personal, diperlukan sistem yang dapat menangani berbagai aspek pemesanan travel secara terintegrasi. Sistem konvensional seringkali menghadapi keterbatasan dalam hal skalabilitas, personalisasi, dan kemampuan untuk menangani multiple domain secara bersamaan.

Perkembangan teknologi Artificial Intelligence (AI), khususnya Large Language Models (LLM), telah membuka peluang baru dalam pengembangan sistem yang lebih intelligent dan responsif. Model bahasa besar seperti GPT-4 telah menunjukkan kemampuan luar biasa dalam memahami konteks natural language dan memberikan respons yang relevan untuk berbagai domain.

Arsitektur multi-agent berbasis AI menawarkan solusi yang menjanjikan untuk mengatasi kompleksitas sistem travel booking. Dengan menggunakan pendekatan supervisor agent yang diimplementasikan melalui LangGraph framework, sistem dapat mendistribusikan tugas-tugas spesifik kepada agent yang specialized, sehingga meningkatkan efisiensi dan akurasi dalam penanganan permintaan pengguna. LangGraph menyediakan state management yang robust dan workflow orchestration yang memungkinkan koordinasi yang seamless antar multiple agents.

Perkembangan terbaru dalam teknologi AI, khususnya Retrieval-Augmented Generation (RAG) dan Model Context Protocol (MCP), membuka peluang baru untuk meningkatkan kualitas layanan customer service dan integrasi data real-time. RAG memungkinkan sistem untuk mengakses knowledge base yang comprehensive melalui semantic search menggunakan vector databases seperti Pinecone, sementara MCP menyediakan standardized protocol untuk mengintegrasikan data real-time dari multiple external sources seperti Booking.com, TripAdvisor, dan Airbnb.

Teknologi cloud computing dan containerization seperti Docker memungkinkan deployment yang scalable dan maintainable. Integrasi dengan layanan modern seperti Supabase untuk database management dan authentication, Redis Stack untuk advanced caching dan monitoring dengan Redis Insight, serta monitoring stack menggunakan Prometheus dan Grafana memberikan foundation yang solid untuk sistem enterprise-grade. Implementasi LangSmith untuk AI agent tracing dan observability memungkinkan monitoring dan debugging yang comprehensive untuk sistem multi-agent. Cloudflare Tunnel menyediakan secure public access dengan zero-trust architecture tanpa memerlukan complex firewall configuration.

## 1.2 Rumusan Masalah

Berdasarkan latar belakang di atas, rumusan masalah dalam penelitian ini adalah:

1. Bagaimana merancang arsitektur multi-agent yang efektif untuk sistem travel booking menggunakan supervisor pattern dengan LangGraph framework?
2. Bagaimana mengimplementasikan integrasi Large Language Model (LLM) dengan specialized agents untuk menangani domain-specific tasks (hotel, flight, tour, customer service)?
3. Bagaimana mengintegrasikan RAG (Retrieval-Augmented Generation) dengan Pinecone vector database untuk meningkatkan kualitas customer service responses?
4. Bagaimana mengimplementasikan Model Context Protocol (MCP) untuk integrasi real-time data dari multiple external sources (Booking.com, TripAdvisor, Airbnb)?
5. Bagaimana membangun sistem autentikasi yang secure menggunakan Supabase Auth dengan SMTP email verification dan JWT token management?
6. Bagaimana mengoptimalkan performa sistem menggunakan Redis Stack dengan Redis Insight monitoring, database connection pooling, dan caching strategies?
7. Bagaimana mengimplementasikan observability dan tracing untuk sistem multi-agent menggunakan LangSmith dan Prometheus/Grafana stack?
8. Bagaimana melakukan deployment yang scalable dan secure menggunakan Docker containers, Traefik reverse proxy, Cloudflare Tunnel, dan cloud infrastructure?

## 1.3 Tujuan Penelitian

### 1.3.1 Tujuan Umum
Mengembangkan sistem multi-agent travel booking berbasis AI dengan implementasi Large Language Model yang dapat menangani pemesanan hotel, penerbangan, dan paket tur secara terintegrasi.

### 1.3.2 Tujuan Khusus
1. Merancang dan mengimplementasikan arsitektur supervisor agent untuk koordinasi multi-domain tasks menggunakan LangGraph StateGraph
2. Mengintegrasikan OpenAI GPT-4.1-mini sebagai core LLM dengan specialized agents (hotel, flight, tour, customer service) menggunakan LangGraph framework
3. Mengimplementasikan RAG (Retrieval-Augmented Generation) system menggunakan Pinecone vector database untuk enhanced knowledge retrieval dalam customer service
4. Mengintegrasikan Model Context Protocol (MCP) untuk real-time data access dari external sources (Booking.com, TripAdvisor, Airbnb, Supabase)
5. Membangun sistem autentikasi berbasis Supabase Auth dengan SMTP email verification, JWT token management, dan template modern
6. Mengimplementasikan Redis Stack dengan Redis Insight untuk advanced caching, monitoring, dan session management
7. Mengembangkan RESTful API menggunakan FastAPI dengan comprehensive monitoring, rate limiting, dan error handling
8. Membangun user interface melalui Telegram Bot dan Web UI (Next.js) untuk aksesibilitas maksimal
9. Mengimplementasikan sistem tools yang comprehensive untuk setiap agent dengan external API integrations dan MCP tools
10. Melakukan deployment menggunakan Docker containers dengan Traefik reverse proxy, Cloudflare Tunnel, dan load balancing
11. Mengimplementasikan monitoring dan observability system menggunakan Grafana, Prometheus, Redis Insight, dan LangSmith untuk AI agent tracing
12. Mengintegrasikan database management menggunakan Supabase PostgreSQL dengan connection pooling dan backup strategies

## 1.4 Manfaat Penelitian

### 1.4.1 Manfaat Teoritis
1. Memberikan kontribusi pada pengembangan arsitektur multi-agent systems dalam domain travel booking dengan supervisor pattern
2. Menyediakan framework untuk integrasi LLM dengan specialized agents menggunakan LangGraph untuk state management dan workflow orchestration
3. Mendemonstrasikan implementasi praktis dari LangGraph StateGraph untuk complex multi-agent coordination
4. Memberikan insight tentang observability dan monitoring untuk AI agent systems menggunakan LangSmith tracing
5. Menyediakan reference implementation untuk microservices architecture dengan containerization
6. Mendemonstrasikan implementasi RAG systems dalam multi-agent architecture untuk enhanced knowledge retrieval
7. Memberikan framework untuk Model Context Protocol (MCP) integration dalam production AI systems
8. Menyediakan best practices untuk Redis Stack implementation dengan advanced monitoring capabilities

### 1.4.2 Manfaat Praktis
1. Menyediakan solusi travel booking yang comprehensive dan user-friendly dengan multiple interface (Telegram Bot dan Web UI)
2. Memberikan template implementasi untuk sistem multi-agent berbasis AI dengan production-ready deployment
3. Menyediakan reference architecture untuk deployment scalable menggunakan modern DevOps practices (Docker, Traefik, Cloudflare Tunnel, monitoring stack)
4. Memberikan insight tentang optimasi performa menggunakan Redis Stack dengan Redis Insight, database connection pooling, dan monitoring systems
5. Menyediakan implementasi autentikasi yang secure dengan email verification dan JWT token management
6. Memberikan contoh integrasi dengan external APIs dan services untuk real-world applications
7. Mendemonstrasikan implementasi RAG untuk enhanced customer service dengan semantic search capabilities
8. Menyediakan practical implementation dari Model Context Protocol untuk real-time external data integration
9. Memberikan zero-trust security implementation menggunakan Cloudflare Tunnel untuk secure public access

## 1.5 Batasan Penelitian

1. **Scope Fungsional**: Sistem fokus pada tiga domain utama yaitu hotel booking, flight booking, dan tour packages dengan customer service support yang enhanced dengan RAG
2. **Teknologi LLM**: Menggunakan OpenAI GPT-4.1-mini sebagai primary language model dan GPT-4.1 untuk RAG dengan LangGraph untuk orchestration
3. **Framework AI**: Implementasi menggunakan LangChain ecosystem (LangGraph, LangSmith) untuk multi-agent coordination dengan RAG dan MCP integration
4. **Vector Database**: Menggunakan Pinecone sebagai vector database untuk RAG knowledge base dengan existing index 'agen-travel-faq'
5. **External Data Integration**: MCP integration terbatas pada Booking.com, TripAdvisor, Airbnb, dan Supabase servers
6. **Platform Deployment**: Implementasi pada Google Cloud Platform (GCP) dengan Docker containerization, Traefik reverse proxy, dan Cloudflare Tunnel
7. **User Interface**: Terbatas pada Telegram Bot dan Web UI (Next.js), tidak mencakup mobile native applications
8. **Database**: Menggunakan Supabase PostgreSQL sebagai primary database dengan Redis Stack untuk advanced caching dan monitoring
9. **Geographic Scope**: Data dan layanan terfokus pada market Indonesia dengan bahasa Indonesia sebagai primary language
10. **Payment Integration**: Simulasi payment processing, tidak terintegrasi dengan real payment gateways untuk keamanan
11. **External APIs**: Integrasi terbatas pada Tavily API untuk search, currency rate APIs, dan MCP servers untuk real-time data
12. **Scale Testing**: Testing dilakukan pada environment development dan staging, tidak mencakup production-scale load testing

## 1.6 Sistematika Penulisan

**BAB I PENDAHULUAN**
Berisi latar belakang, rumusan masalah, tujuan penelitian, manfaat penelitian, batasan penelitian, dan sistematika penulisan.

**BAB II TINJAUAN PUSTAKA**
Membahas teori-teori yang mendukung penelitian meliputi multi-agent systems, Large Language Models, arsitektur microservices, dan teknologi pendukung lainnya.

**BAB III METODOLOGI PENELITIAN**
Menjelaskan metodologi pengembangan sistem, arsitektur yang digunakan, tools dan teknologi, serta tahapan implementasi.

**BAB IV IMPLEMENTASI DAN PEMBAHASAN**
Menyajikan detail implementasi sistem, hasil pengujian, analisis performa, dan pembahasan hasil penelitian.

**BAB V PENUTUP**
Berisi kesimpulan dari penelitian yang telah dilakukan dan saran untuk pengembangan lebih lanjut.

**DAFTAR PUSTAKA**
Memuat referensi yang digunakan dalam penelitian.

**LAMPIRAN**
Berisi dokumentasi teknis, kode program, dan hasil pengujian sistem.
