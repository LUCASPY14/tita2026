"""
Carga el catálogo de ciudades paraguayas (tabla Ciudad) — hoy vacía en
producción. Mismo listado que ya usa el combobox del frontend
(frontend/src/pages/clientes/shared.tsx::CIUDADES_PY), para que
`importar_clientes` pueda validar `cliente_ciudad` contra un catálogo real
y el formulario de Google pueda ofrecer un desplegable con las mismas
opciones que ya usa el sistema.

Idempotente — correrlo de nuevo no duplica nada.

Uso:
    python manage.py seed_ciudades
"""

from django.core.management.base import BaseCommand

from apps.clientes.models import Ciudad, Pais

CIUDADES_PY = [
    'Asunción', 'San Lorenzo', 'Luque', 'Capiatá', 'Lambaré',
    'Fernando de la Mora', 'Limpio', 'Ñemby', 'Mariano Roque Alonso',
    'Encarnación', 'Ciudad del Este', 'Pedro Juan Caballero',
    'Concepción', 'Coronel Oviedo', 'Caaguazú', 'Villarrica',
    'Pilar', 'Caazapá', 'San Juan Bautista', 'Villa Hayes',
    'Pozo Colorado', 'Fuerte Olimpo', 'Filadelfia', 'Loma Plata',
    'Minga Guazú', 'Hernandarias', 'Presidente Franco',
]


class Command(BaseCommand):
    help = "Carga el catálogo de ciudades paraguayas (idempotente)."

    def handle(self, *args, **options):
        paraguay, _ = Pais.objects.get_or_create(nombre="Paraguay")

        creadas = 0
        for nombre in CIUDADES_PY:
            _, creada = Ciudad.objects.get_or_create(nombre=nombre, pais=paraguay)
            if creada:
                creadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"Ciudades: {creadas} creadas, {len(CIUDADES_PY) - creadas} ya existían. Total: {len(CIUDADES_PY)}."
        ))
