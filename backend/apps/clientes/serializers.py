"""
Serializers para la app clientes
"""

from rest_framework import serializers

from .models import (
    Cliente,
    CuentaCorrienteCliente,
    TipoCliente,
    Hijo,
    Grado,
    HistorialGrado,
    RestriccionHijo,
    AutorizacionSaldoNegativo,
    Pais,
    Ciudad,
)


class ClienteSerializer(serializers.ModelSerializer):
    saldo_cuenta_corriente = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    tipo_cliente_nombre = serializers.CharField(source="tipo_cliente.nombre", read_only=True)

    class Meta:
        model = Cliente
        fields = "__all__"
        read_only_fields = ["fecha_registro"]


class CuentaCorrienteClienteSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)

    class Meta:
        model = CuentaCorrienteCliente
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]


class TipoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCliente
        fields = "__all__"


class HijoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente_responsable.nombre_completo", read_only=True)

    class Meta:
        model = Hijo
        fields = "__all__"


class GradoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grado
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class HistorialGradoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)

    class Meta:
        model = HistorialGrado
        fields = "__all__"
        read_only_fields = ["fecha_cambio"]


class RestriccionHijoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)

    class Meta:
        model = RestriccionHijo
        fields = "__all__"
        read_only_fields = ["fecha_registro", "fecha_actualizacion"]


class AutorizacionSaldoNegativoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)

    class Meta:
        model = AutorizacionSaldoNegativo
        fields = "__all__"
        read_only_fields = ["fecha_autorizacion", "saldo_anterior", "saldo_resultante"]


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = "__all__"


class CiudadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = "__all__"