"""
Validadores para el módulo de Reportes
Cantina Tita - Sistema de Gestión

Este módulo contiene validadores para todos los modelos del sistema de reportes,
incluyendo plantillas de reportes, dashboards, KPIs, tareas programadas y sus ejecuciones.
"""

import json
import re
from decimal import Decimal

from django.core.exceptions import ValidationError

# =============================================================================
# VALIDADORES - PLANTILLAS DE REPORTE
# =============================================================================


def validar_nombre_plantilla_reporte(value):
    """
    Valida el nombre de una plantilla de reporte.

    Reglas:
    - Mínimo 3 caracteres
    - Máximo 100 caracteres
    """
    if not value or len(value.strip()) < 3:
        raise ValidationError("El nombre de la plantilla debe tener al menos 3 caracteres.")

    if len(value) > 100:
        raise ValidationError("El nombre de la plantilla no puede exceder 100 caracteres.")


def validar_query_sql(value):
    """
    Valida una query SQL para reportes.

    Reglas:
    - Mínimo 10 caracteres
    - Máximo 10,000 caracteres
    - Debe contener SELECT (case-insensitive)
    """
    if not value or len(value.strip()) < 10:
        raise ValidationError("La query SQL debe tener al menos 10 caracteres.")

    if len(value) > 10000:
        raise ValidationError("La query SQL no puede exceder 10,000 caracteres.")

    # Verificar que contiene SELECT
    if "SELECT" not in value.upper():
        raise ValidationError("La query SQL debe contener una sentencia SELECT.")


def validar_parametros_reporte(value):
    """
    Valida los parámetros JSON de un reporte.

    Reglas:
    - Debe ser un dict válido
    - Máximo 20 parámetros
    - Cada clave debe tener entre 2 y 50 caracteres
    """
    if value is None:
        return

    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("Los parámetros deben ser un JSON válido.")

    if not isinstance(value, dict):
        raise ValidationError("Los parámetros deben ser un diccionario.")

    if len(value) > 20:
        raise ValidationError("No se permiten más de 20 parámetros.")

    for clave in value.keys():
        if not isinstance(clave, str):
            raise ValidationError("Cada clave de parámetro debe ser un string.")
        if len(clave) < 2 or len(clave) > 50:
            raise ValidationError("Cada clave de parámetro debe tener entre 2 y 50 caracteres.")


def validar_tipo_reporte(value):
    """
    Valida el tipo de reporte.

    Tipos válidos: Ventas, Inventario, Compras, Financiero, Cliente, Empleado, Personalizado
    """
    TIPOS_VALIDOS = [
        "Ventas",
        "Inventario",
        "Compras",
        "Financiero",
        "Cliente",
        "Empleado",
        "Personalizado",
    ]

    if value not in TIPOS_VALIDOS:
        raise ValidationError(f'Tipo de reporte inválido. Debe ser uno de: {", ".join(TIPOS_VALIDOS)}')


def validar_frecuencia_reporte(value):
    """
    Valida la frecuencia de un reporte.

    Frecuencias válidas: Diario, Semanal, Mensual, Trimestral, Anual, Manual
    """
    FRECUENCIAS_VALIDAS = ["Diario", "Semanal", "Mensual", "Trimestral", "Anual", "Manual"]

    if value not in FRECUENCIAS_VALIDAS:
        raise ValidationError(f'Frecuencia inválida. Debe ser una de: {", ".join(FRECUENCIAS_VALIDAS)}')


# =============================================================================
# VALIDADORES - DASHBOARDS
# =============================================================================


def validar_nombre_dashboard(value):
    """
    Valida el nombre de un dashboard.

    Reglas:
    - Mínimo 3 caracteres
    - Máximo 100 caracteres
    """
    if not value or len(value.strip()) < 3:
        raise ValidationError("El nombre del dashboard debe tener al menos 3 caracteres.")

    if len(value) > 100:
        raise ValidationError("El nombre del dashboard no puede exceder 100 caracteres.")


def validar_configuracion_dashboard(value):
    """
    Valida la configuración JSON de un dashboard.

    Reglas:
    - Debe ser un dict válido
    - Debe contener 'widgets' (lista)
    - Máximo 20 widgets
    """
    if value is None:
        raise ValidationError("La configuración del dashboard es requerida.")

    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("La configuración debe ser un JSON válido.")

    if not isinstance(value, dict):
        raise ValidationError("La configuración debe ser un diccionario.")

    # Verificar que tiene widgets
    if "widgets" not in value:
        raise ValidationError("La configuración debe contener una lista de widgets.")

    if not isinstance(value["widgets"], list):
        raise ValidationError("Los widgets deben ser una lista.")

    if len(value["widgets"]) > 20:
        raise ValidationError("No se permiten más de 20 widgets por dashboard.")


