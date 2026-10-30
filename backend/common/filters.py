"""
Búsqueda insensible a acentos (usa la extensión Postgres `unaccent`, ver
apps/core/migrations/0036_unaccent_extension.py).

Sin esto, buscar "Gonzalez" no encuentra a alguien guardado como "González"
(ILIKE compara letra por letra, "a" != "á") — en la práctica el personal
carga nombres con y sin tilde indistintamente, así que una búsqueda sin
esto deja afuera a una parte real de los resultados.
"""
import unicodedata

from django.db.models import CharField, TextField, Transform
from rest_framework import filters


class Unaccent(Transform):
    """django.db.models lookup: `campo__unaccent` → UNACCENT(campo) en SQL."""
    lookup_name = "unaccent"
    function = "UNACCENT"


CharField.register_lookup(Unaccent)
TextField.register_lookup(Unaccent)


def quitar_acentos(texto: str) -> str:
    """Quita acentos del lado Python (para el término que tipea el usuario)."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )


class UnaccentSearchFilter(filters.SearchFilter):
    """
    SearchFilter de DRF, pero ignorando acentos de los dos lados (columna y
    término buscado). Los `search_fields` de texto libre deben llevar el
    sufijo `__unaccent` (ej. "apellidos__unaccent") para que compare contra
    UNACCENT(columna); campos no textuales (ruc_ci, nro_tarjeta) no lo
    necesitan.
    """

    def get_search_terms(self, request):
        terms = super().get_search_terms(request)
        return [quitar_acentos(t) for t in terms]
