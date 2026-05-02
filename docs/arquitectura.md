# Arquitectura del Sistema

## Visión General

El sistema de Cantina Tita está diseñado con una arquitectura de tres capas:

1. **Backend (API REST)**: Django + Django REST Framework
2. **Frontend Web**: React + Vite
3. **Frontend Móvil**: React Native / Expo

## Principios de Diseño

### 1. Separación de Responsabilidades
- El backend solo expone APIs REST
- El frontend consume las APIs y maneja la UI
- Cada módulo Django es independiente

### 2. Versionado de API
- Todas las APIs están versionadas (v1, v2, etc.)
- Permite evolución de la API sin romper clientes existentes

### 3. Reutilización de Código
- Componentes compartidos en `common/`
- Utilidades en `utils/`
- Validadores personalizados

### 4. Testing
- Tests unitarios para modelos y servicios
- Tests de integración para APIs
- Tests E2E para flujos críticos

## Flujo de Datos

```
Usuario → Frontend → API REST → Backend → Base de Datos
                                    ↓
                              Lógica de Negocio
                                    ↓
                              Validaciones
```

## Módulos Principales

### Core
- Configuraciones base
- Modelos abstractos
- Mixins comunes

### Usuarios
- Autenticación
- Autorización
- Permisos por rol

### Clientes
- CRUD de clientes
- Gestión de hijos
- Validación RUC/CI

### Ventas
- Punto de venta
- Registro de transacciones
- Múltiples métodos de pago
- Cierres de caja

### Almuerzos
- Planes mensuales
- Registro diario de consumo
- Facturación mensual

### Inventario
- Control de stock
- Alertas de stock mínimo
- Movimientos de inventario

## Base de Datos

### Consideraciones
- SQL Server para producción
- SQLite para desarrollo
- Migraciones versionadas
- Índices en campos frecuentemente consultados

### Relaciones
- Cliente → Hijos (OneToMany)
- Venta → DetalleVenta (OneToMany)
- Producto → MovimientoInventario (OneToMany)

## Seguridad

### Autenticación
- Token-based authentication
- Refresh tokens
- Expiración de sesiones

### Autorización
- Permisos basados en roles
- Permisos a nivel de objeto
- Validación en frontend y backend

### Validación
- Validación en ambos lados (frontend/backend)
- Sanitización de inputs
- Prevención de SQL injection (ORM)

## Performance

### Backend
- Query optimization
- Select related / Prefetch related
- Caché de consultas frecuentes
- Paginación

### Frontend
- Code splitting
- Lazy loading
- Memoization
- Debouncing en búsquedas

## Despliegue

### Desarrollo
```
Backend: localhost:8000
Frontend: localhost:3000
SQL Server: localhost:1433
```

### Producción
```
Backend: Gunicorn + Nginx
Frontend: Build estático en CDN
Base de Datos: SQL Server (managed)
```

## Escalabilidad

### Horizontal
- Múltiples instancias del backend
- Load balancer
- Redis para caché compartido

### Vertical
- Optimización de queries
- Índices de base de datos
- Compresión de responses