def validar_es_publico_dashboard(value):
    """
    Valida el campo es_publico de un dashboard.

    Reglas:
    - Debe ser 0 (privado) o 1 (público)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo es_publico debe ser 0 (privado) o 1 (público).")


def validar_predeterminado_dashboard(value):
    """
    Valida el campo predeterminado de un dashboard.

    Reglas:
    - Debe ser 0 (no) o 1 (sí)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo predeterminado debe ser 0 (no) o 1 (sí).")


# =============================================================================
# VALIDADORES - KPI MÉTRICAS
# =============================================================================


def validar_nombre_kpi(value):
    """
    Valida el nombre de un KPI.

    Reglas:
    - Mínimo 3 caracteres
    - Máximo 100 caracteres
    """
    if not value or len(value.strip()) < 3:
        raise ValidationError("El nombre del KPI debe tener al menos 3 caracteres.")

    if len(value) > 100:
        raise ValidationError("El nombre del KPI no puede exceder 100 caracteres.")


def validar_descripcion_kpi(value):
    """
    Valida la descripción de un KPI.

    Reglas:
    - Mínimo 10 caracteres
    - Máximo 1,000 caracteres
    """
    if not value or len(value.strip()) < 10:
        raise ValidationError("La descripción del KPI debe tener al menos 10 caracteres.")

    if len(value) > 1000:
        raise ValidationError("La descripción del KPI no puede exceder 1,000 caracteres.")


def validar_formula_kpi(value):
    """
    Valida la fórmula de un KPI.

    Reglas:
    - Mínimo 5 caracteres
    - Máximo 500 caracteres
    """
    if not value or len(value.strip()) < 5:
        raise ValidationError("La fórmula del KPI debe tener al menos 5 caracteres.")

    if len(value) > 500:
        raise ValidationError("La fórmula del KPI no puede exceder 500 caracteres.")


def validar_unidad_kpi(value):
    """
    Valida la unidad de medida de un KPI.

    Unidades válidas: %, ₲, USD, unidades, días, horas, ratio, puntos
    """
    UNIDADES_VALIDAS = ["%", "₲", "USD", "unidades", "días", "horas", "ratio", "puntos"]

    if value not in UNIDADES_VALIDAS:
        raise ValidationError(f'Unidad inválida. Debe ser una de: {", ".join(UNIDADES_VALIDAS)}')


def validar_valor_objetivo_kpi(value):
    """
    Valida el valor objetivo de un KPI.

    Reglas:
    - Puede ser None (opcional)
    - Si existe: entre -999,999,999.99 y 999,999,999.99
    - Máximo 2 decimales
    """
    if value is None:
        return

    if value < Decimal("-999999999.99"):
        raise ValidationError("El valor objetivo no puede ser menor a -999,999,999.99")

    if value > Decimal("999999999.99"):
        raise ValidationError("El valor objetivo no puede exceder 999,999,999.99")

    # Verificar decimales
    if value.as_tuple().exponent < -2:
        raise ValidationError("El valor objetivo solo puede tener 2 decimales.")


def validar_categoria_kpi(value):
    """
    Valida la categoría de un KPI.

    Categorías válidas: Ventas, Inventario, Compras, Financiero, Cliente, Empleado, Operacional
    """
    CATEGORIAS_VALIDAS = [
        "Ventas",
        "Inventario",
        "Compras",
        "Financiero",
        "Cliente",
        "Empleado",
        "Operacional",
    ]

    if value not in CATEGORIAS_VALIDAS:
        raise ValidationError(f'Categoría inválida. Debe ser una de: {", ".join(CATEGORIAS_VALIDAS)}')


def validar_frecuencia_kpi(value):
    """
    Valida la frecuencia de cálculo de un KPI.

    Frecuencias válidas: Diario, Semanal, Mensual, Trimestral, Anual
    """
    FRECUENCIAS_VALIDAS = ["Diario", "Semanal", "Mensual", "Trimestral", "Anual"]

    if value not in FRECUENCIAS_VALIDAS:
        raise ValidationError(f'Frecuencia inválida. Debe ser una de: {", ".join(FRECUENCIAS_VALIDAS)}')


# =============================================================================
# VALIDADORES - VALORES KPI
# =============================================================================


def validar_valor_kpi(value):
    """
    Valida el valor de un KPI registrado.

    Reglas:
    - Entre -999,999,999.99 y 999,999,999.99
    - Máximo 2 decimales
    """
    if value < Decimal("-999999999.99"):
        raise ValidationError("El valor del KPI no puede ser menor a -999,999,999.99")

    if value > Decimal("999999999.99"):
        raise ValidationError("El valor del KPI no puede exceder 999,999,999.99")

    # Verificar decimales
    if value.as_tuple().exponent < -2:
        raise ValidationError("El valor del KPI solo puede tener 2 decimales.")


