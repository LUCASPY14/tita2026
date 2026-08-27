"""
Importa clientes (padres/tutores, o el familiar allegado que se hace cargo
económico cuando el padre no está) e hijos desde un CSV — una fila por
familia, con los hijos en grupos de columnas repetidos (hijo1_*, hijo2_*,
hijo3_*, ...). Así es como sale un Google Form donde cada familia completa
el formulario una sola vez y carga tantos hijos como tenga, sin secciones
repetibles (Google Forms no las soporta de forma nativa).

La cantidad de "hijoN" se detecta automáticamente a partir de las columnas
del CSV — no hay un máximo fijo. Un hijoN vacío (sin nombre ni apellido) se
omite en silencio; solo hijo1 es obligatorio.

No toca restricciones alimentarias/alergias (RestriccionHijo) — eso se carga
aparte, no viene de este import.

Si el alumno ya tiene una tarjeta física de la cantina (columna hijoN_tarjeta),
se crea el registro Tarjeta vinculado a ese hijo con estado ACTIVA y saldo 0
— el número lo escribe la familia en el formulario, no lo genera el sistema.
Si el número ya está registrado a nombre de otro titular, o el hijo ya tenía
una tarjeta distinta, no se toca nada y se avisa para resolverlo a mano.

Columnas obligatorias: ruc_ci, cliente_nombres, cliente_apellidos,
hijo1_nombre, hijo1_apellido
Columnas opcionales: cliente_email, cliente_telefono, cliente_direccion,
cliente_ciudad, cliente_tipo, cliente_lista_precio, hijoN_fecha_nacimiento
(acepta AAAA-MM-DD, DD/MM/AAAA o DD-MM-AAAA), hijoN_grado, hijoN_tarjeta,
para cada N detectado (hijo2_nombre, hijo2_apellido, hijo3_nombre, ...)

Si el CSV no trae "cliente_tipo"/"cliente_lista_precio" (o vienen vacíos en
una fila), se usan los valores de --tipo-cliente/--lista-precio. Si tampoco
se pasan por CLI, --lista-precio cae al ListaPrecio con es_por_defecto=True
si existe una; --tipo-cliente es obligatorio de alguna de las dos formas.

Un cliente existente (mismo ruc_ci) se reutiliza para asociar los hijos, sin
tocar sus datos de contacto salvo que se pase --actualizar-clientes. Un hijo
ya existente para ese cliente (mismo nombre+apellido) se omite, no duplica.

Uso:
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia --dry-run
    python manage.py importar_clientes entrada.csv --tipo-cliente Familia --actualizar-clientes
"""

import csv
import re
from datetime import date, datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.clientes.models import Ciudad, Cliente, Grado, Hijo, TipoCliente
from apps.core.models import Tarjeta
from apps.productos.models import ListaPrecio

RUC_CI_REGEX = re.compile(r"^(\d{6,8}(-\d{1,2})?|\d{1,8}-\d{1}|\d{6,8})$")
HIJO_COL_REGEX = re.compile(r"^hijo(\d+)_nombre$")

# Orden de prueba: ISO primero, después DD/MM/AAAA (formato paraguayo, y el
# que exporta Sheets al bajar un formulario de Google Forms a CSV).
FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]


def _parsear_fecha(fecha_str: str) -> date | None:
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    return None

REQUERIDAS = ["ruc_ci", "cliente_nombres", "cliente_apellidos", "hijo1_nombre", "hijo1_apellido"]


