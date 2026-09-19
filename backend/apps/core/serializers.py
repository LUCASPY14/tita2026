"""
Serializers para la app core
"""

import logging

from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from common.permissions import ROLES_AUTORIZADORES, exigir_rol

from .models import (
    Tarjeta,
    MovimientoTarjeta,
    CargaSaldo,
    MedioPago,
    PagoBancard,
)

logger = logging.getLogger(__name__)


class TarjetaSerializer(serializers.ModelSerializer):
    # ── Datos del alumno (null cuando es tarjeta de docente/funcionario) ──────
    es_alumno = serializers.SerializerMethodField()
    hijo_nombre = serializers.SerializerMethodField()
    hijo_foto = serializers.SerializerMethodField()
    hijo_grado = serializers.SerializerMethodField()
    hijo_restricciones = serializers.SerializerMethodField()
    hijo_cumple_hoy = serializers.SerializerMethodField()
    saldo_disponible = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    sobregiro_sin_tope = serializers.BooleanField(read_only=True)
    deuda_maxima = serializers.SerializerMethodField()
    saldo_almuerzo = serializers.SerializerMethodField()

    # ── Datos del cliente responsable o del cliente directo ───────────────────
    cliente_id = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    cliente_ruc = serializers.SerializerMethodField()
    cliente_saldo_cc = serializers.SerializerMethodField()
    cliente_limite_credito = serializers.SerializerMethodField()
    cliente_permite_cuenta_corriente = serializers.SerializerMethodField()

    # Lista de precios asignada al cliente (para que el POS aplique precios correctos)
    lista_precio_id = serializers.SerializerMethodField()
    lista_es_default = serializers.SerializerMethodField()

    # Campos con impacto económico: solo ADMIN/SUPERVISOR pueden fijarlos o
    # cambiarlos (valor = el que se considera "sin autorización especial").
    CAMPOS_SENSIBLES = {
        "permite_saldo_negativo": False,
        "limite_credito": Decimal("0"),
        "fecha_vencimiento": None,
    }

    class Meta:
        model = Tarjeta
        fields = "__all__"
        # saldo_actual jamás se edita a mano: solo cambia por operaciones que
        # dejan movimiento (carga, venta, reverso, ajuste).
        read_only_fields = ["fecha_creacion", "ultima_notificacion_saldo", "estado", "saldo_actual"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            return attrs
        cambios = []
        for campo, sin_autorizacion in self.CAMPOS_SENSIBLES.items():
            if campo not in attrs:
                continue
            actual = getattr(self.instance, campo) if self.instance else sin_autorizacion
            if attrs[campo] != actual:
                cambios.append(campo)
        if self.instance:
            for campo in ("hijo", "cliente_directo"):
                if campo in attrs and attrs[campo] != getattr(self.instance, campo):
                    cambios.append(campo)
        if cambios:
            exigir_rol(
                request.user, ROLES_AUTORIZADORES,
                "Solo un administrador o supervisor puede cambiar: " + ", ".join(cambios) + ".",
            )
        return attrs

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
        # No es la URL cruda de /media/ — es el endpoint de clientes que
        # chequea permiso (ADMIN/CAJERO) antes de servir el archivo.
        if obj.hijo_id and obj.hijo.foto_perfil:
            return f"/clientes/hijos/{obj.hijo_id}/foto/"
        return None

    def get_deuda_maxima(self, obj):
        """Tope de deuda en Gs. (0 = prepago, null = sin tope)."""
        tope = obj.deuda_maxima
        return None if tope is None else int(tope)

    def get_saldo_almuerzo(self, obj):
        """Saldo corriente de almuerzo del alumno (puede ser negativo). None si no es alumno."""
        if not obj.hijo_id:
            return None
        try:
            return int(obj.hijo.saldo_almuerzo.saldo_actual)
        except ObjectDoesNotExist:
            return 0

    def get_hijo_grado(self, obj):
        if obj.hijo_id:
            return obj.hijo.grado_nombre
        return None

    def get_hijo_cumple_hoy(self, obj):
        if not obj.hijo_id or not obj.hijo.fecha_nacimiento:
            return False
        from django.utils.timezone import localdate
        hoy = localdate()
        return (obj.hijo.fecha_nacimiento.month, obj.hijo.fecha_nacimiento.day) == (hoy.month, hoy.day)

    def get_hijo_restricciones(self, obj):
        if not obj.hijo_id:
            return []
        restricciones = obj.hijo.restricciones.filter(activo=True)
        return [
            {
                "id_restriccion": r.id_restriccion,
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
        except AttributeError:
            return None

    def get_cliente_nombre(self, obj):
        try:
            return self._get_cliente(obj).nombre_completo
        except AttributeError:
            return None

    def get_cliente_ruc(self, obj):
        try:
            return self._get_cliente(obj).ruc_ci
        except AttributeError:
            return None

    def get_cliente_saldo_cc(self, obj):
        try:
            return int(self._get_cliente(obj).saldo_cuenta_corriente)
        except AttributeError:
            return 0

    def get_cliente_limite_credito(self, obj):
        try:
            return int(self._get_cliente(obj).limite_credito)
        except AttributeError:
            return 0

    def get_cliente_permite_cuenta_corriente(self, obj):
        try:
            return bool(self._get_cliente(obj).permite_cuenta_corriente)
        except AttributeError:
            return False

    def get_lista_precio_id(self, obj):
        try:
            return self._get_cliente(obj).lista_precio_id
        except AttributeError:
            return None

    def get_lista_es_default(self, obj):
        try:
            return bool(self._get_cliente(obj).lista_precio.es_por_defecto)
        except AttributeError:
            logger.debug("TarjetaSerializer: lista_precio no disponible para tarjeta pk=%s", getattr(obj, 'pk', '?'))
            return True

    cliente_modalidad_facturacion = serializers.SerializerMethodField()

    def get_cliente_modalidad_facturacion(self, obj):
        try:
            return self._get_cliente(obj).modalidad_facturacion
        except AttributeError:
            return "INMEDIATA"


class MovimientoTarjetaSerializer(serializers.ModelSerializer):
    tarjeta_nro = serializers.CharField(source="tarjeta.nro_tarjeta", read_only=True)

    class Meta:
        model = MovimientoTarjeta
        fields = "__all__"
        read_only_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]


class CargaSaldoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="responsable.nombre_completo", read_only=True, default=None)

    class Meta:
        model = CargaSaldo
        fields = "__all__"
        # El estado lo fija el servidor (PENDIENTE al crear; CONFIRMADA solo
        # mediante el servicio que acredita el saldo).
        read_only_fields = [
            "fecha_carga", "fecha_confirmacion", "fecha_aprobacion", "fecha_creacion", "estado",
        ]


class MedioPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedioPago
        fields = "__all__"


class PagoBancardSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre_completo", read_only=True, default="")
    tarjeta_nro = serializers.CharField(source="tarjeta.nro_tarjeta", read_only=True, default=None)
    cuenta_almuerzo_id_display = serializers.IntegerField(source="cuenta_almuerzo_id", read_only=True)
    hijo_id_display = serializers.IntegerField(source="hijo_id", read_only=True)

    class Meta:
        model = PagoBancard
        fields = [
            "shop_process_id", "tipo", "estado", "monto", "descripcion",
            "cliente_nombre", "tarjeta_nro", "cuenta_almuerzo_id_display", "hijo_id_display",
            "fecha_creacion", "fecha_confirmacion",
            "card_id_bancard", "card_masked_number",
        ]


class PagoBancardDetailSerializer(PagoBancardSerializer):
    """Variante con la respuesta cruda de Bancard — solo para la vista de detalle
    administrativa, no se incluye en el listado para no inflar ese payload."""

    class Meta(PagoBancardSerializer.Meta):
        fields = PagoBancardSerializer.Meta.fields + [
            "process_id", "ip_origen", "bancard_response",
        ]
