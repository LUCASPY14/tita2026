# 🚀 Guía de Deployment - Cantina Tita

## 📋 Pre-requisitos

- Python 3.14+
- Node.js 18+
- SQL Server 2025
- Redis 6+ (para Celery)

---

## ⚙️ Configuración Inicial

### 1. Clonar Repositorio
```bash
git clone https://github.com/tu-usuario/cantina-tita.git
cd cantina-tita
```

### 2. Backend Setup

#### Crear entorno virtual
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

#### Instalar dependencias
```bash
pip install -r requirements.txt
```

#### Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

**Variables importantes:**
```env
DJANGO_ENVIRONMENT=production
DJANGO_SECRET_KEY=<genera-una-clave-segura-aqui>
DB_ENGINE=mssql
DB_NAME=titadb
DB_USER=sa
DB_PASSWORD=<password-seguro>
DB_HOST=localhost
DB_PORT=1433
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
```

#### Ejecutar migraciones
```bash
python manage.py migrate
```

#### Crear superusuario
```bash
python manage.py createsuperuser
```

#### Recolectar archivos estáticos
```bash
python manage.py collectstatic --no-input
```

---

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

#### Configurar API endpoint
```bash
# Crear .env.production
echo "REACT_APP_API_URL=https://api.tudominio.com" > .env.production
```

#### Build de producción
```bash
npm run build
```

---

## 🧪 Ejecutar Tests

### Backend
```bash
cd backend
pytest tests/integration/ -v
```

**Resultado esperado:** 17/17 tests passing ✅

### Frontend
```bash
cd frontend
npm test -- --watchAll=false
```

**Resultado esperado:** 620-670 tests passing (92-100%) ⚠️

---

## 🐳 Deployment con Docker

### Desarrollo
```bash
cd docker
docker-compose up -d
```

### Producción
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Servicios incluidos:**
- Backend (Django + Gunicorn)
- Frontend (Nginx sirviendo build)
- SQL Server Database
- Redis (Celery broker)

---

## 🔒 Seguridad Pre-Deploy

### Checklist Crítico
- [ ] `DEBUG = False` en producción
- [ ] `SECRET_KEY` única y segura
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] HTTPS habilitado
- [ ] CORS configurado restrictivamente
- [ ] Base de datos con usuario no-root
- [ ] Backups automáticos configurados
- [ ] Logs monitoreados (Sentry/similar)

### Generar SECRET_KEY segura
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## 📊 Monitoreo y Logs

### Ver logs en Docker
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Logs de Django
```bash
tail -f backend/logs/django.log
```

### Logs de Nginx
```bash
tail -f frontend/logs/nginx/access.log
tail -f frontend/logs/nginx/error.log
```

---

## 🔄 Tareas Periódicas (Celery)

### Iniciar workers
```bash
cd backend
celery -A backend worker -l info
```

### Iniciar scheduler (Celery Beat)
```bash
celery -A backend beat -l info
```

### Monitorear tareas
```bash
celery -A backend events
```

---

## 📈 Performance Tuning

### Backend (Gunicorn)
```bash
# Recomendado: (2 x CPU cores) + 1
gunicorn backend.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 5 \
  --timeout 120
```

### Database (SQL Server)
```sql
-- Query Store (recomendado para análisis de rendimiento)
ALTER DATABASE [titadb] SET QUERY_STORE = ON;
```

### Frontend (Nginx)
```nginx
# Habilitar compresión gzip
gzip on;
gzip_types text/css application/javascript application/json;
gzip_min_length 1000;
```

---

## 🆘 Troubleshooting

### Error: "Can't connect to SQL Server"
```bash
# Verificar que SQL Server esté corriendo
systemctl status mssql-server

# Verificar credenciales
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P '<tu-password>' -Q "SELECT 1" -C
```

### Error: "SECRET_KEY is insecure"
```bash
# Generar nueva clave
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Actualizar en .env
DJANGO_SECRET_KEY=nueva-clave-generada
```

### Frontend no conecta con Backend
```bash
# Verificar CORS en backend/settings
CORS_ALLOWED_ORIGINS = ['https://tudominio.com']

# Verificar API URL en frontend
echo $REACT_APP_API_URL
```

---

## 📚 Recursos Adicionales

- **Documentación Backend:** [backend/README.md](backend/README.md)
- **Reporte de Tests:** [backend/tests/README.md](backend/tests/README.md)
- **Reporte de Validación:** [VALIDATION_REPORT.md](VALIDATION_REPORT.md)
- **API Documentation:** `http://localhost:8000/swagger/` (desarrollo)

---

## 🎯 Métricas de Producción

### Backend
- Response time: < 200ms promedio
- Uptime: 99.9%
- Error rate: < 0.1%

### Frontend
- Bundle size: < 500KB (gzip)
- Time to Interactive: < 3s
- Lighthouse score: > 90

---

## 🔄 Actualización de Producción

### Proceso Zero-Downtime

1. **Pull latest code:**
```bash
git pull origin main
```

2. **Update backend:**
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart gunicorn
```

3. **Update frontend:**
```bash
cd frontend
npm install
npm run build
sudo systemctl restart nginx
```

4. **Verificar:**
```bash
curl -I https://tudominio.com  # Debe retornar 200
```

---

## 📞 Soporte

**Equipo de Desarrollo:** dev@cantinatita.com  
**Issues:** GitHub Issues  
**Documentación:** Wiki del proyecto

---

**Última actualización:** 5 de Marzo, 2026
