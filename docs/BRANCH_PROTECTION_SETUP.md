# Configuración de Branch Protection para Cantina Tita

**Objetivo:** Proteger branches principales con reglas que requieran CI passing y code reviews.

---

## 📋 Branches a Proteger

1. **`main`** - Producción
2. **`desarrollo`** - Staging/Pre-producción

---

## 🔒 Pasos de Configuración

### 1. Acceder a Branch Protection Settings

**URL Directa:**
```
https://github.com/LUCASPY14/tita2026/settings/branches
```

**O manualmente:**
1. Ir a repositorio: https://github.com/LUCASPY14/tita2026
2. Click en "Settings" (tab superior)
3. Click en "Branches" (menú izquierdo)
4. Scroll a "Branch protection rules"

### 2. Configurar Protección para `main`

**Click en "Add rule" o "Add branch protection rule"**

#### Branch name pattern:
```
main
```

#### ✅ Reglas Recomendadas:

**Require a pull request before merging:**
- ✓ Require approvals: `1` (mínimo)
- ✓ Dismiss stale pull request approvals when new commits are pushed
- ✓ Require review from Code Owners (opcional)

**Require status checks to pass before merging:**
- ✓ **Require branches to be up to date before merging**
- Buscar y seleccionar estos status checks:
  - `backend-tests` ✓
  - `frontend-tests` ✓
  - `backend-linting` ✓
  - `frontend-linting` ✓
  - `build-backend` ✓
  - `build-frontend` ✓

**Require conversation resolution before merging:**
- ✓ Require conversation resolution before merging

**Do not allow bypassing the above settings:**
- ⚠️ Opcional: Permite a admins hacer push directo
- Recomendado: DESACTIVADO (ni siquiera admins pueden saltarse)

**Allow force pushes:**
- ❌ NO permitir force pushes

**Allow deletions:**
- ❌ NO permitir borrar branch

**Configuración Final:**
```
✓ Require a pull request before merging (1 approval)
✓ Require status checks to pass (6 checks)
✓ Require conversation resolution
✓ Require branches to be up to date
❌ Allow force pushes
❌ Allow deletions
```

Click en **"Create"** o **"Save changes"**

### 3. Configurar Protección para `desarrollo`

**Repetir proceso anterior con configuración MENOS ESTRICTA:**

#### Branch name pattern:
```
desarrollo
```

#### ✅ Reglas para Desarrollo:

**Require status checks to pass before merging:**
- ✓ **Require branches to be up to date before merging**
- Status checks requeridos:
  - `backend-tests` ✓
  - `frontend-tests` ✓
  - (Linting es opcional para desarrollo)

**Require pull request reviews:**
- Opcional para desarrollo
- Si trabajas solo: puede estar DESACTIVADO
- Si hay equipo: `1` approval mínimo

**Allow force pushes:**
- ⚠️ Opcional: Puedes permitirlo en desarrollo
- Recomendado: Permitir solo para administradores

**Configuración Final para Desarrollo:**
```
⚠️ Require a pull request (opcional, 0-1 approvals)
✓ Require status checks to pass (2 checks mínimo)
⚠️ Allow force pushes (solo admins)
❌ Allow deletions
```

Click en **"Create"** o **"Save changes"**

---

## 🔄 Flujo de Trabajo Post-Configuración

### Workflow para Features

```bash
# 1. Crear feature branch desde desarrollo
git checkout desarrollo
git pull origin desarrollo
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios y commits
git add .
git commit -m "feat: Agregar nueva funcionalidad"

# 3. Push a GitHub
git push origin feature/nueva-funcionalidad

# 4. Crear Pull Request en GitHub
# - Base: desarrollo
# - Compare: feature/nueva-funcionalidad
# - Title: "feat: Agregar nueva funcionalidad"

# 5. CI Pipeline se ejecuta automáticamente
# ✓ backend-tests (debe pasar)
# ✓ frontend-tests (debe pasar)
# ✓ linting (debe pasar)
# ✓ builds (debe pasar)

# 6. Request review (si configurado)
# - Esperar aprobación de reviewer

# 7. Merge cuando:
# ✓ Todos los checks pasen
# ✓ Tenga las aprobaciones requeridas
# ✓ Conflictos resueltos

# 8. Borrar feature branch
git branch -d feature/nueva-funcionalidad
git push origin --delete feature/nueva-funcionalidad
```

