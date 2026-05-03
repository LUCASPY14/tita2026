"""
Tests de cobertura completa para almuerzos.validators
Objetivo: Alcanzar 100% de cobertura en casos edge de validaciones

Cobertura de líneas:
- L220: Validación de precio con más de 2 decimales
- L530: Return temprano cuando id_hijo o fecha_consumo es None
- L534-539: Conversión de fecha string y manejo de fecha inválida
- L549: Branch de límite de registros
- L584: Return True cuando id_hijo o fecha es None
- L588-593: Conversión de fecha string en determinar_si_cobra
- L601: Branch de primer registro del día
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError

import pytest

from apps.almuerzos.models import RegistrosConsumoAlmuerzo
from apps.almuerzos.validators import (
    determinar_si_cobra,
    validar_limite_registros_diarios,
    validar_precio_unitario_tipo,
)
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios


@pytest.mark.parametrize(
    "precio_invalido,decimales",
    [
        (Decimal("100.123"), 3),  # L220: 3 decimales
        (Decimal("50.9999"), 4),  # L220: 4 decimales
        (Decimal("25.12345"), 5),  # L220: 5 decimales
        (Decimal("1.999"), 3),  # L220: 3 decimales (caso mínimo)
    ],
)
def test_validar_precio_unitario_tipo_decimales_excesivos(precio_invalido, decimales):
    """
    Test L220: Validación de precio con más de 2 decimales

    El sistema solo permite máximo 2 decimales en precios.
    Cualquier precio con 3 o más decimales debe ser rechazado.
    """
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validar_precio_unitario_tipo(precio_invalido)

    # Verificar mensaje de error
    assert "2 decimales" in str(exc_info.value).lower() or "decimales" in str(exc_info.value).lower()


@pytest.mark.parametrize(
    "precio_valido",
    [
        Decimal("100.00"),  # Caso válido: 2 decimales
        Decimal("50.5"),  # Caso válido: 1 decimal
        Decimal("25"),  # Caso válido: sin decimales
        Decimal("1.99"),  # Caso válido: 2 decimales
    ],
)
def test_validar_precio_unitario_tipo_validos(precio_valido):
    """Test complementario: Precios válidos deben pasar"""
    # Act & Assert - No debe lanzar excepción
    try:
        validar_precio_unitario_tipo(precio_valido)
    except ValidationError:
        pytest.fail(f"Precio válido {precio_valido} no debería fallar")


@pytest.mark.django_db
class TestValidarLimiteRegistrosDiariosEdgeCases:
    """Tests para casos edge de validar_limite_registros_diarios"""

    @pytest.fixture
    def hijo(self):
        """Fixture: Hijo para tests de registros"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Test", apellidos="Validator", ruc_ci="1111111", estado=True, id_lista=lista, id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Test",
            apellido="Child",
            fecha_nacimiento="2012-01-01",
            grado="1ro",
            estado=True,
            id_cliente_responsable=cliente,
        )

    def test_limite_registros_id_hijo_none(self):
        """
        Test L530: Return temprano cuando id_hijo es None

        Cuando id_hijo es None, la función debe retornar inmediatamente
        sin hacer validaciones adicionales.
        """
        # Act & Assert - No debe lanzar excepción
        try:
            validar_limite_registros_diarios(None, date.today())
        except ValidationError:
            pytest.fail("No debería lanzar error cuando id_hijo es None")

    def test_limite_registros_fecha_consumo_none(self):
        """
        Test L530: Return temprano cuando fecha_consumo es None

        Similar al caso anterior, debe retornar sin validar.
        """
        # Act & Assert
        try:
            validar_limite_registros_diarios(999, None)  # ID ficticio
        except ValidationError:
            pytest.fail("No debería lanzar error cuando fecha_consumo es None")

    def test_limite_registros_ambos_none(self):
        """Test adicional: Ambos parámetros None"""
        # Act & Assert
        try:
            validar_limite_registros_diarios(None, None)
        except ValidationError:
            pytest.fail("No debería lanzar error cuando ambos son None")

    def test_limite_registros_fecha_string_valida(self, hijo):
        """
        Test L534-539: Conversión de fecha string válida a date

        La función acepta fechas como string en formato ISO y las convierte.
        """
        # Arrange
        fecha_string = "2026-04-19"

        # Act & Assert - Debe convertir y procesar sin error
        try:
            validar_limite_registros_diarios(hijo.id_hijo, fecha_string)
        except ValidationError as e:
            # Puede lanzar error de límite, pero no de conversión de fecha
            assert "fecha" not in str(e).lower() or "formato" not in str(e).lower()

    def test_limite_registros_fecha_string_invalida(self, hijo):
        """
        Test L539: Fecha string inválida debe retornar sin error

        Cuando la fecha no se puede parsear, la función hace return
        para que otro validador maneje el error de formato.
        """
        # Arrange
        fecha_invalida = "fecha-incorrecta-123"

        # Act & Assert - No debe lanzar excepción
        try:
            validar_limite_registros_diarios(hijo.id_hijo, fecha_invalida)
        except ValidationError:
            pytest.fail("No debería lanzar error en fecha inválida (lo maneja otro validador)")

    def test_limite_registros_con_registros_existentes(self, hijo):
        """
        Test L549: Branch cuando ya existen registros en el día

        Verifica el comportamiento cuando ya hay registros del día.
        """
        # Arrange: Crear 2 registros del mismo día (límite)
        from datetime import time

        fecha_test = date.today()

        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo, fecha_consumo=fecha_test, hora_registro=time(12, 0), estado="Registrado", ya_cobrado=True
        )

        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo, fecha_consumo=fecha_test, hora_registro=time(12, 30), estado="Confirmado", ya_cobrado=False
        )

        # Act & Assert: Tercer registro debe fallar
        with pytest.raises(ValidationError) as exc_info:
            validar_limite_registros_diarios(hijo.id_hijo, fecha_test)

        assert "2 registros" in str(exc_info.value).lower() or "límite" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestDeterminarSiCobraEdgeCases:
    """Tests para casos edge de determinar_si_cobra"""

    @pytest.fixture
    def hijo(self):
        """Fixture: Hijo para tests de cobro"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Test", apellidos="Cobro", ruc_ci="2222222", estado=True, id_lista=lista, id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Test",
            apellido="Cobro",
            fecha_nacimiento="2011-05-10",
            grado="2do",
            estado=True,
            id_cliente_responsable=cliente,
        )

    def test_determinar_cobro_id_hijo_none_retorna_true(self):
        """
        Test L584: Return True cuando id_hijo es None

        Por defecto, cuando no hay hijo específico, se cobra.
        """
        # Act
        resultado = determinar_si_cobra(None, date.today())

        # Assert
        assert resultado is True

    def test_determinar_cobro_fecha_consumo_none_retorna_true(self):
        """
        Test L584: Return True cuando fecha_consumo es None

        Similar al caso anterior, sin fecha se asume cobro.
        """
        # Act
        resultado = determinar_si_cobra(999, None)

        # Assert
        assert resultado is True

    def test_determinar_cobro_ambos_none_retorna_true(self):
        """Test adicional: Ambos parámetros None"""
        # Act
        resultado = determinar_si_cobra(None, None)

        # Assert
        assert resultado is True

    def test_determinar_cobro_fecha_string_valida(self, hijo):
        """
        Test L588-593: Conversión de fecha string a date

        La función debe aceptar fechas en formato string ISO.
        """
        # Arrange
        fecha_string = "2026-04-19"

        # Act
        resultado = determinar_si_cobra(hijo.id_hijo, fecha_string)

        # Assert
        assert isinstance(resultado, bool)

    def test_determinar_cobro_fecha_string_invalida_retorna_true(self, hijo):
        """
        Test L593: Fecha string inválida retorna True

        En caso de error de parseo, se asume que sí cobra (True).
        """
        # Arrange
        fecha_mala = "not-a-date-format"

        # Act
        resultado = determinar_si_cobra(hijo.id_hijo, fecha_mala)

        # Assert
        assert resultado is True

    def test_determinar_cobro_primer_registro_del_dia(self, hijo):
        """
        Test L601: Primer registro del día genera cobro (True)

        Cuando no hay registros previos del día, debe retornar True.
        """
        # Arrange: Fecha sin registros previos
        fecha_nueva = date(2026, 5, 1)

        # Act
        resultado = determinar_si_cobra(hijo.id_hijo, fecha_nueva)

        # Assert
        assert resultado is True  # Primer registro cobra

    def test_determinar_cobro_segundo_registro_del_dia(self, hijo):
        """
        Test adicional: Segundo registro del día NO genera cobro

        Cuando ya existe 1 registro, el segundo debe retornar False.
        """
        # Arrange: Crear primer registro del día
        from datetime import time

        fecha_test = date.today()

        RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo, fecha_consumo=fecha_test, hora_registro=time(12, 0), estado="Registrado", ya_cobrado=True
        )

        # Act
        resultado = determinar_si_cobra(hijo.id_hijo, fecha_test)

        # Assert
        assert resultado is False  # Segundo registro NO cobra


@pytest.mark.parametrize(
    "id_hijo,fecha,esperado",
    [
        (None, None, True),  # L584: Ambos None
        (None, "2026-04-19", True),  # L584: Solo id_hijo None
        (123, None, True),  # L584: Solo fecha None
        (456, "fecha-mala", True),  # L593: Fecha inválida
    ],
)
def test_determinar_cobro_parametros_edge_cases(id_hijo, fecha, esperado):
    """
    Tests paramétricos para casos edge de determinar_si_cobra

    Cubre múltiples combinaciones de parámetros inválidos o None.
    """
    # Act
    resultado = determinar_si_cobra(id_hijo, fecha)

    # Assert
    assert resultado == esperado
