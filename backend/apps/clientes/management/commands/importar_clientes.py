"""
Importa clientes (padres/tutores) e hijos desde un CSV — una fila por hijo,
con los datos del cliente responsable repetidos en cada fila (así es como
sale un Google Form cuando cada padre completa el formulario una vez por
hijo). Mismo layout de columnas que `exportar_clientes`.

No toca restricciones alimentarias/alergias (RestriccionHijo) — eso se carga
aparte, no viene de este import.

Columnas requeridas: ruc_ci, cliente_nombres, cliente_apellidos, hijo_nombre,
hijo_apellido
Columnas opcionales: cliente_email, cliente_telefono, cliente_direccion,
cliente_ciudad, cliente_tipo, cliente_lista_precio, hijo_fecha_nacimiento
(YYYY-MM-DD), hijo_grado

Si el CSV no trae "cliente_tipo"/"cliente_lista_precio" (o vienen vacíos en
una fila), se usan los valores de --tipo-cliente/--lista-precio. Si tampoco
se pasan por CLI, --lista-precio cae al ListaPrecio con es_por_defecto=True
si existe una; --tipo-cliente es obligatorio de alguna de las dos formas.

Un cliente existente (mismo ruc_ci) se reutiliza para asociar el hijo, sin
tocar sus datos de contacto salvo que se pase --actualizar-clientes. Un hijo
ya existente para ese cliente (mismo nombre+apellido) se omite, no duplica.

Uso:
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia --lista-precio General
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia --dry-run
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia --actualizar-clientes
"""

import csv
import re
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.clientes.models import Cliente, Grado, Hijo, TipoCliente
from apps.productos.models import ListaPrecio

RUC_CI_REGEX = re.compile(r"^(\d{6,8}(-\d{1,2})?|\d{1,8}-\d{1}|\d{6,8})$")

REQUERIDAS = ["ruc_ci", "cliente_nombres", "cliente_apellidos", "hijo_nombre", "hijo_apellido"]


