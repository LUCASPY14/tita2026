#!/bin/bash

# Script de despliegue del backend
echo "========================================="
echo "Desplegando Backend - Cantina Tita"
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
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"

# Verificar que estamos en el directorio correcto
if [ ! -d "$BACKEND_DIR" ]; then
    print_error "Directorio backend no encontrado"
    exit 1
fi

cd $BACKEND_DIR

# 1. Activar entorno virtual
print_success "Activando entorno virtual..."
source $VENV_DIR/bin/activate

# 2. Obtener últimos cambios
print_success "Obteniendo últimos cambios..."
git pull origin main

# 3. Instalar/actualizar dependencias
print_success "Instalando dependencias..."
pip install -r requirements.txt

# 4. Ejecutar migraciones
print_success "Ejecutando migraciones..."
python manage.py migrate

# 5. Recolectar archivos estáticos
print_success "Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

# 6. Reiniciar Gunicorn
print_success "Reiniciando Gunicorn..."
sudo systemctl restart gunicorn

# 7. Verificar estado
if sudo systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn está corriendo correctamente"
else
    print_error "Error: Gunicorn no está corriendo"
    exit 1
fi

# 8. Limpiar archivos .pyc
print_success "Limpiando archivos compilados..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete

print_success "================================="
print_success "Despliegue completado exitosamente!"
print_success "================================="
