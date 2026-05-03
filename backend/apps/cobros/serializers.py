"""
Serializers para el módulo de cobros.
"""

from decimal import Decimal

from rest_framework import serializers

from apps.ventas.models import Ventas

from .models import AplicacionPagosClientes, PagosClientes


class AplicacionPagoSerializer(serializers.ModelSerializer):
    """Serializer para aplicaciones de pago a facturas"""

    nro_factura = serializers.IntegerField(source="id_venta.nro_factura_venta", read_only=True)
    monto_venta = serializers.DecimalField(
        source="id_venta.monto_total", max_digits=12, decimal_places=2, read_only=True
    )
    saldo_anterior = serializers.SerializerMethodField()
    saldo_restante = serializers.SerializerMethodField()

    class Meta:
        model = AplicacionPagosClientes
        fields = [
            "id_aplicacion",
            "id_venta",
            "nro_factura",
            "monto_venta",
            "monto_aplicado",
            "saldo_anterior",
            "saldo_restante",
            "fecha_aplicacion",
        ]
        read_only_fields = ["id_aplicacion", "fecha_aplicacion"]

    def get_saldo_anterior(self, obj):
        """Obtiene el saldo antes de aplicar este pago"""
        venta = obj.id_venta
        # Sumar el monto aplicado actual al saldo pendiente para obtener el saldo anterior
        return venta.saldo_pendiente + obj.monto_aplicado

    def get_saldo_restante(self, obj):
        """Obtiene el saldo restante después de este pago"""
        return obj.id_venta.saldo_pendiente


class PagosClientesSerializer(serializers.ModelSerializer):
    """Serializer para pagos de clientes"""

    aplicaciones = AplicacionPagoSerializer(many=True, read_only=True)
    nombre_cliente = serializers.CharField(source="id_cliente.nombre_completo", read_only=True)
    ruc_ci_cliente = serializers.CharField(source="id_cliente.ruc_ci", read_only=True)
    nombre_medio_pago = serializers.CharField(source="id_medio_pago.nombre", read_only=True)
    nombre_cajero = serializers.SerializerMethodField()
    monto_aplicado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    monto_pendiente_aplicar = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PagosClientes
        fields = [
            "id_pago_cliente",
            "id_cliente",
            "nombre_cliente",
            "ruc_ci_cliente",
            "monto_total",
            "fecha_pago",
            "id_medio_pago",
            "nombre_medio_pago",
            "referencia",
            "banco_emisor",
            "observaciones",
            "id_empleado_cajero",
            "nombre_cajero",
            "estado",
            "aplicaciones",
            "monto_aplicado",
            "monto_pendiente_aplicar",
            "id_cierre",
        ]
        read_only_fields = ["id_pago_cliente", "fecha_pago", "monto_aplicado", "monto_pendiente_aplicar"]

    def get_nombre_cajero(self, obj):
        """Obtiene el nombre completo del cajero"""
        return f"{obj.id_empleado_cajero.nombre} {obj.id_empleado_cajero.apellido}"


class RegistrarPagoSerializer(serializers.Serializer):
    """Serializer para registrar un nuevo pago con aplicaciones"""

    id_cliente = serializers.IntegerField()
    monto_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    id_medio_pago = serializers.IntegerField()
    referencia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    banco_emisor = serializers.CharField(max_length=100, required=False, allow_blank=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    aplicaciones = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text='Lista de aplicaciones: [{"id_venta": 1, "monto_aplicado": 100.00}, ...]',
    )

    def validate_monto_total(self, value):
        """Valida que el monto sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero")
        return value

    def validate_aplicaciones(self, value):
        """Valida las aplicaciones"""
        if not value:
            return value

        # Validar estructura de cada aplicación
        for app in value:
            if "id_venta" not in app or "monto_aplicado" not in app:
                raise serializers.ValidationError("Cada aplicación debe tener 'id_venta' y 'monto_aplicado'")

            # Validar que el monto sea positivo
            monto = Decimal(str(app["monto_aplicado"]))
            if monto <= 0:
                raise serializers.ValidationError(f"El monto aplicado debe ser positivo (venta {app['id_venta']})")

            # Validar que la venta existe y tiene saldo pendiente
            try:
                venta = Ventas.objects.get(id_venta=app["id_venta"])
                if venta.saldo_pendiente <= 0:
                    raise serializers.ValidationError(f"La venta {app['id_venta']} no tiene saldo pendiente")
                if monto > venta.saldo_pendiente:
                    raise serializers.ValidationError(
                        f"El monto aplicado ({monto}) excede el saldo pendiente "
                        f"de la venta {app['id_venta']} ({venta.saldo_pendiente})"
                    )
            except Ventas.DoesNotExist:
                raise serializers.ValidationError(f"La venta {app['id_venta']} no existe")

        return value

    def validate(self, attrs):
        """Validación global"""
        aplicaciones = attrs.get("aplicaciones", [])

        if aplicaciones:
            # Validar que la suma de aplicaciones no exceda el monto total
            total_aplicaciones = sum(Decimal(str(app["monto_aplicado"])) for app in aplicaciones)
            monto_total = attrs["monto_total"]

            if total_aplicaciones > monto_total:
                raise serializers.ValidationError(
                    f"La suma de aplicaciones ({total_aplicaciones}) excede " f"el monto total del pago ({monto_total})"
                )

        return attrs


class FacturaPendienteSerializer(serializers.ModelSerializer):
    """Serializer para listar facturas pendientes de un cliente"""

    dias_vencido = serializers.SerializerMethodField()

    class Meta:
        model = Ventas
        fields = [
            "id_venta",
            "nro_factura_venta",
            "fecha",
            "monto_total",
            "saldo_pendiente",
            "estado_pago",
            "tipo_venta",
            "dias_vencido",
        ]

    def get_dias_vencido(self, obj):
        """Calcula los días de vencimiento"""
        from django.utils import timezone

        if obj.tipo_venta == "credito" and obj.saldo_pendiente > 0:
            dias = (timezone.now() - obj.fecha).days
            return dias if dias > 0 else 0
        return 0
