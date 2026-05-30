"""
Serializers para la app almuerzos
"""

from rest_framework import serializers

from .models import (
    PrecioAlmuerzo,
    TipoAlmuerzo,
    PlanAlmuerzo,
    SuscripcionAlmuerzo,
    RegistroConsumoAlmuerzo,
    CuentaAlmuerzoMensual,
    PagoCuentaAlmuerzo,
    PagoAlmuerzoMensual,
    Alergeno,
    ProductoAlergeno,
    MenuDiario,
)


# ==============================================================================
# PRECIO ALMUERZO
# ==============================================================================

class PrecioAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


# ==============================================================================
# TIPO ALMUERZO
# ==============================================================================

class TipoAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


# ==============================================================================
# PLAN ALMUERZO
# ==============================================================================

class PlanAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


# ==============================================================================
# SUSCRIPCION ALMUERZO
# ==============================================================================

class SuscripcionAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    plan_nombre = serializers.CharField(source="plan.nombre", read_only=True)

    class Meta:
        model = SuscripcionAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


# ==============================================================================
# REGISTRO CONSUMO ALMUERZO
# ==============================================================================

class RegistroConsumoAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    tipo_almuerzo_nombre = serializers.CharField(source="tipo_almuerzo.nombre", read_only=True)

    class Meta:
        model = RegistroConsumoAlmuerzo
        fields = "__all__"
        read_only_fields = [
            "hora_registro",
            "costo_almuerzo",
            "ya_cobrado",
            "estado",
            "marcado_en_cuenta",
            "registrado_por",
            "fecha_creacion",
        ]

    def validate(self, data):
        hijo = data.get("hijo")
        suscripcion = data.get("suscripcion")
        fecha_consumo = data.get("fecha_consumo")

        if suscripcion and hijo and suscripcion.hijo_id != hijo.pk:
            raise serializers.ValidationError(
                {"suscripcion": "La suscripción no pertenece al estudiante indicado."}
            )

        if suscripcion and fecha_consumo:
            if suscripcion.fecha_inicio > fecha_consumo:
                raise serializers.ValidationError(
                    {"suscripcion": "La suscripción no estaba vigente en la fecha de consumo."}
                )
            if suscripcion.fecha_fin and suscripcion.fecha_fin < fecha_consumo:
                raise serializers.ValidationError(
                    {"suscripcion": "La suscripción ya había vencido en la fecha de consumo."}
                )

        return data


# ==============================================================================
# CUENTA ALMUERZO MENSUAL
# ==============================================================================

class CuentaAlmuerzoMensualSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = CuentaAlmuerzoMensual
        fields = "__all__"
        read_only_fields = [
            "fecha_generacion",
            "fecha_actualizacion",
            "fecha_creacion",
        ]


# ==============================================================================
# PAGO CUENTA ALMUERZO
# ==============================================================================

class PagoCuentaAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoCuentaAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]

    def validate(self, data):
        cuenta = data.get("cuenta")
        monto = data.get("monto")

        if cuenta and monto is not None:
            if monto <= 0:
                raise serializers.ValidationError({"monto": "El monto debe ser mayor a cero."})
            saldo = cuenta.saldo_pendiente
            if monto > saldo:
                raise serializers.ValidationError(
                    {"monto": f"El monto (₲{monto:,.0f}) supera el saldo pendiente (₲{saldo:,.0f})."}
                )
        return data


# ==============================================================================
# PAGO ALMUERZO MENSUAL
# ==============================================================================

class PagoAlmuerzoMensualSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoAlmuerzoMensual
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]

    def validate(self, data):
        suscripcion = data.get("suscripcion")
        mes_pagado = data.get("mes_pagado")

        if suscripcion and mes_pagado:
            if mes_pagado < suscripcion.fecha_inicio.replace(day=1):
                raise serializers.ValidationError(
                    {"mes_pagado": "El mes pagado es anterior al inicio de la suscripción."}
                )
            if suscripcion.fecha_fin and mes_pagado > suscripcion.fecha_fin.replace(day=1):
                raise serializers.ValidationError(
                    {"mes_pagado": "El mes pagado es posterior al vencimiento de la suscripción."}
                )
        return data


# ==============================================================================
# ALERGENO
# ==============================================================================

class AlergenoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alergeno
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


# ==============================================================================
# PRODUCTO ALERGENO
# ==============================================================================

class ProductoAlergenoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    alergeno_nombre = serializers.CharField(source="alergeno.nombre", read_only=True)

    class Meta:
        model = ProductoAlergeno
        fields = "__all__"
        read_only_fields = ["fecha_registro"]


# ==============================================================================
# MENÚ DIARIO
# ==============================================================================

class MenuDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuDiario
        fields = "__all__"
        read_only_fields = ["creado_por", "fecha_creacion", "fecha_actualizacion"]