# 🐳 GUÍA DE DOCKER - SISTEMA CANTINA TITA

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración Inicial](#configuración-inicial)
3. [Levantar el Sistema](#levantar-el-sistema)
4. [Acceder desde Otras PCs](#acceder-desde-otras-pcs)
5. [Comandos Útiles](#comandos-útiles)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos Previos

### 1. Instalar Docker Desktop

**Windows:**
- Descargar de: https://www.docker.com/products/docker-desktop
- Instalar y reiniciar el sistema
- Verificar WSL 2 esté activado

**Verificar instalación:**
```powershell
docker --version
docker-compose --version
```

### 2. Recursos Mínimos Recomendados

- **RAM**: 4 GB disponible
- **CPU**: 2 núcleos
- **Disco**: 10 GB libres
- **Docker Desktop Settings**:
  - Memory: 4 GB
  - CPUs: 2-4
  - Swap: 1 GB

---

## ⚙️ Configuración Inicial

### 1. Navegar al directorio del proyecto

```powershell
cd D:\tita2026\cantina_tita
```

### 2. Verificar que existe el archivo `.env.docker`

El archivo ya está creado con las configuraciones por defecto. Si quieres personalizarlo:

```powershell
# Ver el contenido del archivo
Get-Content .env.docker

# Editar con VS Code (opcional)
code .env.docker
```

### 3. Obtener tu IP local

**Para que otras PCs accedan, necesitas tu IP en la red local:**

```powershell
# Obtener tu IP local
ipconfig | findstr IPv4
```

Ejemplo de salida:
```
IPv4 Address. . . . . . . . . . . : 192.168.1.100
```

### 4. Actualizar ALLOWED_HOSTS (IMPORTANTE)

Edita el archivo `.env.docker` y cambia:

```ini
# Antes:
ALLOWED_HOSTS=*

# Después (reemplaza con tu IP real):
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
```

---

## 🚀 Levantar el Sistema

### Opción 1: Primera vez (construcción completa)

```powershell
# Construir las imágenes y levantar los contenedores
docker-compose up --build -d
```

Esto puede tardar 5-10 minutos la primera vez mientras descarga imágenes y construye los contenedores.

### Opción 2: Ejecución normal

```powershell
# Solo levantar los contenedores (si ya están construidos)
docker-compose up -d
```

### Verificar que los servicios estén corriendo

```powershell
# Ver el estado de los contenedores
docker-compose ps

# Ver los logs en tiempo real
docker-compose logs -f
```

Deberías ver algo como:
```
NAME                  STATUS      PORTS
cantina_db            Up          0.0.0.0:5432->5432/tcp
cantina_redis         Up          0.0.0.0:6379->6379/tcp
cantina_backend       Up          0.0.0.0:8000->8000/tcp
cantina_celery        Up
cantina_celery_beat   Up
cantina_nginx         Up          0.0.0.0:80->80/tcp
```

### Crear el superusuario de Django

```powershell
# Acceder al contenedor del backend
docker-compose exec backend python manage.py createsuperuser
```

Sigue las instrucciones para crear el usuario admin.

---

## 🌐 Acceder desde Otras PCs

### 1. Verificar el Firewall de Windows

**Permitir conexiones en el puerto 80 y 8000:**

```powershell
# Ejecutar como Administrador
New-NetFirewallRule -DisplayName "Cantina TITA - HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "Cantina TITA - Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

O manualmente:
1. Buscar "Windows Defender Firewall"
2. "Configuración avanzada"
3. "Reglas de entrada" → "Nueva regla"
4. Tipo: Puerto → TCP → Puertos específicos: 80, 8000
5. Acción: Permitir la conexión
6. Aplicar a todos los perfiles

### 2. URLs de Acceso

**Desde la PC donde corre Docker:**
- Frontend/API: http://localhost
- Directamente al backend: http://localhost:8000
- Admin Django: http://localhost:8000/admin
- API Docs (Swagger): http://localhost:8000/swagger
- API Docs (Redoc): http://localhost:8000/redoc

**Desde otras PCs en la red (reemplaza `192.168.1.100` con tu IP):**
- Frontend/API: http://192.168.1.100
- Directamente al backend: http://192.168.1.100:8000
- Admin Django: http://192.168.1.100:8000/admin
- API Docs (Swagger): http://192.168.1.100:8000/swagger
- API Docs (Redoc): http://192.168.1.100:8000/redoc

### 3. Probar la Conexión

**Desde otra PC en la red:**

```powershell
# Ping para verificar conectividad
ping 192.168.1.100

# Probar el endpoint de salud
curl http://192.168.1.100/health/
```

Si responde "OK", ¡está funcionando! 🎉

---

## 📝 Comandos Útiles

### Gestión de Contenedores

```powershell
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f db

# Detener todos los contenedores
docker-compose stop

# Reiniciar todos los contenedores
docker-compose restart

# Detener y eliminar contenedores (los datos persisten)
docker-compose down

# Detener y eliminar TODO (incluye volúmenes de base de datos)
docker-compose down -v
```

### Comandos de Django

```powershell
# Migraciones
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Acceder al shell de Django
docker-compose exec backend python manage.py shell

# Ejecutar tests
docker-compose exec backend python manage.py test

# Recolectar archivos estáticos
docker-compose exec backend python manage.py collectstatic --noinput
```

### Comandos de Base de Datos

```powershell
# Acceder a PostgreSQL
docker-compose exec db psql -U cantina_user -d cantina_db

# Backup de la base de datos
docker-compose exec db pg_dump -U cantina_user cantina_db > backup.sql

# Restaurar backup
Get-Content backup.sql | docker-compose exec -T db psql -U cantina_user cantina_db
```

### Comandos de Redis

```powershell
# Acceder a Redis CLI
docker-compose exec redis redis-cli -a redis_pass_2026

# Ver todas las claves
docker-compose exec redis redis-cli -a redis_pass_2026 KEYS '*'

# Limpiar cache
docker-compose exec redis redis-cli -a redis_pass_2026 FLUSHALL
```

### Comandos de Celery

```powershell
# Ver tareas en cola
docker-compose exec celery_worker celery -A backend inspect active

# Ver workers registrados
docker-compose exec celery_worker celery -A backend inspect registered

# Ver estadísticas
docker-compose exec celery_worker celery -A backend inspect stats
```

---

## 🐛 Troubleshooting

### Problema 1: "Port is already allocated"

**Solución:** Otro proceso está usando el puerto.

```powershell
# Ver qué proceso usa el puerto 80
netstat -ano | findstr :80

# Matar el proceso (reemplaza PID con el número obtenido)
taskkill /PID 1234 /F

# O cambiar el puerto en .env.docker
NGINX_PORT=8080
```

### Problema 2: Contenedor se reinicia constantemente

```powershell
# Ver qué está fallando
docker-compose logs backend

# Verificar configuración de la base de datos
docker-compose exec db psql -U cantina_user -d cantina_db -c "\l"
```

### Problema 3: No se puede acceder desde otra PC

1. **Verificar firewall:**
   ```powershell
   Get-NetFirewallRule -DisplayName "*Cantina*"
   ```

2. **Verificar que el servicio escucha en 0.0.0.0:**
   ```powershell
   netstat -an | findstr "80"
   ```

3. **Verificar ALLOWED_HOSTS en `.env.docker`**
   
4. **Hacer ping desde la otra PC:**
   ```powershell
   ping 192.168.1.100
   ```

### Problema 4: Base de datos no se conecta

```powershell
# Verificar que PostgreSQL está corriendo
docker-compose ps db

# Reiniciar el servicio de base de datos
docker-compose restart db

# Ver logs de PostgreSQL
docker-compose logs db
```

### Problema 5: Limpiar todo y empezar de cero

```powershell
# Detener todo
docker-compose down -v

# Eliminar imágenes
docker-compose down --rmi all

# Limpiar volúmenes huérfanos
docker volume prune

# Reconstruir desde cero
docker-compose up --build -d
```

### Problema 6: Rendimiento lento

```powershell
# Aumentar recursos en Docker Desktop:
# Settings → Resources → WSL Integration → Ajustar memoria y CPUs

# O modificar workers de Gunicorn en docker-compose.yml
# Cambiar --workers 4 a --workers 2 si tienes poca RAM
```

---

## 📊 Monitoreo

### Ver uso de recursos

```powershell
# CPU y memoria de cada contenedor
docker stats

# Espacio en disco
docker system df
```

### Health checks

```powershell
# Verificar salud de los contenedores
docker-compose ps

# Probar endpoint de salud
curl http://localhost/health/
```

---

## 🔒 Seguridad (Producción)

Para producción, **DEBES cambiar**:

1. `SECRET_KEY` en `.env.docker`
2. `DEBUG=False` en `.env.docker`
3. Contraseñas de base de datos y Redis
4. `ALLOWED_HOSTS` con dominios específicos
5. Configurar HTTPS con certificados SSL

---

## 📚 Recursos Adicionales

- **Docker Docs**: https://docs.docker.com
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/docs/

---

## ✅ Checklist de Verificación

- [ ] Docker Desktop instalado y corriendo
- [ ] Archivo `.env.docker` configurado con tu IP
- [ ] Firewall configurado para permitir puertos 80 y 8000
- [ ] Contenedores corriendo: `docker-compose ps`
- [ ] Superusuario creado
- [ ] Accesible desde localhost
- [ ] Accesible desde otra PC en la red
- [ ] Logs sin errores críticos

---

¡Listo! Ahora tu sistema Cantina TITA está corriendo con Docker y accesible desde cualquier PC en tu red local. 🚀
