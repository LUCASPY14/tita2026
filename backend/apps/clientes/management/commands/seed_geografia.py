"""
Carga la jerarquía geográfica completa (País → Departamento → Ciudad) —
hoy vacía en producción. Usa la división política real de Paraguay: sus 17
departamentos más Asunción como Distrito Capital (no pertenece a ningún
departamento, tratamiento estándar de la DGEEC para fines estadísticos),
con un municipio representativo por departamento como punto de partida.

Reemplaza al viejo `seed_ciudades` (listado plano de ciudades sin
departamento) — permite que `importar_clientes` y el selector en cascada
País→Departamento→Ciudad del frontend tengan un catálogo real.

Idempotente — correrlo de nuevo no duplica nada.

Uso:
    python manage.py seed_geografia
"""

from django.core.management.base import BaseCommand

from apps.clientes.models import Ciudad, Departamento, Pais

# departamento -> [ciudades]. "Asunción" se modela como su propio
# "departamento" (Distrito Capital) con una única ciudad homónima.
DEPARTAMENTOS_PY = {
    "Asunción (Distrito Capital)": ["Asunción"],
    "Central": [
        "San Lorenzo", "Luque", "Capiatá", "Lambaré", "Fernando de la Mora",
        "Limpio", "Ñemby", "Mariano Roque Alonso",
    ],
    "Concepción": ["Concepción"],
    "San Pedro": ["San Pedro del Ycuamandiyú"],
    "Cordillera": ["Caacupé"],
    "Guairá": ["Villarrica"],
    "Caaguazú": ["Coronel Oviedo", "Caaguazú"],
    "Caazapá": ["Caazapá"],
    "Itapúa": ["Encarnación"],
    "Misiones": ["San Juan Bautista"],
    "Paraguarí": ["Paraguarí"],
    "Alto Paraná": ["Ciudad del Este", "Minga Guazú", "Hernandarias", "Presidente Franco"],
    "Ñeembucú": ["Pilar"],
    "Amambay": ["Pedro Juan Caballero"],
    "Canindeyú": ["Salto del Guairá"],
    "Presidente Hayes": ["Villa Hayes", "Pozo Colorado"],
    "Boquerón": ["Filadelfia", "Loma Plata"],
    "Alto Paraguay": ["Fuerte Olimpo"],
}


class Command(BaseCommand):
    help = "Carga País, Departamentos y Ciudades de Paraguay (idempotente)."

    def handle(self, *args, **options):
        paraguay, _ = Pais.objects.get_or_create(nombre="Paraguay")

        deptos_creados = 0
        ciudades_creadas = 0
        total_ciudades = 0

        for nombre_depto, ciudades in DEPARTAMENTOS_PY.items():
            depto, creado = Departamento.objects.get_or_create(nombre=nombre_depto, pais=paraguay)
            if creado:
                deptos_creados += 1
            for nombre_ciudad in ciudades:
                total_ciudades += 1
                _, creada = Ciudad.objects.get_or_create(nombre=nombre_ciudad, departamento=depto)
                if creada:
                    ciudades_creadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"Departamentos: {deptos_creados} creados, {len(DEPARTAMENTOS_PY) - deptos_creados} ya existían. "
            f"Total: {len(DEPARTAMENTOS_PY)}."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Ciudades: {ciudades_creadas} creadas, {total_ciudades - ciudades_creadas} ya existían. "
            f"Total: {total_ciudades}."
        ))
