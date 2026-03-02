"""
Validadores del módulo de Contabilidad
Sistema completo de validación para facturación electrónica, cajas, comisiones y tributación
"""
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re


# =============================================================================
# 1. VALIDADORES DE CAJAS (3 validadores)
# =============================================================================

def validar_nombre_caja(value):
    """Valida nombre de caja (3-50 caracteres)"""
    if not value or len(value.strip()) < 3:
        raise ValidationError('El nombre de la caja debe tener al menos 3 caracteres.')
    if len(value) > 50:
        raise ValidationError('El nombre de la caja no puede exceder 50 caracteres.')
    
    # Caracteres permitidos: letras, números, espacios, guiones
    if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-]+$', value):
        raise ValidationError('El nombre de la caja solo puede contener letras, números, espacios y guiones.')

def validar_ubicacion_caja(value):
    """Valida ubicación de caja (opcional, max 100)"""
    if value is None or value == '':
        return
    if len(value.strip()) < 3:
        raise ValidationError('La ubicación debe tener al menos 3 caracteres.')
    if len(value) > 100:
        raise ValidationError('La ubicación no puede exceder 100 caracteres.')

def validar_activo_caja(value):
    """Valida campo activo de caja (boolean)"""
    if not isinstance(value, bool):
        raise ValidationError('El campo activo debe ser True o False.')


# =============================================================================
# 2. VALIDADORES DE CIERRES DE CAJA (7 validadores)
# =============================================================================

def validar_fecha_apertura_cierre(apertura, cierre):
    """Valida que fecha de cierre sea posterior a apertura"""
    if cierre is None:
        return  # Cierre puede ser null (caja aún abierta)
    
    if not isinstance(apertura, datetime):
        raise ValidationError('La fecha de apertura debe ser un datetime válido.')
    if not isinstance(cierre, datetime):
        raise ValidationError('La fecha de cierre debe ser un datetime válido.')
    
    if cierre <= apertura:
        raise ValidationError('La fecha de cierre debe ser posterior a la apertura.')
    
    # Validar que no sea más de 48 horas (cierres muy largos)
    diferencia_horas = (cierre - apertura).total_seconds() / 3600
    if diferencia_horas > 48:
        raise ValidationError('El cierre no puede ser mayor a 48 horas después de la apertura.')

def validar_monto_inicial_caja(value):
    """Valida monto inicial de caja (>= 0)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto inicial debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El monto inicial no puede ser negativo.')
    if valor_decimal > Decimal('999999999.99'):
        raise ValidationError('El monto inicial no puede exceder 999,999,999.99')
    
    # Verificar 2 decimales
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto inicial solo puede tener 2 decimales.')

def validar_monto_contado_fisico(value):
    """Valida monto contado físico (>= 0)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto contado debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El monto contado no puede ser negativo.')
    if valor_decimal > Decimal('999999999.99'):
        raise ValidationError('El monto contado no puede exceder 999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto contado solo puede tener 2 decimales.')

