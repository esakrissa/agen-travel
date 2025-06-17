FROM python:3.13-slim

WORKDIR /app

# Install dependensi build dan Node.js untuk MCP servers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Pastikan uv ada di PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy requirements terlebih dahulu untuk caching yang lebih baik
COPY ./requirements.txt /app/
RUN uv pip install --system -r requirements.txt && \
    uv pip install --system psycopg2-binary

# Copy kode backend
COPY . /app/

# Variabel environment default
ENV PORT=2025
ENV HOST="0.0.0.0"

# Expose port
EXPOSE ${PORT}

# Perintah untuk menjalankan aplikasi
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2025"]