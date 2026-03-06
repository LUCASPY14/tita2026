# Sistema de Gestión Cantina Tita

![CI Pipeline](https://github.com/LUCASPY14/tita2026/actions/workflows/ci.yml/badge.svg?branch=desarrollo)
![Backend Tests](https://img.shields.io/badge/backend%20tests-151%20passing-brightgreen)
![Frontend Tests](https://img.shields.io/badge/frontend%20tests-670%20passing-brightgreen)
![Backend Coverage](https://img.shields.io/badge/backend%20coverage-26%25-yellow)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2+-green)
![React](https://img.shields.io/badge/react-18-blue)
![TypeScript](https://img.shields.io/badge/typescript-4.9+-blue)

Sistema integral de gestión para cantina escolar, con módulos de ventas, almuerzos, inventario, clientes y reportes.

## 📊 Estado del Proyecto

### Tests & Cobertura
- ✅ **Backend:** 151/151 tests passing (100%)
- ✅ **Frontend:** 670/670 tests passing (100%)
- 🟡 **Backend Coverage:** 26% (objetivo: 40%)
  - Models: 92% coverage
  - Serializers: 85-100% coverage
  - Admin: 54-73% coverage
- ⏳ **E2E Tests:** Pendiente Sprint 4
- ✅ **CI/CD:** GitHub Actions activo

**Ver Workflow:** [GitHub Actions](https://github.com/LUCASPY14/tita2026/actions)

### Calidad de Código
- ✅ Sin errores de TypeScript
- ✅ Tests funcionando correctamente
- ✅ Arquitectura modular y escalable
- ✅ Linting automatizado (Black, Flake8, ESLint)

## 📁 Estructura del Proyecto

```
cantina_tita/
├── backend/                     # API REST (Django + DRF)
│   ├── manage.py
│   ├── requirements.txt
│   ├── backend/                 # Configuración Django
│   │   ├── settings/           # Settings por ambiente
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/                    # Aplicaciones Django
│   │   ├── core/
│   │   ├── usuarios/
│   │   ├── clientes/
│   │   ├── productos/
│   │   ├── ventas/
│   │   ├── compras/
│   │   ├── inventario/
│   │   ├── almuerzos/
│   │   ├── contabilidad/
│   │   ├── notificaciones/
│   │   ├── api_integrations/
│   │   └── reportes/
│   ├── api/                     # APIs versionadas
│   │   ├── v1/
│   │   └── v2/
│   ├── common/                  # Código compartido
│   │   ├── permissions.py
│   │   ├── authentication.py
│   │   ├── pagination.py
│   │   ├── exceptions.py
│   │   ├── constants.py
│   │   ├── utils/
│   │   └── validators/
│   ├── tests/                   # Tests
│   ├── media/                   # Archivos subidos
│   ├── static/                  # Archivos estáticos
│   └── fixtures/                # Datos iniciales
│
├── frontend/                    # Frontend (React + Vite)
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── routes/             # Rutas
│   │   ├── layouts/            # Layouts
│   │   ├── pages/              # Páginas
│   │   ├── components/         # Componentes reutilizables
│   │   ├── hooks/              # Custom hooks
│   │   ├── services/           # Servicios API
│   │   ├── store/              # Estado global (Zustand)
│   │   ├── utils/              # Utilidades
│   │   ├── assets/             # Recursos estáticos
│   │   └── config/             # Configuración
│   └── tests/
│
├── mobile/                      # App móvil
│   ├── package.json
│   └── src/
│
├── docs/                        # Documentación
├── docker/                      # Configuración Docker
└── scripts/                     # Scripts de utilidad
```

## 🚀 Inicio Rápido

### Backend (Django)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend (React + TypeScript + Tailwind)

```bash
cd frontend
npm install
npm start
```

El frontend estará disponible en `http://localhost:3000`

## 🧪 Testing

### Ejecutar Tests Backend

```bash
cd backend

# Ejecutar todos los tests
python manage.py test apps --keepdb

# Ejecutar tests con cobertura
coverage run --source='apps' manage.py test apps --keepdb
coverage report
coverage html  # Genera reporte HTML en htmlcov/

# Ejecutar tests de una app específica
python manage.py test apps.ventas --keepdb
python manage.py test apps.productos.tests_models --keepdb

# Estado actual: 151 tests, 26% coverage
```

### Ejecutar Tests Frontend

```bash
cd frontend

# Ejecutar todos los tests
npm test

# Ejecutar tests con cobertura
npm test -- --coverage

# Ejecutar tests en modo watch
npm test -- --watch

# Estado actual: 670 tests passing (100%)
```

### Reporte de Cobertura

Los reportes de cobertura están disponibles:
- Backend: `backend/htmlcov/index.html`
- Frontend: `frontend/coverage/lcov-report/index.html`

Ver [VALIDATION_REPORT.md](VALIDATION_REPORT.md) para análisis detallado de testing.


## 🔧 Tecnologías

### Backend
- Django 4.2+
- Django REST Framework
- PostgreSQL / SQLite
- Celery (tareas asíncronas)

### Frontend
- **React 18**
- **TypeScript 4.9+**
- **Tailwind CSS 3.4**
- React Router
- Axios
- Zustand (estado global)
- Create React App

### Mobile
- React Native / Expo

## 📝 Módulos Principales

1. **Usuarios**: Gestión de usuarios y permisos
2. **Clientes**: Registro de clientes y sus hijos
3. **Productos**: Catálogo de productos
4. **Ventas**: Punto de venta y gestión de ventas
5. **Almuerzos**: Planes de almuerzo y seguimiento diario
6. **Inventario**: Control de stock
7. **Compras**: Registro de compras a proveedores
8. **Reportes**: Reportes de ventas, almuerzos, inventario
9. **Contabilidad**: Gestión financiera
10. **Notificaciones**: Sistema de notificaciones

## 🔐 Variables de Entorno

### Backend (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=localhost,127.0.0.1
```

REACT_APP_API_URL=http://localhost:8000/api/v1
REACT
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Cantina Tita
```

## 📚 Documentación

La documentación completa está disponible en el directorio `docs/`.

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.
