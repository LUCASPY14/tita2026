# 🔄 CI/CD Pipeline - Guía Completa

## 📋 Descripción

Workflow unificado que consolida todos los procesos de CI/CD del proyecto Cantina Tita:
- ✅ Tests automatizados (Backend, Frontend, Mobile)
- 🔍 Quality checks (Linting, Type checking, Security)
- 🔨 Build de artifacts
- 🧪 Tests E2E con Cypress
- 🚀 Deploy automático a Staging y Production

**Archivo:** `.github/workflows/ci-cd.yml`

---

## 🎯 ¿Cuándo Se Ejecuta?

### Push a Ramas Principales
```yaml
branches: [desarrollo, staging, main]
```
- **desarrollo** → Deploy automático a **Staging**
- **main** → Deploy automático a **Production** (con E2E tests)

### Pull Requests
Se ejecutan todos los tests y quality checks, pero **sin deploy**.

### Manual (workflow_dispatch)
Puedes ejecutar manualmente desde GitHub Actions con opciones:
- Elegir ambiente: development/staging/production
- Activar/desactivar E2E tests

### Exclusiones
No se ejecuta cuando solo cambias:
- Archivos `.md` (documentación)
- Carpeta `docs/`
- Carpeta `temp_logs/`

---

## 🏗️ Estructura del Pipeline

### 1️⃣ **Security Scan** 🔐
- **Tool:** Trivy
- **Qué hace:** Escanea vulnerabilidades en dependencias y código
- **Severidad:** CRITICAL y HIGH
- **Reporte:** Sube resultados a GitHub Security tab

### 2️⃣ **Backend Tests** 🐍
- **Framework:** pytest + coverage
- **Base de datos:** MySQL 8.0 (igual que producción)
- **Cache:** Redis 7
- **Coverage:** Genera reporte XML/HTML
- **Upload:** Codecov + artifacts en GitHub

**Comandos equivalentes locales:**
```bash
cd backend
pytest apps/ --cov=apps --cov-report=term-missing
```

### 3️⃣ **Backend Quality** 🔍
Checks de calidad de código:
- ✅ **Black:** Formateo de código
- ✅ **isort:** Orden de imports
- ✅ **Flake8:** Linting (max line 120)
- ✅ **Bandit:** Seguridad
- ✅ **Safety:** Vulnerabilidades en dependencias

**Comandos equivalentes locales:**
```bash
cd backend
black --check apps/
isort --check-only apps/
flake8 apps/
bandit -r apps/ -ll
safety check
```

### 4️⃣ **Frontend Tests** ⚛️
- **Framework:** Jest + React Testing Library
- **Coverage:** Completa con reporte
- **Upload:** Codecov

**Comandos equivalentes locales:**
```bash
cd frontend
npm test -- --coverage --watchAll=false
```

### 5️⃣ **Frontend Quality** 🎨
- ✅ **TypeScript:** Type checking
- ✅ **ESLint:** Linting
- ✅ **npm audit:** Seguridad de dependencias

**Comandos equivalentes locales:**
```bash
cd frontend
npx tsc --noEmit
npm run lint
npm audit
```

### 6️⃣ **Mobile Tests** 📱
- **Framework:** Jest + React Native Testing Library
- **Coverage:** Genera reporte

**Comandos equivalentes locales:**
```bash
cd mobile
npm test -- --coverage
```

### 7️⃣ **Build Backend** 🔨
- Instala dependencias
- Ejecuta `collectstatic` de Django
- Construye imagen Docker (si existe Dockerfile)
- Sube static files como artifact

### 8️⃣ **Build Frontend** 🎨
- Build de producción con npm
- Analiza tamaño del bundle
- Construye imagen Docker (si existe)
- Sube build/ como artifact

### 9️⃣ **E2E Tests** 🧪 (Condicional)
- **Framework:** Cypress
- **Browser:** Chrome
- **Cuándo:** 
  - Push a `main`
  - Manual con opción `run_e2e=true`
  - PR con label `e2e`
- **Artifacts:** Screenshots (si falla) y videos

### 🔟 **Deploy Staging** 🚀
**Trigger:** Push a rama `desarrollo`

