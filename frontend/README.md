# Frontend - Cantina Tita

Frontend del sistema de gestión de Cantina Tita, construido con **React + TypeScript + Tailwind CSS**.

## 🚀 Stack Tecnológico

- **React 18** - Biblioteca de UI
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Framework de CSS utility-first
- **React Router** - Navegación
- **Axios** - Cliente HTTP
- **Zustand** - Estado global
- **date-fns** - Manipulación de fechas
- **React Hook Form** - Manejo de formularios

## 📁 Estructura

```
src/
├── assets/           # Recursos estáticos
│   ├── images/
│   ├── fonts/
│   └── styles/
│       └── global.css    # Estilos globales + Tailwind
├── components/       # Componentes reutilizables
│   ├── common/      # Componentes básicos (Button, Input, etc.)
│   ├── forms/       # Componentes de formularios
│   ├── layout/      # Componentes de layout
│   └── charts/      # Componentes de gráficos
├── config/          # Configuración
├── hooks/           # Custom hooks
│   ├── useAuth.ts
│   └── useFetch.ts
├── layouts/         # Layouts de páginas
├── pages/           # Páginas/Vistas
│   ├── auth/        # Login, Register, etc.
│   ├── dashboard/   # Dashboard principal
│   ├── clientes/    # Gestión de clientes
│   ├── ventas/      # Punto de venta
│   ├── productos/   # Catálogo de productos
│   ├── almuerzos/   # Gestión de almuerzos
│   └── reportes/    # Reportes y estadísticas
├── routes/          # Configuración de rutas
├── services/        # Servicios de API
│   ├── api.ts              # Cliente Axios
│   ├── auth.service.ts     # Autenticación
│   ├── clientes.service.ts
│   └── ventas.service.ts
├── store/           # Estado global (Zustand)
│   ├── authSlice.ts
│   └── ventasSlice.ts
├── types/           # Definiciones de tipos TypeScript
│   └── index.ts
└── utils/           # Utilidades
    ├── constants.ts
    ├── formatters.ts
    └── validators.ts
```

## 🎨 Configuración de Tailwind

El proyecto usa Tailwind CSS con una configuración personalizada que incluye:

- Paleta de colores personalizada (primary, secondary, success, danger, etc.)
- Utilidades extendidas de spacing y border-radius
- Clases de componentes predefinidas

### Colores Principales

```css
primary: #2563eb (azul)
secondary: #64748b (gris)
success: #10b981 (verde)
danger: #ef4444 (rojo)
warning: #f59e0b (amarillo)
```

### Componentes CSS Personalizados

```html
<!-- Botones -->
<button class="btn-primary">Primario</button>
<button class="btn-secondary">Secundario</button>
<button class="btn-danger">Peligro</button>

<!-- Card -->
<div class="card">Contenido</div>

<!-- Input -->
<input class="input-field" />
```

## 🔧 Instalación

```bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start

# Build para producción
npm run build

# Ejecutar tests
npm test

# Lint
npm run lint

# Format con Prettier
npm run format
```

## 📝 Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_NAME=Cantina Tita
```

## 🎯 Componentes Principales

### Button

```tsx
import Button from '@components/common/Button';

<Button variant="primary" onClick={handleClick}>
  Guardar
</Button>

<Button variant="danger" fullWidth isLoading={loading}>
  Eliminar
</Button>
```

### Input

```tsx
import Input from '@components/common/Input';

<Input
  label="Nombre"
  name="nombre"
  value={value}
  onChange={handleChange}
  error={error}
  required
/>
```

### LoadingSpinner

```tsx
import LoadingSpinner from '@components/common/LoadingSpinner';

<LoadingSpinner size="lg" text="Cargando..." />
```

## 🔐 Autenticación

```tsx
import { useAuth } from '@hooks/useAuth';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  const handleLogin = async () => {
    await login({ username, password });
  };

  return (
    <div>
      {isAuthenticated ? (
        <p>Hola {user?.username}</p>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
    </div>
  );
}
```

## 📡 Servicios de API

```tsx
import api from '@services/api';

// GET request
const data = await api.get('/clientes/');

// POST request
const newCliente = await api.post('/clientes/', { nombre, ruc });

// PUT request
const updated = await api.put('/clientes/1/', { nombre });

// DELETE request
await api.delete('/clientes/1/');
```

## 🎨 Uso de Tailwind

### Ejemplo de Card con Tailwind

```tsx
<div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
  <h3 className="text-lg font-semibold text-gray-900 mb-2">Título</h3>
  <p className="text-gray-600">Contenido</p>
</div>
```

### Grid Responsivo

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  {/* Contenido */}
</div>
```

### Flexbox

```tsx
<div className="flex items-center justify-between">
  <span>Izquierda</span>
  <span>Derecha</span>
</div>
```

## 🧪 Testing

```bash
# Ejecutar tests
npm test

# Con coverage
npm test -- --coverage
```

## 📦 Build para Producción

```bash
npm run build
```

Los archivos optimizados se generarán en la carpeta `build/`.

## 🚀 Despliegue

### Con Nginx

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    root /var/www/cantina-frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 📚 Documentación Adicional

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [React Router](https://reactrouter.com/)

## 🤝 Contribución

1. Crear branch desde `develop`
2. Hacer cambios
3. Ejecutar linter y tests
4. Crear Pull Request

## 📄 Licencia

Privado y Confidencial - Cantina Tita © 2026
