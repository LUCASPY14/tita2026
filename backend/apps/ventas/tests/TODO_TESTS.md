# Tests Pendientes - Ventas ViewSet

## Estado Actual

**Tests activos:** 2/11 (18%)  
**Tests deshabilitados:** 9/11 (82%)  
**Razón:** Incompatibilidad con el sistema de autenticación real

---

## Problema

Los tests originales fueron creados asumiendo que `Empleados` tiene métodos de autenticación (`set_password()`, `force_authenticate()`), pero el sistema real usa:

- **UsuariosPortal** para autenticación del portal web
- **JWT tokens** para API authentication
- **Empleados** solo almacena datos de empleados, no credenciales

---

## Tests Deshabilitados

### 1. `test_list_ventas_con_autenticacion`
**Propósito:** Verificar que usuarios autenticados pueden listar ventas  
**Estado:** ❌ Deshabilitado  
**Requiere:** 
- JWT token válido
- Usuario con permisos de lectura de ventas

### 2. `test_create_venta_efectivo`
**Propósito:** Crear venta con pago en efectivo  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token válido
- Usuario con rol Cajero o Admin
- Fixtures: cliente, producto, medio_pago_efectivo

### 3. `test_create_venta_tarjeta`
**Propósito:** Crear venta con pago por tarjeta  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token válido
- Fixtures: cliente, producto, tarjeta con saldo

### 4. `test_create_venta_sin_detalles`
**Propósito:** Validar que venta sin detalles falla  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token + validación de detalles vacíos

### 5. `test_create_venta_stock_insuficiente`
**Propósito:** Validar que venta con stock insuficiente falla  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token + validación de stock

### 6. `test_sin_facturar_action`
**Propósito:** Listar ventas sin facturar  
**Estado:** ❌ Deshabilitado  
**Requiere:** 
- JWT token
- Acceso a custom action `/ventas/sin_facturar/`

### 7. `test_update_venta_no_permitido`
**Propósito:** Verificar que UPDATE no está permitido  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token + validación de método HTTP

### 8. `test_delete_venta_solo_admin`
**Propósito:** Verificar que solo admin puede eliminar  
**Estado:** ❌ Deshabilitado  
**Requiere:** 
- JWT token con rol Admin
- Verificación de permisos

### 9. `test_list_detalles_con_autenticacion`
**Propósito:** Listar detalles de venta con auth  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token válido

---

## Cómo Reimplementar

### Paso 1: Crear Fixture de Autenticación JWT

```python
@pytest.fixture
def jwt_token_admin(db):
    """Crear token JWT para admin"""
    from apps.usuarios.models import UsuariosPortal
    from apps.clientes.models import Clientes
    from rest_framework_simplejwt.tokens import RefreshToken
    
    # Crear cliente
    cliente = Clientes.objects.create(
        nombre='Admin',
        apellido='Test',
        email='admin@test.com',
        telefono='0981000000',
        ruc_ci='12345678'
    )
    
    # Crear usuario portal
    usuario = UsuariosPortal.objects.create(
        email='admin@test.com',
        id_cliente=cliente,
        estado=True
    )
    usuario.set_password('admin123')
    usuario.save()
    
    # Generar JWT token
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)


@pytest.fixture
def api_client_authenticated_admin(api_client, jwt_token_admin):
    """Cliente API con autenticación de admin"""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_token_admin}')
    return api_client
```

### Paso 2: Actualizar Tests

```python
def test_list_ventas_con_autenticacion(self, api_client_authenticated_admin):
    """Test listar ventas con autenticación"""
    url = reverse('ventas-list')
    response = api_client_authenticated_admin.get(url)
    assert response.status_code == status.HTTP_200_OK
```

### Paso 3: Agregar Fixtures de Datos

```python
@pytest.fixture
def producto_test(db):
    """Crear producto de prueba"""
    from apps.productos.models import Productos, Categorias
    from decimal import Decimal
    
    categoria = Categorias.objects.create(
        nombre='Bebidas',
        descripcion='Bebidas test',
        activa=True
    )
    
    return Productos.objects.create(
        nombre='Coca Cola',
        codigo='COCA001',
        precio_venta=Decimal('5000.00'),
        precio_compra=Decimal('3000.00'),
        stock_actual=100,
        stock_minimo=10,
        id_categoria=categoria,
        activo=True
    )
```

---

## Prioridad de Reimplementación

### 🔴 ALTA (Core functionality)
1. `test_create_venta_efectivo` - Funcionalidad crítica
2. `test_create_venta_tarjeta` - Funcionalidad crítica
3. `test_create_venta_stock_insuficiente` - Validación importante

### 🟡 MEDIA (Business logic)
4. `test_sin_facturar_action` - Reporte importante
5. `test_list_ventas_con_autenticacion` - Funcionalidad básica
6. `test_list_detalles_con_autenticacion` - Funcionalidad básica

### 🟢 BAJA (Edge cases)
7. `test_create_venta_sin_detalles` - Edge case
8. `test_update_venta_no_permitido` - Validación HTTP
9. `test_delete_venta_solo_admin` - Permisos

---

## Estimación de Tiempo

- **Setup inicial (fixtures JWT):** 30 minutos
- **Reimplementar tests ALTA prioridad:** 1 hora
- **Reimplementar tests MEDIA prioridad:** 45 minutos
- **Reimplementar tests BAJA prioridad:** 30 minutos

**TOTAL:** ~2.5 horas

---

## Referencias

- Modelo UsuariosPortal: `backend/apps/usuarios/models.py` línea 460+
- Autenticación JWT: `backend/backend/urls.py` línea 107-109
- VentasViewSet: `backend/apps/ventas/views.py`
- Ejemplo de auth en tests: Buscar en `apps/usuarios/tests/` (si existe)

---

**Fecha:** 2026-04-21  
**Autor:** Sistema de testing  
**Próxima revisión:** Sprint 5
