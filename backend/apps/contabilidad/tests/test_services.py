"""
Tests de FacturacionService — cubre los caminos críticos de facturación.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db
class TestEmitirFactura:

    def test_emitir_factura_basica(self, cliente):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        factura = FacturacionService.emitir_factura(
            cliente=cliente,
            nro_factura="001-001-0000001",
            monto_total=Decimal("50000"),
            iva_10=Decimal("4545"),
        )

        assert factura.pk is not None
        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.nro_factura == "001-001-0000001"
        assert factura.monto_total == Decimal("50000")
        assert factura.cliente == cliente

    def test_factura_duplicada_falla(self, cliente):
        from apps.contabilidad.services import FacturacionService

        FacturacionService.emitir_factura(
            cliente=cliente,
            nro_factura="001-001-0000002",
            monto_total=Decimal("30000"),
        )

        with pytest.raises(ValidationError, match="ya fue registrada"):
            FacturacionService.emitir_factura(
                cliente=cliente,
                nro_factura="001-001-0000002",
                monto_total=Decimal("30000"),
            )


@pytest.mark.django_db
class TestAnularFactura:

    def _emitir(self, cliente, nro="001-001-0009001"):
        from apps.contabilidad.services import FacturacionService
        return FacturacionService.emitir_factura(
            cliente=cliente,
            nro_factura=nro,
            monto_total=Decimal("20000"),
        )

    def test_anular_factura(self, cliente):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        factura = self._emitir(cliente)
        anulada = FacturacionService.anular_factura(factura)

        assert anulada.estado == Factura.Estado.ANULADA

    def test_anular_dos_veces_falla(self, cliente):
        from apps.contabilidad.services import FacturacionService

        factura = self._emitir(cliente, nro="001-001-0009002")
        FacturacionService.anular_factura(factura)

        with pytest.raises(ValidationError, match="ya esta anulada"):
            FacturacionService.anular_factura(factura)


@pytest.mark.django_db
class TestEmitirParaOrigen:

    def test_emitir_para_carga_saldo(self, carga_saldo):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        factura = FacturacionService.emitir_para_origen(
            tipo="CARGA_SALDO",
            origen_id=carga_saldo.pk,
            nro_factura="001-001-0001001",
        )

        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == carga_saldo.monto_cargado

        carga_saldo.refresh_from_db()
        assert carga_saldo.factura_id == factura.pk

    def test_carga_no_confirmada_falla(self, tarjeta, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService
        from apps.core.models import CargaSaldo

        carga = CargaSaldo.objects.create(
            tarjeta=tarjeta,
            cliente_origen=cliente,
            monto_cargado=Decimal("10000"),
            estado=CargaSaldo.Estado.PENDIENTE,
            responsable=usuario_cajero,
        )

        with pytest.raises(ValidationError, match="Solo se pueden facturar cargas confirmadas"):
            FacturacionService.emitir_para_origen(
                tipo="CARGA_SALDO",
                origen_id=carga.pk,
                nro_factura="001-001-0001002",
            )

    def test_carga_ya_facturada_falla(self, carga_saldo):
        from apps.contabilidad.services import FacturacionService

        FacturacionService.emitir_para_origen(
            tipo="CARGA_SALDO",
            origen_id=carga_saldo.pk,
            nro_factura="001-001-0001003",
        )

        with pytest.raises(ValidationError, match="ya tiene factura emitida"):
            FacturacionService.emitir_para_origen(
                tipo="CARGA_SALDO",
                origen_id=carga_saldo.pk,
                nro_factura="001-001-0001004",
            )

    def test_emitir_para_pago_almuerzo(self, pago_almuerzo):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        factura = FacturacionService.emitir_para_origen(
            tipo="PAGO_ALMUERZO",
            origen_id=pago_almuerzo.pk,
            nro_factura="001-001-0002001",
        )

        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == pago_almuerzo.monto

        pago_almuerzo.refresh_from_db()
        assert pago_almuerzo.factura_id == factura.pk

    def test_pago_ya_facturado_falla(self, pago_almuerzo):
        from apps.contabilidad.services import FacturacionService

        FacturacionService.emitir_para_origen(
            tipo="PAGO_ALMUERZO",
            origen_id=pago_almuerzo.pk,
            nro_factura="001-001-0002002",
        )

        with pytest.raises(ValidationError, match="ya tiene factura emitida"):
            FacturacionService.emitir_para_origen(
                tipo="PAGO_ALMUERZO",
                origen_id=pago_almuerzo.pk,
                nro_factura="001-001-0002003",
            )

    def test_tipo_desconocido_falla(self, cliente):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="Tipo desconocido"):
            FacturacionService.emitir_para_origen(
                tipo="INVALIDO",
                origen_id=1,
                nro_factura="001-001-0099999",
            )


@pytest.mark.django_db
class TestGetPendientes:

    def test_retorna_carga_sin_factura(self, carga_saldo):
        from apps.contabilidad.services import FacturacionService

        resultado = FacturacionService.get_pendientes()

        ids_cargas = list(resultado["cargas"].values_list("pk", flat=True))
        assert carga_saldo.pk in ids_cargas

    def test_retorna_pago_almuerzo_sin_factura(self, pago_almuerzo):
        from apps.contabilidad.services import FacturacionService

        resultado = FacturacionService.get_pendientes()

        ids_pagos = list(resultado["pagos"].values_list("pk", flat=True))
        assert pago_almuerzo.pk in ids_pagos

    def test_excluye_carga_ya_facturada(self, carga_saldo):
        from apps.contabilidad.services import FacturacionService

        FacturacionService.emitir_para_origen(
            tipo="CARGA_SALDO",
            origen_id=carga_saldo.pk,
            nro_factura="001-001-0005001",
        )

        resultado = FacturacionService.get_pendientes()
        ids_cargas = list(resultado["cargas"].values_list("pk", flat=True))
        assert carga_saldo.pk not in ids_cargas