def validar_diferencia_efectivo(value):
    """Valida diferencia de efectivo (puede ser negativo)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('La diferencia debe ser un número válido.')
    
    if abs(valor_decimal) > Decimal('999999999.99'):
        raise ValidationError('La diferencia no puede exceder ±999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('La diferencia solo puede tener 2 decimales.')

def validar_estado_cierre_caja(value):
    """Valida estado de cierre (Abierto/Cerrado)"""
    if not value:
        return  # Puede ser null en creación
    
    estados_validos = ['Abierto', 'Cerrado']
    if value not in estados_validos:
        raise ValidationError(f'El estado debe ser: {", ".join(estados_validos)}')

def validar_consistencia_cierre(monto_inicial, monto_contado, diferencia):
    """Valida que la diferencia sea consistente (contado - inicial = dif)"""
    if monto_inicial is None or monto_contado is None:
        return  # No validar si faltan datos
    
    diferencia_calculada = Decimal(str(monto_contado)) - Decimal(str(monto_inicial))
    
    if diferencia is not None:
        diferencia_decimal = Decimal(str(diferencia))
        # Permitir diferencia de centavos por redondeo
        if abs(diferencia_decimal - diferencia_calculada) > Decimal('0.01'):
            raise ValidationError(f'La diferencia registrada ({diferencia}) no coincide con la calculada ({diferencia_calculada})')


# =============================================================================
# 3. VALIDADORES DE MOVIMIENTOS DE CAJA (5 validadores)
# =============================================================================

def validar_tipo_movimiento_caja(value):
    """Valida tipo de movimiento (Ingreso/Egreso/Transferencia/Apertura/Cierre)"""
    if not value:
        raise ValidationError('El tipo de movimiento es requerido.')
    
    if len(value) > 20:
        raise ValidationError('El tipo de movimiento no puede exceder 20 caracteres.')
    
    tipos_validos = ['Ingreso', 'Egreso', 'Transferencia', 'Apertura', 'Cierre']
    if value not in tipos_validos:
        raise ValidationError(f'El tipo de movimiento debe ser: {", ".join(tipos_validos)}')

def validar_monto_movimiento_caja(value):
    """Valida monto de movimiento (> 0)"""
    if value is None:
        raise ValidationError('El monto es requerido.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto debe ser un número válido.')
    
    if valor_decimal <= Decimal('0'):
        raise ValidationError('El monto debe ser mayor a 0.')
    if valor_decimal > Decimal('999999999999.99'):
        raise ValidationError('El monto no puede exceder 999,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto solo puede tener 2 decimales.')

def validar_monto_comision_movimiento(value):
    """Valida monto de comisión (>= 0)"""
    if value is None:
        raise ValidationError('El monto de comisión es requerido.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto de comisión debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El monto de comisión no puede ser negativo.')
    if valor_decimal > Decimal('999999999999.99'):
        raise ValidationError('El monto de comisión no puede exceder 999,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto de comisión solo puede tener 2 decimales.')

def validar_fecha_movimiento_caja(value):
    """Valida fecha de movimiento (no puede ser futura)"""
    if value is None:
        raise ValidationError('La fecha de movimiento es requerida.')
    
    if not isinstance(value, (datetime, date)):
        raise ValidationError('La fecha de movimiento debe ser un datetime válido.')
    
    # Convertir a datetime si es date
    if isinstance(value, date) and not isinstance(value, datetime):
        value_dt = datetime.combine(value, datetime.min.time())
    else:
        value_dt = value
    
    # No puede ser más de 1 hora en el futuro (tolerancia por diferencias de servidor)
    from datetime import timedelta
    ahora = datetime.now()
    if value_dt > ahora + timedelta(hours=1):
        raise ValidationError('La fecha de movimiento no puede ser futura.')

def validar_descripcion_movimiento(value):
    """Valida descripción de movimiento (opcional, max 200)"""
    if value is None or value == '':
        return
    
    if len(value) > 200:
        raise ValidationError('La descripción no puede exceder 200 caracteres.')


# =============================================================================
# 4. VALIDADORES DE TARIFAS DE COMISIÓN (5 validadores)
# =============================================================================

def validar_fecha_vigencia_tarifa(fecha_inicio, fecha_fin):
    """Valida que fecha fin sea posterior a fecha inicio"""
    if fecha_fin is None:
        return  # Vigencia indefinida
    
    if not isinstance(fecha_inicio, datetime):
        raise ValidationError('La fecha de inicio debe ser un datetime válido.')
    if not isinstance(fecha_fin, datetime):
        raise ValidationError('La fecha de fin debe ser un datetime válido.')
    
    if fecha_fin <= fecha_inicio:
        raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

def validar_porcentaje_comision(value):
    """Valida porcentaje de comisión (0.0000-1.0000 = 0%-100%)"""
    if value is None:
        raise ValidationError('El porcentaje de comisión es requerido.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El porcentaje debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El porcentaje no puede ser negativo.')
    if valor_decimal > Decimal('1.0000'):
        raise ValidationError('El porcentaje no puede exceder 1.0000 (100%)')
    
    # Verificar 4 decimales
    if valor_decimal.as_tuple().exponent < -4:
        raise ValidationError('El porcentaje solo puede tener 4 decimales.')

def validar_monto_fijo_comision(value):
    """Valida monto fijo de comisión (opcional, >= 0)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto fijo debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El monto fijo no puede ser negativo.')
    if valor_decimal > Decimal('9999999999.99'):
        raise ValidationError('El monto fijo no puede exceder 9,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto fijo solo puede tener 2 decimales.')

