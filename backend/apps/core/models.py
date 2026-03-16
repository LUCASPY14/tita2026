"""
Modelos de la app core
Auto-generados desde la base de datos y organizados por funcionalidad
"""

from django.db import models
from decimal import Decimal


class LegacyCompatCoreMixin:
    """Mixin para compatibilidad con nombres de campos legacy en tests."""

    LEGACY_FIELD_MAP = {}
    LEGACY_VALUE_RESOLVERS = {}

    @classmethod
    def _rewrite(cls, kwargs):
        """Reescribe kwargs para mapear campos legacy a campos actuales."""
        legacy_map = getattr(cls, "LEGACY_FIELD_MAP", {})
        resolvers = getattr(cls, "LEGACY_VALUE_RESOLVERS", {})

        # Aplicar resolvers primero
        for legacy_key, resolver in resolvers.items():
            if legacy_key in kwargs:
                kwargs[legacy_key] = resolver(kwargs[legacy_key])

        # Mapear nombres de campos
        new_kwargs = {}
        for key, value in kwargs.items():
            if key in legacy_map:
                new_key = legacy_map[key]
                if new_key is None:  # Campo deprecado, ignorar
                    continue
                # Solo mapear si el campo destino no está ya en kwargs
                if new_key not in kwargs:
                    new_kwargs[new_key] = value
                # Si destino ya existe, ignorar el alias
            else:
                new_kwargs[key] = value

        return new_kwargs


class LegacyCompatQuerySet(models.QuerySet):
    """QuerySet que traduce kwargs legacy a campos actuales."""

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self.model._rewrite(kwargs))

    def create(self, **kwargs):
        return super().create(**self.model._rewrite(kwargs))

    def get_or_create(self, defaults=None, **kwargs):
        if defaults:
            defaults = self.model._rewrite(defaults)
        return super().get_or_create(defaults=defaults, **self.model._rewrite(kwargs))

    def update_or_create(self, defaults=None, **kwargs):
        if defaults:
            defaults = self.model._rewrite(defaults)
        return super().update_or_create(defaults=defaults, **self.model._rewrite(kwargs))


class LegacyCompatManager(models.Manager.from_queryset(LegacyCompatQuerySet)):
    """Manager con compatibilidad para esquema legacy en tests."""

    pass


class TarjetasManager(models.Manager):
    """Manager que acepta kwargs legacy para crear Tarjetas en tests."""

    def create(self, **kwargs):
        from django.utils import timezone as tz
        # Remap saldo → saldo_actual
        if 'saldo' in kwargs:
            kwargs.setdefault('saldo_actual', kwargs.pop('saldo'))
        else:
            kwargs.pop('saldo', None)
        # Ignorar estado booleano (legacy activo=True/False); preservar si es string
        if isinstance(kwargs.get('estado'), bool):
            kwargs.pop('estado', None)
        # Defaults para campos requeridos
        kwargs.setdefault('saldo_actual', Decimal('0.00'))
        kwargs.setdefault('estado', 'activa')
        kwargs.setdefault('fecha_creacion', tz.now())
        kwargs.setdefault('limite_credito', Decimal('0.00'))
        # Crear id_hijo por defecto si no se provee
        if 'id_hijo' not in kwargs and 'id_hijo_id' not in kwargs:
            from apps.clientes.models import Clientes, TiposCliente, Hijos
            from apps.productos.models import ListasPrecios
            lista, _ = ListasPrecios.objects.get_or_create(nombre_lista='General')
            tipo, _ = TiposCliente.objects.get_or_create(nombre_tipo='General')
            cliente, _ = Clientes.objects.get_or_create(
                ruc_ci='0000001',
                defaults={
                    'nombres': 'Padre',
                    'apellidos': 'Genérico',
                    'id_lista': lista,
                    'id_tipo_cliente': tipo,
                },
            )
            hijo, _ = Hijos.objects.get_or_create(
                nombre='Hijo',
                apellido='Genérico',
                id_cliente_responsable=cliente,
            )
            kwargs['id_hijo'] = hijo
        return super().create(**kwargs)


