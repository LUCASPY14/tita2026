# 🎯 PLAN DE DESARROLLO FRONTEND - Sistema Cantina Tita

**Fecha:** 2 de Marzo, 2026  
**Stack:** React 18 + TypeScript + Tailwind CSS + Django REST API  
**Estado Backend:** ✅ 100% Completo - Production Ready  

---

## 📊 ESTADO ACTUAL DEL FRONTEND

### ✅ Ya Implementado (Base)
- [x] Estructura de proyecto React + TypeScript
- [x] Configuración Tailwind CSS personalizada
- [x] Cliente Axios con interceptores JWT
- [x] Configuración ESLint + Prettier
- [x] React Router v6
- [x] Zustand para estado global
- [x] Componentes básicos: Button, Input, LoadingSpinner
- [x] Páginas básicas: Login, Dashboard

### ❌ Pendiente de Implementar (90%)
- [ ] Sistema de autenticación completo
- [ ] Módulos de negocio (12 módulos)
- [ ] Componentes UI profesionales
- [ ] Servicios API completos
- [ ] Estado global estructurado
- [ ] Formularios con validación
- [ ] Dashboards y reportes
- [ ] Notificaciones en tiempo real
- [ ] Sistema de permisos por rol
- [ ] Tests E2E con Cypress

---

## 🏗️ ARQUITECTURA PROPUESTA