class Command(BaseCommand):
    help = "Importa clientes e hijos desde un CSV (una fila por familia, hijos en columnas hijoN_*)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta del archivo CSV de entrada")
        parser.add_argument("--tipo-cliente", help="Nombre del TipoCliente a usar por defecto (ej: Familia)")
        parser.add_argument("--lista-precio", help="Nombre de la ListaPrecio a usar por defecto (ej: Lista General)")
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

        columnas = filas[0].keys() if filas else []
        faltantes = [c for c in REQUERIDAS if c not in columnas]
        if faltantes:
            raise CommandError(f"Faltan columnas obligatorias en el CSV: {', '.join(faltantes)}")

        nros_hijo = sorted(
            int(m.group(1)) for c in columnas if (m := HIJO_COL_REGEX.match(c))
        )

        stats = {
            "clientes_creados": 0, "clientes_reutilizados": 0, "clientes_actualizados": 0,
            "hijos_creados": 0, "hijos_omitidos": 0, "tarjetas_creadas": 0,
        }
        errores: list[str] = []
        warnings: list[str] = []

        with transaction.atomic():
            for i, fila in enumerate(filas, start=2):  # fila 1 es el header
                try:
                    self._procesar_fila(
                        fila, nros_hijo, tipo_default, lista_default,
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

    # ── Procesamiento por fila (una familia, N hijos) ───────────────────────

    def _procesar_fila(self, fila, nros_hijo, tipo_default, lista_default, actualizar_clientes, stats, warnings):
        ruc_ci = (fila.get("ruc_ci") or "").strip()
        nombres = (fila.get("cliente_nombres") or "").strip()
        apellidos = (fila.get("cliente_apellidos") or "").strip()

        if not ruc_ci or not nombres or not apellidos:
            raise _FilaInvalida("faltan datos obligatorios del cliente (ruc_ci/cliente_nombres/cliente_apellidos)")
        if not RUC_CI_REGEX.match(ruc_ci):
            raise _FilaInvalida(f'CI/RUC "{ruc_ci}" no tiene un formato reconocible')

        hijo1_nombre = (fila.get("hijo1_nombre") or "").strip()
        hijo1_apellido = (fila.get("hijo1_apellido") or "").strip()
        if not hijo1_nombre or not hijo1_apellido:
            raise _FilaInvalida("falta hijo1_nombre/hijo1_apellido — toda familia debe tener al menos un hijo")

        tipo_fila = (fila.get("cliente_tipo") or "").strip()
        tipo = self._resolver_tipo_cliente(tipo_fila) if tipo_fila else tipo_default
        if tipo is None:
            raise _FilaInvalida("sin cliente_tipo en el CSV y sin --tipo-cliente por defecto")

        lista_fila = (fila.get("cliente_lista_precio") or "").strip()
        lista = self._resolver_lista_precio(lista_fila) if lista_fila else lista_default
        if lista is None:
            raise _FilaInvalida("sin cliente_lista_precio en el CSV, sin --lista-precio, y no hay ListaPrecio por defecto")

        ciudad = (fila.get("cliente_ciudad") or "").strip()
        if ciudad and not Ciudad.objects.filter(nombre__iexact=ciudad).exists():
            warnings.append(f'Ciudad "{ciudad}" no está en el catálogo (Ciudad) — se guarda igual como texto libre')

        cliente, creado = Cliente.objects.get_or_create(
            ruc_ci=ruc_ci,
            defaults={
                "nombres": nombres,
                "apellidos": apellidos,
                "email": (fila.get("cliente_email") or "").strip() or None,
                "telefono": (fila.get("cliente_telefono") or "").strip() or None,
                "direccion": (fila.get("cliente_direccion") or "").strip() or None,
                "ciudad": ciudad or None,
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
                cliente.ciudad = ciudad or cliente.ciudad
                cliente.save()
                stats["clientes_actualizados"] += 1

        for n in nros_hijo:
            self._procesar_hijo(fila, n, cliente, stats, warnings)

    def _procesar_hijo(self, fila, n, cliente, stats, warnings):
        nombre = (fila.get(f"hijo{n}_nombre") or "").strip()
        apellido = (fila.get(f"hijo{n}_apellido") or "").strip()

        if not nombre and not apellido:
            return  # slot vacío — familia con menos hijos que el máximo del CSV
        if not nombre or not apellido:
            warnings.append(
                f'hijo{n} de "{cliente.nombres} {cliente.apellidos}" tiene nombre o apellido vacío — se omite ese hijo'
            )
            return

        grado = None
        grado_fila = (fila.get(f"hijo{n}_grado") or "").strip()
        if grado_fila:
            grado = Grado.objects.filter(nombre__iexact=grado_fila).first()
            if grado is None:
                warnings.append(f'"{grado_fila}" no coincide con ningún Grado existente — {nombre} {apellido} queda sin grado asignado')

        fecha_nacimiento = None
        fecha_fila = (fila.get(f"hijo{n}_fecha_nacimiento") or "").strip()
        if fecha_fila:
            fecha_nacimiento = _parsear_fecha(fecha_fila)
            if fecha_nacimiento is None:
                warnings.append(f'Fecha de nacimiento inválida "{fecha_fila}" para {nombre} {apellido} — se deja vacía')

        hijo, hijo_creado = Hijo.objects.get_or_create(
            cliente_responsable=cliente,
            nombre=nombre,
            apellido=apellido,
            defaults={"fecha_nacimiento": fecha_nacimiento, "grado": grado},
        )
        if hijo_creado:
            stats["hijos_creados"] += 1
        else:
            stats["hijos_omitidos"] += 1

        nro_tarjeta = (fila.get(f"hijo{n}_tarjeta") or "").strip()
        if nro_tarjeta:
            self._procesar_tarjeta(nro_tarjeta, hijo, stats, warnings)

    def _procesar_tarjeta(self, nro_tarjeta, hijo, stats, warnings):
        existente = Tarjeta.objects.filter(pk=nro_tarjeta).first()
        if existente:
            if existente.hijo_id == hijo.id:
                return  # ya estaba correctamente vinculada, nada que hacer
            titular = existente.hijo or existente.cliente_directo
            warnings.append(
                f'Tarjeta "{nro_tarjeta}" ya está registrada a nombre de {titular} — '
                f'no se reasigna a {hijo.nombre} {hijo.apellido}, revisar a mano'
            )
            return

        tarjeta_previa = Tarjeta.objects.filter(hijo=hijo).first()
        if tarjeta_previa:
            warnings.append(
                f'{hijo.nombre} {hijo.apellido} ya tiene la tarjeta "{tarjeta_previa.pk}" asociada — '
                f'no se crea "{nro_tarjeta}" adicional'
            )
            return

        Tarjeta.objects.create(nro_tarjeta=nro_tarjeta, hijo=hijo)
        stats["tarjetas_creadas"] += 1

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
        self.stdout.write(f"Tarjetas vinculadas: {stats['tarjetas_creadas']}")

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