### Workflow para Releases (desarrollo → main)

```bash
# 1. Crear Release PR
# - Base: main
# - Compare: desarrollo
# - Title: "Release v1.2.0"

# 2. CI Pipeline se ejecuta
# ✓ Todos los tests pasan
# ✓ Coverage estable o mejorando
# ✓ Linting sin errores
# ✓ Builds exitosos

# 3. Code Review obligatorio (1+ approvals)

# 4. Merge to main

# 5. Tag the release
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

---

## 🔧 Verificar Configuración

### Test 1: Intento de Push Directo (Debe Fallar)

```bash
# Intentar push directo a main (debe rechazarse)
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test"
git push origin main

# Resultado esperado:
# remote: error: GH006: Protected branch update failed
# remote: error: Cannot push to main without pull request
```

### Test 2: PR sin CI Passing (Debe Bloquearse)

1. Crear PR con tests fallando
2. Intentar mergear
3. Resultado esperado:
   ```
   ⚠️ Merge blocked
   Required status checks must pass:
   ❌ backend-tests (failing)
   ```

### Test 3: PR Correcto (Debe Permitir Merge)

1. Crear PR con todos los checks passing
2. Obtener approval (si requerido)
3. Resultado esperado:
   ```
   ✓ All checks passed
   ✓ 1 approval
   ✓ Up to date with base branch
   → Merge pull request ✓
   ```

---

## 📊 Configuración Recomendada por Tipo de Proyecto

### Solo / Proyecto Personal
```yaml
main:
  - require_status_checks: [backend-tests, frontend-tests]
  - require_reviews: 0
  - allow_force_push: false

desarrollo:
  - require_status_checks: [backend-tests, frontend-tests]
  - require_reviews: 0
  - allow_force_push: true (admins only)
```

### Equipo Pequeño (2-5 devs)
```yaml
main:
  - require_status_checks: [all 6 checks]
  - require_reviews: 1
  - allow_force_push: false
  - require_conversation_resolution: true

desarrollo:
  - require_status_checks: [backend-tests, frontend-tests]
  - require_reviews: 1
  - allow_force_push: true (admins only)
```

### Equipo Grande (5+ devs)
```yaml
main:
  - require_status_checks: [all 6 checks]
  - require_reviews: 2
  - require_codeowner_review: true
  - allow_force_push: false
  - require_conversation_resolution: true
  - require_signed_commits: true

desarrollo:
  - require_status_checks: [all 6 checks]
  - require_reviews: 1
  - allow_force_push: false
  - require_conversation_resolution: true
```

---

## 🚨 Troubleshooting

### Problema: "No status checks found"

**Causa:** Workflow aún no se ha ejecutado en el repositorio.

**Solución:**
1. Hacer un push a `desarrollo`
2. Esperar que workflow complete
3. Volver a configurar branch protection
4. Ahora aparecerán los checks en la lista

### Problema: "Can't merge - checks haven't run"

**Causa:** Branch desactualizada o checks no iniciados.

**Solución:**
```bash
# Actualizar branch con base
git checkout feature/mi-feature
git pull origin desarrollo
git push origin feature/mi-feature

# Los checks se ejecutarán automáticamente
```

### Problema: "Required review not provided"

**Causa:** Configuraste reviewers pero no hay aprobación.

**Solución:**
1. Pedir a otro dev que revise
2. O temporalmente ajustar regla a 0 reviewers
3. Después de merge, volver a configurar

---

## 📚 Recursos

- **GitHub Branch Protection:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- **Required Status Checks:** https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks
- **Code Owners:** https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

---

## ✅ Criterios de Éxito

Branch Protection está correctamente configurado cuando:

1. ✅ No se puede hacer push directo a `main`
2. ✅ PRs bloqueados si CI falla
3. ✅ PRs requieren aprobación (si configurado)
4. ✅ Force push bloqueado en `main`
5. ✅ Status checks aparecen en PRs
6. ✅ Conversation resolution requerido
7. ✅ Branch deletion bloqueado

**Test final:** Intentar mergear PR con tests fallando → debe bloquearse ✓

---

**Próximo paso:** Actualizar README con badges reales