class Tarjetas(models.Model):
    nro_tarjeta = models.CharField(primary_key=True, max_length=20)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    saldo_alerta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    permite_saldo_negativo = models.BooleanField(
        default=False,
        help_text="Permite realizar compras con saldo negativo (requiere autorización)",
    )
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2)
    notificar_saldo_bajo = models.BooleanField(
        default=True, help_text="Enviar notificación cuando el saldo esté bajo"
    )
    ultima_notificacion_saldo = models.DateTimeField(blank=True, null=True)
    id_hijo = models.OneToOneField("clientes.Hijos", models.DO_NOTHING, db_column="id_hijo")
    codigo_barras = models.CharField(unique=True, max_length=50, blank=True, null=True)

    objects = TarjetasManager()

    def __str__(self):
        return f"Tarjeta {self.nro_tarjeta} - {self.id_hijo}"

    @property
    def saldo_disponible(self):
        """Calcula el saldo disponible considerando límite de crédito"""
        if self.permite_saldo_negativo:
            return self.saldo_actual + self.limite_credito
        return max(self.saldo_actual, 0)

    @property
    def esta_en_alerta(self):
        """Verifica si el saldo está por debajo del nivel de alerta"""
        if self.saldo_alerta:
            return self.saldo_actual <= self.saldo_alerta
        return False

    @property
    def requiere_notificacion(self):
        """Determina si debe enviarse notificación de saldo bajo"""
        return self.notificar_saldo_bajo and self.esta_en_alerta

    def clean(self):
        """Validar que el hijo no tenga otra tarjeta activa"""
        from django.core.exceptions import ValidationError

        if self.id_hijo:
            # Verificar si ya existe otra tarjeta para este hijo
            tarjetas_existentes = Tarjetas.objects.filter(id_hijo=self.id_hijo).exclude(
                nro_tarjeta=self.nro_tarjeta
            )

            if tarjetas_existentes.exists():
                raise ValidationError(
                    {
                        "id_hijo": "Este hijo ya tiene una tarjeta asociada. Solo se permite una tarjeta por hijo."
                    }
                )

    class Meta:
        managed = True
        db_table = "tarjetas"
        verbose_name = "Tarjeta"
        verbose_name_plural = "Tarjetas"


class TarjetasAutorizacion(models.Model):
    id_tarjeta_autorizacion = models.AutoField(primary_key=True)
    codigo_barra = models.CharField(unique=True, max_length=50)
    tipo_autorizacion = models.CharField(max_length=15)
    puede_anular_almuerzos = models.BooleanField(
        default=False, help_text="Permite anular registros de almuerzo"
    )
    puede_anular_ventas = models.BooleanField(default=False, help_text="Permite anular ventas")
    puede_anular_recargas = models.BooleanField(
        default=False, help_text="Permite anular recargas de saldo"
    )
    puede_modificar_precios = models.BooleanField(
        default=False, help_text="Permite modificar precios en punto de venta"
    )
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado", blank=True, null=True
    )

    def __str__(self):
        return f"Tarjeta Autorización {self.codigo_barra} - {self.tipo_autorizacion}"

    class Meta:
        managed = True
        db_table = "tarjetas_autorizacion"
        verbose_name = "Tarjeta de Autorización"
        verbose_name_plural = "Tarjetas de Autorización"


