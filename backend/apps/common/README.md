# Módulo Common - Utilidades Compartidas

## 📋 Descripción General

El módulo `common` proporciona utilidades compartidas y componentes reutilizables para toda la aplicación Cantina Tita. Este módulo contiene clases de permisos personalizados, throttles para limitación de tasa y validadores específicos que son utilizados por otros módulos.

**Tipo:** Módulo de utilidades (sin modelos propios)  
**PropósitoSistema:** Proporcionar funcionalidad transversal compartida  
**Componentes principales:** 8 Permissions, 5 Throttles, 1 Validator

---

## 🏗️ Arquitectura

### Componentes del Módulo

```
apps/common/
├── __init__.py                 # Inicialización del módulo
├── permissions.py              # 7 clases de permisos DRF personalizados
├── throttling.py               # 5 clases de throttling para rate limiting
├── validators/
│   ├── __init__.py
│   └── ruc_validator.py        # Validador RUC/CI Paraguay
├── tests_permissions.py        # Tests de permisos
├── tests_throttling.py         # Tests de throttling
└── tests_validators.py         # Tests de validadores
```

### Rol del Módulo en el Sistema

El módulo `common` actúa como una **capa de utilidades transversal** que:
- Proporciona control de acceso mediante permisos DRF personalizados
- Implementa rate limiting para proteger endpoints sensibles
- Valida datos específicos del dominio (RUC/CI Paraguay)
- Es utilizado por módulos de negocio (ventas, inventario, compras, etc.)

---

## 🔐 Permisos (Permissions)

### 1. IsAdminOrReadOnly

Permiso que permite lectura a usuarios autenticados y escritura solo a administradores.

```python
from apps.common.permissions import IsAdminOrReadOnly

class MiViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    ...
```

**Lógica:**
- `GET`, `HEAD`, `OPTIONS` → ✅ Usuarios autenticados
- `POST`, `PUT`, `PATCH`, `DELETE` → ✅ Solo administradores (`is_staff=True`)

**Casos de uso:**
- APIs de consulta donde solo admins pueden modificar
- Endpoints de configuración del sistema
- Datos maestros que requieren protección adicional

---

### 2. IsCajeroOrAdmin

Permiso para cajeros y administradores del sistema.

```python
from apps.common.permissions import IsCajeroOrAdmin

class VentaViewSet(ModelViewSet):
    permission_classes = [IsCajeroOrAdmin]
    ...
```

**Lógica:**
- Permite acceso si:
  - `request.user.is_staff == True` (admin)
  - `request.user.empleado.id_rol.nombre_rol` in `['cajero', 'administrador']`

**Casos de uso:**
- Endpoints de ventas (creación, consulta)
- Operaciones de caja
- Gestión de transacciones diarias

**Nota:** Requiere que el usuario tenga un `empleado` asociado con rol válido.

---

### 3. IsOwnerOrAdmin

Permiso que permite a los usuarios acceder solo a sus propios datos, excepto administradores.

```python
from apps.common.permissions import IsOwnerOrAdmin

class PedidoViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrAdmin]
    ...
```

**Lógica:**
- `Administradores` → ✅ Acceso total a cualquier objeto
- `Usuarios normales` → ✅ Solo si `obj.usuario == request.user`

**Implementación en el ViewSet:**
```python
def get_queryset(self):
    if self.request.user.is_staff:
        return Pedido.objects.all()
    return Pedido.objects.filter(usuario=self.request.user)
```

**Casos de uso:**
- Pedidos de clientes
- Historiales personales
- Datos privados por usuario

---

### 4. IsClienteOrAdmin

Permiso que verifica se el usuario es un cliente o administrador.

```python
from apps.common.permissions import IsClienteOrAdmin

class CarritoViewSet(ModelViewSet):
    permission_classes = [IsClienteOrAdmin]
    ...
```

**Lógica:**
- Permite acceso si:
  - `request.user.is_staff == True` (admin)
  - `hasattr(request.user, 'cliente')` (es cliente)

**Casos de uso:**
- Endpoints de ecommerce
- Carrito de compras
- Pedidos online

