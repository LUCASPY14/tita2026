#!/bin/bash

# Script de despliegue del frontend
echo "========================================="
echo "Desplegando Frontend - Cantina Tita"
echo "========================================="

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para mensajes
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Variables
PROJECT_DIR="/var/www/cantina_tita"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Verificar que estamos en el directorio correcto
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Directorio frontend no encontrado"
    exit 1
fi

cd $FRONTEND_DIR

# 1. Obtener últimos cambios
print_success "Obteniendo últimos cambios..."
git pull origin main

# 2. Instalar/actualizar dependencias
print_success "Instalando dependencias..."
npm install

# 3. Build para producción
print_success "Construyendo aplicación..."
npm run build

# 4. Verificar que el build fue exitoso
if [ ! -d "dist" ]; then
    print_error "Error: Directorio dist no fue creado"
    exit 1
fi

# 5. Reiniciar Nginx
print_success "Reiniciando Nginx..."
sudo systemctl restart nginx

# 6. Verificar estado
if sudo systemctl is-active --quiet nginx; then
    print_success "Nginx está corriendo correctamente"
else
    print_error "Error: Nginx no está corriendo"
    exit 1
fi

# 7. Limpiar caché de npm (opcional)
print_success "Limpiando caché..."
npm cache clean --force

print_success "================================="
print_success "Despliegue completado exitosamente!"
print_success "================================="
