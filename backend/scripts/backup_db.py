#!/usr/bin/env python
"""
Script para realizar backup de la base de datos
"""
import os
import sys
from datetime import datetime
import subprocess

def backup_database():
    """Realiza backup de la base de datos PostgreSQL"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup_{timestamp}.sql'
    backup_path = os.path.join('backups', backup_file)
    
    # Crear directorio de backups si no existe
    os.makedirs('backups', exist_ok=True)
    
    # Obtener configuración de la base de datos
    db_name = os.getenv('DB_NAME', 'cantina_db')
    db_user = os.getenv('DB_USER', 'cantina_user')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    
    # Comando para backup
    cmd = f'pg_dump -h {db_host} -p {db_port} -U {db_user} -F p -f {backup_path} {db_name}'
    
    try:
        print(f"Realizando backup de la base de datos...")
        subprocess.run(cmd, shell=True, check=True)
        print(f"✓ Backup realizado exitosamente: {backup_path}")
        
        # Comprimir backup
        compressed_file = f'{backup_path}.gz'
        subprocess.run(f'gzip {backup_path}', shell=True, check=True)
        print(f"✓ Backup comprimido: {compressed_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error al realizar backup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    backup_database()