**Nota:** Requiere que el usuario tenga un objeto `cliente` relacionado.

---

### 5. CanManageVentas

Permiso para gestionar ventas (cajeros, administradores, gerentes).

```python
from apps.common.permissions import CanManageVentas

class VentaViewSet(ModelViewSet):
    permission_classes = [CanManageVentas, IsAuthenticated]
    ...
```

**Lógica:**
- Permite acceso si:
  - `request.user.is_staff == True` (admin)
  - `request.user.empleado.id_rol.nombre_rol.lower()` in `['cajero', 'administrador', 'gerente']`

**Operaciones permitidas:**
- Crear ventas
- Consultar ventas
- Modificar ventas (según reglas de negocio)
- Generar reportes de ventas

**Roles con acceso:**
- ✅ Cajero
- ✅ Administrador
- ✅ Gerente
- ❌ Otros roles

---

### 6. CanManageInventario

Permiso para gestionar inventario (administradores, gerentes, encargados de inventario).

```python
from apps.common.permissions import CanManageInventario

class MovimientoInventarioViewSet(ModelViewSet):
    permission_classes = [CanManageInventario]
    ...
```

**Lógica:**
- Permite acceso si:
  - `request.user.is_staff == True` (admin)
  - `request.user.empleado.id_rol.nombre_rol.lower()` in `['administrador', 'gerente', 'encargado_inventario']`

**Operaciones permitidas:**
- Ajustes de stock
- Transferencias entre almacenes
- Conteos físicos
- Gestión de lotes

**Roles con acceso:**
- ✅ Administrador
- ✅ Gerente
- ✅ Encargado de Inventario
- ❌ Cajero (solo consulta, no modificación)

---

### 7. ReadOnly

Permiso que solo permite métodos de lectura a usuarios autenticados.

```python
from apps.common.permissions import ReadOnly

class CategodiaProductoViewSet(ModelViewSet):
    permission_classes = [ReadOnly]
    ...
```

**Lógica:**
- Permite solo `GET`, `HEAD`, `OPTIONS`
- Requiere autenticación (`request.user.is_authenticated`)
- **Nadie puede escribir** (ni siquiera admins con este permiso)

**Casos de uso:**
- APIs de solo consulta
- Datos de referencia inmutables
- Endpoints de auditoría

**Diferencia con IsAdminOrReadOnly:**
- `ReadOnly` → Nadie puede modificar (100% read-only)
- `IsAdminOrReadOnly` → Admins sí pueden modificar

---

## ⏱️ Throttling (Limitación de Tasa)

### Configuración en settings.py

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.common.throttling.BurstRateThrottle',
        'apps.common.throttling.SustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst': '60/min',           # Ráfaga corta
        'sustained': '1000/day',     # Sostenido
        'ventas': '300/hour',        # Endpoints de ventas
        'auth': '5/min',             # Login/autenticación
        'reportes': '10/hour',       # Generación de reportes
    }
}
```

### 1. BurstRateThrottle

Limita ráfagas cortas de requests (protección contra spikes).

```python
from apps.common.throttling import BurstRateThrottle

class ProductoListView(APIView):
    throttle_classes = [BurstRateThrottle]
    ...
```

**Configuración recomendada:** `60/min` (60 requests por minuto)

**Casos de uso:**
- APIs de búsqueda
- Autocomplete
- Endpoints públicos

---

### 2. SustainedRateThrottle

Limita uso sostenido a largo plazo (protección contra abuso).

```python
from apps.common.throttling import SustainedRateThrottle

class APIViewGeneral(APIView):
    throttle_classes = [SustainedRateThrottle]
    ...
```

**Configuración recomendada:** `1000/day` o `10000/day`

**Casos de uso:**
- Rate limit global por usuario
- Protección general de API
- Control de cuotas diarias

---

### 3. VentasRateThrottle

Throttle específico para endpoints de ventas (alto tráfico).

```python
from apps.common.throttling import VentasRateThrottle

class VentaCreateView(APIView):
    throttle_classes = [VentasRateThrottle]
    ...
