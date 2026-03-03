# Testing y QA - Sistema Cantina Tita

## 📋 Contenido

- [Backend Testing (pytest)](#backend-testing-pytest)
- [Frontend Testing (Jest + React Testing Library)](#frontend-testing-jest--react-testing-library)
- [Coverage Reports](#coverage-reports)
- [Ejecutar Tests](#ejecutar-tests)

---

## Backend Testing (pytest)

### Configuración

**Instalación de dependencias:**
```bash
cd backend
pip install -r requirements.txt
```

**Dependencias de testing:**
- `pytest==8.3.4` - Framework de testing
- `pytest-django==4.9.0` - Integración Django con pytest
- `pytest-cov==6.0.0` - Coverage para pytest
- `pytest-mock==3.14.0` - Mocking utilities
- `factory-boy==3.3.1` - Fixtures factories
- `coverage==7.13.4` - Coverage analysis

### Estructura de Tests

```
backend/apps/
├── notificaciones/
│   ├── tests.py                 # Tests unitarios modelos
│   ├── tests_api.py             # Tests API endpoints
│   └── tests_validators.py      # Tests validadores
├── core/
│   ├── tests.py                 # Tests modelos core
│   ├── tests_configuracion.py   # Tests configuración sistema
│   ├── tests_recarga_service.py # Tests service recargas
│   └── tests_viewsets.py        # Tests ViewSets
└── [otras apps]/
    └── tests*.py
```

### Tests Implementados

#### ✅ Notificaciones (tests.py)
- **NotificacionesPortalTest**: 5 tests
  - Crear notificación
  - Marcar como leída
  - Filtrar no leídas
  - Validar tipos
  
- **NotificacionesSaldoTest**: 2 tests
  - Notificación saldo bajo
  - Notificación saldo agotado
  
- **AlertasSistemaTest**: 3 tests
  - Crear alerta crítica
  - Resolver alerta
  - Filtrar pendientes
  
- **PreferenciasNotificacionTest**: 2 tests
  - Crear preferencias default
  - Actualizar preferencias

#### ✅ Notificaciones API (tests_api.py)
- **NotificacionesPortalViewSetTest**: 6 tests
  - Listar notificaciones
  - Filtrar por leída/tipo
  - Marcar leída
  - Marcar todas leídas
  - Obtener resumen
  
- **AlertasSistemaViewSetTest**: 3 tests
  - Listar alertas
  - Filtrar pendientes
  - Resolver alerta
  
- **PreferenciasNotificacionViewSetTest**: 2 tests
  - Obtener preferencias
  - Actualizar preferencias

#### ✅ Configuración Sistema (tests_configuracion.py)
- **ConfiguracionSistemaModelTest**: 5 tests
  - Crear configuración
  - Validación de rango
  - Valores permitidos
  - Requiere reinicio
  - Solo superuser
  
- **ConfiguracionSistemaViewSetTest**: 7 tests
  - Listar como superuser
  - Listar como usuario normal
  - Filtrar por categoría
  - Por categoría action
  - Actualizar valor
  - Resetear default
  - Permisos superuser

### Ejecutar Tests Backend

**Todos los tests:**
```bash
cd backend
pytest
```

**Tests de una app específica:**
```bash
pytest apps/notificaciones/
```

**Un archivo específico:**
```bash
pytest apps/notificaciones/tests_api.py
```

**Un test específico:**
```bash
pytest apps/notificaciones/tests.py::NotificacionesPortalTest::test_crear_notificacion_portal
```

**Con marcadores:**
```bash
# Solo tests API
pytest -m api

# Solo tests unitarios
pytest -m unit

# Excluir tests lentos
pytest -m "not slow"
```

**Con coverage:**
```bash
pytest --cov=apps --cov-report=html
```

---

## Frontend Testing (Jest + React Testing Library)

### Configuración

**Instalación de dependencias:**
```bash
cd frontend
npm install
```

**Dependencias de testing:**
- `@testing-library/react` - Testing library para React
- `@testing-library/jest-dom` - Matchers personalizados Jest
- `@testing-library/user-event` - Simulación eventos usuario
- `@types/jest` - Tipos TypeScript para Jest

### Estructura de Tests

```
frontend/src/
├── components/
│   ├── common/
│   │   ├── Button.test.tsx
│   │   └── Card.test.tsx
│   └── notificaciones/
│       └── ListaNotificaciones.test.tsx
└── services/
    ├── notificaciones.service.test.ts
    └── configuracion.service.test.ts
```

### Tests Implementados

#### ✅ Componentes Comunes

**Button.test.tsx** - 12 tests:
- Renderizar con texto
- Ejecutar onClick
- Variantes (primary, danger, outline)
- Estado disabled
- Estado loading
- Tamaños (sm, lg)
- Full width
- ClassName personalizado

**Card.test.tsx** - 5 tests:
- Renderizar children
- Título
- ClassName
- Estilos base
- Múltiples children

#### ✅ Componentes Notificaciones

**ListaNotificaciones.test.tsx** - 8 tests:
- Renderizar lista
- Estado cargando
- Filtrar no leídas
- Marcar como leída
- Badge "Nueva"
- Iconos por tipo
- Manejar errores
- Sin notificaciones

#### ✅ Services

**notificaciones.service.test.ts** - 15 tests:
- API: getNotificaciones, getById, marcarLeida, marcarTodasLeidas, getResumen
- Helpers: formatearFecha, calcularTiempo, getIcono, getColor
- Error handling

**configuracion.service.test.ts** - 20+ tests:
- API: get, getPorCategoria, actualizar, resetear
- Helpers: formatear, validar, getIcono, getColor
- Validaciones: boolean, int, decimal, email, url, json
- Edge cases

### Ejecutar Tests Frontend

**Modo interactivo (watch):**
```bash
cd frontend
npm test
```

**Todos los tests (una vez):**
```bash
npm test -- --watchAll=false
```

**Con coverage:**
```bash
npm run test:coverage
```

**Un archivo específico:**
```bash
npm test Button.test.tsx
```

**Actualizar snapshots:**
```bash
npm test -- -u
```

---

## Coverage Reports

### Backend Coverage

**Generar reporte:**
```bash
cd backend
pytest --cov=apps --cov-report=html --cov-report=term-missing
```

**Ver reporte HTML:**
```bash
# Abre en navegador
backend/htmlcov/index.html
```

**Configuración (pytest.ini):**
```ini
[pytest]
addopts = 
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
```

### Frontend Coverage

**Generar reporte:**
```bash
cd frontend
npm run test:coverage
```

**Ver reporte:**
```bash
# Abre en navegador
frontend/coverage/lcov-report/index.html
```

**Configuración (package.json):**
```json
{
  "jest": {
    "collectCoverageFrom": [
      "src/**/*.{ts,tsx}",
      "!src/**/*.d.ts",
      "!src/index.tsx",
      "!src/reportWebVitals.ts"
    ]
  }
}
```

---

## Ejecutar Tests

### Quick Start

**Backend:**
```bash
cd backend
pip install -r requirements.txt
pytest
```

**Frontend:**
```bash
cd frontend
npm install
npm test
```

### CI/CD Integration

**GitHub Actions ejemplo:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=apps --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: 18
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

---

## Mejores Prácticas

### Backend
- ✅ Usar fixtures para datos de prueba reutilizables
- ✅ Marcar tests lentos con `@pytest.mark.slow`
- ✅ Separar tests unitarios de integración
- ✅ Usar factory-boy para crear objetos complejos
- ✅ Mantener tests independientes (sin estado compartido)

### Frontend
- ✅ Testear comportamiento, no implementación
- ✅ Usar screen queries accesibles (getByRole, getByLabelText)
- ✅ Mock solo dependencias externas (axios, servicios)
- ✅ Evitar snapshots para lógica compleja
- ✅ Usar waitFor para operaciones asíncronas

---

## Métricas de Cobertura

### Objetivos
- **Modelos Django**: >80% coverage
- **ViewSets/API**: >70% coverage
- **Services**: >80% coverage
- **Componentes React**: >60% coverage
- **Services TS**: >75% coverage

### Estado Actual
```
Backend:
├── apps/notificaciones/ ✅ 85%
├── apps/core/          ✅ 78%
└── apps/[otras]/       ⚠️  Variable

Frontend:
├── components/common/           ✅ 90%
├── components/notificaciones/   ✅ 75%
├── services/                    ✅ 80%
└── pages/                       ⚠️  40%
```

---

## Próximos Pasos

### Short Term
- [ ] Agregar tests para más componentes (Formularios, Tablas)
- [ ] Tests E2E con Cypress/Playwright
- [ ] Integración con SonarQube

### Long Term
- [ ] Visual regression tests (Percy, Chromatic)
- [ ] Performance testing (Lighthouse CI)
- [ ] Mutation testing (mutpy)

---

**Última actualización:** 3 Marzo 2026
**Cobertura general:** Backend 81% | Frontend 68%
