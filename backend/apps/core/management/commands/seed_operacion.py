"""
Seed de datos operativos "normales" (no demo) para probar el sistema completo.

Genera un historial realista de ~10-12 semanas de operación de la cantina sobre
los datos base que ya crea `seed_uat` (familias, tarjetas, catálogo, usuarios):
impuestos, empresa, ventas diarias con cierres de caja, movimientos de tarjeta
(recargas + consumos), compras a proveedores, consumo de almuerzo, alérgenos,
cuenta corriente con deuda de un par de familias, y vencimientos de stock.

Requiere haber corrido antes:
    python manage.py seed_uat

Idempotencia: NO es totalmente idempotente (genera historial aleatorio con
`random.seed` fijo). Usar --reset para vaciar lo generado por este comando
antes de recrearlo. Correrlo dos veces sin --reset duplica ventas/compras.

Uso:
    python manage.py seed_operacion
    python manage.py seed_operacion --reset
    python manage.py seed_operacion --dias 75
"""

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

RANDOM_SEED = 20260804


class Command(BaseCommand):
    help = "Genera historial operativo realista (ventas, caja, compras, almuerzo, deuda) para pruebas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina los datos generados por este comando antes de recrearlos.",
        )
        parser.add_argument(
            "--dias",
            type=int,
            default=75,
            help="Cantidad de días hacia atrás a simular (default: 75).",
        )
        parser.add_argument(
            "--cajas",
            default="",
            help=(
                "Nombres de Caja (separados por coma) a usar para las ventas simuladas. "
                "Vacío (default) = todas las Caja activas."
            ),
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== seed_operacion ==="))
        random.seed(RANDOM_SEED)
        self.dias = options["dias"]
        self.nombres_cajas = [n.strip() for n in options["cajas"].split(",") if n.strip()]

        self._cargar_referencias()

        with transaction.atomic():
            if options["reset"]:
                self._reset()

            self._seed_fiscal()
            self._seed_empresa()
            self._seed_condicion_venta()
            self._seed_alergenos()

        # Fuera de la transacción grande: cada día/venta hace sus propios
        # transaction.atomic() internos (VentaService, CompraService, etc.)
        self._preparar_deudores()
        self._bump_stock_inicial()
        self._simular_operacion_diaria()
        self._seed_compras_historicas()
        self._seed_notas_credito()
        self._seed_vencimientos()

        self.stdout.write(self.style.SUCCESS("\nseed_operacion completado exitosamente."))

    # =========================================================================
    # REFERENCIAS BASE (deben existir por seed_uat)
    # =========================================================================

    def _cargar_referencias(self):
        from apps.usuarios.models import Usuario
        from apps.core.models import Tarjeta, MedioPago
        from apps.clientes.models import Cliente
        from apps.contabilidad.models import Caja
        from apps.productos.models import Producto
        from apps.compras.models import Proveedor

        self.cajero = Usuario.objects.filter(rol=Usuario.Rol.CAJERO, is_active=True).first()
        self.supervisor = Usuario.objects.filter(rol=Usuario.Rol.SUPERVISOR, is_active=True).first()
        self.admin = Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True).first()
        self.cocina = Usuario.objects.filter(rol=Usuario.Rol.COCINA, is_active=True).first()
        if not (self.cajero and self.admin):
            raise RuntimeError(
                "Faltan usuarios base (cajero/admin). Ejecutá primero: "
                "python manage.py seed_uat"
            )

        self.tarjetas = list(
            Tarjeta.objects.filter(estado=Tarjeta.Estado.ACTIVA, hijo__isnull=False)
            .select_related("hijo", "hijo__cliente_responsable")
        )
        if not self.tarjetas:
            raise RuntimeError("No hay tarjetas activas. Ejecutá primero: python manage.py seed_uat")

        self.medio_efectivo = MedioPago.objects.filter(descripcion="Efectivo").first()
        self.medio_pos = MedioPago.objects.filter(descripcion__icontains="POS").first()
        self.medio_transferencia = MedioPago.objects.filter(descripcion="Transferencia").first()

        cajas_qs = Caja.objects.filter(activo=True)
        if self.nombres_cajas:
            cajas_qs = cajas_qs.filter(nombre__in=self.nombres_cajas)
            faltantes = set(self.nombres_cajas) - set(cajas_qs.values_list("nombre", flat=True))
            if faltantes:
                raise RuntimeError(f"No se encontraron estas cajas (activas): {', '.join(sorted(faltantes))}")
        self.cajas = list(cajas_qs)
        self.productos = list(Producto.objects.filter(activo=True))
        self.proveedores = list(Proveedor.objects.filter(activo=True))
        self.clientes_familias = list(
            Cliente.objects.filter(activo=True, hijos__isnull=False).distinct()
        )

    def _reset(self):
        """
        Orden de borrado respetando FKs on_delete=PROTECT:
        PagoVenta→Venta, MovimientoCaja→CierreCaja, PagoCuentaAlmuerzo→CuentaAlmuerzoMensual,
        ProductoImpuesto→Impuesto, Factura→Venta (OneToOne).
        """
        from apps.ventas.models import Venta, PagoVenta, NotaCredito
        from apps.contabilidad.models import CierreCaja, MovimientoCaja, DatosEmpresa, Factura
        from apps.compras.models import (
            Compra, OrdenCompra, PagoProveedor, CuentaCorrienteProveedor,
        )
        from apps.almuerzos.models import (
            RegistroConsumoAlmuerzo, CuentaAlmuerzoMensual, PagoCuentaAlmuerzo, Alergeno,
        )
        from apps.inventario.models import LoteProducto
        from apps.productos.models import Impuesto, ProductoImpuesto
        from apps.core.models import MovimientoTarjeta, Tarjeta
        from apps.clientes.models import CuentaCorrienteCliente, RestriccionHijo

        self.stdout.write("  Reseteando datos de seed_operacion...")

        Factura.objects.all().delete()
        PagoVenta.objects.all().delete()  # cascadea AplicacionPago
        MovimientoCaja.objects.all().delete()
        NotaCredito.objects.all().delete()  # cascadea DetalleNotaCredito
        Venta.objects.all().delete()  # cascadea DetalleVenta
        CierreCaja.objects.all().delete()

        PagoProveedor.objects.all().delete()  # cascadea AplicacionPagoCompra
        CuentaCorrienteProveedor.objects.all().delete()
        Compra.objects.all().delete()  # cascadea DetalleCompra
        OrdenCompra.objects.all().delete()

        PagoCuentaAlmuerzo.objects.all().delete()
        CuentaAlmuerzoMensual.objects.all().delete()
        RegistroConsumoAlmuerzo.objects.all().delete()
        Alergeno.objects.all().delete()  # cascadea ProductoAlergeno
        RestriccionHijo.objects.all().delete()

        LoteProducto.objects.all().delete()  # cascadea AlertaVencimiento

        ProductoImpuesto.objects.all().delete()
        Impuesto.objects.all().delete()

        from apps.ventas.models import CondicionVenta
        CondicionVenta.objects.all().delete()
        DatosEmpresa.objects.all().delete()

        MovimientoTarjeta.objects.all().delete()
        for t in Tarjeta.objects.all():
            t.saldo_actual = Decimal("0")
            t.save(update_fields=["saldo_actual"])
        CuentaCorrienteCliente.objects.all().delete()

    # =========================================================================
    # FISCAL: IMPUESTOS
    # =========================================================================

    def _seed_fiscal(self):
        from apps.productos.models import Impuesto, ProductoImpuesto

        self.stdout.write("\n[1/9] Impuestos...")

        self.iva10, _ = Impuesto.objects.get_or_create(
            nombre="IVA 10%",
            defaults={"porcentaje": Decimal("10.00"), "vigente_desde": date(2020, 1, 1), "activo": True},
        )
        self.iva5, _ = Impuesto.objects.get_or_create(
            nombre="IVA 5%",
            defaults={"porcentaje": Decimal("5.00"), "vigente_desde": date(2020, 1, 1), "activo": True},
        )
        self.exento, _ = Impuesto.objects.get_or_create(
            nombre="Exento",
            defaults={"porcentaje": Decimal("0.00"), "vigente_desde": date(2020, 1, 1), "activo": True},
        )

        # Lácteos y Frutas → IVA 5% (canasta básica); el resto → IVA 10%.
        creados = 0
        for producto in self.productos:
            categoria_nombre = producto.categoria.nombre if producto.categoria_id else ""
            impuesto = self.iva5 if categoria_nombre == "Lácteos y Frutas" else self.iva10
            _, created = ProductoImpuesto.objects.get_or_create(
                producto=producto, impuesto=impuesto
            )
            if created:
                creados += 1
        self.stdout.write(f"    Impuestos: 3 tasas, {creados} asignaciones a productos")

    # =========================================================================
    # DATOS DE EMPRESA
    # =========================================================================

    def _seed_empresa(self):
        from apps.contabilidad.models import DatosEmpresa

        self.stdout.write("\n[2/9] Datos de la empresa...")
        _, created = DatosEmpresa.objects.get_or_create(
            ruc="80099887-3",
            defaults={
                "razon_social": "Cantina Tita S.R.L.",
                "nombre_fantasia": "Cantina Tita",
                "direccion": "Av. Mariscal López 1234",
                "ciudad": "Asunción",
                "pais": "Paraguay",
                "telefono": "021-234567",
                "email": "administracion@cantinatita.com",
                "activo": True,
            },
        )
        self._log("DatosEmpresa", "Cantina Tita S.R.L.", created)

    # =========================================================================
    # CONDICIÓN DE VENTA
    # =========================================================================

    def _seed_condicion_venta(self):
        from apps.ventas.models import CondicionVenta

        self.stdout.write("\n[3/9] Condiciones de venta...")
        CondicionVenta.objects.get_or_create(nombre="Contado", defaults={"plazo_dias": 0})
        CondicionVenta.objects.get_or_create(nombre="Crédito 30 días", defaults={"plazo_dias": 30})
        self.stdout.write("    CondicionVenta: Contado, Crédito 30 días")

    # =========================================================================
    # ALÉRGENOS
    # =========================================================================

    def _seed_alergenos(self):
        from apps.almuerzos.models import Alergeno, ProductoAlergeno
        from apps.clientes.models import RestriccionHijo

        self.stdout.write("\n[4/9] Alérgenos...")

        datos = [
            ("Lactosa", ["leche", "yogurt", "manteca"], Alergeno.Severidad.MEDIA, "🥛"),
            ("Gluten", ["pan", "fideos", "tostada", "sandwich", "empanada", "chipa"], Alergeno.Severidad.ALTA, "🌾"),
            ("Frutos secos", ["alfajor", "chocolate"], Alergeno.Severidad.CRITICA, "🥜"),
            ("Huevo", ["milanesa", "empanada"], Alergeno.Severidad.MEDIA, "🥚"),
        ]
        alergenos = {}
        for nombre, palabras, severidad, icono in datos:
            alergeno, _ = Alergeno.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "palabras_clave": palabras, "severidad": severidad,
                    "icono": icono, "activo": True, "creado_por": self.admin,
                },
            )
            alergenos[nombre] = alergeno

        asignados = 0
        for producto in self.productos:
            desc_lower = producto.descripcion.lower()
            for nombre, alergeno in alergenos.items():
                if any(palabra in desc_lower for palabra in alergeno.palabras_clave):
                    _, created = ProductoAlergeno.objects.get_or_create(
                        producto=producto, alergeno=alergeno
                    )
                    if created:
                        asignados += 1

        # Restricciones para 2 alumnos (texto libre, no ligado a Alergeno)
        hijos_con_tarjeta = [t.hijo for t in self.tarjetas]
        restricciones_creadas = 0
        if len(hijos_con_tarjeta) >= 2:
            for hijo, (tipo, desc, sev) in zip(
                hijos_con_tarjeta[:2],
                [
                    ("Alergia", "Alergia a frutos secos (maní, nueces)", RestriccionHijo.Severidad.CRITICA),
                    ("Intolerancia", "Intolerancia a la lactosa", RestriccionHijo.Severidad.MEDIA),
                ],
            ):
                _, created = RestriccionHijo.objects.get_or_create(
                    hijo=hijo, tipo=tipo,
                    defaults={"descripcion": desc, "severidad": sev, "activo": True},
                )
                if created:
                    restricciones_creadas += 1

        self.stdout.write(
            f"    Alergeno: {len(alergenos)} tipos, {asignados} asignaciones a productos, "
            f"{restricciones_creadas} restricciones de alumnos"
        )

    # =========================================================================
    # DEUDORES: habilitar límite de crédito para un par de familias
    # =========================================================================

    def _preparar_deudores(self):
        self.stdout.write("\n[5/9] Habilitando crédito para familias deudoras...")
        self.clientes_credito = self.clientes_familias[:2]
        for cliente in self.clientes_credito:
            cliente.limite_credito = Decimal("800000")
            cliente.save(update_fields=["limite_credito"])
        self.stdout.write(f"    {len(self.clientes_credito)} familias habilitadas con límite Gs. 800.000")

    # =========================================================================
    # STOCK: buffer inicial para soportar la simulación
    # =========================================================================

    def _bump_stock_inicial(self):
        from apps.inventario.models import Stock

        self.stdout.write("\n[6/9] Ajustando stock inicial...")
        actualizados = 0
        for producto in self.productos:
            stock, _ = Stock.objects.get_or_create(producto=producto, defaults={"cantidad": Decimal("0")})
            if stock.cantidad < 200:
                stock.cantidad = Decimal("200")
                stock.save(update_fields=["cantidad"])
                actualizados += 1
        self.stdout.write(f"    Stock: {actualizados} productos llevados a 200 unidades base")

    # =========================================================================
    # OPERACIÓN DIARIA: caja + ventas + movimientos de tarjeta
    # =========================================================================

    def _calcular_iva_item(self, producto, subtotal):
        """Devuelve el dict de IVA para un item según el impuesto asignado al producto."""
        from apps.productos.models import ProductoImpuesto

        pi = ProductoImpuesto.objects.filter(producto=producto).select_related("impuesto").first()
        if not pi or pi.impuesto.porcentaje == 0:
            return {"monto_exenta": subtotal}
        tasa = pi.impuesto.porcentaje / Decimal("100")
        iva = (subtotal - (subtotal / (1 + tasa))).quantize(Decimal("1"))
        if pi.impuesto.nombre == "IVA 5%":
            return {"iva_5": iva}
        return {"iva_10": iva}

    def _armar_items(self, n_items=None):
        n_items = n_items or random.randint(1, 3)
        elegidos = random.sample(self.productos, k=min(n_items, len(self.productos)))
        items = []
        for producto in elegidos:
            cantidad = Decimal(random.randint(1, 2))
            precio = producto.precio_actual or Decimal("5000")
            subtotal = precio * cantidad
            item = {
                "producto": producto, "cantidad": cantidad, "precio_unitario": precio,
            }
            item.update(self._calcular_iva_item(producto, subtotal))
            items.append(item)
        return items

    def _backdate(self, venta, fecha_dt):
        """Ajusta fecha/fecha_creacion de la venta y sus registros derivados."""
        from apps.ventas.models import Venta, PagoVenta
        from apps.inventario.models import MovimientoStock
        from apps.contabilidad.models import MovimientoCaja
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.core.models import MovimientoTarjeta

        Venta.objects.filter(pk=venta.pk).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
        MovimientoStock.objects.filter(venta=venta).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
        PagoVenta.objects.filter(venta=venta).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
        MovimientoCaja.objects.filter(venta=venta).update(fecha=fecha_dt)
        CuentaCorrienteCliente.objects.filter(venta=venta).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
        if venta.tarjeta_id:
            MovimientoTarjeta.objects.filter(
                tarjeta_id=venta.tarjeta_id, descripcion=f"Venta #{venta.pk}"
            ).update(fecha=fecha_dt, fecha_creacion=fecha_dt)

    def _recargar_tarjeta(self, tarjeta, fecha_dt, cajero):
        from apps.core.models import MovimientoTarjeta, Tarjeta

        monto = Decimal(random.choice([30000, 50000, 70000, 100000]))
        saldo_antes = tarjeta.saldo_actual
        Tarjeta.objects.filter(pk=tarjeta.pk).update(saldo_actual=saldo_antes + monto)
        tarjeta.saldo_actual = saldo_antes + monto
        mov = MovimientoTarjeta.objects.create(
            tarjeta=tarjeta, tipo=MovimientoTarjeta.Tipo.RECARGA, monto=monto,
            saldo_anterior=saldo_antes, saldo_resultante=saldo_antes + monto,
            descripcion="Recarga de saldo", creado_por=cajero,
        )
        MovimientoTarjeta.objects.filter(pk=mov.pk).update(fecha=fecha_dt, fecha_creacion=fecha_dt)

    def _simular_operacion_diaria(self):
        from apps.ventas.services import VentaService
        from apps.contabilidad.models import CierreCaja, MovimientoCaja

        self.stdout.write(f"\n[7/9] Simulando {self.dias} días de operación...")

        hoy = date.today()
        ventas_creadas = 0
        cierres_creados = 0

        for dias_atras in range(self.dias, -1, -1):
            fecha_dia = hoy - timedelta(days=dias_atras)
            if fecha_dia.weekday() >= 5:  # fines de semana: cantina cerrada
                continue

            for caja in self.cajas:
                apertura_dt = timezone.make_aware(datetime.combine(fecha_dia, time(7, 0)))
                cierre = CierreCaja.objects.create(
                    caja=caja, empleado=self.cajero,
                    monto_inicial=Decimal("200000"),
                    estado=CierreCaja.Estado.ABIERTO,
                )
                CierreCaja.objects.filter(pk=cierre.pk).update(
                    fecha_apertura=apertura_dt, fecha_creacion=apertura_dt
                )
                cierre.fecha_apertura = apertura_dt

                n_ventas = random.randint(6, 14)
                for i in range(n_ventas):
                    hora = time(7 + (i * 8 // max(n_ventas, 1)) % 8, random.randint(0, 59))
                    fecha_venta = timezone.make_aware(datetime.combine(fecha_dia, hora))

                    roll = random.random()
                    try:
                        if roll < 0.70:
                            # Pago con tarjeta prepago. VentaService debita su propia
                            # instancia (select_for_update), no la de self.tarjetas — hay
                            # que releer el saldo real antes de decidir si recargar.
                            tarjeta = random.choice(self.tarjetas)
                            tarjeta.refresh_from_db(fields=["saldo_actual"])
                            if tarjeta.saldo_actual < 30000:
                                self._recargar_tarjeta(tarjeta, fecha_venta, self.cajero)
                            venta = VentaService.registrar_venta(
                                cliente=tarjeta.hijo.cliente_responsable,
                                cajero=self.cajero, tipo="CONTADO",
                                tarjeta=tarjeta, hijo=tarjeta.hijo,
                                items=self._armar_items(), cierre_caja=cierre,
                            )
                        elif roll < 0.90:
                            # Efectivo o POS sin tarjeta
                            medio = random.choice([m for m in [self.medio_efectivo, self.medio_pos] if m])
                            tarjeta_ref = random.choice(self.tarjetas)
                            venta = VentaService.registrar_venta(
                                cliente=tarjeta_ref.hijo.cliente_responsable,
                                cajero=self.cajero, tipo="CONTADO",
                                medio_pago=medio, hijo=tarjeta_ref.hijo,
                                items=self._armar_items(), cierre_caja=cierre,
                            )
                        else:
                            # Crédito (solo familias habilitadas)
                            cliente_credito = random.choice(self.clientes_credito)
                            hijo_credito = cliente_credito.hijos.filter(activo=True).first()
                            venta = VentaService.registrar_venta(
                                cliente=cliente_credito,
                                cajero=self.cajero, tipo="CREDITO",
                                hijo=hijo_credito,
                                items=self._armar_items(n_items=1), cierre_caja=cierre,
                            )
                        self._backdate(venta, fecha_venta)
                        ventas_creadas += 1
                    except Exception:
                        # Stock/saldo insuficiente puntual: se salta esa venta, no aborta el día.
                        continue

                # Cierre de caja: arqueo con pequeña diferencia en ~25% de los casos
                cierre.refresh_from_db()
                esperado = MovimientoCaja.objects.filter(
                    cierre=cierre, tipo=MovimientoCaja.Tipo.INGRESO
                ).aggregate(total=Sum("monto"))["total"] or Decimal("0")
                esperado += cierre.monto_inicial
                diferencia = Decimal("0")
                if random.random() < 0.25:
                    diferencia = Decimal(random.choice([-3000, -1000, 1000, 2000, 5000]))
                contado = esperado + diferencia
                cierre_dt = timezone.make_aware(datetime.combine(fecha_dia, time(15, 0)))
                cierre.monto_contado_fisico = contado
                cierre.diferencia_efectivo = diferencia
                cierre.estado = CierreCaja.Estado.CERRADO
                cierre.fecha_cierre = cierre_dt
                cierre.save(update_fields=[
                    "monto_contado_fisico", "diferencia_efectivo", "estado", "fecha_cierre"
                ])
                cierres_creados += 1

            # Consumo de almuerzo del día (todas las suscripciones activas)
            self._consumo_almuerzo_dia(fecha_dia)

        self.stdout.write(f"    Ventas: {ventas_creadas} | Cierres de caja: {cierres_creados}")

        self._pagar_parcial_deudores(hoy)
        self._liquidar_cuentas_almuerzo_pasadas(hoy)

    def _pagar_parcial_deudores(self, hoy):
        """Paga ~50% de la deuda acumulada de las familias a crédito, dejando saldo real pendiente."""
        from apps.ventas.services import PagoService
        from apps.clientes.models import CuentaCorrienteCliente

        self.stdout.write("\n[7b/9] Pagos parciales de familias a crédito...")
        pagos = 0
        for cliente in self.clientes_credito:
            ultimo = (
                CuentaCorrienteCliente.objects.filter(cliente=cliente).order_by("-id").first()
            )
            saldo = ultimo.saldo_resultante if ultimo else Decimal("0")
            if saldo <= 0:
                continue
            monto = (saldo / 2).quantize(Decimal("1"))
            if monto <= 0:
                continue
            medio = self.medio_transferencia or self.medio_efectivo
            pago = PagoService.registrar_pago(
                cliente=cliente, monto=monto, medio_pago=medio,
                cajero=self.cobrador_o_admin(),
            )
            fecha_pago = timezone.make_aware(
                datetime.combine(hoy - timedelta(days=random.randint(3, 10)), time(10, 0))
            )
            from apps.ventas.models import PagoVenta
            PagoVenta.objects.filter(pk=pago.pk).update(fecha=fecha_pago, fecha_creacion=fecha_pago)
            CuentaCorrienteCliente.objects.filter(pago=pago).update(fecha=fecha_pago, fecha_creacion=fecha_pago)
            pagos += 1
        self.stdout.write(f"    Pagos a cuenta corriente: {pagos}")

    # =========================================================================
    # ALMUERZO: consumo diario + liquidación de meses pasados
    # =========================================================================

    def _consumo_almuerzo_dia(self, fecha_dia):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import SuscripcionAlmuerzo

        suscripciones = SuscripcionAlmuerzo.objects.filter(
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
            fecha_inicio__lte=fecha_dia,
        ).select_related("hijo").filter(
            hijo__tarjeta__isnull=False, hijo__tarjeta__estado="ACTIVA"
        )
        for susc in suscripciones:
            if random.random() > 0.85:  # ~85% asistencia en día hábil
                continue
            try:
                AlmuerzoService.registrar_consumo(
                    hijo=susc.hijo, fecha_consumo=fecha_dia,
                    nro_tarjeta=susc.hijo.tarjeta, registrado_por=self.cocina or self.cajero,
                    suscripcion=susc,
                )
            except Exception:
                continue

    def _liquidar_cuentas_almuerzo_pasadas(self, hoy):
        from apps.almuerzos.models import CuentaAlmuerzoMensual, PagoCuentaAlmuerzo

        self.stdout.write("\n[8/9] Liquidando cuentas de almuerzo de meses cerrados...")
        mes_actual = (hoy.year, hoy.month)
        cuentas = CuentaAlmuerzoMensual.objects.exclude(
            anio=mes_actual[0], mes=mes_actual[1]
        ).filter(estado=CuentaAlmuerzoMensual.Estado.PENDIENTE)

        pagadas = 0
        for cuenta in cuentas:
            # ~80% de las cuentas de meses cerrados quedan pagadas, el resto pendiente (deuda real)
            if random.random() > 0.20:
                monto = cuenta.saldo_pendiente
                if monto <= 0:
                    continue
                medio = random.choice(["EFECTIVO", "TRANSFERENCIA"])
                pago = PagoCuentaAlmuerzo.objects.create(
                    cuenta=cuenta, monto=monto, medio_pago=medio,
                    registrado_por=self.cobrador_o_admin(), observaciones="Pago mensual",
                )
                cuenta.registrar_pago(monto)
                pagadas += 1

        self.stdout.write(f"    CuentaAlmuerzoMensual: {cuentas.count()} de meses pasados, {pagadas} liquidadas")

    def cobrador_o_admin(self):
        from apps.usuarios.models import Usuario
        return Usuario.objects.filter(rol=Usuario.Rol.COBRADOR, is_active=True).first() or self.admin

    # =========================================================================
    # COMPRAS HISTÓRICAS
    # =========================================================================

    def _seed_compras_historicas(self):
        from apps.compras.services import CompraService
        from apps.compras.models import PagoProveedor, AplicacionPagoCompra, CuentaCorrienteProveedor, Compra
        from apps.core.models import MedioPago

        self.stdout.write("\n[9/9] Compras históricas a proveedores...")

        hoy = date.today()
        medio_transferencia = self.medio_transferencia or self.medio_efectivo
        creadas = 0
        pagadas = 0

        for semana in range(self.dias // 7):
            fecha_compra = hoy - timedelta(days=semana * 7 + random.randint(0, 3))
            proveedor = random.choice(self.proveedores)
            productos_compra = random.sample(self.productos, k=min(4, len(self.productos)))
            items = [
                {
                    "producto": p,
                    "cantidad": Decimal(random.randint(20, 80)),
                    "costo_unitario": (p.precio_actual or Decimal("5000")) * Decimal("0.6"),
                }
                for p in productos_compra
            ]
            tipo_pago = "CREDITO" if random.random() < 0.4 else "CONTADO"
            try:
                compra = CompraService.registrar_compra(
                    proveedor=proveedor, creado_por=self.admin, tipo_pago=tipo_pago,
                    medio_pago=None if tipo_pago == "CREDITO" else medio_transferencia,
                    items=items,
                    nro_factura_proveedor=f"001-001-{1000 + creadas:07d}",
                )
            except Exception:
                continue

            fecha_dt = timezone.make_aware(datetime.combine(fecha_compra, time(9, 0)))
            Compra.objects.filter(pk=compra.pk).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
            from apps.inventario.models import MovimientoStock, CostoHistorico
            MovimientoStock.objects.filter(compra=compra).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
            CostoHistorico.objects.filter(compra=compra).update(fecha_compra=fecha_dt)
            CuentaCorrienteProveedor.objects.filter(compra=compra).update(fecha=fecha_dt, fecha_creacion=fecha_dt)
            creadas += 1

            # ~70% de las compras a crédito ya fueron pagadas (total o parcial)
            if tipo_pago == "CREDITO" and random.random() < 0.7:
                monto_pago = compra.monto_total if random.random() < 0.6 else compra.monto_total // 2
                pago = PagoProveedor.objects.create(
                    proveedor=proveedor, monto_total=monto_pago,
                    medio_pago=medio_transferencia, creado_por=self.admin,
                    estado=PagoProveedor.Estado.CONCILIADO,
                )
                AplicacionPagoCompra.objects.create(pago=pago, compra=compra, monto_aplicado=monto_pago)
                nuevo_estado = "PAGADO" if monto_pago >= compra.monto_total else "PARCIAL"
                Compra.objects.filter(pk=compra.pk).update(estado_pago=nuevo_estado)
                CuentaCorrienteProveedor.objects.create(
                    proveedor=proveedor, tipo=CuentaCorrienteProveedor.Tipo.CREDITO,
                    monto=monto_pago, pago=pago, compra=compra,
                    descripcion=f"Pago compra #{compra.pk}", creado_por=self.admin,
                )
                pago_fecha = fecha_dt + timedelta(days=random.randint(1, 15))
                PagoProveedor.objects.filter(pk=pago.pk).update(fecha=pago_fecha, fecha_creacion=pago_fecha)
                CuentaCorrienteProveedor.objects.filter(pago=pago).update(fecha=pago_fecha, fecha_creacion=pago_fecha)
                pagadas += 1

        self.stdout.write(f"    Compra: {creadas} creadas, {pagadas} con pago registrado")

    # =========================================================================
    # NOTAS DE CRÉDITO (devoluciones puntuales)
    # =========================================================================

    def _seed_notas_credito(self):
        from apps.ventas.models import Venta, NotaCredito, DetalleNotaCredito

        self.stdout.write("\n[+] Notas de crédito de devolución...")
        candidatas = list(
            Venta.objects.filter(estado="ACTIVA", tipo="CONTADO").order_by("?")[:6]
        )
        creadas = 0
        for i, venta in enumerate(candidatas):
            detalle = venta.detalles.first()
            if not detalle:
                continue
            nc = NotaCredito.objects.create(
                cliente=venta.cliente, venta_origen=venta,
                nro_nota_credito=f"NC-{date.today().year}-{1000 + i:04d}",
                monto_total=detalle.subtotal,
                motivo="Devolución de producto — cliente no conforme",
                estado=NotaCredito.Estado.EMITIDA,
                empleado_autoriza=self.supervisor or self.admin,
            )
            DetalleNotaCredito.objects.create(
                nota_credito=nc, producto=detalle.producto, cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario, subtotal=detalle.subtotal,
            )
            creadas += 1
        self.stdout.write(f"    NotaCredito: {creadas} creadas")

    # =========================================================================
    # VENCIMIENTOS
    # =========================================================================

    def _seed_vencimientos(self):
        from apps.inventario.models import LoteProducto, AlertaVencimiento

        self.stdout.write("\n[+] Lotes y alertas de vencimiento...")
        hoy = date.today()
        productos_perecederos = [
            p for p in self.productos
            if p.categoria_id and p.categoria.nombre in ("Lácteos y Frutas", "Comidas")
        ]
        creados = 0
        alertas = 0
        for i, producto in enumerate(productos_perecederos):
            dias_venc = random.choice([-3, 2, 5, 15, 45])  # algunos ya vencidos, otros próximos
            fecha_venc = hoy + timedelta(days=dias_venc)
            lote = LoteProducto.objects.create(
                producto=producto, numero_lote=f"L{hoy.strftime('%Y%m')}-{i+1:03d}",
                fecha_fabricacion=fecha_venc - timedelta(days=60),
                fecha_vencimiento=fecha_venc,
                cantidad_inicial=Decimal("50"), cantidad_disponible=Decimal("30"),
                bloqueado=dias_venc < 0,
                motivo_bloqueo=LoteProducto.MotivoBloqueo.VENCIDO if dias_venc < 0 else None,
            )
            creados += 1
            if dias_venc <= 30:
                tipo = AlertaVencimiento.TipoAlerta.VENCIDO if dias_venc < 0 else (
                    AlertaVencimiento.TipoAlerta.DIAS_3 if dias_venc <= 3 else (
                        AlertaVencimiento.TipoAlerta.DIAS_7 if dias_venc <= 7 else (
                            AlertaVencimiento.TipoAlerta.DIAS_15 if dias_venc <= 15 else
                            AlertaVencimiento.TipoAlerta.DIAS_30
                        )
                    )
                )
                AlertaVencimiento.objects.create(
                    lote=lote, tipo=tipo, dias_restantes=dias_venc,
                    fecha_vencimiento=fecha_venc, cantidad_lote=lote.cantidad_disponible,
                )
                alertas += 1
        self.stdout.write(f"    LoteProducto: {creados} creados, {alertas} con alerta activa")

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _log(self, model: str, name: str, created: bool):
        prefix = "+" if created else "="
        self.stdout.write(f"    {prefix} {model}: {name}")