class CargasSaldoManager(models.Manager):
    """Manager que ignora campos legacy no existentes."""

    def _translate_kwargs(self, kwargs):
        """Map id_recarga → id_carga, codigo_referencia → custom_identifier, etc. for backwards compatibility."""
        if 'id_recarga' in kwargs:
            kwargs['id_carga'] = kwargs.pop('id_recarga')
        if 'codigo_referencia' in kwargs:
            kwargs['custom_identifier'] = kwargs.pop('codigo_referencia')
        return kwargs

    def get(self, *args, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        return super().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs = self._translate_kwargs(kwargs)
        return super().filter(*args, **kwargs)

    def create(self, **kwargs):
        # Mapear campo monto → monto_cargado
        if 'monto' in kwargs and 'monto_cargado' not in kwargs:
            kwargs['monto_cargado'] = kwargs.pop('monto')
        else:
            kwargs.pop('monto', None)
        # Mapear fecha_creacion → fecha_carga
        if 'fecha_creacion' in kwargs and 'fecha_carga' not in kwargs:
            kwargs['fecha_carga'] = kwargs.pop('fecha_creacion')
        else:
            kwargs.pop('fecha_creacion', None)
        # Proveer fecha_carga por defecto si falta
        if 'fecha_carga' not in kwargs:
            from django.utils import timezone as tz
            kwargs['fecha_carga'] = tz.now()
        # Mapear codigo_referencia → custom_identifier
        cod_ref = kwargs.pop('codigo_referencia', None)
        if cod_ref and 'custom_identifier' not in kwargs:
            kwargs['custom_identifier'] = cod_ref
        # Mapear comision_aplicada → comision
        if 'comision_aplicada' in kwargs and 'comision' not in kwargs:
            kwargs['comision'] = kwargs.pop('comision_aplicada')
        else:
            kwargs.pop('comision_aplicada', None)
        # Ignorar otros campos legacy que no existen en el modelo
        for campo in ['porcentaje_comision', 'ip_origen',
                      'motivo_rechazo', 'requiere_validacion_supervisor', 'imagen_comprobante',
                      'id_factura_old', 'codigo_referencia_interno']:
            kwargs.pop(campo, None)
        return super().create(**kwargs)


class CargasSaldo(models.Model):
    id_carga = models.BigAutoField(primary_key=True)
    fecha_carga = models.DateTimeField()
    monto_cargado = models.DecimalField(max_digits=12, decimal_places=2)
    referencia = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20)
    pay_request_id = models.CharField(max_length=100, blank=True, null=True)
    tx_id = models.CharField(max_length=100, blank=True, null=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)
    custom_identifier = models.CharField(max_length=100, blank=True, null=True)
    id_cliente_origen = models.ForeignKey(
        "clientes.Clientes", models.DO_NOTHING, db_column="id_cliente_origen", blank=True, null=True
    )
    id_nota = models.BigIntegerField(blank=True, null=True)
    nro_tarjeta = models.ForeignKey(
        "Tarjetas",
        models.SET_NULL,
        db_column="nro_tarjeta",
        blank=True,
        null=True,
    )
    id_factura = models.ForeignKey(
        "ventas.Ventas",
        models.SET_NULL,
        db_column="id_factura",
        blank=True,
        null=True,
        related_name="recargas",
    )
    usuario_responsable = models.ForeignKey(
        "usuarios.Empleados",
        models.SET_NULL,
        db_column="usuario_responsable",
        blank=True,
        null=True,
        related_name="recargas_procesadas",
    )
    supervisor_aprobador = models.ForeignKey(
        "usuarios.Empleados",
        models.SET_NULL,
        db_column="supervisor_aprobador",
        blank=True,
        null=True,
        related_name="recargas_aprobadas",
    )
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    comision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cobrado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    numero_comprobante_externo = models.CharField(max_length=100, blank=True, null=True)
    referencia_externa = models.CharField(max_length=200, blank=True, null=True)

    objects = CargasSaldoManager()

    @property
    def id_recarga(self):
        """Alias for id_carga for backwards compatibility."""
        return self.id_carga

    @property
    def codigo_referencia(self):
        """Alias for custom_identifier for backwards compatibility."""
        return self.custom_identifier

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "cargas_saldo"


