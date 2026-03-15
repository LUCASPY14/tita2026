# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Instalar dependencias primero (cacheado si package.json no cambia)
COPY package*.json ./
RUN npm ci

# Copiar código fuente y construir
COPY . .
ENV CI=false
RUN npm run build

# ── Stage 2: Serve con nginx ─────────────────────────────────────────────────
FROM nginx:alpine

# Copiar el build de React al directorio de nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar configuración de nginx para SPA (react-router-dom)
# docker-nginx.conf está en el contexto de build (frontend/)
COPY docker-nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
