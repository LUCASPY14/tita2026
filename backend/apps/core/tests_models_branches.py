"""
Tests de ramas faltantes en core/models.py
Cubre branches en LegacyCompatCoreMixin._rewrite y LegacyCompatQuerySet.
"""

import pytest
from django.test import TestCase

# ──────────────────────────────────────────────────────────────────────────────
# LegacyCompatCoreMixin._rewrite  (branches 23->24, 24->23, 24->25, 32->33, 35->36)
# ──────────────────────────────────────────────────────────────────────────────


class LegacyCompatCoreMixinRewriteTest(TestCase):
    """Tests for LegacyCompatCoreMixin._rewrite resolver and map branches."""

    def setUp(self):
        from apps.core.models import LegacyCompatCoreMixin

        class TestMixin(LegacyCompatCoreMixin):
            LEGACY_FIELD_MAP = {
                "old_name": "new_name",  # normal mapping
                "dep_field": None,  # deprecated → skip
            }
            LEGACY_VALUE_RESOLVERS = {
                "old_name": lambda x: x.upper() if isinstance(x, str) else x,
                "other_resolver": lambda x: x,  # second resolver (for 24->23 branch)
            }

        self.Mixin = TestMixin

    def test_resolver_applied_when_key_present(self):
        """Branches 23->24 (loop body) and 24->25 (resolver applied) covered."""
        result = self.Mixin._rewrite({"old_name": "hello"})
        # Resolver uppercases the value; field is mapped from old_name → new_name
        self.assertEqual(result.get("new_name"), "HELLO")

    def test_resolver_loop_key_not_in_kwargs(self):
        """Branch 24->23: second resolver key not in kwargs → back to loop top."""
        # old_name IS in kwargs (24->25), other_resolver is NOT (24->23 loop back)
        result = self.Mixin._rewrite({"old_name": "test"})
        self.assertIn("new_name", result)

    def test_deprecated_field_is_skipped(self):
        """Branch 32->33: new_key is None → continue (deprecated field skipped)."""
        result = self.Mixin._rewrite({"dep_field": "val", "unrelated": "x"})
        self.assertNotIn("dep_field", result)
        self.assertNotIn(None, result)
        self.assertIn("unrelated", result)

    def test_mapping_target_not_in_kwargs(self):
        """Branch 35->36: new_key not yet in result_kwargs → field is mapped."""
        result = self.Mixin._rewrite({"old_name": "world"})
        # old_name should be mapped to new_name (resolver + field map)
        self.assertIn("new_name", result)
        self.assertEqual(result["new_name"], "WORLD")


# ──────────────────────────────────────────────────────────────────────────────
# LegacyCompatQuerySet.get_or_create and update_or_create branches
# branch 54->56: get_or_create WITHOUT defaults (False arm)
# branch 59->60: update_or_create WITH defaults (True arm)
# branch 59->61: update_or_create WITHOUT defaults (False arm)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class LegacyCompatQuerySetBranchesTest(TestCase):
    """Tests for LegacyCompatQuerySet branches using MediosPago model."""

    def test_get_or_create_without_defaults(self):
        """Branch 54->56: defaults=None → False arm → no rewrite of defaults."""
        from apps.core.models import MediosPago

        # Call WITHOUT defaults → takes False arm at 'if defaults:'
        mp, created = MediosPago.objects.get_or_create(descripcion="TestMedio_NoDefaults_Branch")
        self.assertIsNotNone(mp)
        mp.delete()

    def test_update_or_create_with_defaults(self):
        """Branch 59->60: defaults provided → True arm → defaults are rewritten."""
        from apps.core.models import MediosPago

        mp, created = MediosPago.objects.update_or_create(
            descripcion="TestMedio_WithDefaults_Branch",
            defaults={"genera_comision": False},
        )
        self.assertIsNotNone(mp)
        mp.delete()

    def test_update_or_create_without_defaults(self):
        """Branch 59->61: defaults=None → False arm in update_or_create."""
        from apps.core.models import MediosPago

        mp, created = MediosPago.objects.update_or_create(
            descripcion="TestMedio_NoDefaults_UpdCreate_Branch",
        )
        self.assertIsNotNone(mp)
        mp.delete()