def validar_activo_tarifa(value):
    """Valida campo activo de tarifa (boolean)"""
    if not isinstance(value, bool):
        raise ValidationError('El campo activo debe ser True o False.')


# =============================================================================
# 5. VALIDADORES DE AUDITORÍA DE COMISIONES (4 validadores)
# =============================================================================

def validar_fecha_cambio_auditoria(value):
    """Valida fecha de cambio de auditoría"""
    if value is None:
        raise ValidationError('La fecha de cambio es requerida.')
    
    if not isinstance(value, datetime):
        raise ValidationError('La fecha de cambio debe ser un datetime válido.')
    
    # No puede ser futura
    if value > datetime.now():
        raise ValidationError('La fecha de cambio no puede ser futura.')

def validar_campo_modificado_auditoria(value):
    """Valida nombre del campo modificado (max 50)"""
    if not value or len(value.strip()) < 2:
        raise ValidationError('El campo modificado debe tener al menos 2 caracteres.')
    if len(value) > 50:
        raise ValidationError('El campo modificado no puede exceder 50 caracteres.')

def validar_valor_anterior_auditoria(value):
    """Valida valor anterior en auditoría (opcional, decimal 10,4)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El valor anterior debe ser un número válido.')
    
    if abs(valor_decimal) > Decimal('999999.9999'):
        raise ValidationError('El valor anterior no puede exceder ±999,999.9999')
    
    if valor_decimal.as_tuple().exponent < -4:
        raise ValidationError('El valor anterior solo puede tener 4 decimales.')

def validar_valor_nuevo_auditoria(value):
    """Valida valor nuevo en auditoría (opcional, decimal 10,4)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El valor nuevo debe ser un número válido.')
    
    if abs(valor_decimal) > Decimal('999999.9999'):
        raise ValidationError('El valor nuevo no puede exceder ±999,999.9999')
    
    if valor_decimal.as_tuple().exponent < -4:
        raise ValidationError('El valor nuevo solo puede tener 4 decimales.')


# =============================================================================
# 6. VALIDADORES DE CONCILIACIÓN DE PAGOS (6 validadores)
# =============================================================================

def validar_fecha_acreditacion_conciliacion(value):
    """Valida fecha de acreditación (opcional)"""
    if value is None:
        return
    
    if not isinstance(value, datetime):
        raise ValidationError('La fecha de acreditación debe ser un datetime válido.')

def validar_fecha_conciliacion(value):
    """Valida fecha de conciliación"""
    if value is None:
        raise ValidationError('La fecha de conciliación es requerida.')
    
    if not isinstance(value, datetime):
        raise ValidationError('La fecha de conciliación debe ser un datetime válido.')

def validar_estado_conciliacion(value):
    """Valida estado de conciliación"""
    if not value:
        raise ValidationError('El estado es requerido.')
    
    if len(value) > 20:
        raise ValidationError('El estado no puede exceder 20 caracteres.')
    
    estados_validos = ['Pendiente', 'Conciliado', 'Rechazado', 'En Proceso']
    if value not in estados_validos:
        raise ValidationError(f'El estado debe ser: {", ".join(estados_validos)}')

def validar_monto_acreditado_conciliacion(value):
    """Valida monto acreditado (opcional, >= 0)"""
    if value is None:
        return
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto acreditado debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El monto acreditado no puede ser negativo.')
    if valor_decimal > Decimal('999999999999.99'):
        raise ValidationError('El monto acreditado no puede exceder 999,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto acreditado solo puede tener 2 decimales.')

def validar_observaciones_conciliacion(value):
    """Valida observaciones de conciliación (opcional, text)"""
    if value is None or value == '':
        return
    
    if len(value) > 1000:
        raise ValidationError('Las observaciones no pueden exceder 1000 caracteres.')

def validar_fechas_conciliacion_consistencia(fecha_creacion, fecha_actualizacion):
    """Valida que fecha de actualización sea >= creación"""
    if fecha_creacion is None or fecha_actualizacion is None:
        return
    
    if not isinstance(fecha_creacion, datetime):
        raise ValidationError('La fecha de creación debe ser un datetime válido.')
    if not isinstance(fecha_actualizacion, datetime):
        raise ValidationError('La fecha de actualización debe ser un datetime válido.')
    
    if fecha_actualizacion < fecha_creacion:
        raise ValidationError('La fecha de actualización no puede ser anterior a la creación.')


