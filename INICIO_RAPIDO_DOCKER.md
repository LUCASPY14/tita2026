# 🎯 GUÍA RÁPIDA DE INICIO CON DOCKER

## 🚀 Inicio Rápido (3 pasos)

### 1️⃣ Ejecutar el script de inicio

```powershell
.\start-docker.ps1
```

### 2️⃣ Cuando pregunte "¿Es la primera vez?", responde **"y"**

El script automáticamente:
- ✅ Construye los contenedores
- ✅ Levanta todos los servicios
- ✅ Aplica migraciones de base de datos
- ✅ Te pide crear un superusuario

### 3️⃣ Accede al sistema

- **Desde tu PC**: http://localhost
- **Desde otras PCs**: http://TU-IP-LOCAL (el script te muestra tu IP)

---

## 🌐 Acceder desde Otras PCs

### Paso 1: Identificar tu IP

El script `start-docker.ps1` te muestra tu IP automáticamente. Si necesitas verla de nuevo:

```powershell
ipconfig | findstr IPv4
```

Ejemplo: `192.168.1.100`

### Paso 2: Configurar Firewall

**Permitir tráfico HTTP en Windows:**

```powershell
# Ejecutar como Administrador
New-NetFirewallRule -DisplayName "Cantina HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "Cantina Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Paso 3: Probar desde otra PC

**Desde un navegador en otra PC:**
```
http://192.168.1.100
http://192.168.1.100/admin
http://192.168.1.100:8000/swagger
```

---

## 📝 Comandos Básicos

```powershell
# Iniciar el sistema
.\start-docker.ps1

# Detener el sistema (preserva datos)
.\stop-docker.ps1

# Ver logs en tiempo real
docker-compose logs -f

# Ver estado de contenedores
docker-compose ps

# Reiniciar un servicio específico
docker-compose restart backend

# Acceder al shell de Django
docker-compose exec backend python manage.py shell
```

---

## ❓ Solución de Problemas Comunes

### ❌ Error: "Puerto ya está en uso"

**Opción 1**: Detén el servicio que usa el puerto
```powershell
# Ver qué proceso usa el puerto 80
netstat -ano | findstr :80

# Matar el proceso (reemplaza 1234 con el PID)
taskkill /PID 1234 /F
```

**Opción 2**: Cambia el puerto en `.env.docker`
```ini
NGINX_PORT=8080
```

### ❌ No puedo acceder desde otra PC

1. **Verifica que el firewall permita conexiones:**
   ```powershell
   Get-NetFirewallRule -DisplayName "*Cantina*"
   ```

2. **Prueba la conectividad con ping:**
   ```powershell
   # Desde la otra PC
   ping 192.168.1.100
   ```

3. **Verifica ALLOWED_HOSTS en `.env.docker`:**
   ```ini
   ALLOWED_HOSTS=*
   ```

### ❌ Base de datos no conecta

```powershell
# Reiniciar el servicio de base de datos
docker-compose restart db

# Ver logs para identificar el error
docker-compose logs db
```

### ❌ Limpiar todo y empezar de cero

```powershell
# Detener y eliminar TODO (incluye datos)
docker-compose down -v

# Limpiar imágenes huérfanas
docker system prune -a

# Volver a iniciar
.\start-docker.ps1
```

---

## 📖 Documentación Completa

Para información detallada, consulta:
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)**: Guía completa paso a paso
- **[docker/README.md](docker/README.md)**: Detalles técnicos de arquitectura

---

## ✅ Checklist

- [ ] Docker Desktop instalado
- [ ] Ejecuté `.\start-docker.ps1`
- [ ] Creé el superusuario
- [ ] Puedo acceder desde `http://localhost`
- [ ] Configuré el firewall
- [ ] Puedo acceder desde otra PC en la red

---

¡Listo! Tu sistema está corriendo con Docker. 🎉
