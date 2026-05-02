"""
Conftest de compatibilidad para backend/tests (suite legacy).

Este archivo se mantiene intencionalmente separado de backend/conftest.py para:
- no romper tests legacy que dependen de comportamientos/fixtures antiguas
- permitir migración gradual hacia fixtures canónicas en backend/conftest.py

Regla de mantenimiento:
- Tests nuevos deben preferir fixtures de backend/conftest.py.
- Cuando una fixture legacy quede sin uso, migrar y eliminar duplicación.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient


# ============================================================================
# FIXTURES DE AUTENTICACIÓN
# ============================================================================

@pytest.fixture
def cliente_test(db):
    """Crea un cliente de prueba para asociar con UsuariosPortal"""
    from apps.clientes.models import Clientes
    from apps.productos.models import ListasPrecios
    from apps.clientes.models import TiposCliente
    
    # Crear lista de precios si no existe
    lista, _ = ListasPrecios.objects.get_or_create(
        nombre_lista='General',
        defaults={'estado': True}
    )
    
    # Crear tipo de cliente si no existe
    tipo, _ = TiposCliente.objects.get_or_create(
        nombre_tipo='Regular',
        defaults={'estado': True}
    )
    
    return Clientes.objects.create(
        nombres='Cliente',
        apellidos='Test',
        ruc_ci='12345678',
        email='cliente@test.com',
        telefono='0981000000',
        estado=True,
        id_lista=lista,
        id_tipo_cliente=tipo
    )


@pytest.fixture
def usuario_portal_test(db, cliente_test):
    """Crea un usuario del portal con autenticación JWT"""
    from apps.usuarios.models import UsuariosPortal
    
    usuario = UsuariosPortal.objects.create(
        email='usuario@test.com',
        email_verificado=True,
        estado=True,
        id_cliente=cliente_test
    )
    usuario.set_password('testpass123')
    usuario.save()
    
    return usuario


@pytest.fixture
def usuario_portal_admin(db, cliente_test):
    """Crea un usuario admin del portal"""
    from apps.usuarios.models import UsuariosPortal
    from apps.clientes.models import Clientes
    from apps.productos.models import ListasPrecios
    from apps.clientes.models import TiposCliente
    
    # Crear cliente admin
    lista, _ = ListasPrecios.objects.get_or_create(
        nombre_lista='General',
        defaults={'estado': True}
    )
    tipo, _ = TiposCliente.objects.get_or_create(
        nombre_tipo='Administrador',
        defaults={'estado': True}
    )
    
    cliente_admin = Clientes.objects.create(
        nombres='Admin',
        apellidos='System',
        ruc_ci='00000000',
        email='admin@test.com',
        telefono='0981999999',
        estado=True,
        id_lista=lista,
        id_tipo_cliente=tipo
    )
    
    usuario = UsuariosPortal.objects.create(
        email='admin@test.com',
        email_verificado=True,
        estado=True,
        id_cliente=cliente_admin
    )
    usuario.set_password('adminpass123')
    usuario.save()
    
    return usuario


@pytest.fixture
def api_client():
    """Cliente API sin autenticación"""
    return APIClient()


@pytest.fixture
def authenticated_client(db, usuario_portal_test):
    """Cliente API autenticado con JWT token"""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    client = APIClient()
    
    # Crear token JWT
    refresh = RefreshToken()
    refresh['user_id'] = usuario_portal_test.id_usuario_portal
    refresh['email'] = usuario_portal_test.email
    
    # Autenticar usando el token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    return client


@pytest.fixture
def admin_client(db, usuario_portal_admin):
    """Cliente API autenticado como admin"""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    client = APIClient()
    
    # Crear token JWT
    refresh = RefreshToken()
    refresh['user_id'] = usuario_portal_admin.id_usuario_portal
    refresh['email'] = usuario_portal_admin.email
    refresh['is_admin'] = True
    
    # Autenticar usando el token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    return client


# ============================================================================
# FIXTURES DE MODELOS BASE - PRODUCTOS
# ============================================================================

@pytest.fixture
def categoria_test(db):
    """Categoría de productos de prueba"""
    from apps.productos.models import Categorias
    
    return Categorias.objects.create(
        nombre_categoria='Bebidas',
        descripcion='Bebidas y refrescos',
        estado=True
    )


@pytest.fixture
def unidad_medida_test(db):
    """Unidad de medida de prueba"""
    from apps.productos.models import UnidadesMedida
    
    return UnidadesMedida.objects.create(
        nombre_unidad='Unidad',
        abreviatura='Un',
        estado=True
    )


@pytest.fixture
def impuesto_test(db):
    """Impuesto IVA 10%"""
    from apps.contabilidad.models import Impuestos
    
    return Impuestos.objects.create(
        nombre_impuesto='IVA 10%',
        porcentaje=Decimal('10.00'),
        estado=True
    )


@pytest.fixture
def producto_test(db, categoria_test, unidad_medida_test, impuesto_test):
    """Producto de prueba"""
    from apps.productos.models import Productos
    
    return Productos.objects.create(
        descripcion='Coca Cola 500ml',
        codigo_barra='7891234567890',
        precio_compra=Decimal('5000.00'),
        precio_venta=Decimal('8000.00'),
        stock_actual=Decimal('100.00'),
        stock_minimo=Decimal('10.00'),
        id_categoria=categoria_test,
        id_unidad_medida=unidad_medida_test,
        id_impuesto=impuesto_test,
        estado=True
    )


@pytest.fixture
def producto_sin_stock(db, categoria_test, unidad_medida_test, impuesto_test):
    """Producto sin stock disponible"""
    from apps.productos.models import Productos
    
    return Productos.objects.create(
        descripcion='Producto Agotado',
        codigo_barra='7891111111111',
        precio_compra=Decimal('3000.00'),
        precio_venta=Decimal('5000.00'),
        stock_actual=Decimal('0.00'),
        stock_minimo=Decimal('5.00'),
        id_categoria=categoria_test,
        id_unidad_medida=unidad_medida_test,
        id_impuesto=impuesto_test,
        estado=True
    )


# ============================================================================
# FIXTURES DE MODELOS BASE - VENTAS/COMPRAS
# ============================================================================

@pytest.fixture
def medio_pago_efectivo(db):
    """Medio de pago en efectivo"""
    from apps.core.models import MediosPago
    
    return MediosPago.objects.create(
        descripcion='Efectivo',
        estado=True,
        genera_comision=False,
        requiere_cuenta=False
    )


@pytest.fixture
def medio_pago_tarjeta(db):
    """Medio de pago con tarjeta"""
    from apps.core.models import MediosPago
    
    return MediosPago.objects.create(
        descripcion='Tarjeta Débito',
        estado=True,
        genera_comision=True,
        requiere_cuenta=True
    )


@pytest.fixture
def empleado_test(db):
    """Empleado para asociar con ventas/compras"""
    from apps.usuarios.models import Empleados, Roles
    
    # Crear rol si no existe
    rol, _ = Roles.objects.get_or_create(
        nombre_rol='Cajero',
        defaults={'descripcion': 'Cajero de ventas', 'estado': True}
    )
    
    return Empleados.objects.create(
        nombre='Empleado',
        apellido='Test',
        usuario='emp_test',
        contrasena_hash='hashed_password',
        fecha_ingreso=timezone.now(),
        email='empleado@test.com',
        estado='Activo',
        id_rol=rol
    )


@pytest.fixture
def proveedor_test(db):
    """Proveedor de prueba"""
    from apps.compras.models import Proveedores
    
    return Proveedores.objects.create(
        ruc='80012345-6',
        razon_social='Distribuidora Test S.A.',
        telefono='021-555-0000',
        email='ventas@distribuidora.com',
        direccion='Av. Principal 123',
        ciudad='Asunción',
        estado=True
    )


# ============================================================================
# FIXTURES DE MODELOS BASE - NOTIFICACIONES
# ============================================================================

@pytest.fixture
def plantilla_email_test(db):
    """Plantilla de email de prueba"""
    from apps.notificaciones.models import PlantillasEmail
    
    return PlantillasEmail.objects.create(
        nombre='Bienvenida',
        categoria='transaccional',
        asunto='Bienvenido a Cantina Tita',
        cuerpo_html='<p>Bienvenido {{nombre}}</p>',
        cuerpo_texto='Bienvenido {{nombre}}',
        estado=True
    )


# ============================================================================
# FIXTURES DE DJANGO USER (para tests que requieren User model)
# ============================================================================

@pytest.fixture
def django_user(db):
    """Usuario de Django para tests legacy"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='user@test.com'
    )


@pytest.fixture
def django_admin_user(db):
    """Usuario admin de Django para tests legacy"""
    return User.objects.create_superuser(
        username='admin',
        password='adminpass123',
        email='admin@test.com'
    )