**Pasos:**
1. Descarga artifacts (backend static + frontend build)
2. Conecta por SSH al servidor staging
3. Git pull de rama desarrollo
4. Docker compose pull + up
5. Ejecuta migraciones
6. Collectstatic

**Variables requeridas (GitHub Secrets):**
```
STAGING_SSH_HOST
STAGING_SSH_USER
STAGING_SSH_KEY
STAGING_SSH_PORT (opcional, default: 22)
```

### 1️⃣1️⃣ **Deploy Production** 🚀
**Trigger:** Push a rama `main` + E2E tests passed

**Pasos:**
1. Descarga artifacts
2. Crea GitHub Release (si hay tag)
3. Conecta por SSH al servidor producción
4. Git pull de rama main
5. Docker compose pull + up
6. Ejecuta migraciones
7. **Crea backup de BD automático**
8. Health check
9. Rollback automático si falla

**Variables requeridas (GitHub Secrets):**
```
PROD_SSH_HOST
PROD_SSH_USER
PROD_SSH_KEY
PROD_SSH_PORT (opcional)
PROD_URL (para health check)
```

### 1️⃣2️⃣ **Summary** 📊
Genera resumen final con:
- Estado de cada job
- Branch y commit
- Falla el pipeline si algún test crítico falló

---

## 🔧 Configuración de Secrets

### En GitHub Repository Settings → Secrets and Variables → Actions

#### Staging
```bash
STAGING_SSH_HOST=staging.cantinatita.com
STAGING_SSH_USER=deploy
STAGING_SSH_KEY=<private SSH key>
STAGING_SSH_PORT=22
```

#### Production
```bash
PROD_SSH_HOST=cantinatita.com
PROD_SSH_USER=deploy
PROD_SSH_KEY=<private SSH key>
PROD_SSH_PORT=22
PROD_URL=https://cantinatita.com
```

#### AWS (Opcional)
```bash
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=us-east-1
```

#### Codecov (Opcional)
```bash
CODECOV_TOKEN=<your-token>
```

---

## 📊 Visualización de Resultados

### GitHub Actions Tab
1. Ve a tu repositorio en GitHub
2. Click en tab "Actions"
3. Verás el historial de ejecuciones
4. Click en una ejecución para ver detalles

### Artifacts
Los siguientes artifacts se guardan por 7-30 días:
- `backend-test-results` - Coverage HTML + XML + JUnit
- `frontend-test-results` - Coverage de Jest
- `mobile-test-results` - Coverage de mobile
- `backend-security-reports` - Bandit + Safety reports
- `backend-static` - Static files de Django
- `frontend-build` - Build de producción
- `cypress-screenshots` - Screenshots de E2E (si falla)
- `cypress-videos` - Videos de E2E

### Codecov Dashboard
Si configuraste `CODECOV_TOKEN`, los reportes de coverage se suben a:
- https://codecov.io/gh/LUCASPY14/tita2026

---

## 🚀 Flujos de Trabajo Comunes

### Desarrollo Normal
```bash
# 1. Crear feature branch
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios y commits
git add .
git commit -m "feat: nueva funcionalidad"

# 3. Push a GitHub
git push origin feature/nueva-funcionalidad

# 4. Crear Pull Request a 'desarrollo'
# → Se ejecutan: tests + quality checks (sin deploy)

# 5. Merge del PR
# → Se ejecuta pipeline completo + deploy a staging
```

### Deploy a Producción
```bash
# 1. Asegurar que staging funciona correctamente

# 2. Merge de 'desarrollo' a 'main'
git checkout main
git pull origin main
git merge desarrollo
git push origin main

# → Se ejecuta pipeline completo + E2E tests + deploy a production
```

### Rollback Manual
Si algo falla en producción:

```bash
# Opción 1: Git revert
git revert <commit-hash>
git push origin main

# Opción 2: SSH al servidor
ssh deploy@cantinatita.com
cd /var/www/cantina-tita
git reset --hard HEAD~1
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔍 Debugging

### Ver Logs en GitHub Actions
1. Click en el job que falló
2. Expande el step que tiene ❌
3. Lee el error
4. Descarga artifacts si necesitas más info

### Ejecutar Localmente
```bash
# Backend tests
cd backend
pytest apps/ -v

# Frontend tests
cd frontend
npm test

