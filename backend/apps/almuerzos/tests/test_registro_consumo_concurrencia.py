"""
Test de concurrencia: dos POSTs casi simultáneos de registro-consumo para el
mismo hijo (RFID rebotando, o un reintento de la cola offline del Service
Worker cruzándose con un escaneo nuevo) no deben poder cobrar dos "primeros"
almuerzos el mismo día — ver perform_create() en views.py, que ahora toma un
select_for_update() sobre el hijo antes de contar los registros del día.

Requiere DB real (transacciones de verdad para que el lock sea efectivo).
Marcado con @pytest.mark.stress para excluirlo de CI rápido:
    pytest -m "not stress"
"""

import threading
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def hijo_concurrencia(db, cliente):
    from apps.clientes.models import Grado, Hijo
    grado, _ = Grado.objects.get_or_create(
        nombre="Grado Concurrencia", defaults={"nivel": 1, "orden": 1, "activo": True},
    )
    return Hijo.objects.create(
        nombre="Carla", apellido="Concurrencia",
        cliente_responsable=cliente, grado=grado, activo=True,
    )


@pytest.fixture
def tarjeta_concurrencia(db, hijo_concurrencia):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALMZ-CONC01", hijo=hijo_concurrencia,
        saldo_actual=Decimal("50000"), estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def precio_concurrencia(db):
    from apps.almuerzos.models import PrecioAlmuerzo
    return PrecioAlmuerzo.objects.create(
        precio_unitario=Decimal("15000"),
        fecha_inicio_vigencia=date.today() - timedelta(days=30),
        activo=True,
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.stress
class TestRegistroConsumoConcurrencia:

    def test_dos_posts_simultaneos_solo_uno_cobra(
        self, usuario_cajero, hijo_concurrencia, tarjeta_concurrencia, precio_concurrencia,
    ):
        """Sin el lock por alumno, ambos requests podían leer '0 registros
        hoy' antes de que el otro confirmara, y los dos terminaban con
        ya_cobrado=True — doble cobro real en vez de 1 cobrado + 1 repite."""
        results: list[dict] = []
        lock = threading.Lock()

        def registrar():
            client = APIClient()
            client.force_authenticate(user=usuario_cajero)
            resp = client.post(
                "/api/v1/almuerzos/registros-consumo/",
                {
                    "hijo": hijo_concurrencia.pk,
                    "fecha_consumo": str(date.today()),
                    "nro_tarjeta": tarjeta_concurrencia.pk,
                },
                format="json",
            )
            with lock:
                results.append({"status": resp.status_code, "data": resp.data})

        # El registro exitoso encola un WhatsApp vía Celery (transaction.on_commit
        # + .delay()) — bajo transaction=True eso corre de verdad al cerrar la
        # request, y necesita un broker real. Se mockea para que el test valide
        # solo el comportamiento de concurrencia, no la entrega de notificaciones.
        with patch("apps.notificaciones.tasks.enviar_whatsapp_cliente.delay"):
            threads = [threading.Thread(target=registrar) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)

        assert len(results) == 2, "Algún hilo no terminó en 10s"

        creados = [r for r in results if r["status"] == 201]
        assert len(creados) == 2, f"Se esperaban 2 registros creados: {results}"

        cobrados = [r for r in creados if r["data"]["ya_cobrado"] is True]
        assert len(cobrados) == 1, (
            f"Debía cobrarse exactamente 1 almuerzo (el otro es 'repite' gratis), "
            f"pero cobraron {len(cobrados)}: {results}"
        )
