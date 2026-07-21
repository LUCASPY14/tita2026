# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
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

# Crear archivo map faltante en jazzmin (bootstrap.bundle no incluye su .map)
RUN python -c "import json,pathlib; pathlib.Path('/usr/local/lib/python3.11/site-packages/jazzmin/static/vendor/bootstrap/js/bootstrap.bundle.min.js.map').write_text(json.dumps({'version':3,'sources':[],'names':[],'mappings':''}))"

# Recolectar archivos estáticos en tiempo de build
# Usa SECRET_KEY temporal; las credenciales de DB no son necesarias para collectstatic
RUN SECRET_KEY=build-only ALLOWED_HOSTS=localhost DB_HOST=localhost DB_NAME=x DB_USER=x DB_PASSWORD=x \
    DJANGO_SETTINGS_MODULE=backend.settings.production \
    python manage.py collectstatic --noinput --clear

USER cantina

EXPOSE 8000

# Daphne: servidor ASGI para HTTP + WebSockets
# La variable DJANGO_SETTINGS_MODULE se pasa via docker-compose
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]
