# Configuración de BooleanFields - Valores por Defecto

**Fecha**: 1 de Marzo de 2026  
**Versión**: 1.0.0

---

## 📋 Resumen

Este documento detalla los valores predeterminados de todos los BooleanFields del sistema y su justificación según las reglas de negocio.

---

## 🎯 Criterios de Configuración

| Criterio | Valor Default | Justificación |
|----------|---------------|---------------|
| **Seguridad** | `False` | Por defecto restrictivo |
| **Funcionalidad** | `True` | Activado para uso inmediato |
| **Notificaciones** | `True` | Mejor experiencia de usuario |
| **Permisos críticos** | `False` | Asignar explícitamente |

---

## 🔐 Módulo Core - Tarjetas

### **Tarjetas.permite_saldo_negativo**
```python
permite_saldo_negativo = models.BooleanField(
    default=False,
    help_text="Permite realizar compras con saldo negativo (requiere autorización)"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Por seguridad, NO permitir saldo negativo por defecto
- Requiere autorización explícita con tarjeta de supervisor
- Evita deudas no autorizadas
- El cliente/padre debe optar-in para esta funcionalidad

**Casos de uso con `True`**:
- Clientes VIP o con historial de pago confiable
- Estudiantes con plan de crédito mensual aprobado
- Requiere configuración manual por administrador

---

### **Tarjetas.notificar_saldo_bajo**
```python
notificar_saldo_bajo = models.BooleanField(
    default=True,
    help_text="Enviar notificación cuando el saldo esté bajo"
)
```

**Valor**: `True` ✅  
**Justificación**:  
- Mejor experiencia de usuario
- Previene situaciones incómodas (hijo sin saldo)
- El padre puede recargar a tiempo
- Se puede desactivar si el cliente no lo desea

**Casos de uso con `False`**:
- Cliente solicita no recibir notificaciones
- Sistema de recarga automática activo

---

## 🔑 Módulo Core - Tarjetas de Autorización

### **TarjetasAutorizacion.puede_anular_almuerzos**
```python
puede_anular_almuerzos = models.BooleanField(
    default=False,
    help_text="Permite anular registros de almuerzo"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Permiso crítico que afecta facturación
- Solo empleados específicos (Gerentes, Supervisores)
- Requiere asignación manual por administrador

---

### **TarjetasAutorizacion.puede_anular_ventas**
```python
puede_anular_ventas = models.BooleanField(
    default=False,
    help_text="Permite anular ventas"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Permiso de alto riesgo financiero
- Solo Gerentes y Administradores
- Auditoría requerida

---

### **TarjetasAutorizacion.puede_anular_recargas**
```python
puede_anular_recargas = models.BooleanField(
    default=False,
    help_text="Permite anular recargas de saldo"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Afecta el flujo de caja
- Solo empleados autorizados
- Previene fraudes

---

### **TarjetasAutorizacion.puede_modificar_precios**
```python
puede_modificar_precios = models.BooleanField(
    default=False,
    help_text="Permite modificar precios en punto de venta"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Permiso crítico de pricing
- Solo Gerentes y Encargados
- Requiere justificación

---

## 💳 Módulo Core - Medios de Pago

### **MediosPago.genera_comision**
```python
genera_comision = models.BooleanField(
    default=False,
    help_text="Si este medio de pago cobra comisión"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- La mayoría de medios NO generan comisión (efectivo, tarjeta prepago)
- Medios con comisión son excepciones (tarjeta crédito, PayPal)
- Configuración explícita para medios que sí cobran

**Casos de uso con `True`**:
- Tarjetas de crédito (2-3%)
- Pasarelas de pago online
- Transferencias bancarias internacionales

---

### **MediosPago.requiere_validacion**
```python
requiere_validacion = models.BooleanField(
    default=False,
    help_text="Requiere validación externa (ej: tarjeta crédito)"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Medios simples NO requieren validación (efectivo, prepago)
- Solo medios externos necesitan confirmación
- Acelera flujo de venta para casos comunes

**Casos de uso con `True`**:
- Tarjetas de crédito/débito
- Billeteras digitales
- Transferencias bancarias

---

## ⚙️ Módulo Core - Configuración del Sistema

### **ConfiguracionSistema.requerido**
```python
requerido = models.BooleanField(
    default=False,
    help_text="Configuración obligatoria"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- La mayoría de configuraciones son opcionales
- Solo parámetros críticos son requeridos
- Flexibilidad en la configuración

---

### **ConfiguracionSistema.requiere_reinicio**
```python
requiere_reinicio = models.BooleanField(
    default=False,
    help_text="Requiere reiniciar el sistema al cambiar"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- La mayoría de configuraciones aplican en caliente
- Solo configuraciones de infraestructura requieren reinicio
- Minimiza interrupciones del servicio

---

### **ConfiguracionSistema.solo_superuser**
```python
solo_superuser = models.BooleanField(
    default=False,
    help_text="Solo superusuarios pueden modificar"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Flexibilidad para administradores regulares
- Solo configuraciones críticas son exclusivas de superuser
- Mejora la experiencia operativa

**Casos de uso con `True`**:
- Configuraciones de seguridad (JWT secret keys)
- Parámetros de base de datos
- Configuraciones de backup

---

### **CacheConfiguracion.auto_invalidate**
```python
auto_invalidate = models.BooleanField(
    default=True,
    help_text="Invalidar automáticamente el caché"
)
```

**Valor**: `True` ✅  
**Justificación**:  
- Garantiza datos actualizados
- Previene mostrar información obsoleta
- La mayoría de cachés deben invalidarse automáticamente

**Casos de uso con `False`**:
- Cachés de datos estáticos (imágenes, archivos)
- Configuraciones que cambian raramente

---

## 🍽️ Módulo Almuerzos - Tipos de Almuerzo

### **TiposAlmuerzo.incluye_plato_principal**
```python
incluye_plato_principal = models.BooleanField(
    default=True,
    help_text="Incluye plato principal"
)
```

**Valor**: `True` ✅  
**Justificación**:  
- TODO almuerzo debe tener al menos el plato principal
- Es el componente esencial
- Sería inusual un "almuerzo" sin plato principal

---

### **TiposAlmuerzo.incluye_postre**
```python
incluye_postre = models.BooleanField(
    default=False,
    help_text="Incluye postre"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- El postre es opcional según el tipo de almuerzo
- Almuerzos básicos NO incluyen postre
- Se activa para tipos "completo" o "premium"

---

### **TiposAlmuerzo.incluye_bebida**
```python
incluye_bebida = models.BooleanField(
    default=False,
    help_text="Incluye bebida"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- La bebida es opcional según el plan
- Almuerzos básicos pueden no incluirla
- Se vende por separado en la cantina

---

## 📊 Módulo Almuerzos - Registros de Consumo

### **RegistrosConsumoAlmuerzo.marcado_en_cuenta**
```python
marcado_en_cuenta = models.BooleanField(
    default=False,
    help_text="Indica si el consumo se agregó a la cuenta mensual de almuerzo (NO relacionado con saldo de cantina)"
)
```

**Valor**: `False` ✅  
**Justificación**:  
- Inicialmente NO está marcado
- Se marca cuando se agrega a CuentasAlmuerzoMensual
- Permite tracking del proceso de facturación
- **CRÍTICO**: El help_text aclara la independencia con cantina

**Flujo**:
1. Se crea registro → `marcado_en_cuenta=False`
2. ViewSet agrega a cuenta mensual → `marcado_en_cuenta=True`
3. Sistema sabe que ya fue procesado

---

## 🔬 Módulo Almuerzos - Alérgenos

### **ProductosAlergenos.contiene**
```python
contiene = models.BooleanField(
    default=True,
    help_text="True=Contiene el alérgeno, False=Puede contener trazas"
)
```

**Valor**: `True` ✅  
**Justificación**:  
- Por seguridad, se asume que CONTIENE el alérgeno
- Previene reacciones alérgicas por información incorrecta
- Si solo son "trazas", se marca explícitamente como `False`

**Modelo de seguridad**:
- `True` = Contiene definitivamente (advertencia máxima)
- `False` = Puede contener trazas (advertencia menor)

---

## 📈 Resumen de Configuraciones

| Campo | Default | Seguridad | Funcionalidad | Justificación |
|-------|---------|-----------|---------------|---------------|
| **Tarjetas.permite_saldo_negativo** | `False` | ✅ Alta | - | Requiere autorización |
| **Tarjetas.notificar_saldo_bajo** | `True` | - | ✅ UX | Mejor experiencia |
| **TarjetasAutorizacion.puede_*** | `False` | ✅ Crítica | - | Permisos explícitos |
| **MediosPago.genera_comision** | `False` | - | ✅ Operación | Mayoría sin comisión |
| **MediosPago.requiere_validacion** | `False` | - | ✅ Velocidad | Flujo rápido |
| **ConfiguracionSistema.requerido** | `False` | - | ✅ Flexibilidad | Opcionales por defecto |
| **ConfiguracionSistema.requiere_reinicio** | `False` | - | ✅ Disponibilidad | Evita interrupciones |
| **ConfiguracionSistema.solo_superuser** | `False` | ⚖️ Balanceado | ✅ Operación | Flexibilidad operativa |
| **CacheConfiguracion.auto_invalidate** | `True` | ✅ Datos | - | Información actualizada |
| **TiposAlmuerzo.incluye_plato_principal** | `True` | - | ✅ Lógica | Componente esencial |
| **TiposAlmuerzo.incluye_postre** | `False` | - | ✅ Flexibilidad | Opcional según plan |
| **TiposAlmuerzo.incluye_bebida** | `False` | - | ✅ Flexibilidad | Opcional según plan |
| **RegistrosConsumoAlmuerzo.marcado_en_cuenta** | `False` | - | ✅ Proceso | Se marca al procesar |
| **ProductosAlergenos.contiene** | `True` | ✅ Salud | - | Prevención médica |

---

## ✅ Validación de Configuraciones

### Todas las configuraciones cumplen con:

1. **Principio de menor privilegio**: Permisos en `False` por defecto
2. **Seguridad primero**: Restricciones antes que comodidad
3. **Experiencia de usuario**: Notificaciones habilitadas
4. **Lógica de negocio**: Defaults basados en casos de uso comunes
5. **Documentación clara**: help_text explica el propósito

---

## 🔄 Migración de Datos Existentes

### Si hay datos en la base de datos con valores `0` o `1`:

```sql
-- Los BooleanFields en MySQL usan TINYINT(1)
-- 0 = False
-- 1 = True

-- Estos valores ya son compatibles con Django BooleanField
-- No se requiere migración de datos
```

### Verificación post-implementación:

```python
# Test en Django shell
from apps.core.models import Tarjetas

t = Tarjetas.objects.first()
print(t.permite_saldo_negativo)  # True o False (no 1 o 0)
print(type(t.permite_saldo_negativo))  # <class 'bool'>
```

---

## 📝 Recomendaciones

### 1. Revisión Periódica
- Cada 6 meses revisar si los defaults siguen siendo apropiados
- Ajustar según feedback de usuarios

### 2. Documentación de Cambios
- Registrar motivo si se cambia un default
- Notificar a administradores

### 3. Testing
- Verificar que todos los tests usan los defaults correctos
- Agregar tests específicos para validar cada default

### 4. Capacitación
- Explicar a administradores el significado de cada campo
- Documentar cuándo cambiar de `False` a `True`

---

**Fin del Documento**