```

**Configuración recomendada:** `300/hour` (5 ventas/min aprox)

**Casos de uso:**
- Creación de ventas
- Procesamiento de pedidos
- Operaciones de caja

**Justificación:** Evitar creación masiva fraudulenta de ventas manteniendo fluidez operativa.

---

### 4. AuthRateThrottle

Throttle para endpoints de autenticación (prevención brute force).

```python
from apps.common.throttling import AuthRateThrottle

class LoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]
    ...
```

**Configuración recomendada:** `5/min` (5 intentos por minuto, estricto)

**Hereda de:** `AnonRateThrottle` (usa IP, no usuario)

**Casos de uso:**
- `/api/token/` (login)
- `/api/register/`
- Recuperación de contraseña
- 2FA verification

**Seguridad:** Previene ataques de fuerza bruta al limitar intentos por IP.

---

### 5. ReportesRateThrottle

Throttle para generación de reportes (operaciones costosas).

```python
from apps.common.throttling import ReportesRateThrottle

class GenerarReporteVentasView(APIView):
    throttle_classes = [ReportesRateThrottle]
    ...
```

**Configuración recomendada:** `10/hour` (restrictivo, operación costosa)

**Casos de uso:**
- Reportes PDF
- Exportación Excel
- Consultas complejas de BI
- Dashboards con agregaciones pesadas

**Justificación:** Los reportes consumen CPU/memoria significativa, limitarlos protege el servidor.

---

## ✅ Validadores (Validators)

### validate_ruc - Validador RUC/CI Paraguay

Valida números de RUC (Registro Único de Contribuyentes) y CI (Cédula de Identidad) paraguayos.

#### Uso en Modelos

```python
from apps.common.validators.ruc_validator import validate_ruc

class Cliente(models.Model):
    ruc = models.CharField(
        max_length=20,
        validators=[validate_ruc],
        help_text='RUC o CI paraguayo'
    )
```

#### Uso en Serializers

```python
from apps.common.validators.ruc_validator import validate_ruc

class ClienteSerializer(serializers.ModelSerializer):
    ruc = serializers.CharField(validators=[validate_ruc])
    
    class Meta:
        model = Cliente
        fields = ['ruc', ...]
```

#### Formatos Válidos

##### Cédula de Identidad (CI)  
- **Formato:** Solo dígitos (1-8 dígitos)
- **Ejemplos válidos:**
  - `1234567` (7 dígitos)
  - `12345` (5 dígitos)
  - `123456789` (9 dígitos, aunque raro)
- **Regex:** `^\d{1,8}$`

##### RUC con Dígito Verificador
- **Formato:** XXXXXXX-D (dígitos + guión + dígito verificador)
- **Ejemplos válidos:**
  - `1234567-8`
  - `80012345-6`
  - `123-4` (formato corto)
- **Regex:** `^\d{1,8}-\d$`

#### Comportamiento

```python
# ✅ Válidos
validate_ruc('1234567')      # CI simple
validate_ruc('1234567-8')    # RUC con verificador
validate_ruc('  123456  ')   # Se hace trim automático

# ❌ Inválidos (raise ValidationError)
validate_ruc('')            # Vacío → "RUC/CI es requerido"
validate_ruc('ABC123')      # Letras → "Formato inválido..."
validate_ruc('123-45-67')   # Múltiples guiones → "Formato inválido..."
validate_ruc('1234567-AB')  # Verificador no numérico → "Formato inválido..."
```

#### Mensaje de Error

```
"Formato inválido. Use: XXXXXXX-D (RUC) o XXXXXXX (CI)"
```

#### Implementación Interna

```python
def validate_ruc(value):
    if not value:
        raise ValidationError('RUC/CI es requerido')
    
    value_clean = str(value).strip()
    
    # Patrón RUC: dígitos-dígito
    ruc_pattern = r'^\d{1,8}-\d$'
    # Patrón CI: solo dígitos
    ci_pattern = r'^\d{1,8}$'
    
    if not (re.match(ruc_pattern, value_clean) or re.match(ci_pattern, value_clean)):
        raise ValidationError('Formato inválido. Use: XXXXXXX-D (RUC) o XXXXXXX (CI)')
    
    return value_clean