# =============================================================================
# 7. VALIDADORES DE DOCUMENTOS TRIBUTARIOS (9 validadores)
# =============================================================================

def validar_nro_secuencial_documento(value):
    """Valida número secuencial de documento (> 0, max 999999999)"""
    if value is None:
        raise ValidationError('El número secuencial es requerido.')
    
    if not isinstance(value, int):
        raise ValidationError('El número secuencial debe ser un entero.')
    
    if value < 1:
        raise ValidationError('El número secuencial debe ser mayor a 0.')
    if value > 999999999:
        raise ValidationError('El número secuencial no puede exceder 999,999,999')

def validar_fecha_emision_documento(value):
    """Valida fecha de emisión de documento"""
    if value is None:
        raise ValidationError('La fecha de emisión es requerida.')
    
    if not isinstance(value, datetime):
        raise ValidationError('La fecha de emisión debe ser un datetime válido.')
    
    # No puede ser más de 24 horas en el futuro
    from datetime import timedelta
    if value > datetime.now() + timedelta(hours=24):
        raise ValidationError('La fecha de emisión no puede ser más de 24 horas en el futuro.')

def validar_monto_total_documento(value):
    """Valida monto total del documento (> 0)"""
    if value is None:
        raise ValidationError('El monto total es requerido.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto total debe ser un número válido.')
    
    if valor_decimal <= Decimal('0'):
        raise ValidationError('El monto total debe ser mayor a 0.')
    if valor_decimal > Decimal('999999999999.99'):
        raise ValidationError('El monto total no puede exceder 999,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto total solo puede tener 2 decimales.')

def validar_tipo_documento_tributario(value):
    """Valida tipo de documento tributario"""
    if not value:
        raise ValidationError('El tipo de documento es requerido.')
    
    if len(value) > 11:
        raise ValidationError('El tipo de documento no puede exceder 11 caracteres.')
    
    tipos_validos = ['Factura', 'NotaCredito', 'NotaDebito', 'Recibo']
    if value not in tipos_validos:
        raise ValidationError(f'El tipo de documento debe ser: {", ".join(tipos_validos)}')

def validar_cdc_documento(value):
    """Valida CDC (Código de Control) - exactamente 44 caracteres alfanuméricos"""
    if value is None or value == '':
        return  # CDC es opcional
    
    if len(value) != 44:
        raise ValidationError('El CDC debe tener exactamente 44 caracteres.')
    
    # CDC es alfanumérico
    if not re.match(r'^[A-Za-z0-9]+$', value):
        raise ValidationError('El CDC solo puede contener caracteres alfanuméricos.')

def validar_url_kude_documento(value):
    """Valida URL del KUDE (Kuati Documentos Electrónicos)"""
    if value is None or value == '':
        return  # URL es opcional
    
    if len(value) > 255:
        raise ValidationError('La URL del KUDE no puede exceder 255 caracteres.')
    
    # Validar formato URL
    validator = URLValidator()
    try:
        validator(value)
    except ValidationError:
        raise ValidationError('La URL del KUDE no tiene un formato válido.')

def validar_estado_sifen_documento(value):
    """Valida estado SIFEN (Sistema Integrado de Facturación Electrónica Nacional)"""
    if value is None or value == '':
        return  # Estado es opcional
    
    if len(value) > 9:
        raise ValidationError('El estado SIFEN no puede exceder 9 caracteres.')
    
    estados_validos = ['Aprobado', 'Rechazado', 'Pendiente']
    if value not in estados_validos:
        raise ValidationError(f'El estado SIFEN debe ser: {", ".join(estados_validos)}')

def validar_nro_preimpreso_documento(value):
    """Valida número preimpreso interno (formato XXX-XXX-XXXXXXX)"""
    if value is None or value == '':
        return  # Opcional
    
    if len(value) > 20:
        raise ValidationError('El número preimpreso no puede exceder 20 caracteres.')
    
    # Formato típico: 001-001-0000001
    patron = r'^\d{3}-\d{3}-\d{7}$'
    if not re.match(patron, value):
        raise ValidationError('El número preimpreso debe tener el formato XXX-XXX-XXXXXXX (ej: 001-001-0000001)')

