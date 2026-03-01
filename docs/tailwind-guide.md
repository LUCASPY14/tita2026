# Guía de Componentes - Tailwind CSS

## 🎨 Componentes Disponibles

### Button Component

```tsx
import Button from '@components/common/Button';

// Variantes
<Button variant="primary">Primario</Button>
<Button variant="secondary">Secundario</Button>
<Button variant="success">Éxito</Button>
<Button variant="danger">Peligro</Button>
<Button variant="outline">Outline</Button>

// Full Width
<Button variant="primary" fullWidth>Ancho Completo</Button>

// Loading State
<Button variant="primary" isLoading>
  Guardando...
</Button>

// Disabled
<Button variant="primary" disabled>
  Deshabilitado
</Button>
```

### Input Component

```tsx
import Input from '@components/common/Input';

// Input básico
<Input
  label="Nombre"
  name="nombre"
  value={value}
  onChange={handleChange}
/>

// Required
<Input
  label="Email"
  name="email"
  type="email"
  required
/>

// Con error
<Input
  label="Teléfono"
  name="telefono"
  error="El teléfono es inválido"
/>

// Con helper text
<Input
  label="RUC"
  name="ruc"
  helperText="Formato: 12345678-9"
/>
```

### LoadingSpinner Component

```tsx
import LoadingSpinner from '@components/common/LoadingSpinner';

// Tamaños
<LoadingSpinner size="sm" />
<LoadingSpinner size="md" />
<LoadingSpinner size="lg" />

// Con texto
<LoadingSpinner size="lg" text="Cargando datos..." />

// Color personalizado
<LoadingSpinner color="text-green-600" />
```

## 📐 Layouts con Tailwind

### Container
```tsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  {/* Contenido centrado con padding responsivo */}
</div>
```

### Grid Responsivo
```tsx
// 1 columna en mobile, 2 en tablet, 4 en desktop
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
  <div>Item 4</div>
</div>
```

### Flexbox
```tsx
// Centrado vertical y horizontal
<div className="flex items-center justify-center min-h-screen">
  <div>Contenido centrado</div>
</div>

// Space between
<div className="flex items-center justify-between">
  <span>Izquierda</span>
  <span>Derecha</span>
</div>

// Stack vertical
<div className="flex flex-col gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

## 🎴 Cards

### Card Básico
```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h3 className="text-lg font-semibold mb-2">Título</h3>
  <p className="text-gray-600">Contenido</p>
</div>
```

### Card con Hover
```tsx
<div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
  <h3 className="text-lg font-semibold mb-2">Título</h3>
  <p className="text-gray-600">Contenido</p>
</div>
```

### Card de Estadística
```tsx
<div className="bg-white rounded-xl shadow-md p-6">
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-gray-600 text-sm font-medium">Ventas</h3>
    <svg className="w-6 h-6 text-primary-600">...</svg>
  </div>
  <p className="text-3xl font-bold text-primary-600 mb-1">Gs. 1.500.000</p>
  <p className="text-gray-500 text-sm">Total del día</p>
</div>
```

## 📝 Formularios

### Form Layout
```tsx
<form onSubmit={handleSubmit} className="space-y-6">
  <Input label="Nombre" name="nombre" required />
  <Input label="Email" name="email" type="email" required />
  
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Input label="Teléfono" name="telefono" />
    <Input label="RUC" name="ruc" />
  </div>
  
  <Button type="submit" variant="primary" fullWidth>
    Guardar
  </Button>
</form>
```

## 🎨 Colores y Tipografía

### Textos
```tsx
// Tamaños
<p className="text-xs">Extra pequeño</p>
<p className="text-sm">Pequeño</p>
<p className="text-base">Normal</p>
<p className="text-lg">Grande</p>
<p className="text-xl">Extra grande</p>
<p className="text-2xl">2X grande</p>

// Pesos
<p className="font-light">Light</p>
<p className="font-normal">Normal</p>
<p className="font-medium">Medium</p>
<p className="font-semibold">Semibold</p>
<p className="font-bold">Bold</p>

// Colores
<p className="text-gray-900">Texto primario</p>
<p className="text-gray-600">Texto secundario</p>
<p className="text-primary-600">Texto primary</p>
<p className="text-red-600">Texto error</p>
```

### Backgrounds
```tsx
<div className="bg-white">Blanco</div>
<div className="bg-gray-50">Gris claro</div>
<div className="bg-primary-600">Primary</div>
<div className="bg-gradient-to-r from-primary-500 to-primary-700">Gradiente</div>
```

## 📊 Tablas

### Tabla Básica
```tsx
<div className="overflow-x-auto">
  <table className="min-w-full divide-y divide-gray-200">
    <thead className="bg-gray-50">
      <tr>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Nombre
        </th>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Email
        </th>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Acciones
        </th>
      </tr>
    </thead>
    <tbody className="bg-white divide-y divide-gray-200">
      <tr className="hover:bg-gray-50">
        <td className="px-6 py-4 whitespace-nowrap">Juan Pérez</td>
        <td className="px-6 py-4 whitespace-nowrap">juan@example.com</td>
        <td className="px-6 py-4 whitespace-nowrap">
          <button className="text-primary-600 hover:text-primary-900">
            Editar
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

## 🔔 Alerts y Notificaciones

### Alert Success
```tsx
<div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
  <p className="text-green-700">Operación exitosa!</p>
</div>
```

### Alert Error
```tsx
<div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
  <p className="text-red-700">Ha ocurrido un error</p>
</div>
```

### Alert Warning
```tsx
<div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
  <p className="text-yellow-700">Advertencia</p>
</div>
```

### Alert Info
```tsx
<div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
  <p className="text-blue-700">Información</p>
</div>
```

## 🎭 Estados y Transiciones

### Hover
```tsx
<button className="bg-primary-600 hover:bg-primary-700 transition-colors">
  Hover me
</button>
```

### Focus
```tsx
<input className="border focus:ring-2 focus:ring-primary-500 focus:border-primary-500" />
```

### Disabled
```tsx
<button className="bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
  Disabled
</button>
```

## 📱 Responsive Design

### Breakpoints Tailwind
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Ejemplo
```tsx
<div className="
  text-sm sm:text-base md:text-lg lg:text-xl
  p-4 sm:p-6 md:p-8
  grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4
">
  Contenido responsivo
</div>
```

## 🌙 Dark Mode (Preparado para futuro)

```tsx
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  Contenido que cambia con dark mode
</div>
```

## 💡 Tips y Mejores Prácticas

1. **Usa las clases de Tailwind directamente** - No crees CSS personalizado innecesario
2. **Aprovecha la composición** - Crea componentes reutilizables
3. **Usa `@apply` con moderación** - Solo para componentes muy repetidos
4. **Mantén la consistencia** - Usa las mismas clases para elementos similares
5. **Responsive first** - Piensa en mobile primero
6. **Usa las utilidades de Tailwind** - spacing, colors, shadows, etc.

## 🔗 Recursos

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Tailwind UI Components](https://tailwindui.com/)
- [Headless UI](https://headlessui.com/) - Componentes accesibles para Tailwind