class ConsumosTarjetaManager(models.Manager):
    """Manager con compatibilidad de kwargs legacy."""

    def create(self, **kwargs):
        from django.utils import timezone as tz
        if 'monto' in kwargs and 'monto_consumido' not in kwargs:
            kwargs['monto_consumido'] = kwargs.pop('monto')
        else:
            kwargs.pop('monto', None)
        kwargs.pop('establecimiento', None)
        kwargs.setdefault('fecha_consumo', tz.now())
        kwargs.setdefault('saldo_anterior', Decimal('0.00'))
        kwargs.setdefault('saldo_posterior', Decimal('0.00'))
        return super().create(**kwargs)


class ConsumosTarjeta(models.Model):
    id_consumo = models.BigAutoField(primary_key=True)
    fecha_consumo = models.DateTimeField()
    monto_consumido = models.DecimalField(max_digits=12, decimal_places=2)
    detalle = models.CharField(max_length=200, blank=True, null=True)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=2)
    id_empleado_registro = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_registro",
        blank=True,
        null=True,
    )
    nro_tarjeta = models.ForeignKey("Tarjetas", models.DO_NOTHING, db_column="nro_tarjeta")

    objects = ConsumosTarjetaManager()

    @property
    def tipo_operacion(self):
        """Tipo de operación basado en el signo del monto_consumido."""
        return "recarga" if self.monto_consumido < 0 else "consumo"

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "consumos_tarjeta"


