# Sistema de Gestión Cantina Tita

Sistema integral de gestión para cantina escolar, con módulos de ventas, almuerzos, inventario, clientes y reportes.

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
