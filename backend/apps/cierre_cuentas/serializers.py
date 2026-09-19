from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.clientes.models import Hijo

from .models import CierreCuentaAlumno, ResolucionSaldo


class ResolucionSaldoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    hijo = serializers.IntegerField(source="cierre.hijo_id", read_only=True)
    hijo_nombre = serializers.CharField(source="cierre.hijo.nombre_completo", read_only=True)
    hijo_destino_nombre = serializers.CharField(source="hijo_destino.nombre_completo", read_only=True, default=None)
    solicitado_por_nombre = serializers.CharField(source="solicitado_por.nombre_completo", read_only=True)
    decidido_por_nombre = serializers.CharField(source="decidido_por.nombre_completo", read_only=True, default=None)

    class Meta:
        model = ResolucionSaldo
        fields = "__all__"
        read_only_fields = [f.name for f in ResolucionSaldo._meta.fields]


class CierreCuentaSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    hijo_grado = serializers.CharField(source="hijo.grado.nombre", read_only=True, default=None)
    hijo_activo = serializers.BooleanField(source="hijo.activo", read_only=True)
    cliente_nombre = serializers.CharField(source="hijo.cliente_responsable.nombre_completo", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    nro_tarjeta = serializers.SerializerMethodField()
    saldo_cantina_actual = serializers.SerializerMethodField()
    saldo_almuerzo_actual = serializers.SerializerMethodField()
    deuda_pendiente = serializers.SerializerMethodField()
    a_favor_pendiente = serializers.SerializerMethodField()
    resoluciones_pendientes = serializers.SerializerMethodField()
    cliente_id = serializers.IntegerField(source="hijo.cliente_responsable_id", read_only=True)
    cliente_permite_cuenta_corriente = serializers.BooleanField(
        source="hijo.cliente_responsable.permite_cuenta_corriente", read_only=True,
    )

    class Meta:
        model = CierreCuentaAlumno
        fields = "__all__"
        read_only_fields = [f.name for f in CierreCuentaAlumno._meta.fields]

    def _saldos(self, obj):
        try:
            cantina = obj.hijo.tarjeta.saldo_actual
        except ObjectDoesNotExist:
            cantina = 0
        try:
            almuerzo = obj.hijo.saldo_almuerzo.saldo_actual
        except ObjectDoesNotExist:
            almuerzo = 0
        return int(cantina), int(almuerzo)

    def get_nro_tarjeta(self, obj):
        try:
            return obj.hijo.tarjeta.nro_tarjeta
        except ObjectDoesNotExist:
            return ""

    def get_saldo_cantina_actual(self, obj):
        return self._saldos(obj)[0]

    def get_saldo_almuerzo_actual(self, obj):
        return self._saldos(obj)[1]

    def get_deuda_pendiente(self, obj):
        return sum(-s for s in self._saldos(obj) if s < 0)

    def get_a_favor_pendiente(self, obj):
        return sum(s for s in self._saldos(obj) if s > 0)

    def get_resoluciones_pendientes(self, obj):
        return sum(1 for r in obj.resoluciones.all() if r.estado == ResolucionSaldo.Estado.SOLICITADA)


class CierreCuentaDetalleSerializer(CierreCuentaSerializer):
    resoluciones = ResolucionSaldoSerializer(many=True, read_only=True)
    hermanos = serializers.SerializerMethodField()

    def get_hermanos(self, obj):
        """Hermanos activos del mismo responsable: posibles destinos de un traspaso."""
        hermanos = Hijo.objects.filter(
            cliente_responsable_id=obj.hijo.cliente_responsable_id, activo=True,
        ).exclude(pk=obj.hijo_id).select_related("grado", "tarjeta")
        salida = []
        for h in hermanos:
            try:
                nro = h.tarjeta.nro_tarjeta
            except ObjectDoesNotExist:
                nro = ""
            salida.append({
                "id_hijo": h.pk, "nombre_completo": h.nombre_completo,
                "grado": h.grado.nombre if h.grado else "", "nro_tarjeta": nro,
            })
        return salida


class RegistrarResolucionSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=ResolucionSaldo.Tipo.choices)
    bolsillo_origen = serializers.ChoiceField(choices=ResolucionSaldo.Bolsillo.choices)
    monto = serializers.DecimalField(max_digits=12, decimal_places=0, min_value=1)
    bolsillo_destino = serializers.ChoiceField(
        choices=ResolucionSaldo.Bolsillo.choices, required=False, allow_blank=True,
    )
    hijo_destino = serializers.PrimaryKeyRelatedField(queryset=Hijo.objects.all(), required=False, allow_null=True)
    metodo_pago = serializers.CharField(required=False, allow_blank=True, max_length=50)
    referencia = serializers.CharField(required=False, allow_blank=True, max_length=100)
    motivo = serializers.CharField(required=False, allow_blank=True)


class AbrirCierreSerializer(serializers.Serializer):
    hijo = serializers.PrimaryKeyRelatedField(queryset=Hijo.objects.all())
    anio = serializers.IntegerField(required=False, min_value=2020, max_value=2100)


class AbrirMasivoSerializer(serializers.Serializer):
    anio = serializers.IntegerField(required=False, min_value=2020, max_value=2100)


class MotivoSerializer(serializers.Serializer):
    motivo = serializers.CharField(allow_blank=False)
