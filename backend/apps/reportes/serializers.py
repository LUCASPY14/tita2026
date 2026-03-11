"""
Serializers para reportes
Maneja la serialización y validación de datos de reportes
"""

from decimal import Decimal
from datetime import date, datetime
from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import (
    PlantillasReporte,
    Dashboards,
    KpiMetricas,
    ValoresKpi,
    PlantillasTarea,
    EjecucionesTarea,
    DestinatariosTarea
)
from .validators import (
    validar_configuracion_json,
    validar_tipo_reporte,
    validar_frecuencia_ejecucion,
    validar_formato_datos_json
)
from apps.usuarios.models import Empleados
from apps.usuarios.serializers import EmpleadosSerializer as EmpleadoBasicoSerializer


class ConfiguracionJSONField(serializers.JSONField):
    """Campo personalizado para configuraciones JSON complejas"""
    
    def to_internal_value(self, data):
        """Validar y convertir datos JSON internos"""
        try:
            validated_data = super().to_internal_value(data)
            # Validación adicional específica de configuraciones
            if isinstance(validated_data, dict):
                return validated_data
            else:
                raise serializers.ValidationError(
                    "La configuración debe ser un objeto JSON válido"
                )
        except Exception as e:
            raise serializers.ValidationError(f"JSON inválido: {str(e)}")

    def to_representation(self, value):
        """Representación optimizada para APIs"""
        if value is None:
            return {}
        return super().to_representation(value)


class PlantillasReporteSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de reportes"""
    
    activo = serializers.BooleanField(default=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    configuracion_json = ConfiguracionJSONField()
    
    # Campos calculados
    total_ejecuciones = serializers.SerializerMethodField()
    ultima_ejecucion = serializers.SerializerMethodField()
    
    class Meta:
        model = PlantillasReporte
        fields = [
            'id_plantilla',
            'nombre',
            'descripcion',
            'tipo_reporte',
            'configuracion_json',
            'activo',
            'fecha_creacion',
            'fecha_modificacion',
            'total_ejecuciones',
            'ultima_ejecucion'
        ]
        read_only_fields = ['id_plantilla', 'fecha_creacion', 'fecha_modificacion']

    def validate_tipo_reporte(self, value):
        """Validar tipo de reporte"""
        return validar_tipo_reporte(value)

    def validate_configuracion_json(self, value):
        """Validar configuración JSON"""
        return validar_configuracion_json(value)

    def validate_nombre(self, value):
        """Validar nombre único para plantillas activas"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 3 caracteres"
            )
        
        # Verificar unicidad en plantillas activas
        query = PlantillasReporte.objects.filter(
            nombre=value.strip(),
            activo=True
        )
        
        # Excluir instancia actual en actualizaciones
        if self.instance:
            query = query.exclude(id_plantilla=self.instance.id_plantilla)
        
        if query.exists():
            raise serializers.ValidationError(
                "Ya existe una plantilla activa con este nombre"
            )
        
        return value.strip()

    def get_total_ejecuciones(self, obj):
        """Calcular total de ejecuciones de la plantilla"""
        return obj.ejecuciones.filter(estado='completada').count()

    def get_ultima_ejecucion(self, obj):
        """Obtener fecha de última ejecución"""
        ultima = obj.ejecuciones.order_by('-fecha_ejecucion').first()
        return ultima.fecha_ejecucion if ultima else None

    def create(self, validated_data):
        """Crear nueva plantilla con validaciones adicionales"""
        # Validar configuración específica por tipo
        tipo_reporte = validated_data['tipo_reporte']
        configuracion = validated_data['configuracion_json']
        
        self._validar_configuracion_por_tipo(tipo_reporte, configuracion)
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Actualizar plantilla preservando integridad"""
        # Solo permitir ciertos cambios si tiene ejecuciones
        if instance.ejecuciones.exists():
            campos_restringidos = ['tipo_reporte']
            for campo in campos_restringidos:
                if campo in validated_data and validated_data[campo] != getattr(instance, campo):
                    raise serializers.ValidationError({
                        campo: "No se puede modificar este campo en plantillas con ejecuciones"
                    })
        
        return super().update(instance, validated_data)

    def _validar_configuracion_por_tipo(self, tipo_reporte, configuracion):
        """Validar configuración específica por tipo de reporte"""
        campos_requeridos = {
            'ventas': ['fecha_inicio', 'fecha_fin', 'incluir_detalles'],
            'inventario': ['incluir_stock_minimo', 'categorias'],
            'financiero': ['periodo', 'incluir_graficos', 'desglosar_por'],
            'clientes': ['incluir_activos', 'incluir_historiales']
        }
        
        if tipo_reporte in campos_requeridos:
            for campo in campos_requeridos[tipo_reporte]:
                if campo not in configuracion:
                    raise serializers.ValidationError(
                        f"Campo '{campo}' requerido para reporte tipo '{tipo_reporte}'"
                    )


class PlantillasReporteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    total_ejecuciones = serializers.SerializerMethodField()
    estado_ultima_ejecucion = serializers.SerializerMethodField()

    class Meta:
        model = PlantillasReporte
        fields = [
            'id_plantilla',
            'nombre',
            'tipo_reporte',
            'activo',
            'fecha_creacion',
            'total_ejecuciones',
            'estado_ultima_ejecucion'
        ]

    def get_total_ejecuciones(self, obj):
        """Total de ejecuciones"""
        return obj.ejecuciones.count()

    def get_estado_ultima_ejecucion(self, obj):
        """Estado de la última ejecución"""
        ultima = obj.ejecuciones.order_by('-fecha_ejecucion').first()
        return ultima.estado if ultima else None


class DashboardsSerializer(serializers.ModelSerializer):
    """Serializer para dashboards"""
    
    activo = serializers.BooleanField(default=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    configuracion_dashboard = ConfiguracionJSONField()
    
    # Campos anidados
    kpis_principales = serializers.SerializerMethodField()
    orden_widgets = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Lista de IDs de widgets en orden de visualización"
    )

    class Meta:
        model = Dashboards
        fields = [
            'id_dashboard',
            'nombre',
            'descripcion',
            'configuracion_dashboard',
            'activo',
            'fecha_creacion',
            'kpis_principales',
            'orden_widgets'
        ]
        read_only_fields = ['id_dashboard', 'fecha_creacion']

    def validate_configuracion_dashboard(self, value):
        """Validar configuración de dashboard"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Debe ser un objeto JSON válido")
        
        # Validar estructura mínima
        campos_requeridos = ['layout', 'widgets']
        for campo in campos_requeridos:
            if campo not in value:
                raise serializers.ValidationError(
                    f"Campo '{campo}' requerido en configuración"
                )
        
        # Validar widgets
        widgets = value.get('widgets', {})
        if not isinstance(widgets, dict):
            raise serializers.ValidationError("'widgets' debe ser un objeto")
        
        return value

    def validate_nombre(self, value):
        """Validar nombre único"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 2 caracteres"
            )
        
        query = Dashboards.objects.filter(nombre=value.strip(), activo=True)
        if self.instance:
            query = query.exclude(id_dashboard=self.instance.id_dashboard)
        
        if query.exists():
            raise serializers.ValidationError(
                "Ya existe un dashboard activo con este nombre"
            )
        
        return value.strip()

    def get_kpis_principales(self, obj):
        """Obtener KPIs principales del dashboard"""
        # Filtrar KPIs activos del dashboard
        kpis = obj.kpis.filter(activo=True).order_by('orden_visualizacion')[:5]
        return KpiMetricasSerializer(kpis, many=True).data


class KpiMetricasSerializer(serializers.ModelSerializer):
    """Serializer para métricas KPI"""
    
    activo = serializers.BooleanField(default=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    configuracion_calculo = ConfiguracionJSONField()
    
    # Campos relacionados
    dashboard_nombre = serializers.CharField(source='id_dashboard.nombre', read_only=True)
    valor_actual = serializers.SerializerMethodField()
    variacion_porcentual = serializers.SerializerMethodField()
    
    # Validaciones
    orden_visualizacion = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    class Meta:
        model = KpiMetricas
        fields = [
            'id_kpi',
            'id_dashboard',
            'nombre_kpi',
            'descripcion',
            'tipo_metrica',
            'configuracion_calculo',
            'orden_visualizacion',
            'activo',
            'fecha_creacion',
            'dashboard_nombre',
            'valor_actual',
            'variacion_porcentual'
        ]
        read_only_fields = ['id_kpi', 'fecha_creacion']

    def validate_configuracion_calculo(self, value):
        """Validar configuración de cálculo KPI"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Debe ser un objeto JSON válido")
        
        # Campos requeridos según tipo de métrica
        campos_base = ['fuente_datos', 'formula']
        for campo in campos_base:
            if campo not in value:
                raise serializers.ValidationError(
                    f"Campo '{campo}' requerido en configuración de cálculo"
                )
        
        # Validar fórmula
        formula = value.get('formula', '')
        if not formula or len(formula.strip()) < 3:
            raise serializers.ValidationError(
                "La fórmula debe tener al menos 3 caracteres"
            )
        
        return value

    def validate_tipo_metrica(self, value):
        """Validar tipo de métrica"""
        tipos_validos = ['suma', 'promedio', 'conteo', 'porcentaje', 'ratio', 'personalizado']
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo de métrica inválido. Opciones: {', '.join(tipos_validos)}"
            )
        return value

    def get_valor_actual(self, obj):
        """Obtener valor actual del KPI"""
        ultimo_valor = obj.valores.order_by('-fecha_calculo').first()
        if ultimo_valor:
            return {
                'valor': str(ultimo_valor.valor),
                'fecha': ultimo_valor.fecha_calculo,
                'unidad': ultimo_valor.unidad_medida
            }
        return None

    def get_variacion_porcentual(self, obj):
        """Calcular variación porcentual respecto al período anterior"""
        valores = obj.valores.order_by('-fecha_calculo')[:2]
        if len(valores) >= 2:
            actual = valores[0].valor
            anterior = valores[1].valor
            if anterior != Decimal('0'):
                variacion = ((actual - anterior) / anterior) * 100
                return float(variacion)
        return None


