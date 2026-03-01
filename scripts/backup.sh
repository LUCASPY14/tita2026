#!/bin/bash

# Script de backup
echo "========================================="
echo "Backup - Cantina Tita"
echo "========================================="

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/cantina_tita"
PROJECT_DIR="/var/www/cantina_tita"

# Crear directorio de backups
mkdir -p $BACKUP_DIR

# 1. Backup de base de datos
echo "Realizando backup de base de datos..."
sudo -u postgres pg_dump cantina_db > $BACKUP_DIR/db_$TIMESTAMP.sql

# Comprimir backup
gzip $BACKUP_DIR/db_$TIMESTAMP.sql

echo "✓ Backup de base de datos completado: db_$TIMESTAMP.sql.gz"

# 2. Backup de archivos media
echo "Realizando backup de archivos media..."
tar -czf $BACKUP_DIR/media_$TIMESTAMP.tar.gz -C $PROJECT_DIR/backend media/

echo "✓ Backup de archivos media completado: media_$TIMESTAMP.tar.gz"

# 3. Limpiar backups antiguos (mantener últimos 7 días)
echo "Limpiando backups antiguos..."
find $BACKUP_DIR -type f -mtime +7 -delete

echo "✓ Limpieza completada"

echo "========================================="
echo "Backup completado exitosamente!"
echo "Archivos guardados en: $BACKUP_DIR"
echo "========================================="
