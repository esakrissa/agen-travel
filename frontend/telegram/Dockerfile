FROM python:3.13-slim

WORKDIR /app

# Install dependensi build dan bersihkan dalam satu langkah untuk mengurangi ukuran image
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Pastikan uv ada di PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy requirements.txt dari direktori telegram
COPY requirements.txt /app/

# Install dependensi Python menggunakan uv
RUN uv pip install --system -r requirements.txt

# Copy hanya file frontend Telegram
COPY . /app/

# Variabel environment default
ENV PORT=8443
ENV WEBHOOK_URL="https://your-webhook-url"
ENV API_URL="http://backend:2025/api/v1/response/"

# Expose port
EXPOSE ${PORT}

# Perintah untuk menjalankan bot Telegram
CMD ["python", "bot.py"]