class ValoresKpiSerializer(serializers.ModelSerializer):
    """Serializer para valores de KPI"""
    
    fecha_calculo = serializers.DateTimeField(read_only=True)
    
    # Campos relacionados
    kpi_nombre = serializers.CharField(source='id_kpi.nombre_kpi', read_only=True)
    
    # Validaciones personalizadas
    valor = serializers.DecimalField(
        max_digits=15, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('-999999999.9999'))]
    )

    class Meta:
        model = ValoresKpi
        fields = [
            'id_valor',
            'id_kpi',
            'valor',
            'unidad_medida',
            'fecha_calculo',
            'observaciones',
            'kpi_nombre'
        ]
        read_only_fields = ['id_valor', 'fecha_calculo']

    def validate_unidad_medida(self, value):
        """Validar unidad de medida"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError(
                "La unidad de medida es requerida"
            )
        return value.strip()

    def validate_valor(self, value):
        """Validar que el valor sea numérico válido"""
        if value is None:
            raise serializers.ValidationError("El valor es requerido")
        
        # Validar rango razonable
        if value < Decimal('-999999999') or value > Decimal('999999999'):
            raise serializers.ValidationError(
                "El valor está fuera del rango válido"
            )
        
        return value


class PlantillasTareaSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de tareas"""
    
    activo = serializers.BooleanField(default=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    configuracion_tarea = ConfiguracionJSONField()
    
    # Validaciones
    frecuencia_ejecucion = serializers.ChoiceField(
        choices=[
            ('diaria', 'Diaria'),
            ('semanal', 'Semanal'),
            ('mensual', 'Mensual'),
            ('manual', 'Manual')
        ]
    )
    
    # Campos calculados
    proxima_ejecucion = serializers.SerializerMethodField()
    total_ejecuciones_exitosas = serializers.SerializerMethodField()

    class Meta:
        model = PlantillasTarea
        fields = [
            'id_plantilla_tarea',
            'nombre_tarea',
            'descripcion',
            'tipo_tarea',
            'frecuencia_ejecucion',
            'configuracion_tarea',
            'activo',
            'fecha_creacion',
            'proxima_ejecucion',
            'total_ejecuciones_exitosas'
        ]
        read_only_fields = ['id_plantilla_tarea', 'fecha_creacion']

    def validate_frecuencia_ejecucion(self, value):
        """Validar frecuencia de ejecución"""
        return validar_frecuencia_ejecucion(value)

    def validate_configuracion_tarea(self, value):
        """Validar configuración de tarea"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Debe ser un objeto JSON válido")
        
        # Campos mínimos requeridos
        campos_requeridos = ['parametros']
        for campo in campos_requeridos:
            if campo not in value:
                raise serializers.ValidationError(
                    f"Campo '{campo}' requerido en configuración"
                )
        
        return value

    def get_proxima_ejecucion(self, obj):
        """Calcular próxima ejecución según frecuencia"""
        if obj.frecuencia_ejecucion == 'manual':
            return None
        
        ultima_ejecucion = obj.ejecuciones.filter(
            estado='completada'
        ).order_by('-fecha_ejecucion').first()
        
        if not ultima_ejecucion:
            return datetime.now()
        
        from datetime import timedelta
        fecha_base = ultima_ejecucion.fecha_ejecucion
        
        if obj.frecuencia_ejecucion == 'diaria':
            return fecha_base + timedelta(days=1)
        elif obj.frecuencia_ejecucion == 'semanal':
            return fecha_base + timedelta(weeks=1)
        elif obj.frecuencia_ejecucion == 'mensual':
            # Aproximación: 30 días
            return fecha_base + timedelta(days=30)
        
        return None

    def get_total_ejecuciones_exitosas(self, obj):
        """Contar ejecuciones exitosas"""
        return obj.ejecuciones.filter(estado='completada').count()


class EjecucionesTareaSerializer(serializers.ModelSerializer):
    """Serializer para ejecuciones de tareas"""
    
    fecha_ejecucion = serializers.DateTimeField(read_only=True)
    fecha_finalizacion = serializers.DateTimeField(read_only=True, allow_null=True)
    
    # Campos relacionados
    plantilla_nombre = serializers.CharField(
        source='id_plantilla_tarea.nombre_tarea', 
        read_only=True
    )
    empleado_ejecutor = EmpleadoBasicoSerializer(
        source='id_empleado_ejecutor',
        read_only=True
    )
    
    # Campos calculados
    duracion_segundos = serializers.SerializerMethodField()
    resultado_resumen = serializers.SerializerMethodField()

    class Meta:
        model = EjecucionesTarea
        fields = [
            'id_ejecucion',
            'id_plantilla_tarea',
            'id_empleado_ejecutor',
            'fecha_ejecucion',
            'fecha_finalizacion',
            'estado',
            'resultado_json',
            'mensaje_error',
            'plantilla_nombre',
            'empleado_ejecutor',
            'duracion_segundos',
            'resultado_resumen'
        ]
        read_only_fields = [
            'id_ejecucion', 
            'fecha_ejecucion', 
            'fecha_finalizacion'
        ]

    def validate_estado(self, value):
        """Validar estado de ejecución"""
        estados_validos = ['pendiente', 'ejecutando', 'completada', 'error']
        if value not in estados_validos:
            raise serializers.ValidationError(
                f"Estado inválido. Opciones: {', '.join(estados_validos)}"
            )
        return value

    def validate_resultado_json(self, value):
        """Validar formato de resultado JSON"""
        if value:
            return validar_formato_datos_json(value)
        return value

    def get_duracion_segundos(self, obj):
        """Calcular duración de ejecución en segundos"""
        if obj.fecha_ejecucion and obj.fecha_finalizacion:
            duracion = obj.fecha_finalizacion - obj.fecha_ejecucion
            return int(duracion.total_seconds())
        return None

    def get_resultado_resumen(self, obj):
        """Crear resumen del resultado para UI"""
        if not obj.resultado_json:
            return None
        
        try:
            resultado = obj.resultado_json
            if isinstance(resultado, dict):
                return {
                    'registros_procesados': resultado.get('registros_procesados', 0),
                    'errores': len(resultado.get('errores', [])),
                    'warnings': len(resultado.get('warnings', [])),
                    'tiempo_ejecucion': resultado.get('tiempo_ejecucion')
                }
        except:
            pass
        
        return None


class DestinatariosTareaSerializer(serializers.ModelSerializer):
    """Serializer para destinatarios de tareas"""
    
    empleado_info = EmpleadoBasicoSerializer(source='id_empleado', read_only=True)
    plantilla_nombre = serializers.CharField(
        source='id_plantilla_tarea.nombre_tarea',
        read_only=True
    )

    class Meta:
        model = DestinatariosTarea
        fields = [
            'id_destinatario',
            'id_plantilla_tarea',
            'id_empleado',
            'tipo_notificacion',
            'activo',
            'empleado_info',
            'plantilla_nombre'
        ]
        read_only_fields = ['id_destinatario']

    def validate_tipo_notificacion(self, value):
        """Validar tipo de notificación"""
        tipos_validos = ['email', 'sistema', 'sms', 'push']
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo de notificación inválido. Opciones: {', '.join(tipos_validos)}"
            )
        return value

    def validate(self, data):
        """Validación cruzada para evitar duplicados"""
        # Evitar destinatarios duplicados
        query = DestinatariosTarea.objects.filter(
            id_plantilla_tarea=data['id_plantilla_tarea'],
            id_empleado=data['id_empleado'],
            tipo_notificacion=data['tipo_notificacion'],
            activo=True
        )
        
        if self.instance:
            query = query.exclude(id_destinatario=self.instance.id_destinatario)
        
        if query.exists():
            raise serializers.ValidationError(
                "Este empleado ya está configurado como destinatario para este tipo de notificación"
            )
        
        return data


# Serializers especializados para reports específicos

class ReporteVentasRequestSerializer(serializers.Serializer):
    """Serializer para parámetros de reporte de ventas"""
    
    fecha_inicio = serializers.DateField(
        help_text="Fecha de inicio del período (formato: YYYY-MM-DD)"
    )
    fecha_fin = serializers.DateField(
        help_text="Fecha de fin del período (formato: YYYY-MM-DD)"
    )
    id_empleado = serializers.IntegerField(
        required=False,
        help_text="ID del empleado para filtrar (opcional)"
    )
    metodo_pago = serializers.ChoiceField(
        choices=[('efectivo', 'Efectivo'), ('tarjeta', 'Tarjeta'), ('online', 'Online')],
        required=False,
        help_text="Método de pago para filtrar (opcional)"
    )
    incluir_detalles = serializers.BooleanField(
        default=True,
        help_text="Incluir detalles de productos vendidos"
    )
    limite_productos = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=100,
        help_text="Límite de productos en top productos"
    )

    def validate(self, data):
        """Validación cruzada de fechas"""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise serializers.ValidationError(
                    "La fecha de inicio no puede ser posterior a la fecha de fin"
                )
            
            # Validar rango máximo
            diferencia = (fecha_fin - fecha_inicio).days
            if diferencia > 365:
                raise serializers.ValidationError(
                    "El rango de fechas no puede exceder 365 días"
                )
        
        return data


class ReporteFinancieroRequestSerializer(serializers.Serializer):
    """Serializer para parámetros de reporte financiero"""
    
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    incluir_graficos = serializers.BooleanField(default=True)
    desglosar_por = serializers.ChoiceField(
        choices=[('dia', 'Día'), ('semana', 'Semana'), ('mes', 'Mes')],
        default='dia'
    )
    moneda = serializers.ChoiceField(
        choices=[('COP', 'Pesos Colombianos'), ('USD', 'Dólares')],
        default='COP'
    )

    def validate(self, data):
        """Validación de parámetros financieros"""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise serializers.ValidationError({
                    'fecha_fin': "Debe ser posterior a la fecha de inicio"
                })
        
        return data


class DashboardRequestSerializer(serializers.Serializer):
    """Serializer para parámetros de dashboard"""
    
    tipo_dashboard = serializers.ChoiceField(
        choices=[
            ('ventas', 'Dashboard de Ventas'),
            ('financiero', 'Dashboard Financiero'),
            ('inventario', 'Dashboard de Inventario'),
            ('clientes', 'Dashboard de Clientes')
        ]
    )
    periodo_dias = serializers.IntegerField(
        default=7,
        min_value=1,
        max_value=365,
        help_text="Período en días para el dashboard"
    )
    incluir_comparacion = serializers.BooleanField(
        default=True,
        help_text="Incluir comparación con período anterior"
    )
    widgets_activos = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="Lista de widgets a incluir en el dashboard"
    )

    def validate_widgets_activos(self, value):
        """Validar widgets disponibles"""
        if value:
            widgets_validos = [
                'ventas_totales', 'clientes_activos', 'productos_top',
                'ingresos_mes', 'tickets_promedio', 'inventario_bajo'
            ]
            
            for widget in value:
                if widget not in widgets_validos:
                    raise serializers.ValidationError(
                        f"Widget '{widget}' no es válido. Opciones: {', '.join(widgets_validos)}"
                    )
        
        return value