def validar_fechas_envio_respuesta_documento(fecha_envio, fecha_respuesta):
    """Valida que fecha respuesta sea posterior a fecha envío"""
    if fecha_envio is None or fecha_respuesta is None:
        return  # Ambas son opcionales
    
    if not isinstance(fecha_envio, datetime):
        raise ValidationError('La fecha de envío debe ser un datetime válido.')
    if not isinstance(fecha_respuesta, datetime):
        raise ValidationError('La fecha de respuesta debe ser un datetime válido.')
    
    if fecha_respuesta < fecha_envio:
        raise ValidationError('La fecha de respuesta no puede ser anterior a la fecha de envío.')


# =============================================================================
# 8. VALIDADORES DE DOCUMENTO IMPUESTOS (2 validadores)
# =============================================================================

def validar_base_imponible(value):
    """Valida base imponible (>= 0)"""
    if value is None:
        raise ValidationError('La base imponible es requerida.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('La base imponible debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('La base imponible no puede ser negativa.')
    if valor_decimal > Decimal('999999999999.99'):
        raise ValidationError('La base imponible no puede exceder 999,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('La base imponible solo puede tener 2 decimales.')

def validar_monto_impuesto(value):
    """Valida monto de impuesto (>= 0)"""
    if value is None:
        raise ValidationError('El monto del impuesto es requerido.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El monto del impuesto debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El monto del impuesto no puede ser negativo.')
    if valor_decimal > Decimal('9999999999.99'):
        raise ValidationError('El monto del impuesto no puede exceder 9,999,999,999.99')
    
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El monto del impuesto solo puede tener 2 decimales.')


# =============================================================================
# 9. VALIDADORES DE TIMBRADOS (7 validadores)
# =============================================================================

def validar_nro_timbrado(value):
    """Valida número de timbrado (10 dígitos)"""
    if value is None:
        raise ValidationError('El número de timbrado es requerido.')
    
    if not isinstance(value, int):
        raise ValidationError('El número de timbrado debe ser un entero.')
    
    # Timbrados de Paraguay tienen 8 dígitos típicamente
    if value < 10000000:
        raise ValidationError('El número de timbrado debe tener al menos 8 dígitos.')
    if value > 99999999999:
        raise ValidationError('El número de timbrado no puede exceder 11 dígitos.')

def validar_tipo_documento_timbrado(value):
    """Valida tipo de documento del timbrado"""
    if not value:
        raise ValidationError('El tipo de documento es requerido.')
    
    if len(value) > 12:
        raise ValidationError('El tipo de documento no puede exceder 12 caracteres.')
    
    tipos_validos = ['Factura', 'NotaCredito', 'NotaDebito', 'Recibo', 'Autofactura']
    if value not in tipos_validos:
        raise ValidationError(f'El tipo de documento debe ser: {", ".join(tipos_validos)}')

def validar_fechas_timbrado(fecha_inicio, fecha_fin):
    """Valida que fecha fin sea posterior a fecha inicio"""
    if fecha_inicio is None:
        raise ValidationError('La fecha de inicio es requerida.')
    if fecha_fin is None:
        raise ValidationError('La fecha de fin es requerida.')
    
    if not isinstance(fecha_inicio, date):
        raise ValidationError('La fecha de inicio debe ser un date válido.')
    if not isinstance(fecha_fin, date):
        raise ValidationError('La fecha de fin debe ser un date válido.')
    
    if fecha_fin <= fecha_inicio:
        raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
    
    # Validar vigencia razonable (timbrados típicamente 1-2 años)
    from datetime import timedelta
    diferencia_dias = (fecha_fin - fecha_inicio).days
    if diferencia_dias > 730:  # 2 años
        raise ValidationError('La vigencia del timbrado no puede exceder 2 años (730 días).')

def validar_numeros_timbrado(nro_inicial, nro_final):
    """Valida que nro_final sea mayor a nro_inicial"""
    if nro_inicial is None:
        raise ValidationError('El número inicial es requerido.')
    if nro_final is None:
        raise ValidationError('El número final es requerido.')
    
    if not isinstance(nro_inicial, int):
        raise ValidationError('El número inicial debe ser un entero.')
    if not isinstance(nro_final, int):
        raise ValidationError('El número final debe ser un entero.')
    
    if nro_inicial < 1:
        raise ValidationError('El número inicial debe ser mayor a 0.')
    if nro_final <= nro_inicial:
        raise ValidationError('El número final debe ser mayor al número inicial.')
    
    # Validar cantidad razonable de documentos
    cantidad = nro_final - nro_inicial + 1
    if cantidad > 999999999:
        raise ValidationError('La cantidad de documentos no puede exceder 999,999,999')

def validar_es_electronico_timbrado(value):
    """Valida campo es_electronico (0 o 1)"""
    if value is None:
        raise ValidationError('El campo es_electronico es requerido.')
    
    if not isinstance(value, int):
        raise ValidationError('El campo es_electronico debe ser un entero.')
    
    if value not in [0, 1]:
        raise ValidationError('El campo es_electronico debe ser 0 (no) o 1 (sí).')

def validar_activo_timbrado(value):
    """Valida campo activo de timbrado (boolean)"""
    if not isinstance(value, bool):
        raise ValidationError('El campo activo debe ser True o False.')


# =============================================================================
# 10. VALIDADORES DE PUNTOS DE EXPEDICIÓN (3 validadores)
# =============================================================================

def validar_codigo_establecimiento(value):
    """Valida código de establecimiento (3 dígitos: 001-999)"""
    if not value:
        raise ValidationError('El código de establecimiento es requerido.')
    
    if len(value) != 3:
        raise ValidationError('El código de establecimiento debe tener exactamente 3 caracteres.')
    
    # Debe ser numérico
    if not value.isdigit():
        raise ValidationError('El código de establecimiento solo puede contener dígitos.')
    
    codigo_int = int(value)
    if codigo_int < 1 or codigo_int > 999:
        raise ValidationError('El código de establecimiento debe estar entre 001 y 999.')

def validar_codigo_punto_expedicion(value):
    """Valida código de punto de expedición (3 dígitos: 001-999)"""
    if not value:
        raise ValidationError('El código de punto de expedición es requerido.')
    
    if len(value) != 3:
        raise ValidationError('El código de punto de expedición debe tener exactamente 3 caracteres.')
    
    # Debe ser numérico
    if not value.isdigit():
        raise ValidationError('El código de punto de expedición solo puede contener dígitos.')
    
    codigo_int = int(value)
    if codigo_int < 1 or codigo_int > 999:
        raise ValidationError('El código de punto de expedición debe estar entre 001 y 999.')

def validar_descripcion_punto_expedicion(value):
    """Valida descripción de punto de expedición (opcional, max 100)"""
    if value is None or value == '':
        return
    
    if len(value.strip()) < 3:
        raise ValidationError('La descripción debe tener al menos 3 caracteres.')
    if len(value) > 100:
        raise ValidationError('La descripción no puede exceder 100 caracteres.')


# =============================================================================
# 11. VALIDADORES DE DATOS EMPRESA (7 validadores)
# =============================================================================

def validar_ruc_empresa(value):
    """Valida RUC de empresa (formato Paraguay: XXXXXXXX-X)"""
    if not value:
        raise ValidationError('El RUC es requerido.')
    
    if len(value) > 20:
        raise ValidationError('El RUC no puede exceder 20 caracteres.')
    
    # Formato típico de Paraguay: 80000000-0 (8 dígitos + guion + dígito verificador)
    patron = r'^\d{8}-\d{1}$'
    if not re.match(patron, value):
        raise ValidationError('El RUC debe tener el formato XXXXXXXX-X (ej: 80000000-0)')

def validar_razon_social_empresa(value):
    """Valida razón social de empresa (5-255 caracteres)"""
    if not value or len(value.strip()) < 5:
        raise ValidationError('La razón social debe tener al menos 5 caracteres.')
    if len(value) > 255:
        raise ValidationError('La razón social no puede exceder 255 caracteres.')

def validar_direccion_empresa(value):
    """Valida dirección de empresa (opcional, max 255)"""
    if value is None or value == '':
        return
    
    if len(value.strip()) < 5:
        raise ValidationError('La dirección debe tener al menos 5 caracteres.')
    if len(value) > 255:
        raise ValidationError('La dirección no puede exceder 255 caracteres.')

def validar_ciudad_empresa(value):
    """Valida ciudad de empresa (opcional, max 100)"""
    if value is None or value == '':
        return
    
    if len(value.strip()) < 3:
        raise ValidationError('La ciudad debe tener al menos 3 caracteres.')
    if len(value) > 100:
        raise ValidationError('La ciudad no puede exceder 100 caracteres.')
    
    # Solo letras, espacios y guiones
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value):
        raise ValidationError('La ciudad solo puede contener letras, espacios y guiones.')

def validar_pais_empresa(value):
    """Valida país de empresa (opcional, max 100)"""
    if value is None or value == '':
        return
    
    if len(value.strip()) < 3:
        raise ValidationError('El país debe tener al menos 3 caracteres.')
    if len(value) > 100:
        raise ValidationError('El país no puede exceder 100 caracteres.')
    
    # Solo letras, espacios y guiones
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value):
        raise ValidationError('El país solo puede contener letras, espacios y guiones.')