# Mobile tests
cd mobile
npm test

# Quality checks
pre-commit run --all-files
```

### Saltarse CI (Emergencias)
```bash
git commit -m "fix: emergencia [skip ci]"
```
⚠️ **NO RECOMENDADO** - Solo para emergencias

---

## 📈 Métricas y Badges

Agrega estos badges al README.md:

```markdown
![CI/CD Pipeline](https://github.com/LUCASPY14/tita2026/actions/workflows/ci-cd.yml/badge.svg?branch=main)
![Backend Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/main/graph/badge.svg?flag=backend)
![Frontend Coverage](https://codecov.io/gh/LUCASPY14/tita2026/branch/main/graph/badge.svg?flag=frontend)
```

---

## ⚡ Optimizaciones

### Cache
El workflow usa cache para:
- ✅ pip dependencies (Python)
- ✅ npm dependencies (Node)

### Concurrency
Si haces múltiples pushes seguidos, los pipelines anteriores se cancelan automáticamente.

### Parallel Jobs
Estos jobs corren en paralelo:
- Backend tests + Backend quality
- Frontend tests + Frontend quality
- Mobile tests
- Security scan

---

## 🔄 Comparación con Workflows Antiguos

| Feature | ci.yml | test-pipeline.yml | advanced-ci-cd.yml | **ci-cd.yml (NUEVO)** |
|---------|--------|-------------------|--------------------|-----------------------|
| Backend tests | ✅ MySQL | ✅ PostgreSQL | ✅ PostgreSQL | ✅ MySQL |
| Frontend tests | ✅ | ✅ | ✅ | ✅ |
| Mobile tests | ❌ | ❌ | ❌ | ✅ |
| Security scan | ❌ | ❌ | ✅ | ✅ |
| E2E tests | ✅ Siempre | ❌ | ✅ Siempre | ✅ Condicional |
| Deploy staging | ❌ | ❌ | ❌ | ✅ Auto |
| Deploy production | ❌ | ❌ | ❌ | ✅ Auto |
| Quality checks | ✅ Básico | ❌ | ✅ Avanzado | ✅ Completo |
| Matrix testing | ❌ | ✅ | ❌ | ❌ |
| Performance tests | ❌ | ❌ | ✅ | ❌ (Futuro) |

**Ventajas del nuevo workflow:**
- ✅ Consolidación: 1 archivo vs 3
- ✅ Deploy automático
- ✅ Tests de mobile incluidos
- ✅ Mejor manejo de artifacts
- ✅ Rollback automático
- ✅ Health checks post-deploy
- ✅ Más eficiente (menos redundancia)

---

## 📚 Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Cypress CI Documentation](https://docs.cypress.io/guides/continuous-integration/introduction)
- [Docker Compose in CI](https://docs.docker.com/compose/production/)

---

## 🆘 Problemas Comunes

### "Error: Process completed with exit code 1"
**Causa:** Tests fallidos o quality check no pasó
**Solución:** 
1. Ejecuta tests localmente
2. Corrige errores
3. Push de nuevo

### "SSH connection failed"
**Causa:** SSH secrets no configurados o incorrectos
**Solución:** Verifica secrets en GitHub Settings

### "MySQL service not ready"
**Causa:** Health check de MySQL falló
**Solución:** Espera automáticamente, si persiste revisa logs

### "npm ci failed"
**Causa:** package-lock.json desactualizado
**Solución:** 
```bash
cd frontend  # o mobile
rm -rf node_modules package-lock.json
npm install
git add package-lock.json
git commit -m "chore: update package-lock"
```

### "Coverage below threshold"
**Causa:** Coverage cayó por debajo del mínimo
**Solución:** Agregar tests o ajustar threshold

---

## 🎯 Próximos Pasos

- [ ] Configurar Codecov token
- [ ] Configurar SSH keys para staging/production
- [ ] Agregar performance tests (locust)
- [ ] Configurar notificaciones (Slack/Discord)
- [ ] Agregar análisis de bundle size trends
- [ ] Configurar Blue/Green deployment
- [ ] Agregar smoke tests post-deploy

---

**Mantenido por:** Equipo de Desarrollo  
**Última actualización:** 2026-04-21  
**Versión:** 1.0.0
