FROM python:3.12-slim

# Copia uv (package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Imposta variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Imposta la directory di lavoro
WORKDIR /app

# Copia file per installare le dipendenze del progetto principale
COPY pyproject.toml uv.lock ./

# Installa le dipendenze del progetto principale
RUN uv sync --frozen --no-cache

# Copia il codice sorgente
COPY ./src /app/src

# Installa la CLI come package
WORKDIR /app/src/cli
RUN uv pip install --system -e .

# Torna alla directory principale
WORKDIR /app

# Espone la porta
EXPOSE 8002

# Comando per avviare l'app
CMD ["uv", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8002"]