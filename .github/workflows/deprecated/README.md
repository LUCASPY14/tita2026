# Workflows Deprecados

Estos workflows fueron consolidados en un único archivo `ci-cd.yml` el 21 de Abril, 2026.

## Archivos Deprecados

### 1. `ci.yml.bak`
**Propósito original:** Pipeline básico de CI con tests backend/frontend y build

**Por qué se deprecó:**
- Funcionalidad básica
- Sin deploy automático
- E2E tests siempre ejecutados (lento)
- Sin tests de mobile

**Reemplazado por:** `ci-cd.yml` - Sección de tests y builds

---

### 2. `test-pipeline.yml.bak`
**Propósito original:** Tests comprehensivos con matrix de versiones

**Por qué se deprecó:**
- Muy lento (matrix de Python 3.11/3.12 + Django 4.2/5.0)
- Usaba PostgreSQL (producción usa MySQL)
- No se usaba activamente en el proyecto
- Diseñado como workflow reutilizable pero nunca se invocó

**Features únicas:**
- Matrix testing (múltiples versiones de Python/Django/Node)
- Tests parametrizados
- Coverage threshold configurable

**Reemplazado por:** `ci-cd.yml` - Con enfoque en MySQL y versiones estables

---

### 3. `advanced-ci-cd.yml.bak`
**Propósito original:** CI/CD avanzado con security scanning

**Por qué se deprecó:**
- Duplicaba funcionalidad de `ci.yml`
- Security scan excelente pero aislado
- Performance tests con locust interesantes pero sin mantener
- Sin deploy automático implementado

**Features únicas:**
- Security scanning (Trivy) ✅ **Migrado a ci-cd.yml**
- Code quality avanzado (mypy, bandit, safety) ✅ **Migrado a ci-cd.yml**
- Performance tests con locust ⏳ **Pendiente migrar**

**Reemplazado por:** `ci-cd.yml` - Incorpora lo mejor del advanced pipeline

---

## ¿Por Qué Consolidar?

### Problemas con 3 Workflows Separados:

1. **Confusión:** Difícil saber cuál workflow se ejecuta cuándo
2. **Redundancia:** Tests duplicados en múltiples workflows
3. **Mantenimiento:** 3x más difícil actualizar dependencias
4. **Inconsistencia:** Diferentes versiones de Python/Node entre workflows
5. **Sin Deploy:** Ninguno tenía deploy automático implementado
6. **Costos:** Más minutos de GitHub Actions consumidos

### Ventajas del Workflow Consolidado:

1. ✅ **Un solo archivo:** `ci-cd.yml`
2. ✅ **Deploy automático:** Staging (desarrollo) y Production (main)
3. ✅ **Mobile tests:** Ahora incluidos
4. ✅ **E2E condicionales:** Solo cuando es necesario (más rápido)
5. ✅ **Security integrado:** Trivy + Bandit + Safety
6. ✅ **Rollback automático:** Si falla production
7. ✅ **Health checks:** Post-deploy validation
8. ✅ **Artifacts organizados:** 7-30 días de retención
9. ✅ **Mejor documentación:** CI_CD_GUIDE.md completo

---

## Migración Completa

### Lo que se mantuvo:
- ✅ MySQL 8.0 (de `ci.yml`)
- ✅ Tests backend con pytest + coverage
- ✅ Tests frontend con Jest
- ✅ Quality checks (black, flake8, isort, eslint, tsc)
- ✅ E2E tests con Cypress
- ✅ Builds de backend y frontend
- ✅ Upload a Codecov

### Lo que se agregó:
- ✅ Tests de mobile (Jest + React Native)
- ✅ Security scanning (Trivy de `advanced-ci-cd.yml`)
- ✅ Advanced security (Bandit + Safety de `advanced-ci-cd.yml`)
- ✅ Deploy automático a staging
- ✅ Deploy automático a production
- ✅ Rollback automático
- ✅ Health checks
- ✅ GitHub Releases
- ✅ Concurrency control
- ✅ Manual trigger con opciones

### Lo que se removió:
- ❌ Matrix testing (Python 3.11/3.12, Django 4.2/5.0) - Muy lento
- ❌ PostgreSQL - Producción usa MySQL
- ❌ Performance tests con locust - Sin mantenimiento

### Lo que está planeado:
- ⏳ Re-agregar performance tests (optimizados)
- ⏳ Notificaciones a Slack/Discord
- ⏳ Blue/Green deployments
- ⏳ Smoke tests automatizados

---

## ¿Necesitas Features de los Workflows Antiguos?

### Si necesitas matrix testing:
Los workflows antiguos están aquí como `.bak` para referencia. Puedes copiar el código de matrix si lo necesitas:

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
    django-version: ['4.2', '5.0']
```

### Si necesitas performance tests:
Código de locust está en `advanced-ci-cd.yml.bak` líneas 120-140. Se puede re-agregar cuando:
1. `performance_tests/locustfile.py` esté actualizado
2. Haya un endpoint de staging para testear
3. Se definan métricas de performance

### Si prefieres PostgreSQL:
Cambiar MySQL por PostgreSQL en `ci-cd.yml`:
```yaml
services:
  postgres:
    image: postgres:15
    # ... resto del config
```

---

## Historial de Cambios

| Fecha | Acción | Razón |
|-------|--------|-------|
| 2024-02-28 | Creación de `ci.yml` | Pipeline inicial |
| 2024-03-15 | Agregado `test-pipeline.yml` | Testing comprehensivo |
| 2024-04-01 | Agregado `advanced-ci-cd.yml` | Security & quality |
| **2026-04-21** | **Consolidación a `ci-cd.yml`** | **Unificar + Deploy automático** |

---

## Restaurar Workflows Antiguos (No Recomendado)

Si por alguna razón necesitas volver a los workflows antiguos:

```bash
cd .github/workflows
cp deprecated/ci.yml.bak ci.yml
cp deprecated/test-pipeline.yml.bak test-pipeline.yml
cp deprecated/advanced-ci-cd.yml.bak advanced-ci-cd.yml
# Eliminar o renombrar ci-cd.yml
mv ci-cd.yml ci-cd.yml.disabled
```

⚠️ **Advertencia:** Los workflows antiguos no tienen deploy automático ni tests de mobile.

---

## Contacto

Si tienes preguntas sobre la consolidación o necesitas features específicas de los workflows antiguos:

- 📧 Email: lucas@cantinatita.com
- 🐛 GitHub Issues: https://github.com/LUCASPY14/tita2026/issues
- 📖 Documentación: `.github/workflows/CI_CD_GUIDE.md`

---

**Fecha de deprecación:** 2026-04-21  
**Reemplazado por:** `ci-cd.yml`  
**Próxima revisión:** 2026-07-21 (3 meses)
