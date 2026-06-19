"""Tests para apps.compras.tasks — alertar_ordenes_compra_pendientes, alertar_compras_pendientes_pago."""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


@pytest.fixture
def proveedor(db):
    from apps.compras.models import Proveedor
    return Proveedor.objects.create(ruc="80001001-1", razon_social="Proveedor Task Test")


@pytest.fixture
def admin_user(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="admin_compras_tasks@test.com",
        password="test1234",
        nombre="Admin",
        apellido="Compras",
        rol=Usuario.Rol.ADMIN,
        is_active=True,
    )


@pytest.fixture
def orden_pendiente_vieja(db, proveedor, usuario_cajero):
    from apps.compras.models import OrdenCompra
    orden = OrdenCompra.objects.create(
        proveedor=proveedor,
        estado=OrdenCompra.Estado.PENDIENTE,
        tipo_pago=OrdenCompra.TipoPago.CONTADO,
        monto_total=Decimal("100000"),
        creado_por=usuario_cajero,
    )
    OrdenCompra.objects.filter(pk=orden.pk).update(
        fecha_creacion=timezone.now() - timedelta(hours=49)
    )
    return orden


@pytest.fixture
def orden_pendiente_reciente(db, proveedor, usuario_cajero):
    from apps.compras.models import OrdenCompra
    return OrdenCompra.objects.create(
        proveedor=proveedor,
        estado=OrdenCompra.Estado.PENDIENTE,
        tipo_pago=OrdenCompra.TipoPago.CONTADO,
        monto_total=Decimal("50000"),
        creado_por=usuario_cajero,
    )


@pytest.fixture
def compra_credito_vencida(db, proveedor, usuario_cajero):
    from apps.compras.models import Compra
    compra = Compra.objects.create(
        proveedor=proveedor,
        tipo_pago=Compra.TipoPago.CREDITO,
        estado_pago=Compra.EstadoPago.PENDIENTE,
        monto_total=Decimal("200000"),
        creado_por=usuario_cajero,
    )
    Compra.objects.filter(pk=compra.pk).update(
        fecha_creacion=timezone.now() - timedelta(days=8)
    )
    return compra


@pytest.fixture
def compra_credito_reciente(db, proveedor, usuario_cajero):
    from apps.compras.models import Compra
    return Compra.objects.create(
        proveedor=proveedor,
        tipo_pago=Compra.TipoPago.CREDITO,
        estado_pago=Compra.EstadoPago.PENDIENTE,
        monto_total=Decimal("150000"),
        creado_por=usuario_cajero,
    )


# ── alertar_ordenes_compra_pendientes ─────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarOrdenesPendientes:

    def test_sin_ordenes_retorna_cero(self, db):
        from apps.compras.tasks import alertar_ordenes_compra_pendientes
        result = alertar_ordenes_compra_pendientes()
        assert result == {"alertas_creadas": 0}

    def test_orden_reciente_no_genera_alerta(self, orden_pendiente_reciente, admin_user):
        from apps.compras.tasks import alertar_ordenes_compra_pendientes
        result = alertar_ordenes_compra_pendientes()
        assert result == {"alertas_creadas": 0}

    def test_orden_vieja_sin_admin_retorna_cero(self, orden_pendiente_vieja):
        from apps.compras.tasks import alertar_ordenes_compra_pendientes
        result = alertar_ordenes_compra_pendientes()
        assert result == {"alertas_creadas": 0}

    def test_orden_vieja_con_admin_crea_notificacion(self, orden_pendiente_vieja, admin_user):
        from apps.compras.tasks import alertar_ordenes_compra_pendientes
        from apps.notificaciones.models import Notificacion
        result = alertar_ordenes_compra_pendientes()
        assert result["alertas_creadas"] == 1
        notif = Notificacion.objects.filter(usuario=admin_user, tipo=Notificacion.Tipo.SISTEMA).first()
        assert notif is not None
        assert str(orden_pendiente_vieja.pk) in notif.mensaje

    def test_orden_aprobada_no_genera_alerta(self, db, proveedor, usuario_cajero, admin_user):
        from apps.compras.models import OrdenCompra
        from apps.compras.tasks import alertar_ordenes_compra_pendientes
        orden = OrdenCompra.objects.create(
            proveedor=proveedor,
            estado=OrdenCompra.Estado.APROBADA,
            tipo_pago=OrdenCompra.TipoPago.CONTADO,
            monto_total=Decimal("100000"),
            creado_por=usuario_cajero,
        )
        OrdenCompra.objects.filter(pk=orden.pk).update(
            fecha_creacion=timezone.now() - timedelta(hours=72)
        )
        result = alertar_ordenes_compra_pendientes()
        assert result == {"alertas_creadas": 0}

    def test_dos_admins_reciben_alerta_independiente(self, orden_pendiente_vieja, admin_user, db):
        from apps.usuarios.models import Usuario
        from apps.compras.tasks import alertar_ordenes_compra_pendientes
        admin2 = Usuario.objects.create_user(
            email="admin2_tasks@test.com", password="test1234",
            nombre="Admin2", apellido="Tasks",
            rol=Usuario.Rol.ADMIN, is_active=True,
        )
        result = alertar_ordenes_compra_pendientes()
        assert result["alertas_creadas"] == 2


