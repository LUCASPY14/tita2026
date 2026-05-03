"""
Tests para apps.almuerzos.tasks — generar_cuentas_mensuales y alertar_cuentas_vencidas

Nota: las tareas usan imports lazy (dentro del body de la función),
por lo que el patch target es el módulo fuente, no apps.almuerzos.tasks.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase


class GenerarCuentasMensualesTest(TestCase):
    """Tests para la tarea generar_cuentas_mensuales."""

    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    @patch("apps.almuerzos.models.SuscripcionesAlmuerzo")
    def test_crea_cuentas_para_suscripciones_activas(self, mock_suscr, mock_cuentas):
        """Crea una CuentasAlmuerzoMensual por cada suscripción activa sin cuenta aún."""
        from apps.almuerzos.tasks import generar_cuentas_mensuales

        mock_hijo = MagicMock()
        mock_suscripcion = MagicMock()
        mock_suscripcion.id_hijo = mock_hijo
        mock_suscripcion.id_hijo_id = 1

        mock_suscr.objects.filter.return_value.select_related.return_value = [mock_suscripcion]
        mock_cuentas.objects.filter.return_value.exists.return_value = False

        result = generar_cuentas_mensuales()

        mock_cuentas.objects.create.assert_called_once()
        self.assertEqual(result["creadas"], 1)

    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    @patch("apps.almuerzos.models.SuscripcionesAlmuerzo")
    def test_omite_cuentas_ya_existentes(self, mock_suscr, mock_cuentas):
        """No crea duplicados si ya existe la cuenta del mes."""
        from apps.almuerzos.tasks import generar_cuentas_mensuales

        mock_suscr.objects.filter.return_value.select_related.return_value = [MagicMock()]
        mock_cuentas.objects.filter.return_value.exists.return_value = True  # ya existe

        result = generar_cuentas_mensuales()

        mock_cuentas.objects.create.assert_not_called()
        self.assertEqual(result["creadas"], 0)

    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    @patch("apps.almuerzos.models.SuscripcionesAlmuerzo")
    def test_no_falla_si_no_hay_suscripciones(self, mock_suscr, mock_cuentas):
        """Retorna creadas=0 si no hay suscripciones activas."""
        from apps.almuerzos.tasks import generar_cuentas_mensuales

        mock_suscr.objects.filter.return_value.select_related.return_value = []

        result = generar_cuentas_mensuales()

        self.assertEqual(result["creadas"], 0)
        self.assertIn("mes", result)
        self.assertIn("anio", result)

    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    @patch("apps.almuerzos.models.SuscripcionesAlmuerzo")
    def test_maneja_error_individual_sin_abortar(self, mock_suscr, mock_cuentas):
        """Un error en una suscripción no aborta el bucle completo."""
        from apps.almuerzos.tasks import generar_cuentas_mensuales

        suscr1, suscr2 = MagicMock(), MagicMock()
        suscr1.id_hijo_id, suscr2.id_hijo_id = 1, 2

        mock_suscr.objects.filter.return_value.select_related.return_value = [suscr1, suscr2]
        mock_cuentas.objects.filter.return_value.exists.return_value = False
        mock_cuentas.objects.create.side_effect = [Exception("DB error"), None]

        result = generar_cuentas_mensuales()

        # Solo 1 fue exitoso (el segundo)
        self.assertEqual(result["creadas"], 1)


class AlertarCuentasVencidasTest(TestCase):
    """Tests para la tarea alertar_cuentas_vencidas."""

    @patch("apps.notificaciones.models.AlertasSistema")
    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    def test_crea_alertas_para_cuentas_pendientes_de_meses_anteriores(self, mock_cuentas, mock_alertas):
        """Crea AlertasSistema para cada cuenta vencida sin alerta previa."""
        from decimal import Decimal

        from apps.almuerzos.tasks import alertar_cuentas_vencidas

        cuenta = MagicMock()
        cuenta.pk = 10
        cuenta.mes = 1
        cuenta.anio = 2026
        cuenta.monto_total = Decimal("5000")
        cuenta.monto_pagado = Decimal("0")

        mock_cuentas.objects.filter.return_value.exclude.return_value.select_related.return_value = [cuenta]
        mock_alertas.objects.filter.return_value.exists.return_value = False

        result = alertar_cuentas_vencidas()

        mock_alertas.objects.create.assert_called_once()
        self.assertEqual(result["alertas"], 1)

    @patch("apps.notificaciones.models.AlertasSistema")
    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    def test_no_duplica_alertas_existentes(self, mock_cuentas, mock_alertas):
        """No crea alerta si ya existe una para esa cuenta."""
        from apps.almuerzos.tasks import alertar_cuentas_vencidas

        cuenta = MagicMock(pk=10)
        mock_cuentas.objects.filter.return_value.exclude.return_value.select_related.return_value = [cuenta]
        mock_alertas.objects.filter.return_value.exists.return_value = True  # ya existe

        result = alertar_cuentas_vencidas()

        mock_alertas.objects.create.assert_not_called()
        self.assertEqual(result["alertas"], 0)

    @patch("apps.notificaciones.models.AlertasSistema")
    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    def test_retorna_alertas_cero_si_no_hay_cuentas_vencidas(self, mock_cuentas, mock_alertas):
        """Retorna alertas=0 si no hay cuentas pendientes de meses anteriores."""
        from apps.almuerzos.tasks import alertar_cuentas_vencidas

        mock_cuentas.objects.filter.return_value.exclude.return_value.select_related.return_value = []

        result = alertar_cuentas_vencidas()

        self.assertEqual(result["alertas"], 0)

    @patch("apps.notificaciones.models.AlertasSistema")
    @patch("apps.almuerzos.models.CuentasAlmuerzoMensual")
    def test_maneja_error_individual_sin_abortar(self, mock_cuentas, mock_alertas):
        """Un error en una cuenta no aborta el bucle completo."""
        from apps.almuerzos.tasks import alertar_cuentas_vencidas

        c1, c2 = MagicMock(pk=1), MagicMock(pk=2)
        mock_cuentas.objects.filter.return_value.exclude.return_value.select_related.return_value = [c1, c2]
        mock_alertas.objects.filter.return_value.exists.return_value = False
        mock_alertas.objects.create.side_effect = [Exception("DB error"), None]

        result = alertar_cuentas_vencidas()

        self.assertEqual(result["alertas"], 1)
