from datetime import date, datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import (
    Alergenos,
    CuentasAlmuerzoMensual,
    PlanesAlmuerzo,
    PrecioAlmuerzo,
    RegistrosConsumoAlmuerzo,
    SuscripcionesAlmuerzo,
    TiposAlmuerzo,
)
from .serializers import (
    AlergenosSerializer,
    CuentasAlmuerzoMensualSerializer,
    PlanesAlmuerzoSerializer,
    PrecioAlmuerzoSerializer,
    RegistrosConsumoAlmuerzoSerializer,
    SuscripcionesAlmuerzoSerializer,
    TiposAlmuerzoSerializer,
)


def get_precio_almuerzo_activo(fecha=None):
    """Retorna el PrecioAlmuerzo vigente para la fecha dada (hoy si no se especifica)."""
    if fecha is None:
        fecha = date.today()
    return (
        PrecioAlmuerzo.objects.filter(
            fecha_inicio_vigencia__lte=fecha,
            activo=True,
        )
        .filter(Q(fecha_fin_vigencia__isnull=True) | Q(fecha_fin_vigencia__gte=fecha))
        .order_by("-fecha_inicio_vigencia")
        .first()
    )


class PlanesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PlanesAlmuerzo.objects.all()
    serializer_class = PlanesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado", "tipo_plan"]
    search_fields = ["nombre_plan"]


class PrecioAlmuerzoViewSet(viewsets.ModelViewSet):
    """
    Gestión del historial de precios unitarios del almuerzo.

    GET /precios-almuerzo/precio-actual/  → retorna el precio vigente hoy
    """

    queryset = PrecioAlmuerzo.objects.all()
    serializer_class = PrecioAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["activo"]
    ordering = ["-fecha_inicio_vigencia"]

    @action(detail=False, methods=["get"], url_path="precio-actual")
    def precio_actual(self, request):
        precio = get_precio_almuerzo_activo()
        if precio:
            return Response(PrecioAlmuerzoSerializer(precio).data)
        return Response(
            {"precio_unitario": "25000.00", "mensaje": "Sin precio configurado — usando valor predeterminado"}
        )


class TiposAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TiposAlmuerzo.objects.all()
    serializer_class = TiposAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado"]
    search_fields = ["nombre"]


class SuscripcionesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = SuscripcionesAlmuerzo.objects.all()
    serializer_class = SuscripcionesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "id_hijo", "id_plan_almuerzo"]
    ordering = ["-fecha_inicio"]


class RegistrosConsumoAlmuerzoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar consumos de almuerzo.

    REGLA DE NEGOCIO:
    - La tarjeta se usa SOLO como identificación de acceso al comedor.
    - NO se descuenta saldo de la tarjeta.
    - Máximo 2 registros por alumno por día, pero se factura como 1 ALMUERZO por día:
        · 1.er registro del día: ya_cobrado=True  → se agrega el costo a la cuenta mensual
        · 2.do registro del día: ya_cobrado=False → costo=0, solo trazabilidad operativa
    - Límite de crédito mensual: si el plan tiene limite_credito_mensual, se bloquea
      cuando el monto acumulado en CuentasAlmuerzoMensual alcanza ese tope.
    - Plan tipo 'cantidad': además, se bloquea cuando se superan los días únicos
      de consumo incluidos en la cuota mensual.
    """

    queryset = RegistrosConsumoAlmuerzo.objects.select_related("id_hijo", "nro_tarjeta").all()
    serializer_class = RegistrosConsumoAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "id_hijo", "fecha_consumo", "ya_cobrado"]
    search_fields = ["id_hijo__nombre", "id_hijo__apellido", "nro_tarjeta__nro_tarjeta"]
    ordering = ["-fecha_consumo", "-hora_registro"]

    def perform_create(self, serializer):
        from .validators import validar_limite_registros_diarios

        registro_data = serializer.validated_data
        id_hijo = registro_data.get("id_hijo")
        fecha_consumo = registro_data.get("fecha_consumo")
        nro_tarjeta = registro_data.get("nro_tarjeta")
        id_tipo_almuerzo = registro_data.get("id_tipo_almuerzo")
        id_suscripcion = registro_data.get("id_suscripcion")

        # Tarjeta requerida como identificación
        if not nro_tarjeta:
            raise ValidationError({"error": "Debe especificar la tarjeta para registrar el ingreso al almuerzo"})

        # Validar límite de 2 registros por día (lanza excepción si excede)
        validar_limite_registros_diarios(id_hijo, fecha_consumo)

        # Validar suscripción si se provee
        if id_suscripcion and id_suscripcion.estado != "Activa":
            raise ValidationError(
                {
                    "error": "La suscripción no está activa",
                    "estado_suscripcion": id_suscripcion.estado,
                }
            )

        # ── Determinar si es 1.er o 2.do registro del día ────────────────────
        registros_hoy = RegistrosConsumoAlmuerzo.objects.filter(
            id_hijo=id_hijo,
            fecha_consumo=fecha_consumo,
            estado__in=["Registrado", "Confirmado"],
        ).count()
        es_primer_registro = registros_hoy == 0
        nro_registro_hoy = registros_hoy + 1

        # ── Solo el 1.er registro se factura (= 1 almuerzo/día) ──────────────
        if es_primer_registro:
            # Obtener precio unitario vigente
            precio_obj = get_precio_almuerzo_activo(fecha_consumo)
            if precio_obj:
                costo_calculado = precio_obj.precio_unitario
            elif id_tipo_almuerzo:
                costo_calculado = id_tipo_almuerzo.precio_unitario
            else:
                raise ValidationError(
                    {"error": "No hay precio de almuerzo configurado. Configure un precio vigente primero."}
                )

            plan = id_suscripcion.id_plan_almuerzo if id_suscripcion else None

            # ── Verificar cuota de días para planes tipo 'cantidad' ───────────
            if plan and plan.tipo_plan == "cantidad":
                cuota_dias = plan.cantidad_almuerzos_mes or 0
                if cuota_dias > 0:
                    # Contar días únicos ya consumidos en el mes (no registros individuales)
                    dias_consumidos = (
                        RegistrosConsumoAlmuerzo.objects.filter(
                            id_hijo=id_hijo,
                            id_suscripcion=id_suscripcion,
                            fecha_consumo__year=fecha_consumo.year,
                            fecha_consumo__month=fecha_consumo.month,
                            estado__in=["Registrado", "Confirmado"],
                            ya_cobrado=True,  # solo días ya facturados
                        )
                        .values("fecha_consumo")
                        .distinct()
                        .count()
                    )
                    if dias_consumidos >= cuota_dias:
                        raise ValidationError(
                            {
                                "error": (
                                    f"Cuota mensual alcanzada: el alumno ya consumió {dias_consumidos} "
                                    f"de {cuota_dias} almuerzos incluidos este mes."
                                ),
                                "dias_consumidos": dias_consumidos,
                                "cuota_mensual": cuota_dias,
                            }
                        )

            # ── Verificar límite de crédito mensual ──────────────────────────
            if plan and plan.limite_credito_mensual:
                cuenta_mes = CuentasAlmuerzoMensual.objects.filter(
                    id_hijo=id_hijo,
                    anio=fecha_consumo.year,
                    mes=fecha_consumo.month,
                ).first()
                acumulado = cuenta_mes.monto_total if cuenta_mes else Decimal("0")
                saldo_pendiente = acumulado - (cuenta_mes.monto_pagado if cuenta_mes else Decimal("0"))
                if saldo_pendiente + costo_calculado > plan.limite_credito_mensual:
                    raise ValidationError(
                        {
                            "error": (
                                f"Límite de crédito mensual alcanzado. "
                                f"Saldo pendiente: Gs {saldo_pendiente:,.0f} / "
                                f"Límite: Gs {plan.limite_credito_mensual:,.0f}."
                            ),
                            "saldo_pendiente": float(saldo_pendiente),
                            "limite_credito": float(plan.limite_credito_mensual),
                        }
                    )
        else:
            # 2.do registro del día: trazabilidad sin costo
            costo_calculado = Decimal("0")

        hora_ahora = datetime.now().time()

        with transaction.atomic():
            registro = serializer.save(
                hora_registro=hora_ahora,
                costo_almuerzo=costo_calculado,
                ya_cobrado=es_primer_registro,
                estado="Confirmado",
            )
            # Solo agregar a la cuenta mensual cuando hay costo real (1.er registro)
            if es_primer_registro:
                self._agregar_a_cuenta_mensual(registro)

        registro._nro_registro_hoy = nro_registro_hoy
        registro._precio_usado = float(costo_calculado)

    def _agregar_a_cuenta_mensual(self, registro):
        """
        Agrega el consumo a la cuenta mensual de almuerzo del hijo.
        INDEPENDIENTE del saldo de cantina.
        """
        fecha = registro.fecha_consumo
        plan = None
        forma_cobro = "mensual"
        if registro.id_suscripcion:
            plan = registro.id_suscripcion.id_plan_almuerzo
            forma_cobro = plan.tipo_plan if plan else "mensual"

        cuenta, _ = CuentasAlmuerzoMensual.objects.get_or_create(
            id_hijo=registro.id_hijo,
            anio=fecha.year,
            mes=fecha.month,
            defaults={
                "cantidad_almuerzos": 0,
                "monto_total": 0,
                "monto_pagado": 0,
                "forma_cobro": forma_cobro,
                "estado": "pendiente",
                "fecha_generacion": datetime.now().date(),
                "fecha_actualizacion": datetime.now(),
            },
        )

        cuenta.cantidad_almuerzos = F("cantidad_almuerzos") + 1
        cuenta.monto_total = F("monto_total") + registro.costo_almuerzo
        cuenta.fecha_actualizacion = datetime.now()
        cuenta.save()
        cuenta.refresh_from_db()


class AlergenosViewSet(viewsets.ModelViewSet):
    queryset = Alergenos.objects.all()
    serializer_class = AlergenosSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado", "nivel_severidad"]
    search_fields = ["nombre"]


class CuentasAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = CuentasAlmuerzoMensual.objects.select_related("id_hijo").all()
    serializer_class = CuentasAlmuerzoMensualSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["id_hijo", "anio", "mes", "estado"]
    ordering_fields = ["anio", "mes", "monto_total"]
    ordering = ["-anio", "-mes"]

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _get_datos_empresa():
        from apps.contabilidad.models import DatosEmpresa
        from apps.contabilidad.serializers import DatosEmpresaSerializer

        empresa = DatosEmpresa.objects.filter(estado=True).first()
        return DatosEmpresaSerializer(empresa).data if empresa else {}

    @staticmethod
    def _calcular_iva(monto_total):
        """Calcula IVA 10% incluido (los almuerzos tributan IVA 10%)."""
        from decimal import Decimal

        monto = Decimal(str(monto_total))
        iva_10 = (monto * Decimal("10") / Decimal("110")).quantize(Decimal("1"))
        base_10 = monto - iva_10
        return {
            "base_imponible_10": str(base_10),
            "iva_10": str(iva_10),
            "base_imponible_5": "0",
            "iva_5": "0",
            "monto_exento": "0",
            "total": str(monto),
        }

    # ── acciones de documentos ───────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="recibo-pago")
    def recibo_pago(self, request, pk=None):
        """
        Devuelve todos los datos necesarios para imprimir un RECIBO DE COBRO.
        No genera documento tributario — es solo un comprobante interno de pago.
        """
        cuenta = self.get_object()
        if cuenta.monto_pagado <= 0:
            return Response(
                {"error": "Esta cuenta no tiene pagos registrados para emitir un recibo."},
                status=400,
            )
        hijo = cuenta.id_hijo
        from apps.contabilidad.serializers import DatosEmpresaSerializer

        empresa = self._get_datos_empresa()
        meses_nombre = [
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
        return Response(
            {
                "tipo": "recibo_cobro",
                "empresa": empresa,
                "recibo": {
                    "nro_interno": f"RC-{cuenta.id_cuenta:06d}",
                    "fecha_emision": cuenta.fecha_pago.isoformat() if cuenta.fecha_pago else date.today().isoformat(),
                    "alumno": f"{hijo.nombre} {hijo.apellido}",
                    "concepto": f"Almuerzos escolares – {meses_nombre[cuenta.mes]} {cuenta.anio}",
                    "cantidad_almuerzos": cuenta.cantidad_almuerzos,
                    "monto_total": str(cuenta.monto_total),
                    "monto_cobrado": str(cuenta.monto_pagado),
                    "saldo_pendiente": str(cuenta.monto_total - cuenta.monto_pagado),
                    "forma_pago": cuenta.forma_pago or cuenta.forma_cobro,
                    "comprobante_ref": cuenta.comprobante_pago or "",
                    "estado": cuenta.estado,
                    "mes_nombre": meses_nombre[cuenta.mes],
                    "anio": cuenta.anio,
                },
            }
        )

    @action(detail=True, methods=["post"], url_path="generar-factura")
    def generar_factura(self, request, pk=None):
        """
        Genera (o devuelve) la factura física (timbrada) para la cuenta mensual.

        Reglas:
        - Si ya tiene id_documento, devuelve la factura existente (no duplica).
        - Busca timbrado físico (es_electronico=0) vigente a la fecha de hoy.
        - Asigna el siguiente número secuencial dentro del rango del timbrado.
        - Crea un DocumentosTributarios con tipo 'Factura'.
        - Actualiza la cuenta con id_documento + nro_comprobante.
        """
        from django.db.models import Max

        from apps.contabilidad.models import DocumentosTributarios, Timbrados
        from apps.contabilidad.serializers import (
            DocumentosTributariosSerializer,
            TimbradoSerializer,
        )

        cuenta = self.get_object()

        # Si ya fue facturada, devolver la existente
        if cuenta.id_documento_id:
            empresa = self._get_datos_empresa()
            doc = cuenta.id_documento
            timbrado = doc.nro_timbrado
            iva = self._calcular_iva(cuenta.monto_total)
            return Response(
                {
                    "tipo": "factura_fisica",
                    "es_nueva": False,
                    "empresa": empresa,
                    "factura": self._build_factura_payload(cuenta, doc, timbrado, iva),
                }
            )

        # Buscar timbrado vigente
        hoy = date.today()
        timbrado = (
            Timbrados.objects.filter(
                estado=True,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy,
            )
            .order_by("-fecha_inicio")
            .first()
        )

        if not timbrado:
            return Response(
                {"error": "No hay timbrado vigente. Configurá uno en Gestión de Timbrado."},
                status=400,
            )

        # Calcular siguiente secuencial
        ultimo = DocumentosTributarios.objects.filter(nro_timbrado=timbrado).aggregate(maximo=Max("nro_secuencial"))
        siguiente = (ultimo["maximo"] or timbrado.nro_inicial - 1) + 1

        if siguiente > timbrado.nro_final:
            return Response(
                {"error": f"Timbrado {timbrado.nro_timbrado} agotado (último número: {timbrado.nro_final})."},
                status=400,
            )

        # Formatear nro de comprobante: "001-001-0000001"
        punto = timbrado.id_punto
        nro_fmt = f"{punto.codigo_establecimiento}-" f"{punto.codigo_punto_expedicion}-" f"{siguiente:07d}"

        # Crear el documento tributario
        with transaction.atomic():
            doc = DocumentosTributarios.objects.create(
                nro_secuencial=siguiente,
                fecha_emision=datetime.now(),
                monto_total=cuenta.monto_total,
                nro_timbrado=timbrado,
                tipo_documento="Factura",
                nro_preimpreso_interno=nro_fmt,
            )
            cuenta.id_documento = doc
            cuenta.nro_comprobante = nro_fmt
            cuenta.save(update_fields=["id_documento", "nro_comprobante"])

        empresa = self._get_datos_empresa()
        iva = self._calcular_iva(cuenta.monto_total)
        return Response(
            {
                "tipo": "factura_fisica",
                "es_nueva": True,
                "empresa": empresa,
                "factura": self._build_factura_payload(cuenta, doc, timbrado, iva),
            },
            status=201,
        )

    @staticmethod
    def _build_factura_payload(cuenta, doc, timbrado, iva):
        meses_nombre = [
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
        hijo = cuenta.id_hijo
        return {
            "nro_comprobante": doc.nro_preimpreso_interno,
            "nro_timbrado": timbrado.nro_timbrado,
            "timbrado_desde": timbrado.fecha_inicio.isoformat(),
            "timbrado_hasta": timbrado.fecha_fin.isoformat(),
            "fecha_emision": doc.fecha_emision.strftime("%d/%m/%Y %H:%M"),
            "alumno": f"{hijo.nombre} {hijo.apellido}",
            "concepto": f"Almuerzos escolares – {meses_nombre[cuenta.mes]} {cuenta.anio}",
            "cantidad_almuerzos": cuenta.cantidad_almuerzos,
            "precio_unitario_promedio": (
                str(cuenta.monto_total / cuenta.cantidad_almuerzos) if cuenta.cantidad_almuerzos else "0"
            ),
            "iva": iva,
            "estado_sifen": doc.estado_sifen or "no_aplica",
            "cdc": doc.cdc or None,
            "mes_nombre": meses_nombre[cuenta.mes],
            "anio": cuenta.anio,
            "id_cuenta": cuenta.id_cuenta,
        }