def validar_auto_calc_valores_kpi(value):
    """
    Valida el campo auto_calc de valores KPI.

    Reglas:
    - Debe ser 0 (manual) o 1 (automático)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo auto_calc debe ser 0 (manual) o 1 (automático).")


# =============================================================================
# VALIDADORES - PLANTILLAS DE TAREA
# =============================================================================


def validar_nombre_plantilla_tarea(value):
    """
    Valida el nombre de una plantilla de tarea.

    Reglas:
    - Mínimo 3 caracteres
    - Máximo 100 caracteres
    """
    if not value or len(value.strip()) < 3:
        raise ValidationError("El nombre de la plantilla de tarea debe tener al menos 3 caracteres.")

    if len(value) > 100:
        raise ValidationError("El nombre de la plantilla de tarea no puede exceder 100 caracteres.")


def validar_descripcion_tarea(value):
    """
    Valida la descripción de una tarea.

    Reglas:
    - Mínimo 10 caracteres
    - Máximo 1,000 caracteres
    """
    if not value or len(value.strip()) < 10:
        raise ValidationError("La descripción de la tarea debe tener al menos 10 caracteres.")

    if len(value) > 1000:
        raise ValidationError("La descripción de la tarea no puede exceder 1,000 caracteres.")


def validar_tipo_tarea(value):
    """
    Valida el tipo de tarea.

    Tipos válidos: Reporte, Backup, Limpieza, Sincronización, Cálculo, Notificación, Personalizado
    """
    TIPOS_VALIDOS = [
        "Reporte",
        "Backup",
        "Limpieza",
        "Sincronización",
        "Cálculo",
        "Notificación",
        "Personalizado",
    ]

    if value not in TIPOS_VALIDOS:
        raise ValidationError(f'Tipo de tarea inválido. Debe ser uno de: {", ".join(TIPOS_VALIDOS)}')


def validar_comando_tarea(value):
    """
    Valida el comando de una tarea.

    Reglas:
    - Mínimo 5 caracteres
    - Máximo 500 caracteres
    """
    if not value or len(value.strip()) < 5:
        raise ValidationError("El comando debe tener al menos 5 caracteres.")

    if len(value) > 500:
        raise ValidationError("El comando no puede exceder 500 caracteres.")


def validar_parametros_tarea(value):
    """
    Valida los parámetros JSON de una tarea.

    Reglas:
    - Debe ser un dict válido
    - Máximo 20 parámetros
    """
    if value is None:
        return

    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("Los parámetros deben ser un JSON válido.")

    if not isinstance(value, dict):
        raise ValidationError("Los parámetros deben ser un diccionario.")

    if len(value) > 20:
        raise ValidationError("No se permiten más de 20 parámetros.")


def validar_frecuencia_tarea(value):
    """
    Valida la frecuencia de ejecución de una tarea.

    Frecuencias válidas: Cada hora, Diario, Semanal, Mensual, Personalizado
    """
    FRECUENCIAS_VALIDAS = ["Cada hora", "Diario", "Semanal", "Mensual", "Personalizado"]

    if value not in FRECUENCIAS_VALIDAS:
        raise ValidationError(f'Frecuencia inválida. Debe ser una de: {", ".join(FRECUENCIAS_VALIDAS)}')


def validar_cron_expresion(value):
    """
    Valida una expresión cron.

    Reglas:
    - Formato: 5 campos separados por espacios
    - Ejemplo: "0 2 * * *" (diario a las 2 AM)
    """
    if not value or len(value.strip()) < 9:
        raise ValidationError("La expresión cron debe tener al menos 9 caracteres.")

    if len(value) > 100:
        raise ValidationError("La expresión cron no puede exceder 100 caracteres.")

    # Validar formato básico (5 campos)
    partes = value.split()
    if len(partes) != 5:
        raise ValidationError("La expresión cron debe tener exactamente 5 campos separados por espacios.")


def validar_timeout_tarea(value):
    """
    Valida el timeout de una tarea (en segundos).

    Reglas:
    - Mínimo 10 segundos
    - Máximo 86400 segundos (24 horas)
    """
    if value < 10:
        raise ValidationError("El timeout debe ser de al menos 10 segundos.")

    if value > 86400:
        raise ValidationError("El timeout no puede exceder 86,400 segundos (24 horas).")


def validar_max_reintentos_tarea(value):
    """
    Valida el máximo de reintentos de una tarea.

    Reglas:
    - Entre 0 y 10 reintentos
    """
    if value < 0:
        raise ValidationError("El máximo de reintentos no puede ser negativo.")

    if value > 10:
        raise ValidationError("El máximo de reintentos no puede exceder 10.")


def validar_notif_exito_tarea(value):
    """
    Valida el campo notif_exito de una tarea.

    Reglas:
    - Debe ser 0 (no notificar) o 1 (notificar)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo notif_exito debe ser 0 (no) o 1 (sí).")