```

---

## 🧪 Testing

### Estadísticas de Cobertura

- **Total de tests:** 48
- **Tiempo de ejecución:** ~38s (con base de datos de test)
- **Resultado:** ✅ 100% PASS

#### Desglose por Componente

| Componente | Archivo | Tests | Descripción |
|------------|---------|-------|-------------|
| Permissions | `tests_permissions.py` | 8 | Tests de IsAdminOrReadOnly, ReadOnly |
| Throttling | `tests_throttling.py` | 24 | Tests de scopes y herencias |
| Validators | `tests_validators.py` | 16 | Tests de validate_ruc (CI/RUC Paraguay) |

### Ejecutar Tests

```bash
# Todos los tests del módulo common
python manage.py test apps.common

# Solo permissions
python manage.py test apps.common.tests_permissions

# Solo throttling
python manage.py test apps.common.tests_throttling

# Solo validators
python manage.py test apps.common.tests_validators

# Con verbosidad
python manage.py test apps.common -v 2

# Con settings de test específicos
python manage.py test apps.common --settings=backend.settings.test
```

### Ejemplos de Tests

#### Test de Permission

```python
def test_authenticated_user_can_read(self):
    """Usuario autenticado puede leer (GET)"""
    permission = IsAdminOrReadOnly()
    request = self.factory.get('/test/')
    request.user = self.normal_user
    
    self.assertTrue(permission.has_permission(request, None))
```

#### Test de Throttle

```python
def test_throttle_tiene_scope_correcto(self):
    """BurstRateThrottle tiene scope 'burst'"""
    throttle = BurstRateThrottle()
    self.assertEqual(throttle.scope, 'burst')
```

#### Test de Validator

```python
def test_ruc_con_digito_verificador_valido(self):
    """RUC con dígito verificador (XXXXXXX-D) válido"""
    valores_validos = ['1234567-8', '80012345-6', '123-4']
    
    for valor in valores_validos:
        result = validate_ruc(valor)
        self.assertEqual(result, valor)
```

---

## 📊 Integración con Otros Módulos

### Módulos que Usan `common`

| Módulo | Componentes Usados | Descripción |
|--------|-------------------|-------------|
| **ventas** | `CanManageVentas`, `VentasRateThrottle` | Permisos y rate limiting para ventas |
| **inventario** | `CanManageInventario`, `IsAdminOrReadOnly` | Control de acceso a inventario |
| **compras** | `IsAdminOrReadOnly`, `CanManageInventario` | Protección de endpoints de compras |
| **contabilidad** | `validate_ruc`, `IsAdminOrReadOnly` | Validación RUC en facturas |
| **clientes** | `IsClienteOrAdmin`, `validate_ruc` | Gestión de clientes y RUC |
| **core** | `ReadOnly`, `IsAdminOrReadOnly` | Datos maestros del sistema |
| **api_integrations** | `AuthRateThrottle` | Prevención brute force en APIs externas |
| **reportes** | `ReportesRateThrottle`, `IsAdminOrReadOnly` | Limitación de generación de reportes |

### Ejemplo de Integración en ventas

```python
# apps/ventas/api/v1/viewsets.py
from rest_framework import viewsets
from apps.common.permissions import CanManageVentas
from apps.common.throttling import VentasRateThrottle

class VentaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ventas"""
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    
    def get_queryset(self):
        # Cajeros ven solo sus ventas, admins ven todas
        if self.request.user.is_staff:
            return Venta.objects.all()
        return Venta.objects.filter(id_cajero__user=self.request.user)
```

### Ejemplo de Integración en contabilidad

```python
# apps/contabilidad/models.py
from django.db import models
from apps.common.validators.ruc_validator import validate_ruc

class Proveedor(models.Model):
    razon_social = models.CharField(max_length=200)
    ruc = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_ruc],
        help_text='RUC o CI paraguayo'
    )
    # ... otros campos
```

---

## 🔧 Configuración y Personalización

### Configurar Throttle Rates

En `backend/settings/base.py` o `production.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'burst': '100/min',       # Aumentar para mayor tráfico
        'sustained': '5000/day',   # Cuota diaria más generosa
        'ventas': '500/hour',      # Permitir más ventas/hora
        'auth': '3/min',           # Más estricto para seguridad
        'reportes': '5/hour',      # Más restrictivo en producción
    }
}
```

### Crear Permission Personalizado

```python
# apps/common/permissions.py
from rest_framework import permissions

class CanManage Reports(permissions.BasePermission):
    """Permiso para gestionar reportes"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_staff:
            return True
        
        try:
            empleado = request.user.empleado
            roles_permitidos = ['analista', 'gerente', 'administrador']
            return empleado.id_rol.nombre_rol.lower() in roles_permitidos
        except:
            return False