### Principios de Diseño
1. **Separation of Concerns** - Separación clara entre presentación, lógica y datos
2. **DRY (Don't Repeat Yourself)** - Reutilización máxima de componentes
3. **SOLID** - Componentes con responsabilidad única
4. **Type Safety** - TypeScript estricto en todo el proyecto
5. **Performance First** - Code splitting, lazy loading, memoization

### Patrones Utilizados
- **Container/Presenter Pattern** - Separación entre lógica y presentación
- **Custom Hooks Pattern** - Lógica reutilizable
- **Compound Components** - Componentes complejos composables
- **Provider Pattern** - Contextos y estado global
- **Service Layer** - Abstracción de API calls

---

## 📦 MÓDULOS A IMPLEMENTAR (Prioridad)

### 🔐 Fase 1: Autenticación y Base (CRÍTICO)
**Prioridad:** MÁXIMA  
**Tiempo estimado:** 2-3 días  

#### 1.1 Sistema de Autenticación
- [x] Login básico (ya existe)
- [ ] Login con validación completa
- [ ] Recuperación de contraseña
- [ ] Cambio de contraseña
- [ ] Refresh token automático
- [ ] Logout y limpieza de sesión
- [ ] Manejo de sesiones expiradas

#### 1.2 Protección de Rutas
- [ ] ProtectedRoute mejorado
- [ ] Redirección por rol
- [ ] Guard de permisos por módulo
- [ ] Middleware de autorización

#### 1.3 Layout Principal
- [ ] Sidebar con navegación
- [ ] Header con usuario y notificaciones
- [ ] Breadcrumbs dinámicos
- [ ] Footer
- [ ] Responsive design completo

---

### 💳 Fase 2: Módulo de Recargas (CORE BUSINESS)
**Prioridad:** ALTA  
**Tiempo estimado:** 3-4 días  

#### 2.1 Gestión de Tarjetas
**Endpoints Backend:** `/api/v1/tarjetas/`

**Componentes:**
- [ ] `<TarjetasList />` - Lista de tarjetas con búsqueda
- [ ] `<TarjetaCard />` - Card de tarjeta individual
- [ ] `<TarjetaForm />` - Formulario crear/editar tarjeta
- [ ] `<TarjetaStats />` - Estadísticas de tarjeta
- [ ] `<SaldoDisplay />` - Visualización de saldo

**Funcionalidades:**
- Listar todas las tarjetas (paginado)
- Buscar por número de tarjeta / hijo
- Filtrar por estado (Activa/Inactiva/Bloqueada)
- Ver detalle de tarjeta
- Ver historial de consumos
- Ver historial de recargas
- Activar/Desactivar tarjeta
- Bloquear tarjeta temporalmente

#### 2.2 Sistema de Recargas
**Endpoints Backend:** `/api/v1/cargas-saldo/`

**Componentes:**
- [ ] `<RecargaModal />` - Modal para nueva recarga
- [ ] `<MetodoPagoSelector />` - Selector de método de pago
- [ ] `<RecargaForm />` - Formulario de recarga
- [ ] `<RecargasList />` - Historial de recargas
- [ ] `<RecargaStatus />` - Estado de recarga
- [ ] `<ComisionCalculator />` - Calculadora de comisión

**Métodos de Pago (9 opciones):**
1. [ ] Efectivo (sin comisión)
2. [ ] Tarjeta POS (3.4% comisión)
3. [ ] Transferencia Bancaria (validación manual)
4. [ ] Bancard Online (3.4% comisión)
5. [ ] Débito automático
6. [ ] Giro Tigo
7. [ ] Giro Personal
8. [ ] Billetera Móvil (MóvilPY)
9. [ ] QR Bancario

**Flujos Especiales:**
- [ ] **Efectivo:** Registro directo → Completada
- [ ] **Bancard:** Init → Payment URL → Webhook → Completada
- [ ] **Transferencia:** Generar referencia → Upload comprobante → Validación → Aprobación
- [ ] **POS:** Registro con comisión → Terminal confirmation → Completada

#### 2.3 Validación de Recargas
**Componentes:**
- [ ] `<RecargasPendientesList />` - Lista de pendientes validación
- [ ] `<ValidacionForm />` - Validar transferencia
- [ ] `<AprobacionSupervisor />` - Aprobación supervisor (>₲500K)
- [ ] `<ComprobanteViewer />` - Visor de comprobantes

---

### 🛒 Fase 3: Punto de Venta (POS)
**Prioridad:** ALTA  
**Tiempo estimado:** 4-5 días  

#### 3.1 Interfaz de Venta
**Endpoints Backend:** `/api/v1/ventas/`, `/api/v1/productos/`

**Componentes:**
- [ ] `<POSLayout />` - Layout especial para POS
- [ ] `<ProductoCatalog />` - Catálogo de productos
- [ ] `<ProductoCard />` - Card de producto
- [ ] `<CarritoCompra />` - Carrito de compras
- [ ] `<TotalCalculator />` - Calculadora de total
- [ ] `<MetodoPagoVenta />` - Selector método pago venta
- [ ] `<CobrarModal />` - Modal de cobro
- [ ] `<TicketPrint />` - Vista de impresión ticket

**Funcionalidades:**
- Buscar productos por nombre/código
- Agregar productos al carrito
- Modificar cantidades
- Aplicar descuentos
- Calcular total con impuestos
- Cobro múltiple (efectivo + tarjeta)
- Generar ticket venta
- Imprimir ticket
- Registrar venta

#### 3.2 Consumo con Tarjeta
**Componentes:**
- [ ] `<TarjetaScanInput />` - Input escaneo tarjeta
- [ ] `<SaldoVerificacion />` - Verificar saldo disponible
- [ ] `<ConsumoConfirmation />` - Confirmar consumo
- [ ] `<ConsumoReceipt />` - Comprobante consumo

**Flujo:**
1. Escanear tarjeta
2. Verificar saldo
3. Agregar productos
4. Confirmar consumo
5. Actualizar saldo
6. Generar comprobante

---

### 👥 Fase 4: Gestión de Clientes e Hijos
**Prioridad:** MEDIA  
**Tiempo estimado:** 2-3 días  

#### 4.1 Clientes
**Endpoints Backend:** `/api/v1/clientes/`

**Componentes:**
- [ ] `<ClientesList />` - Lista de clientes
- [ ] `<ClienteForm />` - Formulario cliente
- [ ] `<ClienteProfile />` - Perfil de cliente
- [ ] `<ClienteStats />` - Estadísticas cliente

**Funcionalidades:**
- CRUD completo de clientes
- Búsqueda y filtros
- Ver historial de compras
- Ver tarjetas asociadas
- Gestionar límite de crédito
- Activar/Desactivar cliente

#### 4.2 Hijos (Estudiantes)
**Endpoints Backend:** `/api/v1/hijos/`

**Componentes:**
- [ ] `<HijosList />` - Lista de hijos
- [ ] `<HijoForm />` - Formulario hijo
- [ ] `<HijoCard />` - Card de hijo
- [ ] `<RestriccionesForm />` - Restricciones alimentarias

**Funcionalidades:**
- CRUD completo de hijos
- Asignar tarjeta al hijo
- Configurar restricciones
- Ver consumos del hijo
- Foto de perfil

---

### 📦 Fase 5: Gestión de Productos e Inventario
**Prioridad:** MEDIA  
**Tiempo estimado:** 3-4 días  

#### 5.1 Productos
**Endpoints Backend:** `/api/v1/productos/`

**Componentes:**
- [ ] `<ProductosList />` - Lista de productos
- [ ] `<ProductoForm />` - Formulario producto
- [ ] `<ProductoCard />` - Card de producto
- [ ] `<CategoriaSelector />` - Selector categorías
- [ ] `<PreciosPorLista />` - Precios por lista

**Funcionalidades:**
- CRUD completo de productos
- Gestión de categorías
- Múltiples listas de precios
- Upload de imágenes
- Estado activo/inactivo
- SKU y código de barras

#### 5.2 Inventario
**Endpoints Backend:** `/api/v1/inventario/`

**Componentes:**
- [ ] `<InventarioList />` - Lista de stock
- [ ] `<StockCard />` - Card de stock
- [ ] `<AjusteInventarioForm />` - Ajustes de inventario
- [ ] `<AlertasStock />` - Alertas stock bajo
- [ ] `<StockHistory />` - Historial movimientos

**Funcionalidades:**
- Ver stock actual
- Alertas de stock bajo
- Ajustes de inventario
- Transferencias entre almacenes
- Historial de movimientos

---

### 🍽️ Fase 6: Gestión de Almuerzos (Menú Diario)
**Prioridad:** MEDIA  
**Tiempo estimado:** 2-3 días  

#### 6.1 Menús
**Endpoints Backend:** `/api/v1/menus/`

**Componentes:**
- [ ] `<MenuDiarioList />` - Lista de menús
- [ ] `<MenuForm />` - Formulario menú
- [ ] `<MenuCard />` - Card de menú del día
- [ ] `<PlatosSelector />` - Selector de platos
- [ ] `<MenuCalendar />` - Calendario de menús

**Funcionalidades:**
- Crear menú diario
- Programar menús semanales
- Duplicar menú
- Ver menús históricos
- Activar/Desactivar menú

#### 6.2 Pedidos de Almuerzos
**Endpoints Backend:** `/api/v1/pedidos-almuerzo/`

**Componentes:**
- [ ] `<PedidoAlmuerzoForm />` - Formulario pedido
- [ ] `<PedidosList />` - Lista de pedidos
- [ ] `<PedidosReporte />` - Reporte consolidado

**Funcionalidades:**
- Registrar pedidos
- Ver pedidos del día
- Marcar como entregado
- Reporte de pedidos por menú

---

### 📊 Fase 7: Reportes y Dashboards
**Prioridad:** MEDIA  
**Tiempo estimado:** 4-5 días  

#### 7.1 Dashboard Principal
**Endpoints Backend:** `/api/v1/reportes/dashboard/`

**Componentes:**
- [ ] `<DashboardLayout />` - Layout del dashboard
- [ ] `<KPICard />` - Card de KPI
- [ ] `<ChartVentas />` - Gráfico de ventas
- [ ] `<ChartRecargas />` - Gráfico de recargas
- [ ] `<TopProductos />` - Top productos
- [ ] `<AlertasWidget />` - Widget de alertas

**KPIs (8 principales):**
1. Ventas del día
2. Cantidad de ventas
3. Recargas del día
4. Cantidad de recargas
5. Tarjetas activas
6. Productos bajo stock
7. Ticket promedio
8. Saldo total tarjetas

#### 7.2 Reportes
**Endpoints Backend:** `/api/v1/reportes/`

**Componentes:**
- [ ] `<ReporteVentas />` - Reporte de ventas
- [ ] `<ReporteRecargas />` - Reporte de recargas
- [ ] `<ReporteFinanciero />` - Reporte financiero
- [ ] `<ReporteProductos />` - Reporte productos
- [ ] `<ReporteTarjetas />` - Reporte tarjetas
- [ ] `<FiltrosReporte />` - Filtros de reportes
- [ ] `<ExportButton />` - Exportar Excel/PDF

**Tipos de Reportes:**
1. Ventas (por fecha, método pago, empleado)
2. Recargas (por fecha, método pago, estado)
3. Top productos más vendidos
4. Consumos por tarjeta
5. Financiero consolidado
6. Proyecciones fin de mes

---

### 🔔 Fase 8: Sistema de Notificaciones
**Prioridad:** BAJA  
**Tiempo estimado:** 2-3 días  

#### 8.1 Notificaciones en Tiempo Real
**Tecnología:** WebSockets / Server-Sent Events

**Componentes:**
- [ ] `<NotificationBell />` - Campana de notificaciones
- [ ] `<NotificationList />` - Lista de notificaciones
- [ ] `<NotificationItem />` - Item de notificación
- [ ] `<NotificationSettings />` - Configuración

**Tipos de Notificaciones:**
- Saldo bajo en tarjeta
- Recarga completada
- Recarga pendiente validación
- Stock bajo producto
- Vencimiento tarjeta
- Consumo realizado

---

### 🛠️ Fase 9: Administración
**Prioridad:** BAJA  
**Tiempo estimado:** 3-4 días  

#### 9.1 Usuarios y Empleados
**Endpoints Backend:** `/api/v1/usuarios/`, `/api/v1/empleados/`

**Componentes:**
- [ ] `<UsuariosList />` - Lista de usuarios
- [ ] `<UsuarioForm />` - Formulario usuario
- [ ] `<EmpleadosList />` - Lista de empleados
- [ ] `<RolesManager />` - Gestión de roles
- [ ] `<PermisosMatrix />` - Matriz de permisos

#### 9.2 Configuración del Sistema
**Endpoints Backend:** `/api/v1/configuracion/`

**Componentes:**
- [ ] `<ConfiguracionGeneral />` - Config general
- [ ] `<ConfiguracionPagos />` - Config pagos
- [ ] `<ConfiguracionNotificaciones />` - Config notificaciones
- [ ] `<LogsViewer />` - Visor de logs

---

## 🎨 SISTEMA DE DISEÑO

### Componentes UI Base (Atomic Design)

#### Atoms
- [ ] `<Button />` - Variantes: primary, secondary, danger, success
- [ ] `<Input />` - Text, number, email, password
- [ ] `<Select />` - Dropdown select
- [ ] `<Checkbox />` - Checkbox con label
- [ ] `<Radio />` - Radio button
- [ ] `<Switch />` - Toggle switch
- [ ] `<Badge />` - Badge de estado
- [ ] `<Avatar />` - Avatar de usuario
- [ ] `<Icon />` - Iconos (Heroicons/Lucide)
- [ ] `<Spinner />` - Loading spinner

#### Molecules
- [ ] `<FormField />` - Input con label y error
- [ ] `<SearchBar />` - Barra de búsqueda
- [ ] `<Pagination />` - Paginación
- [ ] `<DatePicker />` - Selector de fecha
- [ ] `<FilePicker />` - Selector de archivos
- [ ] `<Card />` - Card básica
- [ ] `<Alert />` - Alertas (success, error, warning)
- [ ] `<Toast />` - Notificación toast
- [ ] `<Modal />` - Modal base
- [ ] `<Dropdown />` - Dropdown menu

#### Organisms
- [ ] `<Table />` - Tabla con sorting, filtros, paginación
- [ ] `<Form />` - Formulario con validación
- [ ] `<Sidebar />` - Sidebar de navegación
- [ ] `<Header />` - Header con usuario
- [ ] `<EmptyState />` - Estado vacío
- [ ] `<ErrorBoundary />` - Manejo de errores

### Paleta de Colores
```css
primary: #2563eb      /* Azul principal */
secondary: #64748b    /* Gris secundario */
success: #10b981      /* Verde éxito */
danger: #ef4444       /* Rojo error */
warning: #f59e0b      /* Amarillo advertencia */
info: #3b82f6         /* Azul info */
```

---

## 🔧 SERVICIOS API

### Estructura de Servicio
```typescript
// services/tarjetas.service.ts
class TarjetasService {
  async getAll(params?: QueryParams): Promise<TarjetasResponse>
  async getById(id: string): Promise<Tarjeta>
  async create(data: TarjetaCreate): Promise<Tarjeta>
  async update(id: string, data: TarjetaUpdate): Promise<Tarjeta>
  async delete(id: string): Promise<void>
  async activate(id: string): Promise<Tarjeta>
  async deactivate(id: string): Promise<Tarjeta>
}
```

### Servicios a Crear
- [ ] `tarjetas.service.ts` - Gestión de tarjetas
- [ ] `recargas.service.ts` - Gestión de recargas
- [ ] `ventas.service.ts` - Punto de venta
- [ ] `productos.service.ts` - Gestión de productos
- [ ] `inventario.service.ts` - Gestión de inventario
- [ ] `clientes.service.ts` - Gestión de clientes
- [ ] `hijos.service.ts` - Gestión de hijos
- [ ] `almuerzos.service.ts` - Gestión de almuerzos
- [ ] `reportes.service.ts` - Reportes
- [ ] `usuarios.service.ts` - Gestión de usuarios
- [ ] `notificaciones.service.ts` - Notificaciones

---

## 📦 ESTADO GLOBAL (Zustand)

### Stores a Crear
```typescript
// store/authStore.ts
interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (credentials) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

// store/cartStore.ts
interface CartStore {
  items: CartItem[]
  total: number
  addItem: (item) => void
  removeItem: (id) => void
  updateQuantity: (id, quantity) => void
  clear: () => void
}

// store/notificationStore.ts
interface NotificationStore {
  notifications: Notification[]
  unreadCount: number
  addNotification: (notification) => void
  markAsRead: (id) => void
  clearAll: () => void
}
```

---

## 🧪 TESTING

### Unit Tests (Jest + React Testing Library)
- [ ] Tests de componentes
- [ ] Tests de hooks
- [ ] Tests de servicios
- [ ] Tests de utilidades

### Integration Tests
- [ ] Flujo de login
- [ ] Flujo de recarga
- [ ] Flujo de venta
- [ ] Flujo de validación

### E2E Tests (Cypress)
- [ ] Flujo completo de usuario
- [ ] Navegación entre módulos
- [ ] CRUD operations
- [ ] Validaciones de formularios

---

## 📋 CHECKLIST DE DESARROLLO

### Configuración Inicial
- [ ] Actualizar dependencias npm
- [ ] Configurar variables de entorno
- [ ] Configurar ruta API backend
- [ ] Configurar Tailwind con diseño custom

### Desarrollo
- [ ] Implementar sistema de autenticación
- [ ] Crear componentes UI base
- [ ] Implementar módulo de recargas
- [ ] Implementar punto de venta
- [ ] Implementar gestión de clientes
- [ ] Implementar gestión de productos
- [ ] Implementar reportes
- [ ] Implementar notificaciones

### Testing
- [ ] Unit tests (80%+ cobertura)
- [ ] Integration tests
- [ ] E2E tests críticos
- [ ] Tests de performance

### Optimización
- [ ] Code splitting
- [ ] Lazy loading de rutas
- [ ] Memoization de componentes
- [ ] Optimización de imágenes
- [ ] Service Worker (PWA)

### Deployment
- [ ] Build de producción
- [ ] Optimización bundle size
- [ ] Configurar nginx
- [ ] Configurar SSL
- [ ] Deploy a servidor

---

## 🚀 PRÓXIMOS PASOS INMEDIATOS

### Prioridad 1 (HOY)
1. ✅ Crear este plan de desarrollo
2. [ ] Actualizar dependencias npm
3. [ ] Crear componentes UI base (Button, Input, Card, Modal)
4. [ ] Implementar layout principal (Sidebar + Header)
5. [ ] Mejorar sistema de autenticación

### Prioridad 2 (MAÑANA)
1. [ ] Implementar servicio de tarjetas
2. [ ] Crear componentes de tarjetas
3. [ ] Implementar lista de tarjetas
4. [ ] Implementar detalle de tarjeta

### Prioridad 3 (SIGUIENTE)
1. [ ] Implementar servicio de recargas
2. [ ] Crear modal de recarga
3. [ ] Implementar selector de método de pago
4. [ ] Implementar flujo completo de recarga efectivo

---

## 📊 ESTIMACIÓN DE TIEMPO

| Fase | Días | Prioridad |
|------|------|-----------|
| Fase 1: Autenticación y Base | 2-3 | CRÍTICO |
| Fase 2: Módulo de Recargas | 3-4 | ALTA |
| Fase 3: Punto de Venta | 4-5 | ALTA |
| Fase 4: Clientes e Hijos | 2-3 | MEDIA |
| Fase 5: Productos e Inventario | 3-4 | MEDIA |
| Fase 6: Almuerzos | 2-3 | MEDIA |
| Fase 7: Reportes y Dashboards | 4-5 | MEDIA |
| Fase 8: Notificaciones | 2-3 | BAJA |
| Fase 9: Administración | 3-4 | BAJA |
| **TOTAL** | **25-34 días** | |

---

## ✅ ENTREGABLES

1. **Aplicación frontend funcional** con todos los módulos
2. **Componentes UI reutilizables** (30+ componentes)
3. **Servicios API** completos (11 servicios)
4. **Tests automatizados** (80%+ cobertura)
5. **Documentación técnica** para desarrolladores
6. **Manual de usuario** para operadores
7. **Guía de deployment** para producción

---

**Nota:** Este plan es flexible y se ajustará según las prioridades del negocio y feedback del cliente.
