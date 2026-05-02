"""
Configuración base de pytest para todo el backend.

Este conftest es la capa canónica para fixtures compartidas usadas por:
- tests de apps (backend/apps/**)
- tests legacy de backend/tests cuando no redefinen fixture local

Nota sobre estabilidad:
- backend/tests/conftest.py existe para compatibilidad legacy y puede
  sobreescribir fixtures con el mismo nombre en ese subárbol.
- Mantener las nuevas fixtures aquí reduce divergencias y flaky tests.
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
def authenticated_client(db, empleado_test):
    """Cliente API autenticado con JWT token (empleado)"""
    from django.contrib.auth.models import User
    from rest_framework_simplejwt.tokens import RefreshToken
    
    client = APIClient()
    
    # Crear User de Django para el empleado
    django_user, _ = User.objects.get_or_create(
        username=empleado_test.usuario,
        defaults={
            'first_name': empleado_test.nombre,
            'last_name': empleado_test.apellido,
            'email': empleado_test.email or '',
            'is_active': empleado_test.estado,
        }
    )
    
    # Generar token JWT
    refresh = RefreshToken.for_user(django_user)
    refresh['id_empleado'] = empleado_test.id_empleado
    refresh['usuario'] = empleado_test.usuario
    refresh['id_rol'] = empleado_test.id_rol.id_rol if empleado_test.id_rol else None
    refresh['nombre_completo'] = f'{empleado_test.nombre} {empleado_test.apellido}'
    
    # Autenticar usando el token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    return client


@pytest.fixture
def admin_client(db):
    """Cliente API autenticado como admin (empleado con rol Admin)"""
    from django.contrib.auth.models import User
    from rest_framework_simplejwt.tokens import RefreshToken
    from apps.usuarios.models import Empleados, Roles
    from django.utils import timezone
    
    client = APIClient()
    
    # Crear rol Admin
    rol_admin, _ = Roles.objects.get_or_create(
        nombre_rol='Admin',
        defaults={'descripcion': 'Administrador del sistema'}
    )
    
    # Crear empleado admin
    empleado_admin, _ = Empleados.objects.get_or_create(
        usuario='admin_test',
        defaults={
            'nombre': 'Admin',
            'apellido': 'Test',
            'email': 'admin@test.com',
            'fecha_ingreso': timezone.now(),
            'estado': True,
            'id_rol': rol_admin,
            'contrasena_hash': ''
        }
    )
    
    # Crear User de Django
    django_user, _ = User.objects.get_or_create(
        username=empleado_admin.usuario,
        defaults={
            'first_name': empleado_admin.nombre,
            'last_name': empleado_admin.apellido,
            'email': empleado_admin.email or '',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    # Generar token JWT
    refresh = RefreshToken.for_user(django_user)
    refresh['id_empleado'] = empleado_admin.id_empleado
    refresh['usuario'] = empleado_admin.usuario
    refresh['id_rol'] = rol_admin.id_rol
    refresh['nombre_completo'] = f'{empleado_admin.nombre} {empleado_admin.apellido}'
    
    # Autenticar usando el token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    return client


# ============================================================================
# FIXTURES DE MODELOS BASE - PRODUCTOS
# ============================================================================


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
        nombre='Unidad',
        abreviatura='Un',
        estado=True
    )


@pytest.fixture
def impuesto_test(db):
    """Impuesto IVA 10%"""
    from apps.contabilidad.models import Impuestos
    from django.utils import timezone
    
    return Impuestos.objects.create(
        nombre_impuesto='IVA 10%',
        porcentaje=Decimal('10.00'),
        vigente_desde=timezone.now().date(),
        estado=True
    )


@pytest.fixture
def producto_test(db, categoria_test, unidad_medida_test, impuesto_test):
    """Producto de prueba con stock y precio"""
    from apps.productos.models import Productos, PreciosPorLista, ListasPrecios
    from apps.inventario.models import StockUnico
    
    producto = Productos.objects.create(
        descripcion='Coca Cola 500ml',
        codigo_barra='7891234567890',
        stock_minimo=Decimal('10.00'),
        id_categoria=categoria_test,
        id_unidad_medida=unidad_medida_test,
        id_impuesto=impuesto_test,
        estado=True,
        requiere_stock=True
    )
    
    # Crear stock
    StockUnico.objects.create(
        id_producto=producto,
        cantidad=Decimal('100.00')
    )
    
    # Crear precio en lista por defecto
    lista_default, _ = ListasPrecios.objects.get_or_create(
        nombre_lista='Lista General',
        defaults={'estado': True}
    )
    PreciosPorLista.objects.create(
        id_producto=producto,
        id_lista=lista_default,
        precio_unitario=Decimal('8000.00')
    )
    
    return producto


@pytest.fixture
def producto_sin_stock(db, categoria_test, unidad_medida_test, impuesto_test):
    """Producto sin stock disponible"""
    from apps.productos.models import Productos, PreciosPorLista, ListasPrecios
    from apps.inventario.models import StockUnico
    
    producto = Productos.objects.create(
        descripcion='Producto Agotado',
        codigo_barra='7891111111111',
        stock_minimo=Decimal('5.00'),
        id_categoria=categoria_test,
        id_unidad_medida=unidad_medida_test,
        id_impuesto=impuesto_test,
        estado=True,
        requiere_stock=True
    )
    
    # Crear stock en cero
    StockUnico.objects.create(
        id_producto=producto,
        cantidad=Decimal('0.00')
    )
    
    # Crear precio
    lista_default, _ = ListasPrecios.objects.get_or_create(
        nombre_lista='Lista General',
        defaults={'estado': True}
    )
    PreciosPorLista.objects.create(
        id_producto=producto,
        id_lista=lista_default,
        precio_unitario=Decimal('5000.00')
    )
    
    return producto


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
        requiere_validacion=False
    )


@pytest.fixture
def medio_pago_tarjeta(db):
    """Medio de pago con tarjeta"""
    from apps.core.models import MediosPago
    
    return MediosPago.objects.create(
        descripcion='Tarjeta Débito',
        estado=True,
        genera_comision=True,
        requiere_validacion=True
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
        estado=True,  # Boolean, not string
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
