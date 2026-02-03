FROM python:3.12-slim

# Installa CA certificates E strumenti di debug network
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dnsutils \
    iputils-ping \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copia UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src



WORKDIR /app

# 1. Copia i file di configurazione principali
COPY pyproject.toml uv.lock ./

# 2. COPIA I METADATI DELLA CLI PRIMA DEL SYNC
COPY src/cli/pyproject.toml ./src/cli/pyproject.toml

# 3. Sync delle dipendenze
RUN uv sync --frozen --no-cache

# 4. Ora copi tutto il codice sorgente
COPY ./src /app/src

# 5. Installa la CLI in modalità editable
WORKDIR /app/src/cli
RUN uv pip install --system -e .

WORKDIR /app

EXPOSE 8002

CMD ["uv", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8002"]