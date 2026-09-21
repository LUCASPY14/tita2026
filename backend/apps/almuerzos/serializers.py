"""
Serializers para la app almuerzos
"""

from rest_framework import serializers

from .models import (
    Alergeno,
    CuentaAlmuerzoMensual,
    DetalleMenuDiario,
    MenuDiario,
    MovimientoSaldoAlmuerzo,
    PagoCuentaAlmuerzo,
    PrecioAlmuerzo,
    ProductoAlergeno,
    RecargaSaldoAlmuerzo,
    RegistroConsumoAlmuerzo,
    SaldoAlmuerzo,
    SuscripcionAlmuerzo,
    TipoAlmuerzo,
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
# SUSCRIPCION ALMUERZO
# ==============================================================================

class SuscripcionAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)

    class Meta:
        model = SuscripcionAlmuerzo
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]

    def validate(self, data):
        # unique_suscripcion_activa_por_hijo (a lo sumo una ACTIVA por hijo)
        # daría un IntegrityError feo (500) sin este chequeo explícito.
        hijo = data.get("hijo") or getattr(self.instance, "hijo", None)
        estado = data.get("estado", getattr(self.instance, "estado", SuscripcionAlmuerzo.Estado.ACTIVA))
        if hijo and estado == SuscripcionAlmuerzo.Estado.ACTIVA:
            qs = SuscripcionAlmuerzo.objects.filter(
                hijo=hijo, estado=SuscripcionAlmuerzo.Estado.ACTIVA,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "hijo": "Este alumno ya tiene una suscripción activa. Cancelala o suspendela primero."
                })
        return data


# ==============================================================================
# REGISTRO CONSUMO ALMUERZO
# ==============================================================================

class RegistroConsumoAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    tipo_almuerzo_nombre = serializers.CharField(source="tipo_almuerzo.nombre", read_only=True)
    # Sin validators=[]: DRF genera un UniqueValidator automático para todo
    # campo unique=True, que rechazaría con 400 el reintento legítimo de la
    # cola offline antes de llegar a la deduplicación de perform_create()
    # (RegistroConsumoAlmuerzoViewSet). La unicidad real la sigue
    # garantizando la constraint de la base de datos.
    client_request_id = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=64, validators=[],
    )

    class Meta:
        model = RegistroConsumoAlmuerzo
        fields = "__all__"
        read_only_fields = [
            "hora_registro",
            "costo_almuerzo",
            "ya_cobrado",
            "estado",
            "registrado_por",
            "fecha_creacion",
            # La suscripción activa se resuelve del lado del servidor
            # (RegistroConsumoAlmuerzoViewSet.perform_create) — es obligatoria
            # y a lo sumo hay una por hijo (unique_suscripcion_activa_por_hijo),
            # así que no tiene sentido que el cliente la elija.
            "suscripcion",
        ]


# ==============================================================================
# CUENTA ALMUERZO MENSUAL
# ==============================================================================

class CuentaAlmuerzoMensualSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    hijo_grado = serializers.CharField(source="hijo.grado.nombre", read_only=True, default="")
    nro_tarjeta = serializers.SerializerMethodField()
    saldo_pendiente = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    def get_nro_tarjeta(self, obj):
        tarjeta = getattr(obj.hijo, "tarjeta", None)
        return tarjeta.nro_tarjeta if tarjeta else ""

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
        read_only_fields = ["fecha_creacion", "registrado_por", "factura"]

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
# SALDO DE ALMUERZO (CUENTA CORRIENTE)
# ==============================================================================

class SaldoAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    hijo_grado = serializers.CharField(source="hijo.grado.nombre", read_only=True, default=None)
    nro_tarjeta = serializers.SerializerMethodField()

    def get_nro_tarjeta(self, obj):
        tarjeta = getattr(obj.hijo, "tarjeta", None)
        return tarjeta.nro_tarjeta if tarjeta else ""

    class Meta:
        model = SaldoAlmuerzo
        fields = "__all__"
        read_only_fields = ["saldo_actual", "fecha_actualizacion", "fecha_creacion"]


class MovimientoSaldoAlmuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoSaldoAlmuerzo
        fields = "__all__"


class RecargaSaldoAlmuerzoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    registrado_por_nombre = serializers.CharField(
        source="registrado_por.nombre_completo", read_only=True, default=None
    )

    class Meta:
        model = RecargaSaldoAlmuerzo
        fields = "__all__"
        read_only_fields = [
            "estado", "fecha_carga", "fecha_creacion", "registrado_por", "factura",
        ]

    def validate_monto_cargado(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero.")
        return value


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
# MENÚ DIARIO + DETALLE
# ==============================================================================

class DetalleMenuDiarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.descripcion", read_only=True)
    producto_codigo = serializers.CharField(source="producto.codigo", read_only=True)
    unidad_medida = serializers.CharField(
        source="producto.unidad_medida.abreviatura", read_only=True, allow_null=True
    )
    curso_display = serializers.CharField(source="get_curso_display", read_only=True)

    class Meta:
        model = DetalleMenuDiario
        fields = [
            "id_detalle_menu", "menu", "producto", "producto_nombre", "producto_codigo",
            "unidad_medida", "curso", "curso_display",
            "cantidad", "es_opcional", "observaciones",
        ]

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return value


class MenuDiarioSerializer(serializers.ModelSerializer):
    detalles = DetalleMenuDiarioSerializer(many=True, read_only=True)
    tiene_alergenos = serializers.BooleanField(read_only=True)

    class Meta:
        model = MenuDiario
        fields = "__all__"
        read_only_fields = ["creado_por", "fecha_creacion", "fecha_actualizacion"]
