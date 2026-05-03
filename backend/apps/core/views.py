from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.clientes.models import RestriccionesHijos

from .models import CargasSaldo, ConfiguracionSistema, ConsumosTarjeta, MediosPago, Tarjetas
from .serializers import (
    CargasSaldoSerializer,
    ConfiguracionSistemaSerializer,
    ConsumosTarjetaSerializer,
    MediosPagoSerializer,
    TarjetasSerializer,
)
from .services import RecargaService


class TarjetasViewSet(viewsets.ModelViewSet):
    queryset = Tarjetas.objects.all()
    serializer_class = TarjetasSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "id_hijo"]
    search_fields = ["nro_tarjeta", "codigo_barras"]
    ordering_fields = ["fecha_creacion"]
    ordering = ["nro_tarjeta"]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def scan(self, request):
        """
        Endpoint para escaneo de código de barras en POS.

        POST: { "codigo_barras": "ABC123456" }
        Returns: Información completa de la tarjeta incluyendo foto del hijo
        """
        codigo_barras = request.data.get("codigo_barras", "").strip()

        if not codigo_barras:
            return Response({"error": "Código de barras requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tarjeta = Tarjetas.objects.select_related("id_hijo").get(codigo_barras=codigo_barras)

            # Verificar estado de la tarjeta (case-insensitive)
            if tarjeta.estado.upper() != "ACTIVA":
                return Response(
                    {"error": "Tarjeta inactiva", "estado": tarjeta.estado, "codigo_barras": codigo_barras},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Retornar información completa
            serializer = self.get_serializer(tarjeta, context={"request": request})

            # Obtener restricciones activas del hijo
            restricciones = list(
                RestriccionesHijos.objects.filter(id_hijo=tarjeta.id_hijo, estado=True).values(
                    "tipo_restriccion", "descripcion", "severidad", "requiere_autorizacion"
                )
            )

            return Response(
                {
                    "tarjeta": serializer.data,
                    "verificacion": {
                        "estado_ok": True,
                        "saldo_disponible": tarjeta.saldo_disponible,
                        "alerta_saldo_bajo": tarjeta.esta_en_alerta,
                        "timestamp": timezone.now(),
                        "restricciones": restricciones,
                    },
                }
            )

        except Tarjetas.DoesNotExist:
            return Response(
                {"error": "Tarjeta no encontrada", "codigo_barras": codigo_barras}, status=status.HTTP_404_NOT_FOUND
            )


class CargasSaldoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de recargas de saldo prepago.

    Endpoints personalizados:
    - POST /recargas/init/ - Inicia recarga por pasarela Bancard
    - POST /recargas/caja/ - Registra recarga en efectivo/POS
    - POST /recargas/transferencia/referencia/ - Genera código para transferencia
    - POST /recargas/transferencia/validar/ - Valida transferencia bancaria
    - POST /recargas/{id}/aprobar/ - Aprueba recarga (supervisor)
    """

    queryset = CargasSaldo.objects.all()
    serializer_class = CargasSaldoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "nro_tarjeta", "id_cliente_origen"]
    search_fields = ["referencia", "pay_request_id", "tx_id", "custom_identifier"]
    ordering_fields = ["fecha_carga", "fecha_confirmacion"]
    ordering = ["-fecha_carga"]

    @action(detail=False, methods=["post"], url_path="caja")
    def recarga_caja(self, request):
        """
        Registra recarga en efectivo o tarjeta POS (cajero).

        Body:
        {
            "hijo_id": 123,
            "monto": 100000,
            "metodo_pago": "efectivo",  // o "tarjeta_pos"
            "referencia": "CAJA-001" (opcional)
        }
        """
        try:
            hijo_id = request.data.get("hijo_id")
            monto = Decimal(str(request.data.get("monto")))
            metodo_pago = request.data.get("metodo_pago", "efectivo")
            referencia = request.data.get("referencia")

            # Obtener empleado del request (asumiendo autenticación)
            # empleado_id = request.user.empleado.id_empleado
            # Por ahora, usamos un valor de prueba
            empleado_id = request.data.get("empleado_id", 1)

            resultado = RecargaService.procesar_recarga_caja(
                hijo_id=hijo_id,
                monto=monto,
                metodo_pago=metodo_pago,
                empleado_id=empleado_id,
                referencia=referencia,
            )

            return Response(resultado, status=status.HTTP_201_CREATED)

        except (DjangoValidationError, Exception) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="transferencia/referencia")
    def generar_referencia_transferencia(self, request):
        """
        Genera código de referencia para transferencia bancaria.

        Body:
        {
            "hijo_id": 123,
            "monto": 100000
        }

        Response:
        {
            "codigo_referencia": "REF-20260302-00001",
            "monto_transferir": 100000,
            "datos_bancarios": {...},
            "instrucciones": "..."
        }
        """
        try:
            hijo_id = request.data.get("hijo_id")
            monto = Decimal(str(request.data.get("monto")))

            resultado = RecargaService.iniciar_recarga_transferencia(hijo_id=hijo_id, monto=monto)

            return Response(resultado, status=status.HTTP_201_CREATED)

        except (DjangoValidationError, Exception) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="transferencia/validar")
    def validar_transferencia(self, request):
        """
        Valida y registra transferencia bancaria.

        Flujo A - Con código de referencia:
        {
            "codigo_referencia": "REF-20260302-00001",
            "numero_comprobante": "COMP-555",
            "empleado_id": 5,
            "imagen_comprobante": "/path/to/image.jpg" (opcional)
        }

        Flujo B - Sin código (manual):
        {
            "hijo_id": 123,
            "monto": 103400,
            "numero_comprobante": "COMP-555",
            "empleado_id": 5,
            "imagen_comprobante": "/path/to/image.jpg" (opcional)
        }
        """
        try:
            codigo_referencia = request.data.get("codigo_referencia")
            numero_comprobante = request.data.get("numero_comprobante")
            imagen_path = request.data.get("imagen_comprobante")

            # Obtener empleado del request
            # empleado_id = request.user.empleado.id_empleado
            empleado_id = request.data.get("empleado_id", 1)

            # Flujo manual (sin código)
            hijo_id = request.data.get("hijo_id")
            monto = Decimal(str(request.data.get("monto"))) if request.data.get("monto") else None

            resultado = RecargaService.validar_transferencia(
                codigo_referencia=codigo_referencia,
                numero_comprobante=numero_comprobante,
                empleado_id=empleado_id,
                hijo_id=hijo_id,
                monto=monto,
                imagen_path=imagen_path,
            )

            return Response(resultado, status=status.HTTP_200_OK)

        except (DjangoValidationError, Exception) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="aprobar")
    def aprobar_supervisor(self, request, pk=None):
        """
        Aprueba recarga pendiente de validación (supervisor).

        Body:
        {
            "supervisor_id": 10
        }
        """
        try:
            recarga_id = int(pk)

            # Obtener supervisor del request
            # supervisor_id = request.user.empleado.id_empleado
            supervisor_id = request.data.get("supervisor_id", 2)

            resultado = RecargaService.aprobar_recarga_supervisor(recarga_id=recarga_id, supervisor_id=supervisor_id)

            return Response(resultado, status=status.HTTP_200_OK)

        except (DjangoValidationError, Exception) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="init")
    def iniciar_recarga_bancard(self, request):
        """
        Inicia recarga por pasarela de pago Bancard.

        Body:
        {
            "hijo_id": 123,
            "monto": 100000,
            "return_url": "https://app.cantinatita.com/recarga/success",
            "cancel_url": "https://app.cantinatita.com/recarga/cancel",
            "buyer_info": {  # Opcional
                "ci": "12345678",
                "nombre": "Juan Pérez",
                "email": "juan@example.com",
                "telefono": "0981234567"
            }
        }

        Response:
        {
            "success": true,
            "id_recarga": 456,
            "payment_url": "https://vpos.infonet.com.py/checkout/new?process_id=...",
            "process_id": "abc123xyz",
            "shop_process_id": "REC-456-1234567890",
            "total_cobrado": 103400,
            "comision": 3400,
            "monto_acreditar": 100000
        }
        """
        from django.utils import timezone

        from apps.api_integrations.services import BancardService
        from apps.clientes.models import Hijos

        try:
            # Validar datos requeridos
            hijo_id = request.data.get("hijo_id")
            monto = request.data.get("monto")
            return_url = request.data.get("return_url")
            cancel_url = request.data.get("cancel_url")
            buyer_info = request.data.get("buyer_info", {})

            if not all([hijo_id, monto, return_url, cancel_url]):
                return Response(
                    {"error": "Faltan datos requeridos: hijo_id, monto, return_url, cancel_url"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar hijo existe
            try:
                hijo = Hijos.objects.select_related("tarjetas").get(id_hijo=hijo_id)
            except Hijos.DoesNotExist:
                return Response(
                    {"error": f"Hijo con ID {hijo_id} no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validar que el hijo tiene tarjeta asignada
            try:
                tarjeta = hijo.tarjetas
            except Exception:
                return Response(
                    {"error": f"El hijo con ID {hijo_id} no tiene tarjeta asignada"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar monto
            try:
                monto_decimal = Decimal(str(monto))
                if monto_decimal <= 0:
                    raise ValueError("Monto debe ser mayor a cero")
            except (ValueError, InvalidOperation) as e:  # pragma: no cover
                return Response({"error": f"Monto inválido: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # Calcular montos
            resultado_montos = RecargaService.calcular_montos(monto_recarga=monto_decimal, metodo_pago="bancard")

            # Crear recarga en estado pendiente
            recarga = CargasSaldo.objects.create(
                nro_tarjeta=tarjeta,
                monto_cargado=resultado_montos["monto_recarga"],
                comision=resultado_montos["comision_monto"],
                total_cobrado=resultado_montos["total_cobrado"],
                metodo_pago="bancard",
                estado="pendiente",
                fecha_carga=timezone.now(),
            )

            # Iniciar transacción con Bancard
            bancard_service = BancardService()
            resultado_bancard = bancard_service.iniciar_transaccion(
                recarga_id=recarga.id_carga,
                monto=resultado_montos["total_cobrado"],
                descripcion=f"Recarga saldo tarjeta - {hijo.nombre_completo}",
                return_url=return_url,
                cancel_url=cancel_url,
                buyer_info=buyer_info,
            )

            # Validar respuesta de Bancard
            if not resultado_bancard.get("success"):
                # Cancelar recarga si Bancard falló
                recarga.estado = "rechazada"
                recarga.referencia = str(resultado_bancard.get("error", "Error desconocido de Bancard"))[:100]
                recarga.save()

                return Response(
                    {
                        "success": False,
                        "error": resultado_bancard.get("error"),
                        "id_recarga": recarga.id_carga,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Actualizar recarga con datos de Bancard
            recarga.referencia = resultado_bancard["shop_process_id"]
            recarga.pay_request_id = resultado_bancard.get("process_id", "")
            recarga.save()

            # Retornar respuesta exitosa
            return Response(
                {
                    "success": True,
                    "id_recarga": recarga.id_carga,
                    "payment_url": resultado_bancard["payment_url"],
                    "process_id": resultado_bancard["process_id"],
                    "shop_process_id": resultado_bancard["shop_process_id"],
                    "total_cobrado": float(resultado_montos["total_cobrado"]),
                    "comision": float(resultado_montos["comision_monto"]),
                    "monto_acreditar": float(resultado_montos["monto_recarga"]),
                    "mensaje": "Redirigir al usuario a payment_url para completar el pago",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:  # pragma: no cover
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConsumosTarjetaViewSet(viewsets.ModelViewSet):
    queryset = ConsumosTarjeta.objects.all()
    serializer_class = ConsumosTarjetaSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["nro_tarjeta"]
    ordering_fields = ["fecha_consumo"]
    ordering = ["-fecha_consumo"]


class MediosPagoViewSet(viewsets.ModelViewSet):
    queryset = MediosPago.objects.all()
    serializer_class = MediosPagoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado"]
    search_fields = ["descripcion"]


class ConfiguracionSistemaViewSet(viewsets.ModelViewSet):
    """ViewSet para configuración del sistema"""

    queryset = ConfiguracionSistema.objects.all()
    serializer_class = ConfiguracionSistemaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["tipo", "categoria", "estado"]
    search_fields = ["clave", "descripcion"]

    def get_queryset(self):
        """Filtra configs solo_superuser para usuarios no-superuser."""
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(solo_superuser=False)
        return qs

    @action(detail=False, methods=["get"])
    def por_categoria(self, request):
        """Obtiene configuraciones agrupadas por categoría"""
        try:
            configuraciones = ConfiguracionSistema.objects.filter(estado=True).order_by("categoria", "clave")

            # Agrupar por categoría
            por_categoria = {}
            for config in configuraciones:
                if config.categoria not in por_categoria:
                    por_categoria[config.categoria] = []
                por_categoria[config.categoria].append(self.get_serializer(config).data)

            return Response(por_categoria)
        except Exception as e:  # pragma: no cover
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def actualizar_valor(self, request, pk=None):
        """Actualiza el valor de una configuración"""
        config = self.get_object()
        try:
            nuevo_valor = request.data.get("valor")

            if nuevo_valor is None:
                return Response({"error": "El campo valor es requerido"}, status=status.HTTP_400_BAD_REQUEST)

            # Validar el valor según el tipo y restricciones de la configuración
            error_validacion = self._validar_valor_config(config, nuevo_valor)
            if error_validacion:
                return Response({"error": error_validacion}, status=status.HTTP_400_BAD_REQUEST)

            config.valor = str(nuevo_valor)

            # Actualizar updated_by con el usuario autenticado
            config.updated_by = request.user

            from django.utils import timezone

            config.updated_at = timezone.now()
            config.save()

            serializer = self.get_serializer(config)
            return Response(serializer.data)
        except Exception as e:  # pragma: no cover
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _validar_valor_config(config, nuevo_valor) -> str | None:
        """
        Valida el nuevo valor según el tipo y restricciones de la configuración.

        Returns:
            Mensaje de error (str) si la validación falla, None si es válido.
        """
        import json

        tipo = config.tipo  # 'string', 'integer', 'decimal', 'boolean', 'json'
        valor_str = str(nuevo_valor).strip()

        # Validar tipo de dato
        if tipo == "integer":
            try:
                valor_num = int(valor_str)
            except (ValueError, TypeError):
                return f"El valor debe ser un número entero (tipo: {tipo})"
            if config.valor_min:
                try:
                    if valor_num < int(config.valor_min):
                        return f"El valor mínimo permitido es {config.valor_min}"
                except (ValueError, TypeError):
                    pass
            if config.valor_max:
                try:
                    if valor_num > int(config.valor_max):
                        return f"El valor máximo permitido es {config.valor_max}"
                except (ValueError, TypeError):
                    pass

        elif tipo == "decimal":
            try:
                from decimal import Decimal, InvalidOperation

                valor_num = Decimal(valor_str)
            except (InvalidOperation, TypeError):
                return f"El valor debe ser un número decimal (tipo: {tipo})"
            if config.valor_min:
                try:
                    if valor_num < Decimal(config.valor_min):
                        return f"El valor mínimo permitido es {config.valor_min}"
                except (InvalidOperation, TypeError):
                    pass
            if config.valor_max:
                try:
                    if valor_num > Decimal(config.valor_max):
                        return f"El valor máximo permitido es {config.valor_max}"
                except (InvalidOperation, TypeError):
                    pass

        elif tipo == "boolean":
            if valor_str.lower() not in ("true", "false", "1", "0"):
                return "El valor debe ser true o false"

        elif tipo == "json":
            try:
                json.loads(valor_str)
            except (json.JSONDecodeError, TypeError):
                return "El valor debe ser JSON válido"

        # Validar valores permitidos (lista blanca)
        if config.valores_permitidos:
            permitidos = config.valores_permitidos if isinstance(config.valores_permitidos, list) else []
            if permitidos and valor_str not in [str(v) for v in permitidos]:
                return f"Valor no permitido. Valores válidos: {', '.join(str(v) for v in permitidos)}"

        return None

    @action(detail=True, methods=["post"])
    def resetear_default(self, request, pk=None):
        """Resetea una configuración a su valor por defecto"""
        try:
            config = self.get_object()
            config.valor = config.valor_defecto

            from django.utils import timezone

            config.updated_at = timezone.now()
            config.save()

            serializer = self.get_serializer(config)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
