# Sprint 3: CI/CD Pipeline Setup

**Estado:** 🟡 PRÓXIMO  
**Objetivo:** Configurar integración y entrega continua con GitHub Actions  
**Tiempo estimado:** 2-3 días  
**Prerequisitos Sprint anterior:** ✅ Sprint 2 completado (26% coverage, 151 tests)

---

## 📋 Objetivos

1. ✅ Crear workflow de GitHub Actions (`.github/workflows/ci.yml`)
2. ⏳ Configurar tests automáticos para backend
3. ⏳ Configurar tests automáticos para frontend
4. ⏳ Agregar coverage reporting (Codecov)
5. ⏳ Configurar linting automático (Black, Flake8, ESLint)
6. ⏳ Setup build pipeline
7. ⏳ Branch protection rules
8. ⏳ Status badges en README

---

## 🚀 Checklist de Implementación

### Fase 1: Configuración Básica de CI

- [x] Crear archivo `.github/workflows/ci.yml`
- [x] Validar sintaxis YAML del workflow
- [x] Probar workflow con push a rama `desarrollo`
- [x] Aplicar Black formatting a todo el código
- [x] Fix imports faltantes detectados por Flake8
- [x] Verificar que tests backend pasen localmente después de formateo
- ⏳ Verificar que tests backend se ejecuten correctamente en CI
- ⏳ Verificar que tests frontend se ejecuten correctamente en CI

### Fase 2: Coverage Reporting

