# 🚀 Guía de Implementación - Base de Datos Cantina Tita

## 📋 Estado Actual

✅ **Completado:**
- Configuración de Django con MySQL
- Estructura de directorios backend y frontend
- Frontend con React + TypeScript + Tailwind CSS + CRA
- Esquema SQL completo copiado a `backend/database/`
- Scripts de importación creados (PowerShell y Batch)

## 🔄 Próximos Pasos

### 1. Importar el Esquema de la Base de Datos

Tienes 3 opciones para importar la base de datos:

#### Opción A: Script PowerShell (Recomendado) ⭐

```powershell
cd d:\tita2026\cantina_tita\backend
.\database\import_database.ps1
```

Este script:
- ✓ Verifica que MySQL esté instalado
- ✓ Solicita credenciales de forma segura
- ✓ Verifica si la BD ya existe
- ✓ Ejecuta el schema SQL
- ✓ Muestra estadísticas de creación

#### Opción B: MySQL Workbench

1. Abrir MySQL Workbench
2. Conectarse a localhost (credenciales: root / L01G05S33Vice.42)
3. File → Open SQL Script
4. Seleccionar: `d:\tita2026\cantina_tita\backend\database\dbcantinatita_schema.sql`
5. Ejecutar el script completo (⚡)

#### Opción C: Línea de Comandos

```bash
mysql -u root -p < d:\tita2026\cantina_tita\backend\database\dbcantinatita_schema.sql
```

Cuando solicite la contraseña, ingresa: `L01G05S33Vice.42`

---

### 2. Generar Modelos Django desde la Base de Datos

Una vez importada la base de datos, genera los modelos Django:

```powershell
cd d:\tita2026\cantina_tita\backend
python manage.py inspectdb > database\generated_models.py
```

Este comando:
- Lee todas las tablas de `dbcantinatita`
- Genera clases de modelo Django automáticamente
- Incluye todas las relaciones (ForeignKey, etc.)

---

### 3. Organizar los Modelos por Apps

El archivo `generated_models.py` contendrá TODOS los modelos. Necesitarás separarlos por app:

**Estructura sugerida:**

```
apps/
├── core/
│   └── models.py (configuracion_sistema, datos_empresa, etc.)
├── usuarios/
│   └── models.py (empleados, roles, perfiles_usuario, etc.)
├── clientes/
│   └── models.py (clientes, tipos_cliente, listas_precios, hijos)
├── productos/
│   └── models.py (productos, categorias, stock_unico, precios_por_lista)
├── ventas/
│   └── models.py (ventas, detalles_venta, pagos_venta)
├── compras/
│   └── models.py (compras, detalles_compra, proveedores)
├── inventario/
│   └── models.py (movimientos_stock, ajustes_inventario)
├── almuerzos/
│   └── models.py (tipos_almuerzo, planes_almuerzo, registros_consumo_almuerzo)
├── tarjetas/
│   └── models.py (tarjetas, cargas_saldo, consumos_tarjeta)
└── facturacion/
    └── models.py (documentos_tributarios, timbrados, puntos_expedicion)
```

---

### 4. Crear Migraciones Iniciales

Una vez organizados los modelos:

```powershell
python manage.py makemigrations
python manage.py migrate --fake-initial
```

**Nota:** Usamos `--fake-initial` porque las tablas ya existen en la base de datos.

---

### 5. Crear Superusuario Django

```powershell
python manage.py createsuperuser
```

Credenciales sugeridas:
- Usuario: `admin`
- Email: `admin@cantinatita.com`
- Contraseña: `admin123` (cambiar en producción)

---

### 6. Ejecutar el Servidor de Desarrollo

```powershell
# Terminal 1: Backend Django
cd d:\tita2026\cantina_tita\backend
python manage.py runserver

# Terminal 2: Frontend React
cd d:\tita2026\cantina_tita\frontend
npm start
```

URLs de acceso:
- Backend API: http://localhost:8000/
- Django Admin: http://localhost:8000/admin/
- Frontend React: http://localhost:3000/

---

## 📊 Estructura de la Base de Datos

La base de datos `dbcantinatita` incluye:

- **55+ tablas** organizadas por módulos
- **5 vistas** para consultas comunes
- **Facturación electrónica** para Paraguay (SET/SIFEN)
- **Sistema de tarjetas** RFID/códigos de barras
- **Gestión de almuerzos** con suscripciones
- **Control de inventario** con movimientos
- **Auditoría completa** de operaciones
- **Seguridad** multinivel

Para más detalles, consulta: `backend/database/README.md`

---

## 🗂️ Apps Django Configuradas

Según el esquema SQL, estas son las apps que deberías tener:

```python
INSTALLED_APPS = [
    # ... Django apps ...
    
    # Third party
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'apps.core',              # Configuración y datos empresa
    'apps.usuarios',          # Empleados, roles, perfiles
    'apps.clientes',          # Clientes y sus hijos
    'apps.productos',         # Productos, categorías, stock
    'apps.ventas',            # Ventas y detalles
    'apps.compras',           # Compras y proveedores
    'apps.inventario',        # Movimientos y ajustes
    'apps.almuerzos',         # Sistema de almuerzos
    'apps.tarjetas',          # Tarjetas y recargas
    'apps.facturacion',       # Documentos tributarios
    'apps.cajas',             # Cajas y cierres
    'apps.notificaciones',    # Notificaciones de saldo
    'apps.reportes',          # Reportes y dashboards
    'apps.auditoria',         # Auditoría y seguridad
]
```

---

## 🔐 Seguridad

**IMPORTANTE:** La configuración actual tiene la contraseña de MySQL en `base.py`:

```python
'PASSWORD': 'L01G05S33Vice.42',
```

**Recomendaciones:**
1. Mover a variable de entorno
2. Crear archivo `.env` (ya existe `.env.example`)
3. No commitear contraseñas al repositorio de Git

---

## 📝 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `backend/database/dbcantinatita_schema.sql` | Esquema completo de la BD (2000+ líneas) |
| `backend/database/README.md` | Documentación detallada de tablas |
| `backend/database/import_database.ps1` | Script de importación PowerShell |
| `backend/settings/development.py` | Configuración de desarrollo |
| `backend/requirements.txt` | Dependencias Python |
| `frontend/package.json` | Dependencias Node.js |

---

## 🐛 Solución de Problemas

### Error: "MySQL no está instalado"
- Descargar de: https://dev.mysql.com/downloads/mysql/
- Agregar al PATH del sistema

### Error: "Access denied for user 'root'"
- Verificar contraseña en `backend/settings/development.py`
- Verificar que MySQL esté ejecutándose

### Error al ejecutar inspectdb
- Verificar que la BD exista: `SHOW DATABASES;`
- Verificar conexión Django: `python manage.py dbshell`

---

## 📞 Siguiente Sesión

**Prioridad ALTA:**
1. ✅ Importar el esquema SQL
2. ⏳ Generar modelos con `inspectdb`
3. ⏳ Organizar modelos por apps
4. ⏳ Crear serializers DRF
5. ⏳ Crear endpoints API

**Prioridad MEDIA:**
- Crear admin.py para cada app
- Implementar permisos y autenticación
- Crear vistas del frontend

---

## 📚 Recursos

- [Django inspectdb](https://docs.djangoproject.com/en/4.2/howto/legacy-databases/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [MySQL para Django](https://docs.djangoproject.com/en/4.2/ref/databases/#mysql-notes)

---

**Última actualización:** 28 de Febrero de 2026  
**Estado:** ✅ Listo para importar base de datos