@pytest.mark.django_db
class TarjetasCleanBranchesTest(TestCase):
    """
    Branch 158->-154: Tarjetas.clean() when id_hijo is falsy → exits without checking.
    Branch 158->160 + 164->-154: when id_hijo is set but no duplicate tarjeta → clean pass.
    Branch 158->160 + 164->165: when id_hijo is set AND duplicate exists → raises ValidationError.
    """

    def test_clean_no_hijo_exits_cleanly(self):
        """Branch 158->-154: id_hijo is None → if block skipped, clean() returns None."""
        from unittest.mock import MagicMock
        from apps.core.models import Tarjetas

        tarjeta = MagicMock(spec=Tarjetas)
        tarjeta.id_hijo = None
        # Call the unbound clean() with the mock
        result = Tarjetas.clean(tarjeta)
        self.assertIsNone(result)  # clean() with no hijo returns None

    def test_clean_with_id_hijo_no_duplicate_passes(self):
        """Branches 158->160 + 164->-154: id_hijo set, no other tarjeta → clean() passes."""
        from decimal import Decimal
        from apps.core.models import Tarjetas

        # Create a tarjeta (TarjetasManager auto-creates id_hijo)
        t1 = Tarjetas.objects.create(nro_tarjeta="br_clean_nodup_01")
        # calling clean() on t1: filter(id_hijo=t1.id_hijo).exclude(nro_tarjeta='br_clean_nodup_01')
        # → empty queryset → 164->-154 (exits without raising)
        result = t1.clean()
        self.assertIsNone(result)

    def test_clean_with_id_hijo_duplicate_raises(self):
        """Branches 158->160 + 164->165: id_hijo set, duplicate in DB → raises ValidationError."""
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        from apps.core.models import Tarjetas

        # Create T1 with auto-created id_hijo
        t1 = Tarjetas.objects.create(nro_tarjeta="br_clean_dup_01")
        # Build T2 as Python object (NOT saved) pointing to the SAME id_hijo
        t2 = Tarjetas(
            nro_tarjeta="br_clean_dup_02",
            id_hijo=t1.id_hijo,
            saldo_actual=Decimal("0"),
            estado="activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0"),
        )
        # clean() should raise because T1 already owns id_hijo
        with self.assertRaises(ValidationError):
            t2.clean()


@pytest.mark.django_db
class CargasSaldoFechaCargaDefaultBranchTest(TestCase):
    """
    Branch 241->242: CargasSaldoManager.create without fecha_carga → auto-sets tz.now().
    """

    def test_create_without_fecha_carga_sets_default(self):
        """Branch 241->242: fecha_carga absent → manager sets tz.now() automatically."""
        from decimal import Decimal
        from apps.core.models import CargasSaldo

        # CargasSaldo has nro_tarjeta nullable, so FK is not required
        carga = CargasSaldo.objects.create(
            monto_cargado=Decimal("5.00"),
            estado="pendiente",
            # NOT providing fecha_carga or fecha_creacion → triggers branch 241->242
        )
        self.assertIsNotNone(carga.fecha_carga)


@pytest.mark.django_db
class LimitesTransaccionBranchesTest(TestCase):
    """
    Branch 632->634: requiere_autorizacion when no LimitesTransaccion exists for rol.
    """

    def test_requiere_autorizacion_no_limite_returns_not_required(self):
        """Branch 632->634: obtener_limite returns None → returns no-restriction dict."""
        from apps.core.models import LimitesTransaccion
        from apps.usuarios.models import Roles
        from decimal import Decimal

        rol, _ = Roles.objects.get_or_create(nombre_rol="TestLimiteRol", defaults={"descripcion": "test"})
        # No LimitesTransaccion for this rol → obtener_limite returns None → 632->634
        result = LimitesTransaccion.requiere_autorizacion(rol, "venta_sin_limite", Decimal("100"))
        self.assertFalse(result["requiere"])
        self.assertIsNone(result["limite"])
