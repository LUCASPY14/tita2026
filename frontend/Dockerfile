# ── Stage 1: build React/Vite app ────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

COPY . .
RUN npm run build

# ── Stage 2: serve with Nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remover config por defecto
RUN rm /etc/nginx/conf.d/default.conf

# Copiar assets compilados
COPY --from=builder /app/dist /usr/share/nginx/html

# Config de Nginx para SPA (maneja React Router)
COPY nginx.conf /etc/nginx/conf.d/frontend.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
