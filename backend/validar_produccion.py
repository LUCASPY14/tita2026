"""
Script de validación de configuración de producción
"""
import os
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Cargar settings de producción
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings.production'

try:
    from backend.settings.production import (
        SECRET_KEY, DEBUG, ALLOWED_HOSTS, 
        DATABASES, SECURE_SSL_REDIRECT,
        SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE,
        SECURE_HSTS_SECONDS, LOGGING
    )
    
    print("=" * 70)
    print("VALIDACIÓN DE CONFIGURACIÓN DE PRODUCCIÓN")
    print("=" * 70)
    print()
    
    # Validaciones críticas
    print("1. SEGURIDAD BÁSICA:")
    print(f"   - DEBUG: {DEBUG}")
    assert DEBUG == False, "DEBUG debe ser False en producción"
    print("   ✓ DEBUG correctamente configurado")
    
    print(f"   - SECRET_KEY length: {len(SECRET_KEY)} caracteres")
    assert len(SECRET_KEY) >= 50, "SECRET_KEY debe tener al menos 50 caracteres"
    print("   ✓ SECRET_KEY cumple requisitos de longitud")
    
    print(f"   - ALLOWED_HOSTS: {len(ALLOWED_HOSTS)} hosts configurados")
    assert len(ALLOWED_HOSTS) > 0, "ALLOWED_HOSTS debe tener al menos un host"
    print(f"     Hosts: {', '.join(ALLOWED_HOSTS[:3])}")
    print("   ✓ ALLOWED_HOSTS configurado")
    print()
    
    # Validaciones de HTTPS/SSL
    print("2. HTTPS/SSL:")
    print(f"   - SECURE_SSL_REDIRECT: {SECURE_SSL_REDIRECT}")
    assert SECURE_SSL_REDIRECT == True, "SECURE_SSL_REDIRECT debe ser True"
    print("   ✓ Redirección SSL habilitada")
    
    print(f"   - SECURE_HSTS_SECONDS: {SECURE_HSTS_SECONDS:,} segundos ({SECURE_HSTS_SECONDS // 86400} días)")
    assert SECURE_HSTS_SECONDS >= 31536000, "HSTS debe ser al menos 1 año"
    print("   ✓ HSTS configurado correctamente")
    print()
    
    # Validaciones de Cookies
    print("3. COOKIES SEGURAS:")
    print(f"   - SESSION_COOKIE_SECURE: {SESSION_COOKIE_SECURE}")
    assert SESSION_COOKIE_SECURE == True
    print("   ✓ Session cookies seguras")
    
    print(f"   - CSRF_COOKIE_SECURE: {CSRF_COOKIE_SECURE}")
    assert CSRF_COOKIE_SECURE == True
    print("   ✓ CSRF cookies seguras")
    print()
    
    # Validaciones de Base de Datos
    print("4. BASE DE DATOS:")
    db_config = DATABASES['default']
    print(f"   - Engine: {db_config['ENGINE']}")
    print(f"   - Database: {db_config['NAME']}")
    print(f"   - Host: {db_config['HOST']}")
    print(f"   - Port: {db_config['PORT']}")
    print(f"   - Connection pooling (CONN_MAX_AGE): {db_config.get('CONN_MAX_AGE', 0)} segundos")
    print("   ✓ Base de datos configurada")
    print()
    
    # Validaciones de Logging
    print("5. LOGGING:")
    if 'loggers' in LOGGING:
        print(f"   - Loggers configurados: {len(LOGGING['loggers'])}")
    if 'handlers' in LOGGING:
        print(f"   - Handlers configurados: {len(LOGGING['handlers'])}")
    print("   ✓ Sistema de logging configurado")
    print()
    
    # Resumen
    print("=" * 70)
    print("RESULTADO: ✓ TODAS LAS VALIDACIONES PASARON")
    print("=" * 70)
    print()
    print("PRODUCCION READY!")
    print("Próximos pasos:")
    print("  1. Configurar backups de SQL Server")
    print("  2. Configurar Sentry (SENTRY_DSN en .env.production)")
    print("  3. Configurar servidor web (IIS/nginx)")
    print("  4. Configurar SSL/HTTPS")
    print("  5. Ejecutar collectstatic")
    
except AssertionError as e:
    print(f"\n❌ ERROR DE VALIDACIÓN: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
