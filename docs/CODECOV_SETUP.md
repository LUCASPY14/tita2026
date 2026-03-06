# Configuración de Codecov para Cantina Tita

**Objetivo:** Integrar reportes de cobertura automáticos con Codecov.io

---

## 📋 Pasos de Configuración

### 1. Crear Cuenta en Codecov

1. **Acceder a Codecov:**
   - URL: https://codecov.io
   - Click en "Sign up with GitHub"
   - Autorizar acceso a tu cuenta de GitHub

2. **Agregar Repositorio:**
   - Una vez logueado, click en "+ Add new repository"
   - Buscar: `LUCASPY14/tita2026`
   - Click en "Setup repo"

### 2. Obtener Token de Codecov

**Opción A: Token Público (Repositorios Públicos)**
```bash
# No necesitas token para repos públicos
# El workflow ya está configurado para subir sin token
```

**Opción B: Token Privado (Repositorios Privados)**
1. En Codecov, ir a: Settings → General
2. Copiar el **Upload Token**
3. Formato: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 3. Configurar GitHub Secret (Solo repos privados)

1. **Ir a GitHub Repository Settings:**
   ```
   https://github.com/LUCASPY14/tita2026/settings/secrets/actions
   ```

2. **Crear Nuevo Secret:**
   - Click en "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: [pegar token de Codecov]
   - Click en "Add secret"

3. **Actualizar Workflow (si es necesario):**
   - El workflow ya incluye soporte para token
   - Si el repo es privado, descomentar línea de token:

   ```yaml
   # .github/workflows/ci.yml
   - name: Upload coverage report
     uses: codecov/codecov-action@v3
     with:
       token: ${{ secrets.CODECOV_TOKEN }}  # ← Descomenta esta línea
       file: ./backend/coverage.xml
       flags: backend
   ```

### 4. Verificar Primera Subida

1. **Hacer un push al repositorio:**
   ```bash
   cd D:\tita2026\cantina_tita
   git push origin desarrollo
   ```

2. **Esperar que el workflow complete**
   - GitHub Actions: https://github.com/LUCASPY14/tita2026/actions
   - Job: "Upload coverage report" debe mostrar ✓

3. **Ver Reporte en Codecov:**
   - URL: https://codecov.io/gh/LUCASPY14/tita2026
   - Deberías ver:
     - Backend coverage: ~26%
     - Frontend coverage: (calculando)
     - Gráficos de tendencia

### 5. Configurar Badges

**Backend Coverage Badge:**
```markdown
![Backend Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/desarrollo/graph/badge.svg?flag=backend)
```

**Frontend Coverage Badge:**
```markdown
![Frontend Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/desarrollo/graph/badge.svg?flag=frontend)
```

**Overall Coverage Badge:**
```markdown
![Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/desarrollo/graph/badge.svg)
```

**Agregar a README.md:**
```markdown
# Sistema de Gestión Cantina Tita

![CI Pipeline](https://github.com/LUCASPY14/tita2026/workflows/CI%20Pipeline%20-%20Cantina%20Tita/badge.svg)
![Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/desarrollo/graph/badge.svg)
![Backend Tests](https://img.shields.io/badge/backend%20tests-151%20passing-brightgreen)
...
```

### 6. Configurar Codecov Settings (Opcional)

**En Codecov.io → Settings:**

1. **Coverage Targets:**
   ```yaml
   coverage:
     status:
       project:
         default:
           target: 40%  # Meta de cobertura
           threshold: 2%  # Tolerancia de bajada
   ```

2. **PR Comments:**
   - Habilitar "Comment on Pull Request"
   - Codecov comentará automáticamente en PRs con:
     - Coverage delta
     - Archivos modificados con baja cobertura
     - Sugerencias de mejora

3. **Notifications:**
   - Email notifications (opcional)
   - Slack integration (opcional)

---

## 🔧 Troubleshooting

### Problema: "No coverage uploaded"

**Síntomas:**
```
There was an error running the uploader: Error uploading to Codecov
```

**Soluciones:**

1. **Verificar formato del reporte:**
   ```bash
   # Backend - debe generar coverage.xml
   cd backend
   coverage xml
   ls coverage.xml  # Debe existir
   ```

2. **Verificar paths en workflow:**
   ```yaml
   - name: Upload coverage
     uses: codecov/codecov-action@v3
     with:
       file: ./backend/coverage.xml  # ← Path correcto
       flags: backend
   ```

3. **Verificar token (repos privados):**
   ```bash
   # En GitHub Actions logs, NO debe aparecer:
   # "Codecov token not found"
   ```

### Problema: "Coverage decreased"

**Síntomas:**
```
Coverage decreased (-0.05%) to 25.95%
```

**Es normal si:**
- Agregaste código nuevo sin tests
- Refactorizaste archivos ya testeados

**Solución:**
- Agregar tests para nuevo código
- O ajustar threshold en codecov.yml

### Problema: Badge muestra "unknown"

**Causas:**
1. Codecov aún está procesando el primer reporte
2. Branch name incorrecto en URL del badge
3. Repo no es público y falta configuración

**Solución:**
```markdown
<!-- Verificar que branch sea correcto -->
![Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/desarrollo/graph/badge.svg)
                                                                    ^^^^^^^^^^
                                                                    Debe coincidir con tu branch
```

---

## 📊 Métricas Esperadas Post-Integración

### Backend
```
Statements: 23,062
Covered: 5,960
Coverage: 26%
Files: 180+
```

### Frontend
```
Statements: (calculando en primer run)
Coverage: ~85-90% (estimado)
Files: 150+
```

### Tendencia Objetivo
```
Semana 1: 26% → 30%
Semana 2: 30% → 35%
Semana 3: 35% → 40%
```

---

## 📚 Recursos

- **Codecov Docs:** https://docs.codecov.com/docs
- **GitHub Actions Integration:** https://docs.codecov.com/docs/github-actions-integration
- **Badge Reference:** https://docs.codecov.com/docs/status-badges
- **YAML Configuration:** https://docs.codecov.com/docs/codecov-yaml

---

## ✅ Criterios de Éxito

Codecov está correctamente configurado cuando:

1. ✅ Reporte subido automáticamente en cada push
2. ✅ Coverage visible en dashboard de Codecov
3. ✅ Badges mostrando % correcto en README
4. ✅ PR comments automáticos (si habilitado)
5. ✅ Trending graph visible en Codecov
6. ✅ No errores en GitHub Actions logs

---

**Próximo paso:** [Branch Protection Configuration](BRANCH_PROTECTION_SETUP.md)
