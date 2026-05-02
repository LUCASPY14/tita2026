from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.common.permissions import CanManageVentas, IsAdminOrReadOnly
from apps.common.throttling import VentasRateThrottle, BurstRateThrottle
from .models import Ventas, DetallesVenta, PagosVenta, NotasCreditoCliente, Promociones, CondicionVenta
from .serializers import (
    VentasSerializer,
    DetallesVentaSerializer,
    PagosVentaSerializer,
    NotasCreditoClienteSerializer,
    PromocionesSerializer,
    CondicionVentaSerializer,
)
from .services import PromocionService, DevolucionService


class VentasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar ventas.

    Permisos:
    - Admin, Gerentes y Cajeros: Acceso total
    - Otros: Sin acceso
    """

    queryset = Ventas.objects.select_related(
        "id_cliente", "id_empleado_cajero", "id_medio_pago"
    ).prefetch_related("detallesventa_set", "pagosventa_set")
    serializer_class = VentasSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle, BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado_pago", "estado", "tipo_venta", "id_cliente", "fecha"]
    search_fields = ["nro_factura_venta", "id_cliente__nombres", "id_cliente__apellidos"]
    ordering_fields = ["fecha", "monto_total"]
    ordering = ["-fecha"]

    def _calcular_comision(self, medio_pago, monto_base):
        """
        Calcula la comisión según el medio de pago y tarifa vigente.

        Args:
            medio_pago: Instancia de MediosPago
            monto_base: Monto de la venta (sin comisión)

        Returns:
            tuple: (monto_comision, tarifa_aplicada)

        Ejemplo:
            >>> medio_pago = MediosPago('Tarjeta Débito Bancard')
            >>> comision, tarifa = _calcular_comision(medio_pago, Decimal('10000'))
            >>> print(comision)  # 340.00 (3.4%)
        """
        from apps.contabilidad.models import TarifasComision

        # Si no genera comisión, retornar 0
        if not medio_pago.genera_comision:
            return Decimal("0.00"), None

        # Buscar tarifa vigente
        now = timezone.now()
        tarifa = (
            TarifasComision.objects.filter(
                id_medio_pago=medio_pago, estado=True, fecha_inicio_vigencia__lte=now
            )
            .filter(
                models.Q(fecha_fin_vigencia__isnull=True) | models.Q(fecha_fin_vigencia__gte=now)
            )
            .order_by("-fecha_inicio_vigencia")
            .first()
        )

        if not tarifa:
            # No hay tarifa configurada
            return Decimal("0.00"), None

        # Calcular comisión porcentual
        comision = monto_base * tarifa.porcentaje_comision

        # Agregar monto fijo si existe
        if tarifa.monto_fijo_comision:
            comision += tarifa.monto_fijo_comision

        # Redondear a 2 decimales
        return comision.quantize(Decimal("0.01")), tarifa

    def _registrar_pago_con_comision(self, venta, medio_pago, monto_base, referencias=None):
        """
        Registra el pago con comisión separada.

        Reglas Bancard:
        - La factura solo incluye el monto base (productos)
        - La comisión es un recargo aparte (trasladado al cliente)
        - No afecta la base imponible para IVA
        - Se registra en MovimientosCaja como conceptos separados

        Args:
            venta: Instancia de Ventas
            medio_pago: Instancia de MediosPago o ID
            monto_base: Monto de productos (sin comisión)
            referencias: Dict con ref_pago_pos, ref_pg_transf, banco_emisor (opcional)

        Returns:
            PagosVenta: Instancia del pago creado
        """
        from apps.core.models import MediosPago

        referencias = referencias or {}
        
        # Asegurar que medio_pago sea un objeto MediosPago
        if isinstance(medio_pago, int):
            medio_pago = MediosPago.objects.get(id_medio_pago=medio_pago)
        
        # Calcular comisión
        monto_comision, tarifa = self._calcular_comision(medio_pago, monto_base)

        # Crear registro de pago
        pago = PagosVenta.objects.create(
            monto=monto_base,
            monto_comision=monto_comision,
            fecha_pago=timezone.now(),
            estado="confirmado",
            id_medio_pago=medio_pago,
            id_venta=venta,
            referencia_transaccion=f"POS-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            ref_pago_pos=referencias.get('ref_pago_pos'),
            ref_pg_transf=referencias.get('ref_pg_transf'),
            banco_emisor=referencias.get('banco_emisor'),
        )

        return pago

    def _registrar_pagos_multiples(self, venta, pagos_data):
        """
        Registra múltiples pagos para una venta (pago mixto).
        
        Args:
            venta: Instancia de Ventas
            pagos_data: Lista de dicts con {id_medio_pago, monto, ref_pago_pos?, ref_pg_transf?, banco_emisor?}
        
        Returns:
            list: Lista de PagosVenta creados
        
        Raises:
            ValidationError: Si la suma de pagos no coincide con el total de la venta
        """
        from apps.core.models import MediosPago
        import logging
        logger = logging.getLogger(__name__)
        
        # Validar que la suma de pagos coincida con el total
        total_pagos = sum(Decimal(str(p['monto'])) for p in pagos_data)
        if total_pagos != venta.monto_total:
            logger.warning(f"Venta #{venta.id_venta}: suma de pagos no coincide ({total_pagos} vs {venta.monto_total})")
            raise ValidationError({
                'error': 'La suma de pagos no coincide con el total de la venta',
                'total_venta': str(venta.monto_total),
                'total_pagos': str(total_pagos),
                'diferencia': str(abs(venta.monto_total - total_pagos))
            })
        
        pagos_creados = []
        for idx, pago_data in enumerate(pagos_data):
            try:
                medio_pago = MediosPago.objects.get(id_medio_pago=pago_data['id_medio_pago'])
            except MediosPago.DoesNotExist:
                logger.error(f"Medio de pago no encontrado: {pago_data['id_medio_pago']}")
                raise ValidationError({
                    'error': f'Medio de pago no encontrado en pago #{idx + 1}',
                    'id_medio_pago_invalido': pago_data['id_medio_pago'],
                    'mensaje': 'El medio de pago especificado no existe en el sistema'
                })
            
            monto = Decimal(str(pago_data['monto']))
            referencias = {
                'ref_pago_pos': pago_data.get('ref_pago_pos'),
                'ref_pg_transf': pago_data.get('ref_pg_transf'),
                'banco_emisor': pago_data.get('banco_emisor'),
            }
            
            pago = self._registrar_pago_con_comision(venta, medio_pago, monto, referencias)
            pagos_creados.append(pago)
        
        logger.info(f"Venta #{venta.id_venta}: {len(pagos_creados)} pagos registrados (pago mixto)")
        return pagos_creados

    def create(self, request, *args, **kwargs):
        """
        Override para inyectar campos servidor-side antes de validar serializer:
        - monto_total: calculado desde los detalles enviados
        - id_cliente: tomado del hijo (si aplica) o cliente genérico de cantina
        - id_empleado_cajero: el usuario autenticado (o cajero sistema como fallback)
        - estado: 'Activa'
        - estado_pago: 'Pagada'
        """
        from decimal import Decimal as D
        from apps.clientes.models import Clientes, Hijos, TiposCliente
        from apps.productos.models import ListasPrecios
        from apps.usuarios.models import Empleados
        from django.utils import timezone as tz

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

        # 1. monto_total desde detalles
        detalles = data.get('detalles', [])
        if not detalles:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError({'detalles': 'Se requiere al menos un producto.'})
        monto_total = sum(
            D(str(d['total'])) if d.get('total') else
            D(str(d.get('precio_unitario', 0))) * D(str(d.get('cantidad', 1)))
            for d in detalles
        )
        data['monto_total'] = str(monto_total)

        # 2. id_empleado_cajero desde el usuario autenticado
        empleado_cajero = getattr(request.user, 'empleado', None)
        if empleado_cajero:
            data['id_empleado_cajero'] = empleado_cajero.id_empleado
        else:
            emp, _ = Empleados.objects.get_or_create(
                email='cajero@sistema.com',
                defaults={
                    'nombre': 'Cajero', 'apellido': 'Sistema',
                    'fecha_ingreso': tz.now(), 'contrasena_hash': '',
                },
            )
            data['id_empleado_cajero'] = emp.id_empleado

        # 3. id_cliente desde el hijo (si aplica) o cliente genérico
        id_hijo = data.get('id_hijo')
        if id_hijo:
            try:
                hijo = Hijos.objects.get(id_hijo=id_hijo)
                data['id_cliente'] = hijo.id_cliente_responsable_id
            except Hijos.DoesNotExist:
                pass
        if 'id_cliente' not in data or not data['id_cliente']:
            lista, _ = ListasPrecios.objects.get_or_create(nombre_lista='General')
            tipo, _ = TiposCliente.objects.get_or_create(nombre_tipo='General')
            cliente, _ = Clientes.objects.get_or_create(
                ruc_ci='0000000',
                defaults={
                    'nombres': 'Cliente', 'apellidos': 'Genérico',
                    'id_lista': lista, 'id_tipo_cliente': tipo,
                },
            )
            data['id_cliente'] = cliente.id_cliente

        # 4. estado / estado_pago defaults
        data.setdefault('estado', 'Activa')
        data.setdefault('estado_pago', 'Pagada')

        # 5. id_caja: inyectar desde el request para vincular la venta al terminal POS correcto
        if 'id_caja' not in data or not data['id_caja']:
            id_caja_request = request.data.get('id_caja')
            if id_caja_request:
                data['id_caja'] = id_caja_request

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Valida stock y saldo antes de crear venta.
        Aplica todas las reglas de negocio críticas.

        Flujo de validaciones:
        0. VALIDAR LÍMITES POR ROL (nuevo)
        1. VALIDAR STOCK DISPONIBLE
        2. Validar límite de crédito (ventas a crédito)
        3. Validar saldo de tarjeta (compras con tarjeta)
        4. Descontar stock
        5. Registrar pago y comisiones
        6. Registrar autorización (si aplica)

        Reglas de negocio aplicadas:
        - Valida límites de transacción por rol
        - Valida disponibilidad de stock ANTES de vender
        - NO permite saldo negativo sin autorización (tarjetas)
        - Descuenta el saldo de la tarjeta del hijo
        - Registra el consumo en ConsumosTarjeta
        - Calcula comisión POS Bancard (si aplica)
        - Separa monto facturado vs recargo POS
        - Valida límite de crédito para ventas a crédito
        """
        from apps.inventario.services import StockService
        from apps.core.services import AutorizacionService

        venta_data = serializer.validated_data
        id_hijo = venta_data.get("id_hijo")
        id_cliente = venta_data.get("id_cliente")
        monto_total = venta_data.get("monto_total")
        id_medio_pago = venta_data.get("id_medio_pago")
        tipo_venta = venta_data.get("tipo_venta", "Contado")
        autorizado_por = venta_data.get("autorizado_por")

        # VALIDACIÓN -1: LÍMITES POR ROL (NUEVO - Control de autorización)
        empleado_cajero = (
            self.request.user.empleado if hasattr(self.request.user, "empleado") else None
        )
        validacion_limite = {"puede_ejecutar": True, "requiere_autorizacion": False}

        if empleado_cajero:
            validacion_limite = AutorizacionService.validar_operacion(
                empleado=empleado_cajero,
                tipo_operacion="venta",
                monto=monto_total,
                autorizador=autorizado_por,
                motivo=self.request.data.get("motivo_autorizacion", "Venta estándar"),
            )

            if not validacion_limite["puede_ejecutar"]:
                raise ValidationError(
                    {
                        "error": "Requiere autorización de supervisor",
                        "limite_rol": str(validacion_limite["limite"]),
                        "monto_operacion": str(monto_total),
                        "excedente": str(validacion_limite.get("excedente", 0)),
                        "requiere_autorizacion": True,
                        "doble_autorizacion": validacion_limite.get("doble_autorizacion", False),
                        "mensaje": validacion_limite["mensaje"],
                        "errores": validacion_limite["errores"],
                    }
                )

        # VALIDACIÓN 0: STOCK DISPONIBLE (CRÍTICO - Nuevo)
        # Obtener detalles de la venta desde el request
        detalles = self.request.data.get("detalles", [])
        codigo_promocion = self.request.data.get("codigo_promocion")
        aplicar_promociones = self.request.data.get("aplicar_promociones", True)

        if detalles:
            # Preparar items para validación
            items_validacion = []
            for detalle in detalles:
                items_validacion.append(
                    {
                        "id_producto": detalle.get("id_producto"),
                        "cantidad": Decimal(str(detalle.get("cantidad", 0))),
                        "precio": Decimal(str(detalle.get("precio_unitario", 0))),
                    }
                )

            # Validar disponibilidad de TODOS los productos
            validacion_stock = StockService.validar_disponibilidad_multiple(items_validacion)

            if not validacion_stock["todo_disponible"]:
                # Construir mensaje detallado
                productos_faltantes = []
                for item in validacion_stock["productos_faltantes"]:
                    productos_faltantes.append(
                        {
                            "producto": item["producto"]["descripcion"],
                            "codigo": item["producto"]["codigo_barra"],
                            "stock_actual": str(item["stock_actual"]),
                            "cantidad_solicitada": str(item["faltante"] + item["stock_actual"]),
                            "faltante": str(item["faltante"]),
                        }
                    )

                raise ValidationError(
                    {
                        "error": "Stock insuficiente para uno o más productos",
                        "productos_faltantes": productos_faltantes,
                        "mensaje": "No se puede completar la venta. Verifique el stock disponible.",
                    }
                )

        # NUEVO: APLICAR PROMOCIONES (si aplica)
        total_descuentos = Decimal("0.00")
        promociones_a_aplicar = []

        if aplicar_promociones and detalles:
            # Obtener promociones aplicables
            promociones_disponibles = PromocionService.obtener_promociones_aplicables(
                items=items_validacion,
                monto_total=monto_total,
                cliente_id=id_cliente.id_cliente if id_cliente else None,
                codigo_promocion=codigo_promocion,
            )

            # Calcular descuentos
            for promo_dict in promociones_disponibles:
                promo = promo_dict["promocion"]
                descuento = PromocionService.calcular_descuento(
                    promocion=promo, items=items_validacion, monto_total=monto_total
                )

                promociones_a_aplicar.append((promo, descuento))
                total_descuentos += descuento["monto_descuento"]

            # Ajustar monto total con descuentos
            if total_descuentos > 0:
                monto_total_con_descuento = monto_total - total_descuentos
                venta_data["monto_total"] = monto_total_con_descuento

        # VALIDACIÓN 1: Límite de crédito para ventas a crédito
        if tipo_venta and tipo_venta.lower() == "crédito":
            from apps.clientes.models import Clientes

            try:
                cliente = Clientes.objects.get(id_cliente=id_cliente.id_cliente)

                # Verificar si tiene límite de crédito configurado
                if not cliente.limite_credito or cliente.limite_credito == 0:
                    raise ValidationError(
                        {
                            "error": "Cliente no tiene límite de crédito configurado",
                            "cliente": cliente.nombre_completo,
                            "ruc_ci": cliente.ruc_ci,
                            "mensaje": "Este cliente no puede realizar compras a crédito. Configure un límite de crédito primero.",
                        }
                    )

                # Calcular crédito disponible
                credito_usado = cliente.credito_utilizado
                credito_disponible = cliente.credito_disponible

                # Validar si hay crédito suficiente
                if monto_total > credito_disponible:
                    # Si tiene autorización de supervisor, permitir
                    if not autorizado_por:
                        raise ValidationError(
                            {
                                "error": "Excede el límite de crédito del cliente",
                                "cliente": cliente.nombre_completo,
                                "limite_credito": str(cliente.limite_credito),
                                "credito_usado": str(credito_usado),
                                "credito_disponible": str(credito_disponible),
                                "monto_solicitado": str(monto_total),
                                "excedente": str(monto_total - credito_disponible),
                                "requiere_autorizacion": True,
                                "mensaje": "Se requiere autorización de supervisor para exceder el límite de crédito",
                            }
                        )

                # Si está autorizado, inicializar saldo_pendiente
                venta_data["saldo_pendiente"] = monto_total
                venta_data["estado_pago"] = "Pendiente"

            except Clientes.DoesNotExist:
                raise ValidationError({"error": "Cliente no encontrado", "id_cliente": id_cliente})

        # VALIDACIÓN 2: Saldo de tarjeta (para compras con tarjeta de hijo)
        if id_hijo:
            from apps.core.models import Tarjetas

            try:
                # select_for_update MUST be inside atomic block
                with transaction.atomic():
                    tarjeta = Tarjetas.objects.select_for_update().get(id_hijo=id_hijo)

                    # Validar saldo disponible
                    if tarjeta.saldo_actual < monto_total:
                        if not tarjeta.permite_saldo_negativo:
                            raise ValidationError(
                                {
                                    "error": "Saldo insuficiente en la tarjeta",
                                    "saldo_actual": str(tarjeta.saldo_actual),
                                    "monto_requerido": str(monto_total),
                                    "faltante": str(monto_total - tarjeta.saldo_actual),
                                    "requiere_autorizacion": True,
                                    "mensaje": "Se requiere autorización con tarjeta de supervisor para permitir saldo negativo",
                                }
                            )
                        else:
                            # Validar límite de crédito
                            saldo_negativo_proyectado = monto_total - tarjeta.saldo_actual
                            if saldo_negativo_proyectado > tarjeta.limite_credito:
                                raise ValidationError(
                                    {
                                        "error": "Excede el límite de crédito permitido",
                                        "limite_credito": str(tarjeta.limite_credito),
                                        "saldo_negativo_proyectado": str(saldo_negativo_proyectado),
                                        "excedente": str(
                                            saldo_negativo_proyectado - tarjeta.limite_credito
                                        ),
                                    }
                                )

                    venta_obj = serializer.save()
                    self._crear_detalles_venta(venta_obj, detalles)
                    self._descontar_saldo_tarjeta(tarjeta, monto_total, venta_obj)

                    # NUEVO: Descontar stock usando StockService (ACID)
                    self._descontar_stock_venta(venta_obj, detalles)

                    # NUEVO: Aplicar promociones si hay
                    if promociones_a_aplicar:
                        PromocionService.aplicar_promociones_a_venta(
                            venta=venta_obj,
                            promociones_seleccionadas=promociones_a_aplicar,
                            empleado=empleado_cajero,
                        )

                    # Registrar pago(s) con comisión
                    pagos_data = self.request.data.get('pagos_data')
                    if pagos_data and len(pagos_data) > 0:
                        # Pago múltiple (mixto)
                        self._registrar_pagos_multiples(venta_obj, pagos_data)
                    elif id_medio_pago:
                        # Pago simple (compatibilidad con flujo anterior)
                        referencias = {
                            'ref_pago_pos': self.request.data.get('ref_pago_pos'),
                            'ref_pg_transf': self.request.data.get('ref_pg_transf'),
                            'banco_emisor': self.request.data.get('banco_emisor'),
                        }
                        self._registrar_pago_con_comision(
                            venta_obj, id_medio_pago, venta_data["monto_total"], referencias
                        )

                    # Registrar autorización si hubo (auditoría)
                    if autorizado_por and validacion_limite.get("requiere_autorizacion"):
                        AutorizacionService.registrar_autorizacion(
                            tipo_operacion="venta",
                            monto=monto_total,
                            solicitante=empleado_cajero,
                            autorizador=autorizado_por,
                            motivo=self.request.data.get(
                                "motivo_autorizacion", "Excede límite del rol"
                            ),
                            ip_address=self.request.META.get("REMOTE_ADDR"),
                            id_venta=venta_obj,
                        )

            except Tarjetas.DoesNotExist:
                raise ValidationError(
                    {"error": "El hijo no tiene tarjeta asociada", "id_hijo": id_hijo}
                )
        else:
            # Venta sin tarjeta (pago directo)
            with transaction.atomic():
                venta_obj = serializer.save()
                self._crear_detalles_venta(venta_obj, detalles)

                # NUEVO: Descontar stock usando StockService (ACID)
                self._descontar_stock_venta(venta_obj, detalles)

                # NUEVO: Aplicar promociones si hay
                if promociones_a_aplicar:
                    PromocionService.aplicar_promociones_a_venta(
                        venta=venta_obj,
                        promociones_seleccionadas=promociones_a_aplicar,
                        empleado=empleado_cajero,
                    )

                # Registrar pago(s) con comisión
                pagos_data = self.request.data.get('pagos_data')
                if pagos_data and len(pagos_data) > 0:
                    # Pago múltiple (mixto)
                    self._registrar_pagos_multiples(venta_obj, pagos_data)
                elif id_medio_pago:
                    # Pago simple (compatibilidad con flujo anterior)
                    referencias = {
                        'ref_pago_pos': self.request.data.get('ref_pago_pos'),
                        'ref_pg_transf': self.request.data.get('ref_pg_transf'),
                        'banco_emisor': self.request.data.get('banco_emisor'),
                    }
                    self._registrar_pago_con_comision(
                        venta_obj, id_medio_pago, venta_data["monto_total"], referencias
                    )

                # Registrar autorización si hubo (auditoría)
                if autorizado_por and validacion_limite.get("requiere_autorizacion"):
                    AutorizacionService.registrar_autorizacion(
                        tipo_operacion="venta",
                        monto=monto_total,
                        solicitante=empleado_cajero,
                        autorizador=autorizado_por,
                        motivo=self.request.data.get(
                            "motivo_autorizacion", "Excede límite del rol"
                        ),
                        ip_address=self.request.META.get("REMOTE_ADDR"),
                        id_venta=venta_obj,
                    )

    def _descontar_saldo_tarjeta(self, tarjeta, monto, venta):
        """
        Descuenta el saldo de la tarjeta y registra el consumo.
        Este método garantiza la integridad transaccional.
        """
        from apps.core.models import ConsumosTarjeta
        from django.utils import timezone

        # Registrar saldo anterior
        saldo_anterior = tarjeta.saldo_actual

        # Descontar saldo
        tarjeta.saldo_actual -= monto
        tarjeta.save()

        # Registrar consumo en historial
        ConsumosTarjeta.objects.create(
            nro_tarjeta=tarjeta,
            fecha_consumo=venta.fecha,
            monto_consumido=monto,
            detalle=f"Venta #{venta.id_venta} - Cantina",
            saldo_anterior=saldo_anterior,
            saldo_posterior=tarjeta.saldo_actual,
            id_empleado_registro=venta.id_empleado_cajero,
        )

    def _crear_detalles_venta(self, venta, detalles):
        """Crea los registros DetallesVenta para la venta recién creada."""
        from apps.productos.models import Productos

        for detalle in detalles:
            try:
                producto = Productos.objects.get(id_producto=detalle.get('id_producto'))
                DetallesVenta.objects.create(
                    id_venta=venta,
                    id_producto=producto,
                    cantidad=Decimal(str(detalle.get('cantidad', 1))),
                    precio_unitario=Decimal(str(detalle.get('precio_unitario', 0))),
                    subtotal=Decimal(str(detalle.get('precio_unitario', 0))) * Decimal(str(detalle.get('cantidad', 1))),
                )
            except Productos.DoesNotExist:
                raise ValidationError({'error': f"Producto {detalle.get('id_producto')} no encontrado"})

    @action(detail=True, methods=["post"], url_path="emitir_factura")
    def emitir_factura(self, request, pk=None):
        """
        Emite una factura timbrada para una venta pagada sin documento.

        POST /api/v1/ventas/{id}/emitir_factura/

        Body:
        {
            "nro_preimpreso": 123,
            "condicion_venta": "CONTADO",   // opcional, default CONTADO
            "plazo_dias": null               // opcional, para CREDITO
        }
        """
        from apps.contabilidad.facturacion_service import FacturacionService

        venta = self.get_object()

        # Validaciones previas
        if not venta.genera_factura_legal:
            return Response(
                {"error": "Esta venta no requiere factura timbrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if venta.id_documento_id:
            return Response(
                {"error": "Esta venta ya tiene factura emitida."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if venta.estado_pago.lower() != "pagada":
            return Response(
                {"error": "Solo se pueden facturar ventas con estado_pago 'pagada'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nro_preimpreso = request.data.get("nro_preimpreso")
        if not nro_preimpreso:
            return Response(
                {"error": "Se requiere nro_preimpreso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            nro_preimpreso = int(nro_preimpreso)
        except (ValueError, TypeError):
            return Response(
                {"error": "nro_preimpreso debe ser un número entero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        condicion_venta = request.data.get("condicion_venta", "CONTADO")
        plazo_dias = request.data.get("plazo_dias")

        try:
            documento = FacturacionService.emitir(
                id_cliente=venta.id_cliente_id,
                nro_preimpreso=nro_preimpreso,
                ventas_ids=[venta.id_venta],
                almuerzos_ids=[],
                condicion_venta=condicion_venta,
                plazo_dias=plazo_dias,
            )
            return Response(
                {
                    "exito": True,
                    "id_documento": documento.id_documento,
                    "nro_preimpreso_interno": documento.nro_preimpreso_interno,
                    "mensaje": f"Factura {documento.nro_preimpreso_interno} emitida correctamente.",
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Error al emitir factura.", "detalle": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="sin_facturar")
    def sin_facturar(self, request):
        """
        Lista ventas pagadas que requieren factura y aún no la tienen.

        GET /api/v1/ventas/sin_facturar/

        Query params:
          - id_cliente: filtrar por cliente (opcional)
          - fecha_desde: YYYY-MM-DD (opcional)
          - fecha_hasta: YYYY-MM-DD (opcional)
        """
        qs = Ventas.objects.filter(
            genera_factura_legal=True,
            id_documento__isnull=True,
            estado_pago__iexact="pagada",
            estado__iexact="activa",
        ).select_related("id_cliente", "id_medio_pago")

        id_cliente = request.query_params.get("id_cliente")
        if id_cliente:
            qs = qs.filter(id_cliente=id_cliente)

        fecha_desde = request.query_params.get("fecha_desde")
        if fecha_desde:
            qs = qs.filter(fecha__date__gte=fecha_desde)

        fecha_hasta = request.query_params.get("fecha_hasta")
        if fecha_hasta:
            qs = qs.filter(fecha__date__lte=fecha_hasta)

        qs = qs.order_by("id_cliente", "fecha")

        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    def _descontar_stock_venta(self, venta, detalles):
        """
        Descuenta stock usando StockService (centralizado y ACID).

        Este método garantiza:
        - Concurrencia segura con select_for_update()
        - Registro en MovimientosStock
        - Validaciones centralizadas
        - Auditoría completa

        Args:
            venta: Instancia de Ventas
            detalles: Lista de detalles de venta con {id_producto, cantidad}
        """
        from apps.inventario.services import StockService

        # Descontar stock de cada producto
        for detalle in detalles:
            try:
                StockService.reservar_stock(
                    producto_id=detalle.get("id_producto"),
                    cantidad=Decimal(str(detalle.get("cantidad", 0))),
                    empleado=venta.id_empleado_cajero,
                    motivo="venta",
                )
            except ValidationError as e:
                # Si falla el descuento (no debería pasar porque ya validamos)
                # El transaction.atomic() hará rollback automático
                raise ValidationError(
                    {
                        "error": "Error al descontar stock",
                        "detalle": str(e),
                        "producto_id": detalle.get("id_producto"),
                    }
                )


class DetallesVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para detalles de venta.
    """

    queryset = DetallesVenta.objects.all().order_by("pk")
    serializer_class = DetallesVentaSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id_venta", "id_producto"]


class PagosVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos de ventas.
    """

    queryset = PagosVenta.objects.all()
    serializer_class = PagosVentaSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "id_venta", "id_medio_pago"]
    ordering_fields = ["fecha_pago"]
    ordering = ["-fecha_pago"]


class NotasCreditoClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar notas de crédito.

    Endpoints adicionales:
    - POST /crear_devolucion/ : Crea una nota de crédito por devolución
    - POST /validar_devolucion/ : Valida si una devolución es posible
    - POST /{id}/anular/ : Anula una nota de crédito
    """

    queryset = NotasCreditoCliente.objects.all()
    serializer_class = NotasCreditoClienteSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "id_cliente"]
    ordering = ["-fecha_emision"]

    @action(detail=False, methods=["post"])
    def crear_devolucion(self, request):
        """
        Crea una nota de crédito por devolución de productos.

        POST /api/v1/notas-credito/crear_devolucion/

        Body:
        {
            "id_venta": 123,
            "productos": [
                {
                    "id_producto": 1,
                    "cantidad": 2,
                    "motivo_item": "Producto defectuoso"
                }
            ],
            "motivo": "Cliente insatisfecho con calidad",
            "tipo_devolucion": "parcial"
        }
        """
        id_venta = request.data.get("id_venta")
        productos = request.data.get("productos", [])
        motivo = request.data.get("motivo", "")
        tipo_devolucion = request.data.get("tipo_devolucion", "parcial")

        if not id_venta or not productos:
            return Response(
                {"error": "Faltan campos requeridos: id_venta, productos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        empleado = getattr(request.user, "empleado", None)
        if not empleado:
            return Response(
                {"error": "Usuario no tiene empleado asociado"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resultado = DevolucionService.crear_nota_credito(
                id_venta=id_venta,
                productos_devolucion=productos,
                motivo=motivo,
                empleado_autoriza=empleado,
                tipo_devolucion=tipo_devolucion,
            )

            serializer = self.get_serializer(resultado["nota_credito"])

            return Response(
                {
                    "exito": True,
                    "nota_credito": serializer.data,
                    "monto_devuelto": str(resultado["monto_devuelto"]),
                    "mensaje": resultado["mensaje"],
                },
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return Response(
                e.detail if hasattr(e, "detail") else {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"])
    def validar_devolucion(self, request):
        """
        Valida si una devolución es posible antes de crearla.

        POST /api/v1/notas-credito/validar_devolucion/

        Body:
        {
            "id_venta": 123,
            "productos": [
                {"id_producto": 1, "cantidad": 2}
            ]
        }
        """
        id_venta = request.data.get("id_venta")
        productos = request.data.get("productos", [])

        validacion = DevolucionService.validar_productos_devolucion(
            id_venta=id_venta, productos=productos
        )

        return Response(validacion)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        """
        Anula una nota de crédito.

        POST /api/v1/notas-credito/{id}/anular/

        Body:
        {
            "motivo_anulacion": "Error en registro"
        }
        """
        motivo = request.data.get("motivo_anulacion", "")

        if not motivo:
            return Response(
                {"error": "Se requiere motivo de anulación"}, status=status.HTTP_400_BAD_REQUEST
            )

        empleado = getattr(request.user, "empleado", None)

        try:
            resultado = DevolucionService.anular_nota_credito(
                id_nota=pk, empleado_autoriza=empleado, motivo_anulacion=motivo
            )

            return Response(resultado)

        except ValidationError as e:
            return Response(
                e.detail if hasattr(e, "detail") else {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PromocionesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar promociones.

    Permisos:
    - Admin: CRUD completo
    - Otros autenticados: Solo lectura

    Endpoints adicionales:
    - POST /validar_codigo/ : Valida si un código de promoción es válido
    - GET /activas/ : Lista promociones activas actualmente
    """

    queryset = Promociones.objects.all()
    serializer_class = PromocionesSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado", "tipo_promocion"]
    search_fields = ["nombre", "codigo_promocion"]

    @action(detail=False, methods=["post"])
    def validar_codigo(self, request):
        """
        Valida si un código de promoción es válido.

        POST /api/v1/promociones/validar_codigo/

        Body:
        {
            "codigo_promocion": "VERANO2026",
            "monto_total": 50000,
            "productos": [
                {"id_producto": 1, "cantidad": 2, "precio": 25000}
            ],
            "id_cliente": 5
        }

        Returns:
        {
            "valido": true,
            "promocion": {...},
            "descuento_calculado": 5000,
            "mensaje": "Promoción aplicable"
        }
        """
        codigo = request.data.get("codigo_promocion")
        monto_total = Decimal(str(request.data.get("monto_total", 0)))
        productos = request.data.get("productos", [])
        id_cliente = request.data.get("id_cliente")

        if not codigo:
            return Response(
                {"error": "Se requiere código de promoción"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar promociones aplicables con este código
        promociones = PromocionService.obtener_promociones_aplicables(
            items=productos, monto_total=monto_total, cliente_id=id_cliente, codigo_promocion=codigo
        )

        if not promociones:
            return Response(
                {"valido": False, "mensaje": "Código de promoción no válido o no aplicable"}
            )

        # Tomar la primera promoción (mayor prioridad)
        promo_dict = promociones[0]
        promo = promo_dict["promocion"]

        # Calcular descuento
        descuento = PromocionService.calcular_descuento(
            promocion=promo, items=productos, monto_total=monto_total
        )

        serializer = self.get_serializer(promo)

        return Response(
            {
                "valido": True,
                "promocion": serializer.data,
                "descuento_calculado": str(descuento["monto_descuento"]),
                "tipo_descuento": descuento["tipo_descuento"],
                "descripcion": descuento["descripcion"],
                "productos_afectados": descuento["productos_afectados"],
                "mensaje": f'Promoción "{promo.nombre}" aplicable',
            }
        )

    @action(detail=False, methods=["get"])
    def activas(self, request):
        """
        Lista promociones activas en este momento.

        GET /api/v1/promociones/activas/
        """
        ahora = timezone.now()

        promociones = (
            Promociones.objects.filter(estado=True, fecha_inicio__lte=ahora.date())
            .filter(models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=ahora.date()))
            .order_by("prioridad")
        )

        serializer = self.get_serializer(promociones, many=True)

        return Response({"count": promociones.count(), "promociones": serializer.data})

    @action(detail=False, methods=["get"])
    def reporte_efectividad(self, request):
        """
        Reporte de efectividad de promociones.

        GET /api/v1/promociones/reporte_efectividad/?fecha_inicio=2026-01-01&fecha_fin=2026-03-01

        Returns:
            {
                "periodo": {"inicio": "2026-01-01", "fin": "2026-03-01"},
                "resumen": {
                    "total_promociones_activas": 10,
                    "total_usos": 150,
                    "total_descuentos": 450000,
                    "promedio_descuento_por_uso": 3000
                },
                "por_promocion": [
                    {
                        "id_promocion": 1,
                        "nombre": "2x1 Coca Cola",
                        "tipo": "2x1",
                        "usos": 45,
                        "monto_total_descuentos": 135000,
                        "promedio_por_uso": 3000,
                        "efectividad": "Alta"
                    }
                ]
            }
        """
        from apps.ventas.models import PromocionesAplicadas
        from django.db.models import Sum, Count, Avg

        # Parámetros de fecha
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")

        if not fecha_inicio or not fecha_fin:
            return Response(
                {"error": "Se requieren fecha_inicio y fecha_fin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Query base
        aplicaciones = PromocionesAplicadas.objects.filter(
            fecha_aplicacion__date__gte=fecha_inicio, fecha_aplicacion__date__lte=fecha_fin
        )

        # Resumen general
        resumen = aplicaciones.aggregate(
            total_usos=Count("id_aplicacion"),
            total_descuentos=Sum("monto_descontado"),
            promedio_descuento=Avg("monto_descontado"),
        )

        # Por promoción
        por_promocion = (
            aplicaciones.values(
                "id_promocion", "id_promocion__nombre", "id_promocion__tipo_promocion"
            )
            .annotate(
                usos=Count("id_aplicacion"),
                total_descuentos=Sum("monto_descontado"),
                promedio_por_uso=Avg("monto_descontado"),
            )
            .order_by("-usos")
        )

        # Determinar efectividad
        for promo in por_promocion:
            if promo["usos"] >= 50:
                promo["efectividad"] = "Alta"
            elif promo["usos"] >= 20:
                promo["efectividad"] = "Media"
            else:
                promo["efectividad"] = "Baja"

        return Response(
            {
                "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
                "resumen": {
                    "total_promociones_activas": Promociones.objects.filter(estado=True).count(),
                    "total_usos": resumen["total_usos"] or 0,
                    "total_descuentos": str(resumen["total_descuentos"] or 0),
                    "promedio_descuento_por_uso": str(resumen["promedio_descuento"] or 0),
                },
                "por_promocion": [
                    {
                        "id_promocion": p["id_promocion"],
                        "nombre": p["id_promocion__nombre"],
                        "tipo": p["id_promocion__tipo_promocion"],
                        "usos": p["usos"],
                        "monto_total_descuentos": str(p["total_descuentos"]),
                        "promedio_por_uso": str(p["promedio_por_uso"]),
                        "efectividad": p["efectividad"],
                    }
                    for p in por_promocion
                ],
            }
        )

    @action(detail=False, methods=["get"])
    def mas_usadas(self, request):
        """
        Ranking de promociones más usadas.

        GET /api/v1/promociones/mas_usadas/?limite=10

        Returns:
            {
                "ranking": [
                    {
                        "posicion": 1,
                        "id_promocion": 5,
                        "nombre": "DESCUENTO10",
                        "tipo": "porcentaje",
                        "total_usos": 127,
                        "total_descuentos": 380000,
                        "estado": "activa"
                    }
                ]
            }
        """
        from apps.ventas.models import PromocionesAplicadas
        from django.db.models import Count, Sum

        limite = int(request.query_params.get("limite", 10))

        # Query de promociones con sus usos
        ranking = (
            Promociones.objects.annotate(
                total_usos=Count("promocionesaplicadas"),
                total_descuentos=Sum("promocionesaplicadas__monto_descontado"),
            )
            .filter(total_usos__gt=0)
            .order_by("-total_usos")[:limite]
        )

        resultado = []
        for idx, promo in enumerate(ranking, start=1):
            resultado.append(
                {
                    "posicion": idx,
                    "id_promocion": promo.id_promocion,
                    "nombre": promo.nombre,
                    "tipo": promo.tipo_promocion,
                    "total_usos": promo.total_usos,
                    "total_descuentos": str(promo.total_descuentos or 0),
                    "estado": "activa" if promo.estado else "inactiva",
                }
            )

        return Response({"ranking": resultado})

    @action(detail=False, methods=["get"])
    def historico_uso(self, request):
        """
        Histórico de uso de promociones por período.

        GET /api/v1/promociones/historico_uso/?periodo=mensual&fecha_inicio=2026-01-01&fecha_fin=2026-03-01

        Returns:
            {
                "periodo": "mensual",
                "datos": [
                    {
                        "periodo": "2026-01",
                        "usos": 45,
                        "monto_descuentos": 135000
                    },
                    {
                        "periodo": "2026-02",
                        "usos": 52,
                        "monto_descuentos": 158000
                    }
                ]
            }
        """
        from apps.ventas.models import PromocionesAplicadas
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncMonth, TruncWeek, TruncDay

        periodo = request.query_params.get("periodo", "mensual")  # mensual, semanal, diario
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")

        if not fecha_inicio or not fecha_fin:
            return Response(
                {"error": "Se requieren fecha_inicio y fecha_fin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Query base
        aplicaciones = PromocionesAplicadas.objects.filter(
            fecha_aplicacion__date__gte=fecha_inicio, fecha_aplicacion__date__lte=fecha_fin
        )

        # Agrupar según período
        if periodo == "mensual":
            agrupado = (
                aplicaciones.annotate(periodo=TruncMonth("fecha_aplicacion"))
                .values("periodo")
                .annotate(usos=Count("id_aplicacion"), monto_descuentos=Sum("monto_descontado"))
                .order_by("periodo")
            )
        elif periodo == "semanal":
            agrupado = (
                aplicaciones.annotate(periodo=TruncWeek("fecha_aplicacion"))
                .values("periodo")
                .annotate(usos=Count("id_aplicacion"), monto_descuentos=Sum("monto_descontado"))
                .order_by("periodo")
            )
        else:  # diario
            agrupado = (
                aplicaciones.annotate(periodo=TruncDay("fecha_aplicacion"))
                .values("periodo")
                .annotate(usos=Count("id_aplicacion"), monto_descuentos=Sum("monto_descontado"))
                .order_by("periodo")
            )

        return Response(
            {
                "periodo": periodo,
                "datos": [
                    {
                        "periodo": str(item["periodo"].date()),
                        "usos": item["usos"],
                        "monto_descuentos": str(item["monto_descuentos"]),
                    }
                    for item in agrupado
                ],
            }
        )


class CondicionVentaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar condiciones de venta (contado, credito, etc.)."""
    queryset = CondicionVenta.objects.all().order_by('nombre')
    serializer_class = CondicionVentaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    ordering = ['nombre']
