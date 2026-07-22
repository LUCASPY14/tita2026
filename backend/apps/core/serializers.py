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
    # ── Datos del alumno (null cuando es tarjeta de docente/funcionario) ──────
    es_alumno = serializers.SerializerMethodField()
    hijo_nombre = serializers.SerializerMethodField()
    hijo_foto = serializers.SerializerMethodField()
    hijo_grado = serializers.SerializerMethodField()
    hijo_restricciones = serializers.SerializerMethodField()
    saldo_disponible = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    # ── Datos del cliente responsable o del cliente directo ───────────────────
    cliente_id = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    cliente_ruc = serializers.SerializerMethodField()
    cliente_saldo_cc = serializers.SerializerMethodField()
    cliente_limite_credito = serializers.SerializerMethodField()

    # Lista de precios asignada al cliente (para que el POS aplique precios correctos)
    lista_precio_id = serializers.SerializerMethodField()
    lista_es_default = serializers.SerializerMethodField()

    class Meta:
        model = Tarjeta
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "ultima_notificacion_saldo"]

    def _get_cliente(self, obj):
        """Devuelve el cliente responsable del alumno o el cliente directo (docente)."""
        if obj.hijo_id:
            return obj.hijo.cliente_responsable
        return obj.cliente_directo

    def get_es_alumno(self, obj):
        return obj.hijo_id is not None

    def get_hijo_nombre(self, obj):
        if obj.hijo_id:
            return obj.hijo.nombre_completo
        # Para docentes/funcionarios: devuelve su nombre como titular
        if obj.cliente_directo_id:
            return obj.cliente_directo.nombre_completo
        return None

    def get_hijo_foto(self, obj):
        if obj.hijo_id and obj.hijo.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.hijo.foto_perfil.url)
            return obj.hijo.foto_perfil.url
        return None

    def get_hijo_grado(self, obj):
        if obj.hijo_id:
            return obj.hijo.grado_nombre
        return None

    def get_hijo_restricciones(self, obj):
        if not obj.hijo_id:
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

    def get_cliente_id(self, obj):
        try:
            return self._get_cliente(obj).pk
        except Exception:
            return None

    def get_cliente_nombre(self, obj):
        try:
            return self._get_cliente(obj).nombre_completo
        except Exception:
            return None

    def get_cliente_ruc(self, obj):
        try:
            return self._get_cliente(obj).ruc_ci
        except Exception:
            return None

    def get_cliente_saldo_cc(self, obj):
        try:
            return int(self._get_cliente(obj).saldo_cuenta_corriente)
        except Exception:
            return 0

    def get_cliente_limite_credito(self, obj):
        try:
            return int(self._get_cliente(obj).limite_credito)
        except Exception:
            return 0

    def get_lista_precio_id(self, obj):
        try:
            return self._get_cliente(obj).lista_precio_id
        except Exception:
            return None

    def get_lista_es_default(self, obj):
        try:
            return bool(self._get_cliente(obj).lista_precio.es_por_defecto)
        except Exception:
            return True

    cliente_modalidad_facturacion = serializers.SerializerMethodField()

    def get_cliente_modalidad_facturacion(self, obj):
        try:
            return self._get_cliente(obj).modalidad_facturacion
        except Exception:
            return "INMEDIATA"


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