```

### Crear Throttle Personalizado

```python
# apps/common/throttling.py
from rest_framework.throttling import UserRateThrottle

class ExportacionRateThrottle(UserRateThrottle):
    """Throttle para exportaciones (operación muy costosa)"""
    scope = 'exportacion'  # Configurar en settings: 'exportacion': '2/hour'
```

---

## 🚀 Best Practices

### Uso de Permissions

1. **Combinar permissions cuando sea necesario:**
   ```python
   permission_classes = [IsAuthenticated, CanManageVentas]
   ```

2. **Usar permissions más específicos primero:**
   ```python
   # ✅ Bueno
   permission_classes = [CanManageInventario, IsAdminOrReadOnly]
   
   # ❌ Redundante (IsAdminOrReadOnly ya permite a admins)
   permission_classes = [IsAdminOrReadOnly, CanManageInventario]
   ```

3. **Documentar permisos en docstrings:**
   ```python
   class VentaViewSet(ModelViewSet):
       """
       ViewSet para ventas
       
       Permisos:
       - CanManageVentas: Cajeros, gerentes y administradores
       """
   ```

### Uso de Throttles

1. **Throttles más estrictos para operaciones sensibles:**
   ```python
   # Login (muy estricto)
   throttle_classes = [AuthRateThrottle]  # 5/min
   
   # Reportes (estricto)
   throttle_classes = [ReportesRateThrottle]  # 10/hour
   
   # General (permisivo)
   throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
   ```

2. **Combinar burst + sustained para protección multicapa:**
   ```python
   throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
   # Protege contra: spikes (60/min) Y abuso sostenido (1000/day)
   ```

3. **Monitorear throttle en producción:**
   ```python
   # Logs cuando se alcanza el límite
   if throttle.wait():
       logger.warning(f"User {user} hit rate limit: {throttle.scope}")
   ```

### Uso de Validators

1. **Combinar con otros validadores:**
   ```python
   ruc = models.CharField(
       max_length=20,
       validators=[validate_ruc, otro_validador],
       unique=True
   )
   ```

2. **Mensajes de error personalizados en forms:**
   ```python
   from django import forms
   
   class ClienteForm(forms.ModelForm):
       def clean_ruc(self):
           ruc = self.cleaned_data.get('ruc')
           try:
               validate_ruc(ruc)
           except ValidationError as e:
               raise forms.ValidationError(f"RUC inválido: {e.message}")
           return ruc
   ```

---

## 📖 Glosario Paraguay

- **RUC:** Registro Único de Contribuyentes (empresas, comerciantes)
- **CI:** Cédula de Identidad (personas físicas)
- **Dígito Verificador:** Último dígito del RUC para validación

---

## 🔗 Referencias

- [DRF Permissions Documentation](https://www.django-rest-framework.org/api-guide/permissions/)
- [DRF Throttling Documentation](https://www.django-rest-framework.org/api-guide/throttling/)
- [Django Validators Documentation](https://docs.djangoproject.com/en/6.0/ref/validators/)

---

## 📝 Changelog

### Versión 1.0.0 (Actual)
- ✅ 7 permissions implementados
- ✅ 5 throttles configurados
- ✅ Validador RUC/CI Paraguay
- ✅ 48 tests (100% PASS)
- ✅ Documentación completa

---

## 👥 Mantenimiento

Para dudas o mejoras del módulo `common`, contactar al equipo de backend.

**Última actualización:** 2025-01
