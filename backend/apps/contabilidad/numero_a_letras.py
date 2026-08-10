"""Conversión de montos en Guaraníes a su representación en letras, para
imprimir el campo "TOTAL A PAGAR (en letras)" de la factura preimpresa.
"""

UNIDADES = [
    "", "UN", "DOS", "TRES", "CUATRO", "CINCO",
    "SEIS", "SIETE", "OCHO", "NUEVE",
]
DIEZ_DIECINUEVE = [
    "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE",
    "DIECISÉIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE",
]
VEINTE_VEINTINUEVE = [
    "VEINTE", "VEINTIUN", "VEINTIDÓS", "VEINTITRÉS", "VEINTICUATRO",
    "VEINTICINCO", "VEINTISÉIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE",
]
DECENAS = [
    "", "", "", "TREINTA", "CUARENTA", "CINCUENTA",
    "SESENTA", "SETENTA", "OCHENTA", "NOVENTA",
]
CENTENAS = [
    "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
    "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS",
]


def _tres_digitos(n: int) -> str:
    """Convierte un número de 0 a 999 a letras."""
    if n == 0:
        return ""
    centena, resto = divmod(n, 100)
    partes = []
    if centena:
        partes.append("CIEN" if n == 100 else CENTENAS[centena])
    if resto:
        if resto < 10:
            partes.append(UNIDADES[resto])
        elif resto < 20:
            partes.append(DIEZ_DIECINUEVE[resto - 10])
        elif resto < 30:
            partes.append(VEINTE_VEINTINUEVE[resto - 20])
        else:
            decena, unidad = divmod(resto, 10)
            if unidad:
                partes.append(f"{DECENAS[decena]} Y {UNIDADES[unidad]}")
            else:
                partes.append(DECENAS[decena])
    return " ".join(partes)


def numero_a_letras(n: int) -> str:
    """Convierte un entero a su representación en letras (español, Paraguay)."""
    n = int(n)
    if n == 0:
        return "CERO"

    negativo = n < 0
    n = abs(n)

    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)

    partes = []
    if millones:
        partes.append("UN MILLÓN" if millones == 1 else f"{_tres_digitos(millones)} MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 else f"{_tres_digitos(miles)} MIL")
    if unidades or not partes:
        partes.append(_tres_digitos(unidades))

    texto = " ".join(p for p in partes if p)
    return ("MENOS " if negativo else "") + texto


def monto_a_letras(monto) -> str:
    """Convierte un monto en Guaraníes (sin decimales) a letras, ej:
    20500 -> "VEINTE MIL QUINIENTOS GUARANÍES"."""
    return f"{numero_a_letras(int(monto))} GUARANÍES"