class Command(BaseCommand):
    help = "Importa clientes e hijos desde un CSV (una fila por hijo)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta del archivo CSV de entrada")
        parser.add_argument("--tipo-cliente", help="Nombre del TipoCliente a usar por defecto (ej: Familia)")
        parser.add_argument("--lista-precio", help="Nombre de la ListaPrecio a usar por defecto (ej: General)")
        parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué haría, no escribir en la BD")
        parser.add_argument(
            "--actualizar-clientes", action="store_true",
            help="Si el cliente ya existe (mismo ruc_ci), actualizar sus datos de contacto con los del CSV",
        )

    def handle(self, *args, **options):
        tipo_default = self._resolver_tipo_cliente(options["tipo_cliente"]) if options["tipo_cliente"] else None
        lista_default = self._resolver_lista_precio(options["lista_precio"])

        with open(options["csv_path"], newline="", encoding="utf-8-sig") as f:
            filas = list(csv.DictReader(f))

        faltantes = [c for c in REQUERIDAS if c not in (filas[0].keys() if filas else [])]
        if faltantes:
            raise CommandError(f"Faltan columnas obligatorias en el CSV: {', '.join(faltantes)}")

        stats = {
            "clientes_creados": 0, "clientes_reutilizados": 0, "clientes_actualizados": 0,
            "hijos_creados": 0, "hijos_omitidos": 0,
        }
        errores: list[str] = []
        warnings: list[str] = []

        with transaction.atomic():
            for i, fila in enumerate(filas, start=2):  # fila 1 es el header
                try:
                    self._procesar_fila(
                        fila, tipo_default, lista_default,
                        options["actualizar_clientes"], stats, warnings,
                    )
                except _FilaInvalida as e:
                    errores.append(f"Fila {i}: {e}")

            if options["dry_run"]:
                transaction.set_rollback(True)

        self._reportar(stats, errores, warnings, options["dry_run"])

    # ── Resolución de catálogos ─────────────────────────────────────────────

    def _resolver_tipo_cliente(self, nombre: str) -> TipoCliente:
        tipo = TipoCliente.objects.filter(nombre__iexact=nombre).first()
        if tipo is None:
            raise CommandError(f'No existe un TipoCliente llamado "{nombre}".')
        return tipo

    def _resolver_lista_precio(self, nombre: str | None) -> ListaPrecio | None:
        if nombre:
            lista = ListaPrecio.objects.filter(nombre__iexact=nombre).first()
            if lista is None:
                raise CommandError(f'No existe una ListaPrecio llamada "{nombre}".')
            return lista
        return ListaPrecio.objects.filter(es_por_defecto=True).first()

    # ── Procesamiento por fila ──────────────────────────────────────────────

    def _procesar_fila(self, fila, tipo_default, lista_default, actualizar_clientes, stats, warnings):
        ruc_ci = (fila.get("ruc_ci") or "").strip()
        nombres = (fila.get("cliente_nombres") or "").strip()
        apellidos = (fila.get("cliente_apellidos") or "").strip()
        hijo_nombre = (fila.get("hijo_nombre") or "").strip()
        hijo_apellido = (fila.get("hijo_apellido") or "").strip()

        if not ruc_ci or not nombres or not apellidos or not hijo_nombre or not hijo_apellido:
            raise _FilaInvalida("faltan datos obligatorios (ruc_ci/nombres/apellidos/hijo_nombre/hijo_apellido)")
        if not RUC_CI_REGEX.match(ruc_ci):
            raise _FilaInvalida(f'CI/RUC "{ruc_ci}" no tiene un formato reconocible')

        tipo_fila = (fila.get("cliente_tipo") or "").strip()
        tipo = self._resolver_tipo_cliente(tipo_fila) if tipo_fila else tipo_default
        if tipo is None:
            raise _FilaInvalida("sin cliente_tipo en el CSV y sin --tipo-cliente por defecto")

        lista_fila = (fila.get("cliente_lista_precio") or "").strip()
        lista = self._resolver_lista_precio(lista_fila) if lista_fila else lista_default
        if lista is None:
            raise _FilaInvalida("sin cliente_lista_precio en el CSV, sin --lista-precio, y no hay ListaPrecio por defecto")

        cliente, creado = Cliente.objects.get_or_create(
            ruc_ci=ruc_ci,
            defaults={
                "nombres": nombres,
                "apellidos": apellidos,
                "email": (fila.get("cliente_email") or "").strip() or None,
                "telefono": (fila.get("cliente_telefono") or "").strip() or None,
                "direccion": (fila.get("cliente_direccion") or "").strip() or None,
                "ciudad": (fila.get("cliente_ciudad") or "").strip() or None,
                "tipo_cliente": tipo,
                "lista_precio": lista,
            },
        )
        if creado:
            stats["clientes_creados"] += 1
        else:
            stats["clientes_reutilizados"] += 1
            if actualizar_clientes:
                cliente.nombres = nombres
                cliente.apellidos = apellidos
                cliente.email = (fila.get("cliente_email") or "").strip() or cliente.email
                cliente.telefono = (fila.get("cliente_telefono") or "").strip() or cliente.telefono
                cliente.direccion = (fila.get("cliente_direccion") or "").strip() or cliente.direccion
                cliente.ciudad = (fila.get("cliente_ciudad") or "").strip() or cliente.ciudad
                cliente.save()
                stats["clientes_actualizados"] += 1

        grado = None
        grado_fila = (fila.get("hijo_grado") or "").strip()
        if grado_fila:
            grado = Grado.objects.filter(nombre__iexact=grado_fila).first()
            if grado is None:
                warnings.append(f'"{grado_fila}" no coincide con ningún Grado existente — {hijo_nombre} {hijo_apellido} queda sin grado asignado')

        fecha_nacimiento = None
        fecha_fila = (fila.get("hijo_fecha_nacimiento") or "").strip()
        if fecha_fila:
            try:
                fecha_nacimiento = date.fromisoformat(fecha_fila)
            except ValueError:
                warnings.append(f'Fecha de nacimiento inválida "{fecha_fila}" para {hijo_nombre} {hijo_apellido} — se deja vacía')

        _, hijo_creado = Hijo.objects.get_or_create(
            cliente_responsable=cliente,
            nombre=hijo_nombre,
            apellido=hijo_apellido,
            defaults={"fecha_nacimiento": fecha_nacimiento, "grado": grado},
        )
        if hijo_creado:
            stats["hijos_creados"] += 1
        else:
            stats["hijos_omitidos"] += 1

    # ── Reporte final ────────────────────────────────────────────────────────

    def _reportar(self, stats, errores, warnings, dry_run):
        if dry_run:
            self.stdout.write(self.style.WARNING("── DRY RUN: no se escribió nada en la base de datos ──"))

        self.stdout.write(
            f"Clientes creados: {stats['clientes_creados']} | "
            f"reutilizados: {stats['clientes_reutilizados']} | "
            f"actualizados: {stats['clientes_actualizados']}"
        )
        self.stdout.write(
            f"Hijos creados: {stats['hijos_creados']} | "
            f"omitidos (ya existían): {stats['hijos_omitidos']}"
        )

        if warnings:
            self.stdout.write(self.style.WARNING(f"\nAvisos ({len(warnings)}):"))
            for w in warnings:
                self.stdout.write(self.style.WARNING(f"  ! {w}"))

        if errores:
            self.stdout.write(self.style.ERROR(f"\nErrores ({len(errores)}) — filas no importadas:"))
            for e in errores:
                self.stdout.write(self.style.ERROR(f"  ✗ {e}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nSin errores."))


class _FilaInvalida(Exception):
    pass
