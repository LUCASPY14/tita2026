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
    hijo_foto = serializers.SerializerMethodField()
    hijo_grado = serializers.CharField(source="hijo.grado_nombre", read_only=True, allow_null=True)
    hijo_restricciones = serializers.SerializerMethodField()
    saldo_disponible = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    # Datos del cliente responsable (padre/tutor)
    cliente_id = serializers.IntegerField(source="hijo.cliente_responsable.id", read_only=True)
    cliente_nombre = serializers.CharField(source="hijo.cliente_responsable.nombre_completo", read_only=True)
    cliente_ruc = serializers.CharField(source="hijo.cliente_responsable.ruc_ci", read_only=True)

    class Meta:
        model = Tarjeta
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "ultima_notificacion_saldo"]

    def get_hijo_foto(self, obj):
        if obj.hijo and obj.hijo.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.hijo.foto_perfil.url)
            return obj.hijo.foto_perfil.url
        return None

    def get_hijo_restricciones(self, obj):
        if not obj.hijo:
            return []

        restricciones = obj.hijo.restricciones.filter(activo=True)
        return [
            {
                "id": r.id,
                "tipo": r.tipo,
                "descripcion": r.descripcion,
                "severidad": r.severidad,
                "requiere_autorizacion": r.requiere_autorizacion,
            }
            for r in restricciones
        ]


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
    usuario_nombre = serializers.CharField(source="responsable.nombre_completo", read_only=True, default=None)

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
