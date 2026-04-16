# 🔐 Credenciales del Portal de Clientes

**URL de acceso:** http://localhost:3000/portal/login

**Contraseña por defecto para todos:** `Portal123!`

---

## 👥 Usuarios Disponibles

### 1. Juan Garcia
- **Email:** `jgarcia@demo.tita`
- **Password:** `Portal123!`
- **RUC/CI:** 1234567
- **Hijos:** 2 (Mateo Garcia, Valentina Garcia)
- **Estado:** ✓ Verificado y Activo

### 2. Maria Ramirez
- **Email:** `mramirez@demo.tita`
- **Password:** `Portal123!`
- **RUC/CI:** 2345678
- **Hijos:** 1 (Lucia Ramirez)
- **Estado:** ✓ Verificado y Activo

### 3. Carlos Lopez
- **Email:** `clopez@demo.tita`
- **Password:** `Portal123!`
- **RUC/CI:** 3456789
- **Hijos:** 1 (Tomas Lopez)
- **Estado:** ✓ Verificado y Activo

### 4. Ana Martinez
- **Email:** `amartinez@demo.tita`
- **Password:** `Portal123!`
- **RUC/CI:** 4567890
- **Hijos:** 1 (Sofia Martinez)
- **Estado:** ⚠ No verificado (activo)

### 5. Roberto Fernandez
- **Email:** `rfernandez@demo.tita`
- **Password:** `Portal123!`
- **RUC/CI:** 5678901
- **Hijos:** 2 (Diego Fernandez, Isabella Fernandez)
- **Estado:** ⚠ No verificado (activo)

---

## 🚀 Cómo Usar

### Establecer Contraseñas (Primera vez)

Ejecutar desde el directorio `backend/`:

```powershell
venv\Scripts\python.exe manage.py shell < setup_portal_passwords.py
```

O desde Django shell:

```python
exec(open('setup_portal_passwords.py').read())
```

### Probar el Login

1. Ir a: http://localhost:3000/portal/login
2. Usar cualquiera de los emails arriba
3. Password: `Portal123!`
4. Acceder al dashboard

---

## 📊 Datos de Prueba Disponibles

### Total de Consumos: 28 registros

- **Mateo Garcia:** 3 consumos
- **Valentina Garcia:** 11 consumos ⭐ (más activa)
- **Lucia Ramirez:** 0 consumos
- **Tomas Lopez:** 7 consumos
- **Sofia Martinez:** 0 consumos
- **Diego Fernandez:** 2 consumos
- **Isabella Fernandez:** 5 consumos

### Recomendaciones para Pruebas

**Usuario con más actividad:** `jgarcia@demo.tita`
- 2 hijos con tarjetas
- 14 consumos totales
- Ideal para ver dashboard completo

**Usuario simple:** `clopez@demo.tita`
- 1 hijo con tarjeta
- 7 consumos
- Ideal para pruebas básicas

**Usuario sin consumos:** `mramirez@demo.tita`
- 1 hijo sin consumos aún
- Ideal para probar estado inicial

---

## 🔧 Comandos Útiles

### Verificar usuarios portal

```python
from apps.usuarios.models import UsuariosPortal
UsuariosPortal.objects.all().values('email', 'estado', 'email_verificado')
```

### Ver consumos de un hijo específico

```python
from apps.core.models import ConsumosTarjeta, Tarjetas
from apps.clientes.models import Hijos

hijo = Hijos.objects.get(nombre='Valentina', apellido='Garcia')
tarjeta = Tarjetas.objects.get(id_hijo=hijo)
consumos = ConsumosTarjeta.objects.filter(nro_tarjeta=tarjeta).order_by('-fecha_consumo')[:10]

for c in consumos:
    print(f"{c.fecha_consumo} | {c.detalle} | Gs. {c.monto_consumido} | Saldo: Gs. {c.saldo_posterior}")
```

### Agregar consumo de prueba

```python
from apps.core.models import ConsumosTarjeta, Tarjetas
from apps.clientes.models import Hijos
from django.utils import timezone
from decimal import Decimal

hijo = Hijos.objects.get(nombre='Lucia', apellido='Ramirez')
tarjeta = Tarjetas.objects.get(id_hijo=hijo)

# Crear consumo
consumo = ConsumosTarjeta.objects.create(
    nro_tarjeta=tarjeta,
    fecha_consumo=timezone.now(),
    monto_consumido=Decimal('25000'),
    detalle='Almuerzo - Prueba',
    saldo_posterior=tarjeta.saldo_actual - Decimal('25000')
)

# Actualizar saldo de tarjeta
tarjeta.saldo_actual = consumo.saldo_posterior
tarjeta.save()

print(f"✓ Consumo creado: {consumo.detalle} | Gs. {consumo.monto_consumido}")
```

---

## ⚠️ Notas Importantes

- Estas credenciales son **solo para desarrollo/pruebas**
- NO usar en producción con estas contraseñas simples
- Los usuarios con `email_verificado=False` pueden acceder igual (solo afecta flujos de verificación)
- Todos los usuarios están activos (`estado=True`)

---

**Última actualización:** 16 de Abril, 2026