# ── alertar_compras_pendientes_pago ───────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarComprasPendientesPago:

    def test_sin_compras_retorna_cero(self, db):
        from apps.compras.tasks import alertar_compras_pendientes_pago
        result = alertar_compras_pendientes_pago()
        assert result == {"alertas_creadas": 0}

    def test_compra_reciente_no_genera_alerta(self, compra_credito_reciente, admin_user):
        from apps.compras.tasks import alertar_compras_pendientes_pago
        result = alertar_compras_pendientes_pago()
        assert result == {"alertas_creadas": 0}

    def test_compra_vencida_sin_admin_retorna_cero(self, compra_credito_vencida):
        from apps.compras.tasks import alertar_compras_pendientes_pago
        result = alertar_compras_pendientes_pago()
        assert result == {"alertas_creadas": 0}

    def test_compra_vencida_con_admin_crea_notificacion(self, compra_credito_vencida, admin_user):
        from apps.compras.tasks import alertar_compras_pendientes_pago
        from apps.notificaciones.models import Notificacion
        result = alertar_compras_pendientes_pago()
        assert result["alertas_creadas"] == 1
        notif = Notificacion.objects.filter(usuario=admin_user, tipo=Notificacion.Tipo.SISTEMA).first()
        assert notif is not None
        assert str(compra_credito_vencida.pk) in notif.mensaje

    def test_compra_contado_no_genera_alerta(self, db, proveedor, usuario_cajero, admin_user):
        from apps.compras.models import Compra
        from apps.compras.tasks import alertar_compras_pendientes_pago
        compra = Compra.objects.create(
            proveedor=proveedor,
            tipo_pago=Compra.TipoPago.CONTADO,
            estado_pago=Compra.EstadoPago.PENDIENTE,
            monto_total=Decimal("100000"),
            creado_por=usuario_cajero,
        )
        Compra.objects.filter(pk=compra.pk).update(
            fecha_creacion=timezone.now() - timedelta(days=10)
        )
        result = alertar_compras_pendientes_pago()
        assert result == {"alertas_creadas": 0}

    def test_compra_credito_pagada_no_genera_alerta(self, db, proveedor, usuario_cajero, admin_user):
        from apps.compras.models import Compra
        from apps.compras.tasks import alertar_compras_pendientes_pago
        compra = Compra.objects.create(
            proveedor=proveedor,
            tipo_pago=Compra.TipoPago.CREDITO,
            estado_pago=Compra.EstadoPago.PAGADO,
            monto_total=Decimal("80000"),
            creado_por=usuario_cajero,
        )
        Compra.objects.filter(pk=compra.pk).update(
            fecha_creacion=timezone.now() - timedelta(days=10)
        )
        result = alertar_compras_pendientes_pago()
        assert result == {"alertas_creadas": 0}

    def test_notificacion_incluye_monto_y_proveedor(self, compra_credito_vencida, admin_user):
        from apps.compras.tasks import alertar_compras_pendientes_pago
        from apps.notificaciones.models import Notificacion
        alertar_compras_pendientes_pago()
        notif = Notificacion.objects.filter(usuario=admin_user).first()
        assert "Proveedor Task Test" in notif.mensaje
        assert "200.000" in notif.mensaje or "200,000" in notif.mensaje
