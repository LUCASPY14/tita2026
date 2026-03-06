# Tests de Integración - Backend

## 📋 Descripción

Tests de integración para verificar los flujos críticos del sistema Cantina Tita.

## 🏃 Ejecutar Tests

### Todos los tests de integración
```bash
cd backend
python -m pytest tests/integration/ -v -m integration
```

### Tests específicos por módulo
```bash
# Solo autenticación
python -m pytest tests/integration/test_auth_models.py -v

# Solo inventario  
python -m pytest tests/integration/test_inventory_flow.py -v

# Solo pagos
python -m pytest tests/integration/test_payment_flow.py -v
```

### Un test individual
```bash
python -m pytest tests/integration/test_auth_models.py::TestAuthenticationFlow::test_empleado_creation -v
```

## 📊 Cobertura de Tests

### Autenticación (test_auth_models.py) - 9 tests ✅
- ✅ Creación y gestión de empleados
- ✅ Asociación rol-empleado
- ✅ Contraseñas hasheadas
- ✅ Usuarios activos/inactivos
- ✅ Restricciones únicas de roles

### Inventario (test_inventory_flow.py) - 3 tests ⏳
- ⏳ Creación de stock inicial
- ⏳ Movimientos de ingreso
- ⏳ Productos con stock bajo

### Pagos (test_payment_flow.py) - 5 tests ⏳
- ⏳ Ventas de contado
- ⏳ Ventas con múltiples ítems
- ⏳ Ventas a crédito
- ⏳ Historial de ventas
- ⏳ Pagos parciales

## 🔧 Configuración

Los tests utilizan una base de datos SQLite en memoria (`test/conftest.py`):
- ✅ Aislamiento total entre tests
- ✅ Migraciones automáticas
- ✅ Limpieza automática después de cada test

## 📝 Escribir Nuevos Tests

```python
import pytest
from django.utils import timezone
from apps.usuarios.models import Empleados, Roles

@pytest.mark.integration
@pytest.mark.django_db
class TestMiModulo:
    
    @pytest.fixture
    def mi_fixture(self, db):
        # Setup
        rol = Roles.objects.create(nombre_rol='Test', activo=True)
        return rol
    
    def test_mi_funcionalidad(self, mi_fixture):
        # Test
        assert mi_fixture.activo == True
```

## 🛠️ Troubleshooting

**Error: "no such table"**
→ Las migraciones no se ejecutaron. Verificar `conftest.py`.

**Error: "TypeError: unexpected keyword arguments"**
→ Los campos del modelo no coinciden. Verificar documentación del modelo.

## ✅ Estado Actual

- **9/17 tests passing** (53%)
- Módulo de autenticación: 100% ✅
- Módulos de inventario y pagos: En desarrollo ⏳
