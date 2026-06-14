# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements.production.txt usa psycopg2 compilado (sin -binary).
# El builder ya tiene gcc y libpq-dev, que son los únicos prerrequisitos de compilación.
COPY requirements.txt requirements.production.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.production.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --system --no-create-home --shell /bin/false cantina

WORKDIR /app

# Copiar dependencias desde builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código fuente
COPY --chown=cantina:cantina . .

# Crear directorios necesarios
RUN mkdir -p staticfiles media logs && chown -R cantina:cantina staticfiles media logs

USER cantina

EXPOSE 8000

# Daphne: servidor ASGI para HTTP + WebSockets
# La variable DJANGO_SETTINGS_MODULE se pasa via docker-compose
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]
