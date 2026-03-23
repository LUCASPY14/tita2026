from rest_framework import serializers
from .models import (
    PlanesAlmuerzo,
    TiposAlmuerzo,
    SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    Alergenos,
    CuentasAlmuerzoMensual,
    PrecioAlmuerzo,
)


class PrecioAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class PlanesAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanesAlmuerzo
        fields = "__all__"


class TiposAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TiposAlmuerzo
        fields = "__all__"


class SuscripcionesAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="id_hijo.nombre", read_only=True)
    plan_nombre = serializers.CharField(source="id_plan_almuerzo.nombre_plan", read_only=True)
    tipo_plan = serializers.CharField(source="id_plan_almuerzo.tipo_plan", read_only=True)
    cantidad_almuerzos_mes = serializers.IntegerField(
        source="id_plan_almuerzo.cantidad_almuerzos_mes", read_only=True
    )

    class Meta:
        model = SuscripcionesAlmuerzo
        fields = "__all__"


class RegistrosConsumoAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="id_hijo.nombre", read_only=True)
    tipo_almuerzo_nombre = serializers.CharField(source="id_tipo_almuerzo.nombre", read_only=True)
    nro_registro_hoy = serializers.SerializerMethodField()

    class Meta:
        model = RegistrosConsumoAlmuerzo
        fields = "__all__"
        read_only_fields = ["hora_registro", "costo_almuerzo", "ya_cobrado", "estado", "marcado_en_cuenta"]

    def get_nro_registro_hoy(self, obj):
        """Retorna el número ordinal de registro del alumno en el día (1 o 2)."""
        count = RegistrosConsumoAlmuerzo.objects.filter(
            id_hijo=obj.id_hijo,
            fecha_consumo=obj.fecha_consumo,
            estado__in=["Registrado", "Confirmado"],
            id_registro_consumo__lte=obj.id_registro_consumo,
        ).count()
        return count


class AlergenosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alergenos
        fields = "__all__"


class CuentasAlmuerzoMensualSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CuentasAlmuerzoMensual
        fields = "__all__"

    def get_hijo_nombre(self, obj):
        try:
            return f"{obj.id_hijo.nombre} {obj.id_hijo.apellido}"
        except Exception:
            return None
