import pytest

from apps.contabilidad.numero_a_letras import monto_a_letras, numero_a_letras


@pytest.mark.parametrize("valor, esperado", [
    (0, "CERO"),
    (1, "UN"),
    (5, "CINCO"),
    (10, "DIEZ"),
    (15, "QUINCE"),
    (19, "DIECINUEVE"),
    (20, "VEINTE"),
    (21, "VEINTIUN"),
    (29, "VEINTINUEVE"),
    (30, "TREINTA"),
    (45, "CUARENTA Y CINCO"),
    (99, "NOVENTA Y NUEVE"),
    (100, "CIEN"),
    (101, "CIENTO UN"),
    (121, "CIENTO VEINTIUN"),
    (200, "DOSCIENTOS"),
    (500, "QUINIENTOS"),
    (999, "NOVECIENTOS NOVENTA Y NUEVE"),
    (1000, "MIL"),
    (1001, "MIL UN"),
    (2000, "DOS MIL"),
    (21000, "VEINTIUN MIL"),
    (100000, "CIEN MIL"),
    (120500, "CIENTO VEINTE MIL QUINIENTOS"),
    (999999, "NOVECIENTOS NOVENTA Y NUEVE MIL NOVECIENTOS NOVENTA Y NUEVE"),
    (1000000, "UN MILLÓN"),
    (1000001, "UN MILLÓN UN"),
    (1500000, "UN MILLÓN QUINIENTOS MIL"),
    (2340500, "DOS MILLONES TRESCIENTOS CUARENTA MIL QUINIENTOS"),
    (-50, "MENOS CINCUENTA"),
])
def test_numero_a_letras(valor, esperado):
    assert numero_a_letras(valor) == esperado


def test_monto_a_letras_agrega_guaranies():
    assert monto_a_letras(20500) == "VEINTE MIL QUINIENTOS GUARANÍES"


def test_monto_a_letras_acepta_decimal():
    from decimal import Decimal
    assert monto_a_letras(Decimal("50000")) == "CINCUENTA MIL GUARANÍES"
