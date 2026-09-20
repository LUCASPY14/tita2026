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
    Departamento,
    Grado,
    CalendarioLectivo,
    HistorialGrado,
    Hijo,
    Pais,
    PromocionAlumno,
    PromocionAnual,
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
            "id_responsable",
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
            "id_responsable",
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
    saldo_cc_cantina = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    saldo_cc_almuerzo = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
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
    # La foto nunca se expone como URL cruda de /media/ — se sirve por un
    # endpoint propio que chequea permisos (solo ADMIN/CAJERO). foto_perfil
    # queda write_only para no romper la carga por FormData desde ModalHijo.
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Hijo
        fields = "__all__"
        extra_kwargs = {"foto_perfil": {"write_only": True}}
        # Los fija el sistema (baja, purga); no se editan por la API genérica.
        read_only_fields = ["fecha_baja", "purga_solicitada_en", "datos_purgados"]

    def get_responsables(self, obj):
        qs = obj.responsables.filter(activo=True).select_related("cliente").order_by("orden_cobro")
        return AlumnoResponsableResumenSerializer(qs, many=True).data

    def get_foto_url(self, obj):
        if obj.foto_perfil:
            return f"/clientes/hijos/{obj.pk}/foto/"
        return None


class GradoSerializer(serializers.ModelSerializer):
    siguiente_nombre = serializers.CharField(source="siguiente.nombre", read_only=True, default=None)

    class Meta:
        model = Grado
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]

    def validate(self, attrs):
        siguiente = attrs.get("siguiente", getattr(self.instance, "siguiente", None))
        es_ultimo = attrs.get("es_ultimo", getattr(self.instance, "es_ultimo", False))
        if siguiente is not None:
            if self.instance is not None and siguiente.pk == self.instance.pk:
                raise serializers.ValidationError({"siguiente": "Un grado no puede ser su propio siguiente."})
            if es_ultimo:
                raise serializers.ValidationError({"siguiente": "El último curso no tiene grado siguiente."})
        return attrs


class CalendarioLectivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarioLectivo
        fields = "__all__"
        read_only_fields = ["baja_ultimo_curso_aplicada", "fecha_creacion"]

    def validate(self, attrs):
        anio = attrs.get("anio", getattr(self.instance, "anio", None))
        aviso = attrs.get("fecha_aviso_ultimo_curso", getattr(self.instance, "fecha_aviso_ultimo_curso", None))
        cierre = attrs.get("fecha_cierre_lectivo", getattr(self.instance, "fecha_cierre_lectivo", None))
        if aviso and cierre and aviso >= cierre:
            raise serializers.ValidationError(
                {"fecha_aviso_ultimo_curso": "La fecha de aviso debe ser anterior al cierre del año lectivo."}
            )
        for campo, valor in (("fecha_aviso_ultimo_curso", aviso), ("fecha_cierre_lectivo", cierre)):
            if valor and anio and valor.year != anio:
                raise serializers.ValidationError({campo: f"Debe estar dentro del año {anio}."})
        return attrs


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


class DepartamentoSerializer(serializers.ModelSerializer):
    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True, allow_null=True)

    class Meta:
        model = Departamento
        fields = "__all__"


class CiudadSerializer(serializers.ModelSerializer):
    departamento_nombre = serializers.CharField(source="departamento.nombre", read_only=True, allow_null=True)
    pais_nombre = serializers.CharField(source="departamento.pais.nombre", read_only=True, allow_null=True)

    class Meta:
        model = Ciudad
        fields = "__all__"


class PromocionAlumnoSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source="hijo.nombre_completo", read_only=True)
    hijo_activo = serializers.BooleanField(source="hijo.activo", read_only=True)
    grado_origen_nombre = serializers.CharField(source="grado_origen.nombre", read_only=True, default=None)
    grado_destino_nombre = serializers.CharField(source="grado_destino.nombre", read_only=True, default=None)
    origen_es_ultimo = serializers.BooleanField(source="grado_origen.es_ultimo", read_only=True, default=False)
    origen_siguiente = serializers.IntegerField(source="grado_origen.siguiente_id", read_only=True, default=None)
    problema = serializers.SerializerMethodField()

    class Meta:
        model = PromocionAlumno
        fields = [
            "id_promocion_alumno", "hijo", "hijo_nombre", "hijo_activo", "grado_origen", "grado_origen_nombre",
            "origen_es_ultimo", "origen_siguiente", "decision", "grado_destino", "grado_destino_nombre", "motivo", "problema",
        ]
        read_only_fields = fields

    def get_problema(self, obj):
        from .promocion import problema_de_linea
        return problema_de_linea(obj)


class PromocionAnualSerializer(serializers.ModelSerializer):
    creada_por_nombre = serializers.CharField(source="creada_por.email", read_only=True, default=None)
    aplicada_por_nombre = serializers.CharField(source="aplicada_por.email", read_only=True, default=None)
    total_alumnos = serializers.SerializerMethodField()

    class Meta:
        model = PromocionAnual
        fields = [
            "id_promocion", "anio", "estado", "creada_por_nombre", "fecha_creacion",
            "aplicada_por_nombre", "fecha_aplicacion", "total_alumnos",
        ]
        read_only_fields = fields

    def get_total_alumnos(self, obj):
        return obj.lineas.count()


class GenerarPromocionSerializer(serializers.Serializer):
    anio = serializers.IntegerField(min_value=2000, max_value=2100)


class ActualizarLineaSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=PromocionAlumno.Decision.choices)
    grado_destino = serializers.PrimaryKeyRelatedField(queryset=Grado.objects.all(), required=False, allow_null=True)
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=500)


class ActualizarGrupoSerializer(serializers.Serializer):
    grado_origen = serializers.PrimaryKeyRelatedField(queryset=Grado.objects.all())
    decision = serializers.ChoiceField(choices=PromocionAlumno.Decision.choices)
    grado_destino = serializers.PrimaryKeyRelatedField(queryset=Grado.objects.all(), required=False, allow_null=True)