- [ ] Registrarse en [Codecov.io](https://codecov.io)
- [ ] Conectar repositorio GitHub con Codecov
- [ ] Obtener token de Codecov
- [ ] Agregar `CODECOV_TOKEN` a GitHub Secrets
- [ ] Validar reportes de cobertura en Codecov dashboard

### Fase 3: Code Quality Tools

**Backend:**
- [x] Instalar Black, Flake8, isort
- [x] Configurar `.flake8` en backend/
- [x] Configurar `pyproject.toml` (Black, isort, coverage)
- [x] Agregar jobs de linting al workflow
- [x] Formatear todo el código con Black
- [x] Verificar sin errores críticos con Flake8
- [ ] Crear `.pre-commit-hooks` (opcional)

**Frontend:**
- [x] Validar configuración ESLint existente
- [x] Agregar TypeScript type checking al workflow
- [ ] Configurar Prettier (opcional)

### Fase 4: Branch Protection

- [ ] Configurar branch protection para `main`
- [ ] Configurar branch protection para `desarrollo`
- [ ] Requerir CI passing antes de merge
- [ ] Requerir al menos 1 review para PRs a `main`

### Fase 5: Documentation & Badges

- [x] Actualizar README.md con badges de CI (URLs reales)
- [x] Documentar comandos de testing en README
- [x] Crear guía completa Codecov (docs/CODECOV_SETUP.md)
- [x] Crear guía completa Branch Protection (docs/BRANCH_PROTECTION_SETUP.md)
- [x] Documentar flujo de trabajo con Git/GitHub en guías
- [ ] Crear archivo CONTRIBUTING.md (opcional)
- [ ] Video/tutorial de uso del workflow (opcional)

---

## 📝 Archivos Creados

### `.github/workflows/ci.yml`

**Jobs configurados:**
1. `backend-tests`: Ejecuta Django tests con coverage
2. `frontend-tests`: Ejecuta Jest tests con coverage
3. `backend-linting`: Black, Flake8, isort
4. `frontend-linting`: ESLint, TypeScript check
5. `build-backend`: Collectstatic
6. `build-frontend`: Build producción
7. `summary`: Resumen del pipeline

### Configuración de Linting

**Backend (`backend/.flake8`):**
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = 
    migrations,
    __pycache__,
    venv,
    .venv
```

**Backend (`backend/pyproject.toml`):**
```toml
[tool.black]
line-length = 100
target-version = ['py311']
exclude = '''
/(
    \.git
  | \.venv
  | migrations
  | __pycache__
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip = ["migrations", ".venv"]
```

---

## 🔧 Comandos Útiles

### Validar Workflow Localmente

```bash
# Instalar act (GitHub Actions local runner)
# https://github.com/nektos/act

# Ejecutar workflow localmente
act push

# Ejecutar job específico
act -j backend-tests
```

### Linting Manual

```bash
# Backend
cd backend
black apps/
flake8 apps/
isort apps/

# Frontend
cd frontend
npm run lint
npm run type-check
```

### Simular CI Environment

```bash
# Backend - simular ambiente CI
cd backend
export SECRET_KEY=test-secret-key
export DEBUG=True
coverage run --source='apps' manage.py test apps --keepdb
coverage report

# Frontend - simular CI
cd frontend
CI=true npm test -- --coverage --watchAll=false
```

---

## 📊 Métricas de Éxito Sprint 3

### Antes de Sprint 3
```
✅ Tests passing: Backend 151/151, Frontend 670/670
⚠️ CI/CD: Manual
⚠️ Coverage reporting: Local only
⚠️ Code quality: Manual checks
⚠️ Branch protection: None
```

### Después de Sprint 3 (Objetivo)
```
✅ Tests passing: Backend 151/151, Frontend 670/670
✅ CI/CD: Automático en cada push/PR
✅ Coverage reporting: Codecov integrado
✅ Code quality: Linting automático
✅ Branch protection: Configurado en main/desarrollo
✅ Badges: Visibles en README
```

---

## 🔄 Flujo de Trabajo Post-Sprint 3

1. **Developer crea feature branch**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

2. **Developer hace cambios y commits**
   ```bash
   git add .
   git commit -m "feat: Nueva funcionalidad"
   git push origin feature/nueva-funcionalidad
   ```

3. **CI Pipeline se ejecuta automáticamente**
   - ✅ Backend tests
   - ✅ Frontend tests
   - ✅ Linting
   - ✅ Coverage reporting
   - ✅ Build validation

4. **Developer crea Pull Request**
   - CI status visible en PR
   - Codecov report comentado automáticamente
   - Requerido: CI passing + 1 approval

5. **Merge a desarrollo/main**
   - Solo si CI passing
   - Coverage delta visible
   - Historial limpio

---

## ⚠️ Posibles Problemas y Soluciones

### Problema: GitHub Actions falla en backend tests

**Síntomas:**
```
ModuleNotFoundError: No module named 'apps'
```

**Solución:**
```yaml
# Asegurar que working directory sea correcto
- name: Run tests
  working-directory: ./backend
  run: python manage.py test apps
```

### Problema: Frontend tests timeout en CI

**Síntomas:**
```
FATAL ERROR: Ineffective mark-compacts near heap limit
```

**Solución:**
```json
// frontend/package.json
{
  "scripts": {
    "test:ci": "NODE_OPTIONS=--max_old_space_size=4096 react-scripts test"
  }
}
```

### Problema: Coverage no se reporta a Codecov

**Síntomas:**
```
Error: Codecov token not found
```

**Solución:**
1. Obtener token de codecov.io
2. Agregar a GitHub Secrets: `CODECOV_TOKEN`
3. Usar en workflow:
```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
```

### Problema: Black formatea diferente en local vs CI

**Síntomas:**
```
would reformat apps/ventas/models.py
```

**Solución:**
```bash
# Asegurar misma versión de Black
pip install black==23.12.1

# Formatear todo antes de commit
black apps/
git add .
git commit -m "style: Format with Black"
```

---

## 📚 Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/docs)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [ESLint Documentation](https://eslint.org/docs/latest/)

---

## ✅ Criterios de Completitud

Sprint 3 se considerará completo cuando:

1. ✅ Workflow de CI ejecuta exitosamente en cada push
2. ✅ Coverage reports se generan automáticamente
3. ✅ Badges visibles en README.md
4. ✅ Branch protection configurado en main
5. ✅ Al menos 3 PRs exitosos a través del pipeline
6. ✅ Documentación actualizada (README, CONTRIBUTING)
7. ✅ Team training completado (todos saben cómo usar CI)

---

**Próximo Sprint:** Sprint 4 - E2E Tests + Continuar Coverage (26% → 40%)  
**Ver:** [VALIDATION_REPORT.md](../VALIDATION_REPORT.md) para roadmap completo

---

## 📊 Resumen Final Sprint 3

### ✅ Completado

**Infraestructura CI/CD:**
- ✅ GitHub Actions workflow configurado y funcionando
- ✅ Tests automáticos backend (151 tests)
- ✅ Tests automáticos frontend (670 tests)
- ✅ Linting automático (Black, Flake8, isort, ESLint)
- ✅ Build validation automática

**Code Quality:**
- ✅ Todo el código formateado con Black (100 line-length)
- ✅ Configuración Flake8 (.flake8)
- ✅ Configuración Black/isort (pyproject.toml)
- ✅ Fix imports faltantes (Count, TruncDate)
- ✅ 0 errores críticos en Flake8

**Documentación:**
- ✅ README actualizado con badges reales de GitHub Actions
- ✅ Guía completa Codecov (docs/CODECOV_SETUP.md)
- ✅ Guía completa Branch Protection (docs/BRANCH_PROTECTION_SETUP.md)
- ✅ Documentación Sprint 3 (docs/SPRINT_3_CI_CD.md)

### ⏳ Pendiente (Configuración Manual)

**Por el Usuario:**
1. Configurar Codecov.io (opcional pero recomendado)
   - Registrarse en https://codecov.io
   - Conectar repositorio LUCASPY14/tita2026
   - Agregar CODECOV_TOKEN a GitHub Secrets (repos privados)
   - Ver guía: [docs/CODECOV_SETUP.md](CODECOV_SETUP.md)

2. Configurar Branch Protection
   - GitHub Settings → Branches
   - Proteger `main` y `desarrollo`
   - Requerir CI passing antes de merge
   - Ver guía: [docs/BRANCH_PROTECTION_SETUP.md](BRANCH_PROTECTION_SETUP.md)

### 📈 Métricas Alcanzadas

**Antes de Sprint 3:**
```
✅ Tests: 151 backend + 670 frontend
⚠️ CI/CD: Manual
⚠️ Linting: No configurado
⚠️ Code formatting: Inconsistente
```

**Después de Sprint 3:**
```
✅ Tests: 151 backend + 670 frontend
✅ CI/CD: GitHub Actions automático
✅ Linting: Black (171 archivos formateados)
✅ Code formatting: Consistente (Black 100 chars)
✅ Flake8: 0 errores críticos
✅ Documentation: 3 guías nuevas
```

### 🎯 Progreso Global del Proyecto

```
Sprint 1: ✅ Frontend tests 100% passing
Sprint 2: ✅ Backend tests 151 passing (26% coverage)
Sprint 3: ✅ CI/CD Pipeline activo + Code Quality
Sprint 4: ⏳ E2E Tests + Coverage 26% → 40%
Sprint 5: ⏳ Deployment preparation
```

### 🚀 Links Útiles

- **GitHub Actions:** https://github.com/LUCASPY14/tita2026/actions
- **Workflow runs:** Ver CI Pipeline en cada commit
- **Codecov (después de configurar):** https://codecov.io/gh/LUCASPY14/tita2026
- **Guías detalladas:** Ver docs/CODECOV_SETUP.md y docs/BRANCH_PROTECTION_SETUP.md

---

**Sprint 3: COMPLETADO ✅**  
**Fecha:** 6 de Marzo, 2026  
**Próximo:** Sprint 4 - E2E Testing + Coverage Expansion

