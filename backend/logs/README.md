# 📝 Sistema de Logs - Cantina Tita

Este directorio contiene todos los archivos de log de la aplicación.

## 📂 Archivos de Log

### `cantina.log`
- **Nivel:** INFO y superior
- **Contenido:** Logs generales de la aplicación
- **Rotación:** 15 MB, 10 backups
- **Uso:** Tracking general de operaciones

### `errors.log`
- **Nivel:** ERROR y CRITICAL
- **Contenido:** Errores de aplicación y excepciones
- **Rotación:** 10 MB, 10 backups
- **Uso:** Debugging de problemas

### `security.log`
- **Nivel:** WARNING y superior
- **Contenido:** Eventos de seguridad (login fallidos, accesos no autorizados)
- **Rotación:** 5 MB, 20 backups
- **Uso:** Auditoría de seguridad

### `performance.log`
- **Nivel:** DEBUG (queries SQL)
- **Contenido:** Métricas de performance y queries de BD
- **Rotación:** 10 MB, 5 backups
- **Uso:** Optimización de performance

## 🔍 Cómo Usar los Logs

### En el Código

```python
import logging

# Logger general de la app
logger = logging.getLogger('apps.ventas')

# Diferentes niveles
logger.debug('Información de debug')
logger.info('Operación completada exitosamente')
logger.warning('Advertencia: límite alcanzado')
logger.error('Error al procesar venta', exc_info=True)
logger.critical('Sistema en estado crítico')
```

### Loggers Disponibles

- `django` - Framework Django
- `django.request` - Requests HTTP
- `django.security` - Seguridad
- `django.db.backends` - Queries SQL
- `apps` - Todas las aplicaciones
- `apps.ventas` - Módulo de ventas
- `apps.compras` - Módulo de compras
- `apps.inventario` - Módulo de inventario
- `apps.notificaciones` - Notificaciones

### Ver Logs en Tiempo Real

```bash
# Ver todos los logs
tail -f logs/cantina.log

# Solo errores
tail -f logs/errors.log

# Filtrar por nivel
grep "ERROR" logs/cantina.log

# Últimas 100 líneas
tail -n 100 logs/cantina.log
```

## 🔄 Rotación de Logs

Los logs se rotan automáticamente cuando alcanzan el tamaño máximo:
- Se crea un backup con timestamp
- El archivo actual se limpia
- Se mantienen N backups (luego se eliminan los más antiguos)

## 🚨 Alertas por Email

Los errores críticos se envían por email a los administradores configurados en `ADMINS` (solo en producción con `DEBUG=False`).

## 📊 Análisis de Logs

```bash
# Contar errores por día
grep "ERROR" cantina.log | cut -d' ' -f2 | sort | uniq -c

# Top 10 errores más frecuentes
grep "ERROR" errors.log | sort | uniq -c | sort -rn | head -10

# Buscar por usuario
grep "user_id:123" cantina.log
```

## 🔐 Seguridad

- Los logs están en `.gitignore` y no se suben al repositorio
- Nunca hacer log de contraseñas o datos sensibles
- Usar `extra={'user': user.id}` en lugar de `{'password': pwd}`

## 🛠️ Configuración

Editar en `backend/settings/base.py`:

```python
LOGGING = {
    'handlers': {
        'file_general': {
            'maxBytes': 1024 * 1024 * 15,  # Tamaño máximo
            'backupCount': 10,  # Cantidad de backups
        }
    }
}
```
