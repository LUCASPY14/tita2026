# Tests Pendientes - Compras ViewSet

## Estado Actual

**Estado de ejecución actual:** ✅ Suite activa y ejecutándose en CI  
**Tests deshabilitados por marca (`skip/xfail`):** 0  
**Observación:** este documento quedó como registro histórico del rewrite JWT ya completado.

---

## Problema

Similar a los tests de ventas, los tests de compras necesitan ser reescritos para usar:
- **UsuariosPortal** para autenticación
- **JWT tokens** para API authentication
- Permisos adecuados para operaciones de compras

---

## Tests Deshabilitados

### ProveedoresViewSet

#### 1. `test_list_proveedores_con_autenticacion`
**Propósito:** Listar proveedores con autenticación  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token válido

#### 2. `test_create_proveedor`
**Propósito:** Crear nuevo proveedor  
**Estado:** ❌ Deshabilitado  
**Requiere:** 
- JWT token con rol Admin
- Datos válidos de proveedor (RUC, razón social, etc.)

#### 3. `test_update_proveedor`
**Propósito:** Actualizar proveedor existente  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token + fixture de proveedor

#### 4. `test_cuenta_corriente_proveedor`
**Propósito:** Obtener estado de cuenta corriente  
**Estado:** ❌ Deshabilitado  
**Requiere:** 
- JWT token
- Proveedor con compras y pagos
- Custom action `/proveedores/{id}/cuenta_corriente/`

### ComprasViewSet

#### 5. `test_list_compras_con_autenticacion`
**Propósito:** Listar compras con autenticación  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token válido

#### 6. `test_create_compra`
**Propósito:** Crear nueva compra con detalles  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token con permisos de compras
- Fixtures: proveedor, producto, empleado
- Validación de cálculo de totales

#### 7. `test_create_compra_sin_detalles`
**Propósito:** Validar que compra sin detalles falla  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token + validación de errores

#### 8. `test_confirmar_compra`
**Propósito:** Confirmar compra y actualizar stock  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token con permisos
- Compra pendiente
- Validación de actualización de stock
- Custom action `/compras/{id}/confirmar/`

#### 9. `test_pendientes_action`
**Propósito:** Listar compras pendientes  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token
- Custom action `/compras/pendientes/`

#### 10. `test_calcular_totales_action`
**Propósito:** Calcular totales de compra  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token
- Custom action `/compras/calcular_totales/`

#### 11. `test_delete_compra_no_confirmada`
**Propósito:** Eliminar compra no confirmada  
**Estado:** ❌ Deshabilitado  
**Requiere:**
- JWT token con permisos de admin
- Validación de estado de compra

### DetallesCompraViewSet

#### 12. `test_list_detalles_con_autenticacion`
**Propósito:** Listar detalles de compra  
**Estado:** ❌ Deshabilitado  
**Requiere:** JWT token válido

---

## Fixtures Necesarios

### Autenticación
```python
@pytest.fixture
def jwt_token_admin(db):
    """Token JWT para administrador"""
    # Ver: backend/apps/ventas/tests/TODO_TESTS.md
    pass

@pytest.fixture
def jwt_token_comprador(db):
    """Token JWT para usuario con permisos de compras"""
    # Similar al admin pero con rol específico
    pass
```

### Datos de Compras
```python
@pytest.fixture
def proveedor_test(db):
    """Proveedor de prueba"""
    from apps.compras.models import Proveedores
    return Proveedores.objects.create(
        razon_social='Proveedor Test SA',
        ruc='80012345-1',
        telefono='021123456',
        email='proveedor@test.com',
        direccion='Asunción',
        estado=True
    )

@pytest.fixture
def producto_compra(db):
    """Producto para compras"""
    from apps.productos.models import Productos, Categorias
    from decimal import Decimal
    
    categoria = Categorias.objects.create(
        nombre='Insumos',
        activa=True
    )
    
    return Productos.objects.create(
        nombre='Insumo Test',
        codigo='INS001',
        precio_compra=Decimal('10000.00'),
        precio_venta=Decimal('15000.00'),
        stock_actual=50,
        id_categoria=categoria,
        activo=True
    )
```

---

## Prioridad de Reimplementación

### 🔴 ALTA (Core functionality)
1. `test_create_compra` - Funcionalidad crítica
2. `test_confirmar_compra` - Actualización de stock crítica
3. `test_create_proveedor` - Gestión de proveedores

### 🟡 MEDIA (Business logic)
4. `test_cuenta_corriente_proveedor` - Reporte financiero importante
5. `test_pendientes_action` - Gestión de compras pendientes
6. `test_list_compras_con_autenticacion` - Funcionalidad básica
7. `test_list_proveedores_con_autenticacion` - Funcionalidad básica

### 🟢 BAJA (Edge cases & validations)
8. `test_create_compra_sin_detalles` - Validación
9. `test_calcular_totales_action` - Helper action
10. `test_update_proveedor` - CRUD básico
11. `test_delete_compra_no_confirmada` - Permisos
12. `test_list_detalles_con_autenticacion` - Funcionalidad básica

---

## Estimación de Tiempo

- **Setup inicial (fixtures JWT + proveedores):** 45 minutos
- **Reimplementar tests ALTA prioridad:** 1.5 horas
- **Reimplementar tests MEDIA prioridad:** 1 hora
- **Reimplementar tests BAJA prioridad:** 45 minutos

**TOTAL:** ~3.5 horas

---

## Casos de Prueba Especiales

### Test de Confirmación de Compra
```python
def test_confirmar_compra(api_client_authenticated_admin, proveedor_test, producto_compra):
    """Test confirmar compra actualiza stock"""
    from apps.compras.models import Compras, DetallesCompra
    from decimal import Decimal
    
    # Stock inicial
    stock_inicial = producto_compra.stock_actual
    
    # Crear compra
    compra = Compras.objects.create(
        id_proveedor=proveedor_test,
        monto_total=Decimal('100000.00'),
        estado_pago='Pendiente'
    )
    
    DetallesCompra.objects.create(
        id_compra=compra,
        id_producto=producto_compra,
        cantidad=10,
        costo_unitario=Decimal('10000.00'),
        subtotal=Decimal('100000.00')
    )
    
    # Confirmar compra
    url = reverse('compras-confirmar', kwargs={'pk': compra.id_compra})
    response = api_client_authenticated_admin.post(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar stock actualizado
    producto_compra.refresh_from_db()
    assert producto_compra.stock_actual == stock_inicial + 10
```

---

## Referencias

- ComprasViewSet: `backend/apps/compras/views.py`
- CompraService: `backend/apps/compras/services.py`
- Proveedores model: `backend/apps/compras/models.py`
- Sistema de autenticación: Ver `backend/apps/ventas/tests/TODO_TESTS.md`

---

**Fecha:** 2026-04-21  
**Autor:** Sistema de testing  
**Próxima revisión:** Sprint 5
