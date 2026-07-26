"""
Serializers para la app clientes
"""

from rest_framework import serializers

from .models import (
    AlumnoResponsable,
    AutorizacionSaldoNegativo,
    Ciudad,
    Cliente,
    CuentaCorrienteCliente,
    Grado,
    HistorialGrado,
    Hijo,
    Pais,
    RestriccionHijo,
    TipoCliente,
)


class AlumnoResponsableSerializer(serializers.ModelSerializer):
    """Responsable de un alumno — lectura y escritura."""

    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    cliente_ruc_ci = serializers.CharField(source="cliente.ruc_ci", read_only=True)
    cliente_telefono = serializers.CharField(source="cliente.telefono", read_only=True, allow_null=True)
    cliente_email = serializers.EmailField(source="cliente.email", read_only=True, allow_null=True)
    parentesco_display = serializers.CharField(source="get_parentesco_display", read_only=True)

    class Meta:
        model = AlumnoResponsable
        fields = [
            "id",
            "hijo",
            "cliente",
            "cliente_nombre",
            "cliente_ruc_ci",
            "cliente_telefono",
            "cliente_email",
            "parentesco",
            "parentesco_display",
            "es_titular",
            "orden_cobro",
            "recibe_notificaciones",
            "puede_ver_saldo",
            "activo",
            "fecha_creacion",
            "agregado_por",
        ]
        read_only_fields = ["fecha_creacion", "es_titular"]

    def validate(self, attrs):
        # No permitir orden_cobro=0; mínimo 1
        if attrs.get("orden_cobro", 1) < 1:
            raise serializers.ValidationError({"orden_cobro": "Debe ser mayor o igual a 1."})
        return attrs


class AlumnoResponsableResumenSerializer(serializers.ModelSerializer):
    """Versión compacta para incluir en HijoSerializer."""

    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True)
    cliente_telefono = serializers.CharField(source="cliente.telefono", read_only=True, allow_null=True)
    parentesco_display = serializers.CharField(source="get_parentesco_display", read_only=True)

    class Meta:
        model = AlumnoResponsable
        fields = [
            "id",
            "cliente",
            "cliente_nombre",
            "cliente_telefono",
            "parentesco",
            "parentesco_display",
            "es_titular",
            "orden_cobro",
            "recibe_notificaciones",
            "puede_ver_saldo",
            "activo",
        ]


class ClienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()
    saldo_cuenta_corriente = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    saldo_negativo_tarjetas = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True, default=0)
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
    grado_nombre = serializers.CharField(source="grado.nombre", read_only=True, allow_null=True)
    responsables = serializers.SerializerMethodField()

    class Meta:
        model = Hijo
        fields = "__all__"

    def get_responsables(self, obj):
        qs = obj.responsables.filter(activo=True).select_related("cliente").order_by("orden_cobro")
        return AlumnoResponsableResumenSerializer(qs, many=True).data


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
    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True, allow_null=True)

    class Meta:
        model = Ciudad
        fields = "__all__"
