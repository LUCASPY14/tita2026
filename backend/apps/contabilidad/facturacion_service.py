"""
Servicio de facturación física (timbrada) – Epson LX-50.

Flujo:
  1. get_cola()         → items pagados sin factura, agrupados por cliente
  2. emitir()           → crea DocumentosTributarios, vincula ventas y/o almuerzos
  3. texto_impresion()  → texto 80 columnas listo para la matricial
"""

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.contabilidad.models import DocumentosTributarios, Timbrados

# ─── helpers ─────────────────────────────────────────────────────────────────

MESES = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

MESES_CORTO = [
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]

W = 80  # ancho de línea impresora


def _center(text: str) -> str:
    return text.center(W)


def _row(left: str, right: str) -> str:
    space = W - len(left) - len(right)
    return left + " " * max(space, 1) + right


def _init_cliente(c) -> dict:
    return {
        "id_cliente": c.id_cliente,
        "nombres": c.nombres,
        "apellidos": c.apellidos,
        "nombre_completo": f"{c.apellidos}, {c.nombres}",
        "ruc_ci": c.ruc_ci,
        "ventas": [],
        "almuerzos": [],
        "total_pendiente": Decimal("0"),
    }


# ─── servicio ─────────────────────────────────────────────────────────────────


class FacturacionService:

    # ── cola ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_cola() -> list:
        """
        Devuelve la lista de clientes con items pagados pendientes de facturar.

        Ventas incluidas: genera_factura_legal=True, pagadas, sin documento.
        Almuerzos incluidos: con monto_pagado > 0, sin documento.
        """
        from apps.almuerzos.models import CuentasAlmuerzoMensual
        from apps.ventas.models import Ventas

        ventas_qs = (
            Ventas.objects.filter(
                genera_factura_legal=True,
                id_documento__isnull=True,
                estado_pago__iexact="pagada",
                estado__iexact="activa",
            )
            .select_related("id_cliente")
            .order_by("id_cliente", "fecha")
        )

        almuerzos_qs = (
            CuentasAlmuerzoMensual.objects.filter(
                id_documento__isnull=True,
                monto_pagado__gt=0,
            )
            .select_related("id_hijo__id_cliente_responsable")
            .order_by("id_hijo__id_cliente_responsable", "anio", "mes")
        )

        clientes: dict = {}

        for venta in ventas_qs:
            cid = venta.id_cliente_id
            if cid not in clientes:
                clientes[cid] = _init_cliente(venta.id_cliente)
            clientes[cid]["ventas"].append(
                {
                    "id": venta.id_venta,
                    "tipo": "venta",
                    "fecha": venta.fecha.strftime("%d/%m/%Y %H:%M"),
                    "descripcion": f"Venta POS #{venta.id_venta}  ({venta.fecha.strftime('%d/%m/%Y')})",
                    "monto": float(venta.monto_total),
                }
            )
            clientes[cid]["total_pendiente"] += venta.monto_total

        for cuenta in almuerzos_qs:
            hijo = cuenta.id_hijo
            cid = hijo.id_cliente_responsable_id
            if cid not in clientes:
                clientes[cid] = _init_cliente(hijo.id_cliente_responsable)
            desc = f"Almuerzos {MESES_CORTO[cuenta.mes]} {cuenta.anio}" f" – {hijo.nombre} {hijo.apellido}"
            clientes[cid]["almuerzos"].append(
                {
                    "id": cuenta.id_cuenta,
                    "tipo": "almuerzo",
                    "fecha": f"{MESES[cuenta.mes]} {cuenta.anio}",
                    "descripcion": desc,
                    "monto": float(cuenta.monto_pagado),
                }
            )
            clientes[cid]["total_pendiente"] += cuenta.monto_pagado

        # Convertir Decimal a float para serialización y ordenar por apellido
        result = []
        for item in sorted(clientes.values(), key=lambda x: x["apellidos"] + x["nombres"]):
            item["total_pendiente"] = float(item["total_pendiente"])
            result.append(item)

        return result

    # ── emitir ────────────────────────────────────────────────────────────────

    @staticmethod
    def emitir(
        id_cliente: int,
        nro_preimpreso: int,
        ventas_ids: list,
        almuerzos_ids: list,
        condicion_venta: str = "CONTADO",
        plazo_dias: int | None = None,
    ) -> DocumentosTributarios:
        """
        Crea un DocumentosTributarios físico vinculando las ventas y almuerzos indicados.

        El nro_preimpreso es el número del formulario preimpreso que el operador
        toma de la pila (ej: 123 → se registra y formatea como "001-001-0000123").

        Raises:
            ValueError: nro fuera de rango, ya utilizado, sin timbrado
        """
        from apps.almuerzos.models import CuentasAlmuerzoMensual
        from apps.clientes.models import Clientes
        from apps.ventas.models import Ventas

        hoy = datetime.now().date()

        with transaction.atomic():
            # Timbrado vigente con lock para evitar race conditions
            timbrado = (
                Timbrados.objects.select_for_update()
                .filter(estado=True, fecha_inicio__lte=hoy, fecha_fin__gte=hoy)
                .order_by("-fecha_inicio")
                .first()
            )
            if not timbrado:
                raise ValueError("No hay timbrado vigente. Configurá uno en Gestión de Timbrado.")

            # Validar rango
            if not (timbrado.nro_inicial <= nro_preimpreso <= timbrado.nro_final):
                raise ValueError(
                    f"El número {nro_preimpreso} está fuera del rango del timbrado "
                    f"({timbrado.nro_inicial:,} – {timbrado.nro_final:,})."
                )

            # Validar que no esté ya emitido
            if DocumentosTributarios.objects.filter(nro_timbrado=timbrado, nro_secuencial=nro_preimpreso).exists():
                raise ValueError(f"El número de factura {nro_preimpreso} ya fue emitido.")

            # Calcular monto total
            monto_ventas = Ventas.objects.filter(id_venta__in=ventas_ids).aggregate(t=Sum("monto_total"))[
                "t"
            ] or Decimal("0")
            monto_alm = CuentasAlmuerzoMensual.objects.filter(id_cuenta__in=almuerzos_ids).aggregate(
                t=Sum("monto_pagado")
            )["t"] or Decimal("0")
            monto_total = monto_ventas + monto_alm

            # Formatear número de comprobante
            punto = timbrado.id_punto
            nro_fmt = f"{punto.codigo_establecimiento}-" f"{punto.codigo_punto_expedicion}-" f"{nro_preimpreso:07d}"

            cliente = Clientes.objects.get(pk=id_cliente)

            # Crear documento tributario
            doc = DocumentosTributarios.objects.create(
                nro_secuencial=nro_preimpreso,
                fecha_emision=datetime.now(),
                monto_total=monto_total,
                nro_timbrado=timbrado,
                tipo_documento="Factura",
                nro_preimpreso_interno=nro_fmt,
                id_cliente=cliente,
                condicion_venta=condicion_venta,
                plazo_dias=plazo_dias,
            )

            # Vincular ventas → FK apunta al documento
            if ventas_ids:
                Ventas.objects.filter(id_venta__in=ventas_ids).update(id_documento=doc)

            # Vincular cuentas almuerzo
            if almuerzos_ids:
                CuentasAlmuerzoMensual.objects.filter(id_cuenta__in=almuerzos_ids).update(
                    id_documento=doc, nro_comprobante=nro_fmt
                )

        return doc

    # ── anular ────────────────────────────────────────────────────────────────

    @staticmethod
    def anular(id_documento: int) -> None:
        """
        Anula un documento: desvincula ventas y almuerzos para que vuelvan a la cola.
        El registro del documento queda con tipo_documento='Factura-Anulada'.
        """
        from apps.almuerzos.models import CuentasAlmuerzoMensual
        from apps.ventas.models import Ventas

        with transaction.atomic():
            doc = DocumentosTributarios.objects.select_for_update().get(pk=id_documento)
            Ventas.objects.filter(id_documento=doc).update(id_documento=None)
            CuentasAlmuerzoMensual.objects.filter(id_documento=doc).update(id_documento=None, nro_comprobante="")
            doc.tipo_documento = "Factura-Anulada"
            doc.save(update_fields=["tipo_documento"])

    # ── texto impresión ───────────────────────────────────────────────────────

    @staticmethod
    def texto_impresion(id_documento: int) -> str:
        """
        Genera texto de 80 columnas para la Epson LX-50 (texto plano, sin ESC/P especial).
        Devuelve string listo para enviar como text/plain.
        """
        from apps.almuerzos.models import CuentasAlmuerzoMensual
        from apps.contabilidad.models import DatosEmpresa
        from apps.ventas.models import Ventas

        doc = DocumentosTributarios.objects.select_related("nro_timbrado__id_punto", "id_cliente").get(pk=id_documento)
        timbrado = doc.nro_timbrado
        empresa = DatosEmpresa.objects.filter(estado=True).first()

        sep = "─" * W
        lines = []

        # ── Encabezado empresa ────────────────────────────────────────────────
        razon = empresa.razon_social if empresa else "CANTINA"
        lines.append(_center(razon))
        if empresa and empresa.ruc:
            lines.append(_center(f"RUC: {empresa.ruc}"))
        if empresa and empresa.direccion:
            lines.append(_center(empresa.direccion))
        if empresa and empresa.telefono:
            lines.append(_center(f"Tel.: {empresa.telefono}"))
        lines.append(sep)

        # ── Datos timbrado / factura ──────────────────────────────────────────
        nro_fac = doc.nro_preimpreso_interno or str(doc.nro_secuencial)
        lines.append(
            _row(
                f"TIMBRADO Nro: {timbrado.nro_timbrado}",
                f"FACTURA Nro: {nro_fac}",
            )
        )
        lines.append(
            _row(
                f"Vigencia: {timbrado.fecha_inicio.strftime('%d/%m/%Y')} – "
                f"{timbrado.fecha_fin.strftime('%d/%m/%Y')}",
                f"Fecha: {doc.fecha_emision.strftime('%d/%m/%Y %H:%M')}",
            )
        )
        lines.append(sep)

        # ── Datos cliente ─────────────────────────────────────────────────────
        cliente = doc.id_cliente
        if cliente:
            nombre = cliente.razon_social or f"{cliente.nombres} {cliente.apellidos}"
            lines.append(f"Cliente : {nombre}")
            lines.append(f"RUC/CI  : {cliente.ruc_ci}")
            if cliente.direccion:
                lines.append(f"Direcc. : {cliente.direccion}")

        # ── Condición de venta ────────────────────────────────────────────────
        condicion_label = doc.get_condicion_venta_display()
        if doc.condicion_venta == "CREDITO" and doc.plazo_dias:
            condicion_label += f" – {doc.plazo_dias} días"
        lines.append(f"Condición: {condicion_label}")
        lines.append(sep)

        # ── Detalle ───────────────────────────────────────────────────────────
        header_desc = "DESCRIPCIÓN"
        header_monto = "MONTO (Gs)"
        lines.append(f"{header_desc:<56}{header_monto:>24}")
        lines.append(sep)

        subtotal = Decimal("0")

        ventas = Ventas.objects.filter(id_documento=doc).order_by("fecha")
        for v in ventas:
            desc = f"Venta POS #{v.id_venta}  {v.fecha.strftime('%d/%m/%Y')}"[:56]
            monto = v.monto_total
            subtotal += monto
            lines.append(f"{desc:<56}{monto:>22,.0f} ")

        almuerzos = CuentasAlmuerzoMensual.objects.filter(id_documento=doc).select_related("id_hijo")
        for cuenta in almuerzos:
            hijo = cuenta.id_hijo
            desc = (f"Almuerzos {MESES[cuenta.mes]} {cuenta.anio}" f" – {hijo.nombre} {hijo.apellido}")[:56]
            monto = cuenta.monto_pagado
            subtotal += monto
            lines.append(f"{desc:<56}{monto:>22,.0f} ")

        lines.append(sep)

        # ── Totales IVA ───────────────────────────────────────────────────────
        iva_10 = (subtotal * Decimal("10") / Decimal("110")).quantize(Decimal("1"))
        base_10 = subtotal - iva_10
        lines.append(_row("  Base gravada IVA 10%:", f"Gs {base_10:>,.0f}"))
        lines.append(_row("  IVA 10% incluido:", f"Gs {iva_10:>,.0f}"))
        lines.append(_row("  Monto exento:", "Gs 0"))
        lines.append(sep)
        lines.append(_row("  TOTAL A PAGAR:", f"Gs {subtotal:>,.0f}"))
        lines.append(sep)
        lines.append(_center("*** GRACIAS POR SU COMPRA ***"))
        lines.append("")

        return "\n".join(lines)
