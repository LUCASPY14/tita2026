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
- [ ] Validar sintaxis YAML del workflow
- [ ] Probar workflow con push a rama `desarrollo`
- [ ] Verificar que tests backend se ejecuten correctamente
- [ ] Verificar que tests frontend se ejecuten correctamente

### Fase 2: Coverage Reporting

- [ ] Registrarse en [Codecov.io](https://codecov.io)
- [ ] Conectar repositorio GitHub con Codecov
- [ ] Obtener token de Codecov
- [ ] Agregar `CODECOV_TOKEN` a GitHub Secrets
- [ ] Validar reportes de cobertura en Codecov dashboard

### Fase 3: Code Quality Tools

**Backend:**
- [ ] Instalar Black, Flake8, isort
- [ ] Configurar `.flake8` en backend/
- [ ] Agregar jobs de linting al workflow
- [ ] Crear `.pre-commit-hooks` (opcional)

**Frontend:**
- [ ] Validar configuración ESLint existente
- [ ] Agregar TypeScript type checking al workflow
- [ ] Configurar Prettier (opcional)

### Fase 4: Branch Protection

- [ ] Configurar branch protection para `main`
- [ ] Configurar branch protection para `desarrollo`
- [ ] Requerir CI passing antes de merge
- [ ] Requerir al menos 1 review para PRs a `main`

### Fase 5: Documentation & Badges

- [x] Actualizar README.md con badges de CI
- [x] Documentar comandos de testing
- [ ] Crear archivo CONTRIBUTING.md
- [ ] Documentar flujo de trabajo con Git/GitHub

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