class TransaccionesOnline(models.Model):
    id_transaccion = models.AutoField(primary_key=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20)
    estado = models.CharField(max_length=20)
    referencia_pago = models.CharField(max_length=255, blank=True, null=True)
    id_transaccion_externa = models.CharField(max_length=255, blank=True, null=True)
    datos_extra = models.TextField(blank=True, null=True)
    fecha_transaccion = models.DateTimeField()
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()
    nro_tarjeta = models.ForeignKey(
        "Tarjetas", models.DO_NOTHING, db_column="nro_tarjeta", blank=True, null=True
    )
    id_usuario_portal = models.ForeignKey(
        "usuarios.UsuariosPortal",
        models.DO_NOTHING,
        db_column="id_usuario_portal",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "transacciones_online"


class MediosPago(LegacyCompatCoreMixin, models.Model):
    id_medio_pago = models.AutoField(primary_key=True)
    descripcion = models.CharField(unique=True, max_length=50)
    genera_comision = models.BooleanField(
        default=False, help_text="Si este medio de pago cobra comisión"
    )
    requiere_validacion = models.BooleanField(
        default=False, help_text="Requiere validación externa (ej: tarjeta crédito)"
    )
    estado = models.BooleanField(default=True)

    LEGACY_FIELD_MAP = {"nombre": "descripcion"}
    objects = LegacyCompatManager()

    def __str__(self):
        return self.descripcion

    class Meta:
        managed = True
        db_table = "medios_pago"
        verbose_name = "Medio de Pago"
        verbose_name_plural = "Medios de Pago"


class ConfiguracionSistemaManager(models.Manager):
    """Manager que provee defaults para campos NOT NULL en ConfiguracionSistema."""

    def create(self, **kwargs):
        from django.utils import timezone as tz
        # Mapear valor_texto → valor (campo legacy)
        if 'valor_texto' in kwargs and 'valor' not in kwargs:
            kwargs['valor'] = kwargs.pop('valor_texto')
        else:
            kwargs.pop('valor_texto', None)
        kwargs.setdefault('valor', '')
        kwargs.setdefault('tipo', 'texto')
        kwargs.setdefault('categoria', 'general')
        kwargs.setdefault('descripcion', '')
        kwargs.setdefault('valor_defecto', '')
        kwargs.setdefault('updated_at', tz.now())
        kwargs.setdefault('valores_permitidos', [])
        kwargs.setdefault('validacion', '')
        kwargs.setdefault('valor_min', '')
        kwargs.setdefault('valor_max', '')
        return super().create(**kwargs)


class ConfiguracionSistema(models.Model):
    id_config = models.AutoField(primary_key=True)
    clave = models.CharField(unique=True, max_length=100)
    valor = models.TextField()
    tipo = models.CharField(max_length=20)
    categoria = models.CharField(max_length=50)
    descripcion = models.TextField()
    valor_defecto = models.TextField()
    requerido = models.BooleanField(default=False, help_text="Configuración obligatoria")
    validacion = models.CharField(max_length=500)
    valores_permitidos = models.JSONField()
    valor_min = models.CharField(max_length=100)
    valor_max = models.CharField(max_length=100)
    requiere_reinicio = models.BooleanField(
        default=False, help_text="Requiere reiniciar el sistema al cambiar"
    )
    solo_superuser = models.BooleanField(
        default=False, help_text="Solo superusuarios pueden modificar"
    )
    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField()
    updated_by = models.ForeignKey(
        "auth.User", models.SET_NULL, db_column="updated_by", blank=True, null=True
    )

    objects = ConfiguracionSistemaManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    @property
    def id_configuracion(self):
        """Alias de id_config para compatibilidad con código legacy."""
        return self.id_config

    class Meta:
        managed = True
        db_table = "configuracion_sistema"


class CacheConfiguracion(models.Model):
    id_cache = models.AutoField(primary_key=True)
    clave = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField()
    ttl_segundos = models.IntegerField()
    max_size_mb = models.IntegerField()
    tipo_cache = models.CharField(max_length=20)
    auto_invalidate = models.BooleanField(
        default=True, help_text="Invalidar automáticamente el caché"
    )
    eventos_invalid = models.JSONField()
    estado = models.BooleanField(default=True)
    hits = models.BigIntegerField()
    misses = models.BigIntegerField()
    ultima_limpieza = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "cache_configuracion"


class LimitesTransaccion(models.Model):
    """
    Límites de autorización por rol para operaciones críticas.

    Permite configurar montos máximos sin autorización de supervisor.

    Casos de uso:
    - Venta > límite → requiere autorización
    - Descuento > límite → requiere autorización
    - Ajuste inventario > límite → requiere aprobación gerente
    - Nota de crédito > límite → requiere doble autorización
    """

    id_limite = models.AutoField(primary_key=True)
    tipo_operacion = models.CharField(
        max_length=50,
        choices=[
            ("venta", "Venta"),
            ("descuento", "Aplicar descuento"),
            ("nota_credito_cliente", "Nota de crédito a cliente"),
            ("nota_credito_proveedor", "Nota de crédito de proveedor"),
            ("ajuste_inventario", "Ajuste de inventario"),
            ("exceder_credito", "Exceder límite de crédito cliente"),
            ("anular_venta", "Anular venta"),
            ("retiro_caja", "Retiro de caja"),
            ("devolucion", "Procesar devolución"),
        ],
        help_text="Tipo de operación a controlar",
    )
    monto_maximo_sin_autorizacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto máximo que el rol puede procesar sin autorización",
    )
    requiere_autorizacion_doble = models.BooleanField(
        default=False, help_text="Requiere autorización de dos supervisores diferentes"
    )
    roles_autorizadores = models.ManyToManyField(
        "usuarios.Roles",
        related_name="roles_autorizados_para",
        blank=True,
        help_text="Roles que pueden autorizar esta operación",
    )
    estado = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    id_rol = models.ForeignKey(
        "usuarios.Roles",
        models.DO_NOTHING,
        db_column="id_rol",
        related_name="limites_transaccion",
        help_text="Rol al que aplica este límite",
    )
    id_empleado_configurador = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_configurador",
        blank=True,
        null=True,
        help_text="Quién configuró este límite",
    )

    class Meta:
        managed = True
        db_table = "limites_transaccion"
        verbose_name = "Límite de Transacción"
        verbose_name_plural = "Límites de Transacciones"
        unique_together = (("id_rol", "tipo_operacion"),)
        indexes = [
            models.Index(fields=["id_rol", "tipo_operacion"]),
            models.Index(fields=["tipo_operacion", "estado"]),
        ]

    def __str__(self):
        return f"{self.id_rol.nombre_rol} - {self.get_tipo_operacion_display()}: Gs. {self.monto_maximo_sin_autorizacion:,.0f}"

    @staticmethod
    def obtener_limite(rol, tipo_operacion):
        """
        Obtiene el límite configurado para un rol y tipo de operación.

        Returns:
            LimitesTransaccion o None si no hay límite configurado
        """
        try:
            return LimitesTransaccion.objects.get(
                id_rol=rol, tipo_operacion=tipo_operacion, estado=True
            )
        except LimitesTransaccion.DoesNotExist:
            return None

    @staticmethod
    def requiere_autorizacion(rol, tipo_operacion, monto):
        """
        Verifica si una operación requiere autorización.

        Args:
            rol: Instancia de Roles
            tipo_operacion: str (ej: 'venta', 'descuento')
            monto: Decimal

        Returns:
            dict con:
                - requiere: bool
                - limite: Decimal o None
                - mensaje: str
                - doble_autorizacion: bool
        """
        limite = LimitesTransaccion.obtener_limite(rol, tipo_operacion)

        if not limite:
            # Sin límite configurado = sin restricciones
            return {
                "requiere": False,
                "limite": None,
                "mensaje": "No hay límite configurado para este rol",
                "doble_autorizacion": False,
            }

        requiere = monto > limite.monto_maximo_sin_autorizacion

        return {
            "requiere": requiere,
            "limite": limite.monto_maximo_sin_autorizacion,
            "mensaje": (
                f"El monto excede el límite de Gs. {limite.monto_maximo_sin_autorizacion:,.0f}"
                if requiere
                else "Operación dentro del límite"
            ),
            "doble_autorizacion": limite.requiere_autorizacion_doble,
            "excedente": (
                monto - limite.monto_maximo_sin_autorizacion if requiere else Decimal("0.00")
            ),
        }


