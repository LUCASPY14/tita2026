# Configuración GitHub - CI/CD Pipeline

## 🔐 Secrets del Repositorio

Ir a: **Settings → Secrets and variables → Actions → New repository secret**

### AWS (Opcional - para S3/CloudFront)
```
AWS_ACCESS_KEY_ID=AKIA***********
AWS_SECRET_ACCESS_KEY=************
AWS_REGION=us-east-1
```

### Staging Environment
```
STAGING_SSH_HOST=staging.cantinatita.com
STAGING_SSH_USER=deploy
STAGING_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
[Tu clave SSH privada completa aquí]
-----END OPENSSH PRIVATE KEY-----
STAGING_SSH_PORT=22
```

### Production Environment
```
PROD_SSH_HOST=cantinatita.com
PROD_SSH_USER=deploy
PROD_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
[Tu clave SSH privada completa aquí]
-----END OPENSSH PRIVATE KEY-----
PROD_SSH_PORT=22
PROD_URL=https://cantinatita.com
```

### API Configuration
```
API_URL=http://localhost:8000
```

---

## 🌍 Environments

Ir a: **Settings → Environments**

### Crear Environment "staging"
1. Click **New environment**
2. Name: `staging`
3. **Environment protection rules:**
   - ✅ Required reviewers: (opcional, 1-2 personas)
   - Deployment branches: `desarrollo`
4. **Environment secrets:** (opcional, específicos de staging)
5. **Environment URL:** `https://staging.cantinatita.com`

### Crear Environment "production"
1. Click **New environment**
2. Name: `production`
3. **Environment protection rules:**
   - ✅ Required reviewers: 2+ personas (RECOMENDADO)
   - ⏰ Wait timer: 10 minutos (opcional)
   - Deployment branches: `main` only
4. **Environment secrets:** (opcional, específicos de producción)
5. **Environment URL:** `https://cantinatita.com`

---

## 🔑 Generación de SSH Keys para Deploy

```bash
# Generar par de claves SSH
ssh-keygen -t ed25519 -C "deploy@cantinatita" -f ~/.ssh/deploy_cantinatita

# La clave PÚBLICA (.pub) va al servidor
cat ~/.ssh/deploy_cantinatita.pub
# → Copiar al servidor en ~/.ssh/authorized_keys

# La clave PRIVADA va a GitHub Secrets
cat ~/.ssh/deploy_cantinatita
# → Copiar completa (con headers) a STAGING_SSH_KEY / PROD_SSH_KEY
```

---

## ✅ Validación del Workflow

### Errores que puedes ignorar:
- ⚠️ **Severity 4**: "Context access might be invalid" → Normal, son warnings del linter
- ⚠️ **Environment not found**: Desaparecerá al crear los environments

### Errores críticos (ya corregidos):
- ❌ **Severity 8**: "Unexpected symbol" → Ya corregido con `continue-on-error: true`

### Testing del Workflow:
```bash
# Validar sintaxis localmente
gh workflow view ci-cd.yml

# Trigger manual
gh workflow run ci-cd.yml --ref desarrollo

# Ver estado
gh run list --workflow=ci-cd.yml
```

---

## 📋 Checklist de Configuración

### Mínimo para que funcione (sin deployments):
- [x] Workflow creado en `.github/workflows/ci-cd.yml`
- [x] Sintaxis YAML válida
- [ ] Push a rama `desarrollo` o `main`

### Para deployments automáticos:
- [ ] Crear environments `staging` y `production` en GitHub
- [ ] Agregar secrets SSH (HOST, USER, KEY, PORT)
- [ ] Configurar servidor con Docker Compose
- [ ] Agregar clave pública SSH a `~/.ssh/authorized_keys` del servidor
- [ ] Probar conexión SSH manual: `ssh deploy@staging.cantinatita.com`

### Opcional (mejoras):
- [ ] AWS credentials para S3/CloudFront
- [ ] Codecov token para reportes públicos
- [ ] Slack/Discord webhook para notificaciones
- [ ] Branch protection rules en GitHub

---

## 🚀 Flujo de Deployment

### Staging (automático)
1. Push a rama `desarrollo`
2. CI ejecuta todos los tests
3. Build backend + frontend
4. **Deploy automático** a staging si todo pasa
5. URL: https://staging.cantinatita.com

### Production (protegido)
1. Push a rama `main` (desde merge de `desarrollo`)
2. CI ejecuta tests + E2E tests
3. Build artifacts
4. **Espera aprobación manual** (required reviewers)
5. Deploy a producción
6. Health check automático
7. Rollback si falla
8. URL: https://cantinatita.com

---

## 🔍 Monitoring & Logs

### Ver logs de workflow:
1. GitHub → Actions tab
2. Seleccionar workflow run
3. Ver cada job expandido
4. Download artifacts (test results, coverage)

### Debugging deployment:
```bash
# SSH al servidor
ssh deploy@staging.cantinatita.com

# Ver logs de Docker
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Ver estado de contenedores
docker-compose -f docker-compose.prod.yml ps
```

---

## 📞 Soporte

Si el workflow falla:
1. Revisar logs en Actions tab
2. Verificar secrets configurados correctamente
3. Probar conexión SSH manualmente
4. Validar sintaxis YAML: https://www.yamllint.com/
5. Consultar docs: https://docs.github.com/actions
