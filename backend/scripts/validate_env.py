#!/usr/bin/env python
"""
Script de validación de variables de entorno
Valida que todas las variables críticas estén configuradas antes de iniciar la aplicación.

Uso:
    python scripts/validate_env.py
    python scripts/validate_env.py --environment production
"""
import os
import sys
from pathlib import Path

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# Variables requeridas por ambiente
REQUIRED_VARS = {
    'base': {
        'SECRET_KEY': {
            'description': 'Django secret key (min 50 caracteres)',
            'validator': lambda v: len(v) >= 50,
            'error': 'Debe tener al menos 50 caracteres'
        },
        'DB_NAME': {
            'description': 'Nombre de la base de datos',
            'validator': lambda v: len(v) > 0,
            'error': 'No puede estar vacío'
        },
        'DB_USER': {
            'description': 'Usuario de la base de datos',
            'validator': lambda v: len(v) > 0,
            'error': 'No puede estar vacío'
        },
        'DB_PASSWORD': {
            'description': 'Contraseña de la base de datos',
            'validator': lambda v: len(v) >= 8,
            'error': 'Debe tener al menos 8 caracteres'
        },
        'DB_HOST': {
            'description': 'Host de la base de datos',
            'validator': lambda v: len(v) > 0,
            'error': 'No puede estar vacío',
            'default': 'localhost'
        },
        'DB_PORT': {
            'description': 'Puerto de la base de datos',
            'validator': lambda v: v.isdigit() and 1 <= int(v) <= 65535,
            'error': 'Debe ser un puerto válido (1-65535)',
            'default': '3306'
        },
    },
    'production': {
        'ALLOWED_HOSTS': {
            'description': 'Dominios permitidos (separados por coma)',
            'validator': lambda v: len(v.split(',')) > 0 and v != '',
            'error': 'Debe especificar al menos un dominio'
        },
        'DEBUG': {
            'description': 'Modo debug (debe ser False en producción)',
            'validator': lambda v: v.lower() in ['false', '0', 'no'],
            'error': 'DEBUG debe ser False en producción'
        },
        'SECURE_SSL_REDIRECT': {
            'description': 'Redirigir a HTTPS',
            'validator': lambda v: v.lower() in ['true', '1', 'yes'],
            'error': 'Debe estar habilitado en producción',
            'default': 'True'
        },
    },
    'development': {
        'DEBUG': {
            'description': 'Modo debug',
            'validator': lambda v: True,  # Cualquier valor es válido en dev
            'error': '',
            'default': 'True'
        },
    }
}

OPTIONAL_VARS = {
    'REDIS_HOST': 'Host de Redis para caché',
    'REDIS_PORT': 'Puerto de Redis',
    'REDIS_PASSWORD': 'Contraseña de Redis',
    'EMAIL_HOST': 'Servidor SMTP para emails',
    'EMAIL_PORT': 'Puerto SMTP',
    'EMAIL_HOST_USER': 'Usuario SMTP',
    'EMAIL_HOST_PASSWORD': 'Contraseña SMTP',
    'SENTRY_DSN': 'URL de Sentry para tracking de errores',
}


def print_header():
    """Imprime el header del script"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}   Validación de Variables de Entorno - Cantina Tita{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def load_env_file(env_file):
    """Carga variables desde archivo .env"""
    if not env_file.exists():
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        return True
    except ImportError:
        print(f"{Colors.YELLOW}⚠️  python-dotenv no instalado. Usando variables de sistema.{Colors.RESET}")
        return False


def validate_variable(var_name, config, is_required=True):
    """Valida una variable individual"""
    value = os.environ.get(var_name)
    
    # Si no existe y tiene default, usar default
    if value is None and 'default' in config:
        value = config['default']
        print(f"   ℹ️  {var_name}: usando valor por defecto '{value}'")
        return True
    
    # Si es requerida y no existe
    if value is None:
        if is_required:
            print(f"   {Colors.RED}❌ {var_name}: {config['description']}{Colors.RESET}")
            return False
        return True  # Opcional y no existe
    
    # Validar el valor
    if 'validator' in config:
        try:
            if not config['validator'](value):
                print(f"   {Colors.RED}❌ {var_name}: {config['error']}{Colors.RESET}")
                return False
        except Exception as e:
            print(f"   {Colors.RED}❌ {var_name}: Error en validación - {str(e)}{Colors.RESET}")
            return False
    
    # Variable válida (ocultamos valores sensibles)
    display_value = '***' if any(x in var_name.lower() for x in ['password', 'secret', 'key', 'token']) else value[:30]
    print(f"   {Colors.GREEN}✅ {var_name}: {display_value}{Colors.RESET}")
    return True


def validate_environment(environment='development'):
    """Valida todas las variables requeridas para el ambiente especificado"""
    print_header()
    
    # Intentar cargar archivo .env
    env_file = Path(__file__).parent.parent / f'.env.{environment}'
    if not env_file.exists():
        env_file = Path(__file__).parent.parent / '.env'
    
    print(f"🔍 Buscando archivo de configuración: {env_file}")
    if load_env_file(env_file):
        print(f"   {Colors.GREEN}✅ Archivo cargado correctamente{Colors.RESET}\n")
    else:
        print(f"   {Colors.YELLOW}⚠️  No se encontró archivo .env{Colors.RESET}\n")
    
    # Validar variables base
    print(f"\n{Colors.BLUE}📋 Variables Base (Requeridas):{Colors.RESET}")
    all_valid = True
    for var_name, config in REQUIRED_VARS['base'].items():
        if not validate_variable(var_name, config, is_required=True):
            all_valid = False
    
    # Validar variables específicas del ambiente
    if environment in REQUIRED_VARS:
        print(f"\n{Colors.BLUE}📋 Variables de {environment.title()}:{Colors.RESET}")
        for var_name, config in REQUIRED_VARS[environment].items():
            if not validate_variable(var_name, config, is_required=True):
                all_valid = False
    
    # Mostrar variables opcionales
    print(f"\n{Colors.BLUE}📋 Variables Opcionales:{Colors.RESET}")
    for var_name, description in OPTIONAL_VARS.items():
        value = os.environ.get(var_name)
        if value:
            print(f"   {Colors.GREEN}✅ {var_name}: configurado{Colors.RESET}")
        else:
            print(f"   {Colors.YELLOW}⚠️  {var_name}: no configurado ({description}){Colors.RESET}")
    
    # Resultado final
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    if all_valid:
        print(f"{Colors.GREEN}✅ Todas las variables requeridas están configuradas correctamente{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}❌ Hay variables faltantes o inválidas{Colors.RESET}")
        print(f"\n{Colors.YELLOW}💡 Sugerencia:{Colors.RESET}")
        print(f"   1. Copia .env.example a .env")
        print(f"   2. Configura las variables requeridas")
        print(f"   3. Ejecuta este script nuevamente")
        print(f"\n   Generar SECRET_KEY:")
        print(f"   python -c \"import secrets; print(secrets.token_urlsafe(50))\"")
        print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        return 1


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Valida variables de entorno para Cantina Tita')
    parser.add_argument(
        '--environment', '-e',
        choices=['development', 'production', 'test'],
        default='development',
        help='Ambiente a validar (default: development)'
    )
    
    args = parser.parse_args()
    sys.exit(validate_environment(args.environment))


if __name__ == '__main__':
    main()