class RegistroAutorizaciones(models.Model):
    """
    Registro de todas las autorizaciones otorgadas.

    Permite auditoría completa de:
    - Quién autorizó qué operación
    - Cuándo se autorizó
    - Motivo de la autorización
    """

    id_autorizacion = models.AutoField(primary_key=True)
    tipo_operacion = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.TextField(help_text="Justificación de por qué se autorizó")
    fecha_autorizacion = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    id_empleado_solicitante = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_solicitante",
        related_name="autorizaciones_solicitadas",
        help_text="Quien solicita la autorización",
    )
    id_empleado_autorizador = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_autorizador",
        related_name="autorizaciones_otorgadas",
        help_text="Quien autoriza (supervisor/gerente)",
    )
    id_empleado_autorizador_2 = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_autorizador_2",
        blank=True,
        null=True,
        related_name="autorizaciones_dobles",
        help_text="Segundo autorizador (si requiere doble autorización)",
    )

    # Relaciones opcionales con operaciones específicas
    id_venta = models.ForeignKey(
        "ventas.Ventas", models.DO_NOTHING, db_column="id_venta", blank=True, null=True
    )
    id_compra = models.ForeignKey(
        "compras.Compras", models.DO_NOTHING, db_column="id_compra", blank=True, null=True
    )
    id_ajuste = models.ForeignKey(
        "inventario.AjustesInventario",
        models.DO_NOTHING,
        db_column="id_ajuste",
        blank=True,
        null=True,
    )

    class Meta:
        managed = True
        db_table = "registro_autorizaciones"
        verbose_name = "Registro de Autorización"
        verbose_name_plural = "Registro de Autorizaciones"
        ordering = ["-fecha_autorizacion"]
        indexes = [
            models.Index(fields=["id_empleado_solicitante", "-fecha_autorizacion"]),
            models.Index(fields=["id_empleado_autorizador", "-fecha_autorizacion"]),
            models.Index(fields=["tipo_operacion", "-fecha_autorizacion"]),
        ]

    def __str__(self):
        return f"{self.tipo_operacion} - Gs. {self.monto:,.0f} - {self.fecha_autorizacion.strftime('%d/%m/%Y %H:%M')}"