def validar_notif_error_tarea(value):
    """
    Valida el campo notif_error de una tarea.

    Reglas:
    - Debe ser 0 (no notificar) o 1 (notificar)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo notif_error debe ser 0 (no) o 1 (sí).")


# =============================================================================
# VALIDADORES - EJECUCIONES DE TAREA
# =============================================================================


def validar_duracion_seg_ejecucion(value):
    """
    Valida la duración en segundos de una ejecución.

    Reglas:
    - Puede ser None (en ejecución)
    - Si existe: entre 0 y 86400 segundos (24 horas)
    """
    if value is None:
        return

    if value < 0:
        raise ValidationError("La duración no puede ser negativa.")

    if value > 86400:
        raise ValidationError("La duración no puede exceder 86,400 segundos (24 horas).")


def validar_estado_ejecucion(value):
    """
    Valida el estado de una ejecución.

    Estados válidos: Pendiente, Ejecutando, Exitoso, Fallido, Cancelado, Timeout
    """
    ESTADOS_VALIDOS = ["Pendiente", "Ejecutando", "Exitoso", "Fallido", "Cancelado", "Timeout"]

    if value not in ESTADOS_VALIDOS:
        raise ValidationError(f'Estado inválido. Debe ser uno de: {", ".join(ESTADOS_VALIDOS)}')


def validar_pid_ejecucion(value):
    """
    Valida el PID (Process ID) de una ejecución.

    Reglas:
    - Puede ser None (no iniciado)
    - Si existe: entre 1 y 2,147,483,647
    """
    if value is None:
        return

    if value < 1:
        raise ValidationError("El PID debe ser mayor a 0.")

    if value > 2147483647:
        raise ValidationError("El PID excede el máximo permitido.")


def validar_servidor_ejecucion(value):
    """
    Valida el nombre del servidor de ejecución.

    Reglas:
    - Mínimo 2 caracteres
    - Máximo 100 caracteres
    """
    if not value or len(value.strip()) < 2:
        raise ValidationError("El nombre del servidor debe tener al menos 2 caracteres.")

    if len(value) > 100:
        raise ValidationError("El nombre del servidor no puede exceder 100 caracteres.")


# =============================================================================
# VALIDADORES - DESTINATARIOS DE TAREA
# =============================================================================


def validar_notif_inicio_destinatario(value):
    """
    Valida el campo notif_inicio de un destinatario.

    Reglas:
    - Debe ser 0 (no notificar) o 1 (notificar)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo notif_inicio debe ser 0 (no) o 1 (sí).")


def validar_notif_fin_destinatario(value):
    """
    Valida el campo notif_fin de un destinatario.

    Reglas:
    - Debe ser 0 (no notificar) o 1 (notificar)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo notif_fin debe ser 0 (no) o 1 (sí).")


def validar_notif_error_destinatario(value):
    """
    Valida el campo notif_error de un destinatario.

    Reglas:
    - Debe ser 0 (no notificar) o 1 (notificar)
    """
    if value not in [0, 1]:
        raise ValidationError("El campo notif_error debe ser 0 (no) o 1 (sí).")


def validar_configuracion_json(value):
    """Valida que el valor sea un dict JSON válido."""
    if value is None:
        return
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("La configuración debe ser un JSON válido.")
    if not isinstance(value, dict):
        raise ValidationError("La configuración debe ser un objeto JSON (dict).")
    return value


def validar_frecuencia_ejecucion(value):
    """Valida la frecuencia de ejecución de tareas programadas."""
    FRECUENCIAS_VALIDAS = ["manual", "diaria", "semanal", "mensual", "personalizado"]
    if value and value.lower() not in FRECUENCIAS_VALIDAS:
        raise ValidationError(f'Frecuencia inválida. Debe ser una de: {", ".join(FRECUENCIAS_VALIDAS)}')
    return value


def validar_formato_datos_json(value):
    """Valida que el valor tenga un formato de datos JSON correcto."""
    if value is None:
        return
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("El formato de datos debe ser JSON válido.")
    if not isinstance(value, (dict, list)):
        raise ValidationError("El formato de datos debe ser un objeto o lista JSON.")
    return value
