"""
Tests de cobertura de ramas para usuarios/models.py.
Cubre los helpers _resolve_usuario_from_empleado, _resolve_cliente_from_empleado,
el mixin LegacyCompatMixin, y las ramas en los __str__ referidos por el informe.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

import pytest

from apps.usuarios.models import (
    LegacyCompatMixin,
    _resolve_usuario_from_empleado,
)

# ──────────────────────────────────────────────────────────────────────────────
# _resolve_usuario_from_empleado
# ──────────────────────────────────────────────────────────────────────────────


class ResolveUsuarioFromEmpleadoTest(TestCase):
    """
    Tests para _resolve_usuario_from_empleado.
    Missing lines 13, 16 correspond to the two branches inside this function.
    """

    def test_none_returns_none(self):
        """Line 13: value is None → returns None"""
        result = _resolve_usuario_from_empleado(None)
        self.assertIsNone(result)

    def test_value_with_usuario_attribute_returns_usuario(self):
        """Line 16: value has 'usuario' attr → returns value.usuario"""
        mock_empleado = MagicMock()
        mock_empleado.usuario = "juan_test"
        result = _resolve_usuario_from_empleado(mock_empleado)
        self.assertEqual(result, "juan_test")

    def test_plain_value_returned_as_is(self):
        """Line 18: value without 'usuario' attr → returns value unchanged"""
        plain_value = "some_username"
        result = _resolve_usuario_from_empleado(plain_value)
        self.assertEqual(result, plain_value)


# ──────────────────────────────────────────────────────────────────────────────
# LegacyCompatMixin._rewrite_legacy_kwargs
# ──────────────────────────────────────────────────────────────────────────────


class LegacyCompatMixinTest(TestCase):
    """
    Tests for LegacyCompatMixin branches.
    Lines 39->42, 43->51 relate to the resolver and mapped-to-None paths.
    """

    def setUp(self):
        class SampleMixin(LegacyCompatMixin):
            LEGACY_FIELD_MAP = {
                "old_field": "new_field",
                "ignored_field": None,
                "id_empleado": "usuario",
            }
            LEGACY_VALUE_RESOLVERS = {
                "id_empleado": _resolve_usuario_from_empleado,
            }

        self.Mixin = SampleMixin

    def test_mapped_field_is_rewritten(self):
        """Normal field mapping: old_field → new_field"""
        result = self.Mixin._rewrite_legacy_kwargs({"old_field": "value123"})
        self.assertIn("new_field", result)
        self.assertEqual(result["new_field"], "value123")

    def test_none_mapped_field_is_ignored(self):
        """Line 39->42: mapped=None means skip the field entirely"""
        result = self.Mixin._rewrite_legacy_kwargs({"ignored_field": "whatever"})
        self.assertNotIn("ignored_field", result)
        self.assertNotIn(None, result)

    def test_resolver_is_applied(self):
        """Line 43->51: resolver transforms the value"""
        mock_emp = MagicMock()
        mock_emp.usuario = "resolved_user"
        result = self.Mixin._rewrite_legacy_kwargs({"id_empleado": mock_emp})
        self.assertIn("usuario", result)
        self.assertEqual(result["usuario"], "resolved_user")

    def test_field_with_lookup_suffix(self):
        """Field with __ suffix is rewritten correctly"""
        result = self.Mixin._rewrite_legacy_kwargs({"old_field__exact": "value"})
        self.assertIn("new_field__exact", result)

    def test_unknown_field_passes_through(self):
        """Fields not in LEGACY_FIELD_MAP pass through unchanged"""
        result = self.Mixin._rewrite_legacy_kwargs({"unknown_field": "val"})
        self.assertIn("unknown_field", result)


# ──────────────────────────────────────────────────────────────────────────────
# Model __str__ methods — ensure each is called at least once
# ──────────────────────────────────────────────────────────────────────────────


class ModelStrMethodsTest(TestCase):
    """
    Ensure the __str__ methods of models that show up as missing lines
    are reached during tests. Each __str__ returns '{ClassName} #{pk}'.
    """

    @pytest.mark.django_db
    def test_roles_str(self):
        from apps.usuarios.models import Roles

        rol = Roles.objects.create(nombre_rol="TestRolStr", descripcion="test")
        self.assertIn("Roles", str(rol))
        rol.delete()

    @pytest.mark.django_db
    def test_empleados_str(self):
        from django.utils import timezone

        from apps.usuarios.models import Empleados, Roles

        rol = Roles.objects.create(nombre_rol="TestRolEmpl", descripcion="t")
        emp = Empleados.objects.create(
            nombre="Test",
            apellido="Str",
            usuario="test_str_user_unique99",
            fecha_ingreso=timezone.now(),
            id_rol=rol,
        )
        self.assertIn("Empleados", str(emp))

    @pytest.mark.django_db
    def test_sesiones_activas_fecha_cierre_property(self):
        """Line 255: fecha_cierre property on SesionesActivas"""
        from django.utils import timezone

        from apps.usuarios.models import SesionesActivas

        obj = MagicMock(spec=SesionesActivas)
        obj.activa = True
        obj.ultima_actividad = timezone.now()
        # Use the actual property logic
        from apps.usuarios.models import SesionesActivas as SA

        # Test the property branches
        sesion = SesionesActivas.__new__(SesionesActivas)
        sesion.activa = True
        sesion.ultima_actividad = timezone.now()
        # activa=True → fecha_cierre is None
        result = SA.fecha_cierre.fget(sesion)
        self.assertIsNone(result)

    @pytest.mark.django_db
    def test_sesiones_activas_fecha_cierre_inactive(self):
        """Inactive session: fecha_cierre returns ultima_actividad"""
        from django.utils import timezone

        from apps.usuarios.models import SesionesActivas

        sesion = SesionesActivas.__new__(SesionesActivas)
        sesion.activa = False
        t = timezone.now()
        sesion.ultima_actividad = t
        result = SesionesActivas.fecha_cierre.fget(sesion)
        self.assertEqual(result, t)

    @pytest.mark.django_db
    def test_autenticacion_2fa_fecha_deshabilitado_enabled(self):
        """habilitado=True → fecha_deshabilitado is None"""
        from apps.usuarios.models import Autenticacion2Fa

        obj = Autenticacion2Fa.__new__(Autenticacion2Fa)
        obj.habilitado = True
        obj.ultima_verificacion = None
        result = Autenticacion2Fa.fecha_deshabilitado.fget(obj)
        self.assertIsNone(result)

    @pytest.mark.django_db
    def test_autenticacion_2fa_fecha_deshabilitado_disabled(self):
        """habilitado=False → fecha_deshabilitado returns ultima_verificacion"""
        from django.utils import timezone

        from apps.usuarios.models import Autenticacion2Fa

        obj = Autenticacion2Fa.__new__(Autenticacion2Fa)
        obj.habilitado = False
        t = timezone.now()
        obj.ultima_verificacion = t
        result = Autenticacion2Fa.fecha_deshabilitado.fget(obj)
        self.assertEqual(result, t)


# ──────────────────────────────────────────────────────────────────────────────
# _resolve_cliente_from_empleado  (branches 21->22, 25->26, 27->28, 27->30)
# ──────────────────────────────────────────────────────────────────────────────


class ResolveClienteFromEmpleadoTest(TestCase):
    """Tests for _resolve_cliente_from_empleado helper function."""

    def test_none_returns_none(self):
        """Branch 21->22: value is None → returns None immediately."""
        from apps.usuarios.models import _resolve_cliente_from_empleado

        result = _resolve_cliente_from_empleado(None)
        self.assertIsNone(result)

    @pytest.mark.django_db
    def test_nonexistent_pk_returns_none(self):
        """Branch 25->26 and 27->28: integer without id_empleado attr, not in DB → None."""
        from apps.usuarios.models import _resolve_cliente_from_empleado

        # 99999 is an integer (no id_empleado attr) → enters DB lookup → not found → None
        result = _resolve_cliente_from_empleado(999999)
        self.assertIsNone(result)

    @pytest.mark.django_db
    def test_existing_pk_as_integer_covers_27_30(self):
        """Branch 27->30: integer PK that EXISTS in DB → not None → continues to create cliente."""
        from django.utils import timezone

        from apps.clientes.models import TiposCliente
        from apps.productos.models import ListasPrecios
        from apps.usuarios.models import Empleados, Roles, _resolve_cliente_from_empleado

        # Pre-create TiposCliente and ListasPrecios
        TiposCliente.objects.get_or_create(nombre_tipo="General_27_30", defaults={"estado": True})
        ListasPrecios.objects.get_or_create(
            nombre_lista="General_27_30",
            defaults={"fecha_vigencia": timezone.now().date(), "moneda": "PYG", "estado": True},
        )

        rol, _ = Roles.objects.get_or_create(nombre_rol="TestIntPkRol", defaults={"descripcion": "t"})
        emp = Empleados.objects.create(
            nombre="IntPk",
            apellido="Test",
            usuario="intpk_branch_test_xyz",
            fecha_ingreso=timezone.now(),
            id_rol=rol,
        )
        # Pass the PK (integer) → no id_empleado attr → DB lookup finds emp → 27->30 False arm
        result = _resolve_cliente_from_empleado(emp.pk)
        self.assertIsNotNone(result)

    @pytest.mark.django_db
    def test_with_preexisting_tipo_and_lista(self):
        """Branch 39->42 False and 43->51 False: tipo_cliente and lista_precio already exist."""
        from django.utils import timezone

        from apps.clientes.models import TiposCliente
        from apps.productos.models import ListasPrecios
        from apps.usuarios.models import Empleados, Roles, _resolve_cliente_from_empleado

        # Pre-create TiposCliente and ListasPrecios so False arms are taken
        tipo, _ = TiposCliente.objects.get_or_create(nombre_tipo="General_test", defaults={"estado": True})
        lista, _ = ListasPrecios.objects.get_or_create(
            nombre_lista="General_test",
            defaults={"fecha_vigencia": timezone.now().date(), "moneda": "PYG", "estado": True},
        )

        # Create an Empleados instance and pass it (has id_empleado attr — hasattr passes)
        rol, _ = Roles.objects.get_or_create(nombre_rol="TestResolveRol", defaults={"descripcion": "t"})
        emp = Empleados.objects.create(
            nombre="Resolve",
            apellido="Test",
            usuario="resolve_test_unique_abc123",
            fecha_ingreso=timezone.now(),
            id_rol=rol,
        )
        # Pass the Empleados instance (has id_empleado) → skips DB lookup (27->30 False)
        # TiposCliente already exists → 39->42 False arm
        # ListasPrecios already exists → 43->51 False arm
        result = _resolve_cliente_from_empleado(emp)
        self.assertIsNotNone(result)


# ──────────────────────────────────────────────────────────────────────────────
# EmpleadosManager.get_or_create without defaults  (branch 150->152)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class EmpleadosManagerGetOrCreateTest(TestCase):
    """Branch 150->152: get_or_create called WITHOUT defaults parameter."""

    def test_get_or_create_no_defaults_creates_new(self):
        """When defaults=None (not provided), the False arm of 'if defaults:' is taken."""
        from apps.usuarios.models import Empleados

        # This should create a new Empleados without defaults (False arm of if defaults:)
        emp, created = Empleados.objects.get_or_create(usuario="nodefaults_branch_xyz999")
        self.assertTrue(created)
        emp.delete()

    def test_get_or_create_no_defaults_finds_existing(self):
        """When record exists, get_or_create returns (existing, False); True arm never hit."""
        from django.utils import timezone

        from apps.usuarios.models import Empleados

        emp_existing = Empleados.objects.create(
            nombre="Existing", apellido="User", usuario="existing_nodefaults_abc888", fecha_ingreso=timezone.now()
        )
        emp, created = Empleados.objects.get_or_create(usuario="existing_nodefaults_abc888")
        self.assertFalse(created)
        self.assertEqual(emp.pk, emp_existing.pk)
