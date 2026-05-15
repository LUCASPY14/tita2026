"""
Serializers para la app core
"""

from rest_framework import serializers

from .models import (
    Tarjeta,
    MovimientoTarjeta,
    TarjetaAutorizacion,
    CargaSaldo,
    ConsumoTarjeta,
    MedioPago,
    LimiteTransaccion,
    RegistroAutorizacion,
)


class TarjetaSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    saldo_disponible = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = Tarjeta
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "ultima_notificacion_saldo"]


class MovimientoTarjetaSerializer(serializers.ModelSerializer):
    tarjeta_nro = serializers.CharField(source="tarjeta.nro_tarjeta", read_only=True)

    class Meta:
        model = MovimientoTarjeta
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]


class TarjetaAutorizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarjetaAutorizacion
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class CargaSaldoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargaSaldo
        fields = "__all__"
        read_only_fields = ["fecha_carga", "fecha_confirmacion", "fecha_aprobacion", "fecha_creacion"]


class ConsumoTarjetaSerializer(serializers.ModelSerializer):
    tarjeta_nro = serializers.CharField(source="tarjeta.nro_tarjeta", read_only=True)

    class Meta:
        model = ConsumoTarjeta
        fields = "__all__"
        read_only_fields = ["fecha_consumo", "saldo_anterior", "saldo_posterior", "fecha_creacion"]


class MedioPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedioPago
        fields = "__all__"


class LimiteTransaccionSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source="rol.nombre_rol", read_only=True)

    class Meta:
        model = LimiteTransaccion
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "fecha_modificacion"]


class RegistroAutorizacionSerializer(serializers.ModelSerializer):
    solicitante_nombre = serializers.CharField(source="solicitante.nombre_completo", read_only=True)
    autorizador_nombre = serializers.CharField(source="autorizador.nombre_completo", read_only=True)

    class Meta:
        model = RegistroAutorizacion
        fields = "__all__"
        read_only_fields = ["fecha_autorizacion"]