def validar_telefono_empresa(value):
    """Valida teléfono de empresa (formato +595...)"""
    if value is None or value == '':
        return  # Opcional
    
    if len(value) > 20:
        raise ValidationError('El teléfono no puede exceder 20 caracteres.')
    
    # Formato internacional: +595XXXXXXXXX (Paraguay)
    # Permitir también formatos locales: (0XXX) XXX-XXX
    patron = r'^(\+595\d{9}|\(\d{3,4}\)\s?\d{3}-\d{3,4}|\d{9,11})$'
    if not re.match(patron, value.replace(' ', '').replace('-', '')):
        raise ValidationError('El teléfono debe tener un formato válido (ej: +595981234567 o (021) 123-456)')

def validar_email_empresa(value):
    """Valida email de empresa"""
    if value is None or value == '':
        return  # Opcional
    
    if len(value) > 100:
        raise ValidationError('El email no puede exceder 100 caracteres.')
    
    # Validar formato email
    validator = EmailValidator()
    try:
        validator(value)
    except ValidationError:
        raise ValidationError('El email no tiene un formato válido.')


# =============================================================================
# 12. VALIDADORES DE IMPUESTOS (4 validadores)
# =============================================================================

def validar_nombre_impuesto(value):
    """Valida nombre de impuesto (3-50 caracteres, unique)"""
    if not value or len(value.strip()) < 3:
        raise ValidationError('El nombre del impuesto debe tener al menos 3 caracteres.')
    if len(value) > 50:
        raise ValidationError('El nombre del impuesto no puede exceder 50 caracteres.')

