import django
import pytest
from django.conf import settings


@pytest.fixture
def usuario_admin(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="admin@test.com",
        password="test1234",
        nombre="Admin",
        apellido="Test",
        rol=Usuario.Rol.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def usuario_cajero(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="cajero@test.com",
        password="test1234",
        nombre="Cajero",
        apellido="Test",
        rol=Usuario.Rol.CAJERO,
    )


@pytest.fixture
def tipo_cliente(db):
    from apps.clientes.models import TipoCliente
    return TipoCliente.objects.create(nombre="Padre")


@pytest.fixture
def lista_precio(db):
    from apps.productos.models import ListaPrecio
    return ListaPrecio.objects.create(nombre="General", activo=True)


@pytest.fixture
def cliente(db, tipo_cliente, lista_precio):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        ruc_ci="1234567",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )


@pytest.fixture
def medio_pago_efectivo(db):
    from apps.core.models import MedioPago
    return MedioPago.objects.create(
        descripcion="Efectivo",
        activo=True,
    )


@pytest.fixture
def categoria(db):
    from apps.productos.models import Categoria
    return Categoria.objects.create(nombre="Bebidas", activo=True)


@pytest.fixture
def unidad_medida(db):
    from apps.productos.models import UnidadMedida
    return UnidadMedida.objects.create(nombre="Unidad", abreviatura="u")


@pytest.fixture
def producto(db, categoria, unidad_medida, lista_precio):
    from decimal import Decimal
    from apps.productos.models import Producto, PrecioPorLista
    p = Producto.objects.create(
        descripcion="Agua mineral",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=True,
        permite_stock_negativo=False,
        activo=True,
    )
    PrecioPorLista.objects.create(
        producto=p,
        lista=lista_precio,
        precio_unitario=Decimal("3000"),
    )
    return p


@pytest.fixture
def stock_producto(db, producto):
    from decimal import Decimal
    from apps.inventario.models import Stock
    return Stock.objects.create(producto=producto, cantidad=Decimal("50"))