def validar_porcentaje_impuesto(value):
    """Valida porcentaje de impuesto (0.00-99.99)"""
    if value is None:
        raise ValidationError('El porcentaje es requerido.')
    
    try:
        valor_decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError('El porcentaje debe ser un número válido.')
    
    if valor_decimal < Decimal('0'):
        raise ValidationError('El porcentaje no puede ser negativo.')
    if valor_decimal > Decimal('99.99'):
        raise ValidationError('El porcentaje no puede exceder 99.99%')
    
    # Verificar 2 decimales
    if valor_decimal.as_tuple().exponent < -2:
        raise ValidationError('El porcentaje solo puede tener 2 decimales.')

def validar_vigente_desde_impuesto(value):
    """Valida fecha de vigencia desde"""
    if value is None:
        raise ValidationError('La fecha de vigencia desde es requerida.')
    
    if not isinstance(value, date):
        raise ValidationError('La fecha debe ser un date válido.')

def validar_vigente_hasta_impuesto(fecha_desde, fecha_hasta):
    """Valida que fecha hasta sea posterior a fecha desde"""
    if fecha_hasta is None:
        return  # Vigencia indefinida
    
    if fecha_desde is None:
        raise ValidationError('La fecha de vigencia desde es requerida.')
    
    if not isinstance(fecha_desde, date):
        raise ValidationError('La fecha desde debe ser un date válido.')
    if not isinstance(fecha_hasta, date):
        raise ValidationError('La fecha hasta debe ser un date válido.')
    
    if fecha_hasta <= fecha_desde:
        raise ValidationError('La fecha de vigencia hasta debe ser posterior a la fecha desde.')
