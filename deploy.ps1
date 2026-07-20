# deploy.ps1 — Cantina Tita v1
#
# Despliega la última versión desde el repositorio a producción.
# Ejecutar desde la raíz del proyecto (D:\tita2026\) como Administrador.
#
# Uso:
#   .\deploy.ps1
#   .\deploy.ps1 -Branch main
#   .\deploy.ps1 -SkipBuild          # reusar imágenes existentes
#   .\deploy.ps1 -SkipMigrations     # omitir migrate (hot-fix sin cambios de schema)
#
# Requisitos previos:
#   1. Docker Desktop corriendo
#   2. backend\.env.production completado (copiar de backend\.env.production.example)
#   3. PostgreSQL nativo en Windows, cantina_tita accesible
#   4. Git configurado con acceso al repo

param(
    [string]$Branch          = "main",
    [switch]$SkipBuild,
    [switch]$SkipMigrations,
    [string]$HealthUrl       = "http://localhost/api/health/",
    # /ready/ solo verifica DB + Redis, no Celery.
    # Los workers no han sido reiniciados todavía cuando se hace este check.
    [string]$BackendHealthUrl = "http://localhost:8000/api/health/ready/"
)

$ErrorActionPreference = "Stop"
$START = Get-Date

# ── Helpers ────────────────────────────────────────────────────────────────────

function Log {
    param([string]$Msg, [string]$Color = "White")
    Write-Host "$(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor $Color
}

function Step {
    param([string]$Title)
    $line = "─" * 60
    Write-Host ""
    Write-Host $line -ForegroundColor DarkGray
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor DarkGray
}

function Die {
    param([string]$Msg)
    Write-Host ""
    Write-Host "  ERROR: $Msg" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function RunOrDie {
    param([string]$Desc, [scriptblock]$Block)
    Log $Desc
    & $Block
    if ($LASTEXITCODE -ne 0) { Die "$Desc falló (código $LASTEXITCODE)" }
}

function WaitForHttp {
    param([string]$Url, [int]$MaxSeconds = 60, [string]$Label = "servicio")
    Log "Esperando $Label en $Url ($MaxSeconds s máx)..."
    $elapsed = 0
    while ($elapsed -lt $MaxSeconds) {
        Start-Sleep -Seconds 3
        $elapsed += 3
        try {
            $r = Invoke-WebRequest -Uri $Url -TimeoutSec 4 -UseBasicParsing -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                Log "  $Label OK ($elapsed s)" "Green"
                return $true
            }
        } catch {}
        if ($elapsed % 15 -eq 0) { Log "  Todavía esperando... ($elapsed/$MaxSeconds s)" "DarkGray" }
    }
    return $false
}

# ── 0. Directorio de trabajo ────────────────────────────────────────────────

if (-not (Test-Path "docker-compose.yml")) {
    Die "Ejecutar desde la raíz del proyecto (D:\tita2026). docker-compose.yml no encontrado."
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       DEPLOY — Cantina Tita v1                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. Prerequisitos ────────────────────────────────────────────────────────

Step "1/7  Verificando prerequisitos"

if (-not (Get-Command git   -ErrorAction SilentlyContinue)) { Die "git no encontrado en PATH." }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Die "docker no encontrado. Instalar Docker Desktop." }

docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) { Die "Docker no está corriendo. Iniciar Docker Desktop y reintentar." }
Log "Docker:         OK" "Green"
Log "Git:            OK" "Green"

$envFile = "backend\.env.production"
if (-not (Test-Path $envFile)) {
    Die "$envFile no existe.`n  Copiar backend\.env.production.example → $envFile y completar SECRET_KEY, BANCARD_*, etc."
}
Log ".env.production: OK" "Green"

# Verificar que PostgreSQL es accesible antes de continuar
$pgOk = $false
try {
    $conn = New-Object System.Net.Sockets.TcpClient
    $conn.Connect("localhost", 5432)
    $conn.Close()
    $pgOk = $true
} catch {}
if (-not $pgOk) {
    Die "PostgreSQL no responde en localhost:5432.`n  Verificar que el servicio 'postgresql-x64-16' está activo."
}
Log "PostgreSQL:     OK" "Green"

# ── 2. Git pull ─────────────────────────────────────────────────────────────

Step "2/7  Actualizando código (rama: $Branch)"

$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne $Branch) {
    Log "Cambiando de '$currentBranch' a '$Branch'..." "Yellow"
    git checkout $Branch
    if ($LASTEXITCODE -ne 0) { Die "No se pudo cambiar a '$Branch'. Resolver conflictos manualmente." }
}

$dirty = git status --porcelain
if ($dirty) {
    Log "Cambios locales sin commitear — haciendo stash..." "Yellow"
    git stash
    if ($LASTEXITCODE -ne 0) { Die "git stash falló. Resolver cambios locales manualmente." }
    Log "  Stash guardado. Restaurar con: git stash pop" "DarkGray"
}

$hashAntes = git rev-parse HEAD
git pull origin $Branch
if ($LASTEXITCODE -ne 0) { Die "git pull falló. Verificar conectividad y permisos del repo." }
$hashDespues = git rev-parse HEAD

if ($hashAntes -eq $hashDespues) {
    Log "Sin commits nuevos — el código ya estaba actualizado." "Yellow"
} else {
    Log "Actualizado: $($hashAntes.Substring(0,7)) → $($hashDespues.Substring(0,7))" "Green"
    git log --oneline "$hashAntes..$hashDespues" | ForEach-Object { Log "  + $_" "DarkGray" }
}

# Inyectar GIT_COMMIT_SHA en .env.production para que Sentry muestre el release exacto
$commitSha = git rev-parse HEAD
$envContent = Get-Content $envFile -Raw
if ($envContent -match "GIT_COMMIT_SHA=") {
    $envContent = $envContent -replace "GIT_COMMIT_SHA=.*", "GIT_COMMIT_SHA=$commitSha"
} else {
    $envContent += "`nGIT_COMMIT_SHA=$commitSha"
}
$envContent | Set-Content $envFile -Encoding utf8 -NoNewline
Log "GIT_COMMIT_SHA=$($commitSha.Substring(0,7)) inyectado en .env.production" "DarkGray"

# Exportar vars que docker compose build necesita para las build-args del frontend
$env:GIT_COMMIT_SHA = $commitSha
$env:VITE_SENTRY_DSN = (Get-Content $envFile | Select-String "^VITE_SENTRY_DSN=") -replace "^VITE_SENTRY_DSN=", ""
if (-not $env:VITE_SENTRY_DSN) {
    # Fallback: leer desde backend .env.production si está bajo el mismo nombre
    $env:VITE_SENTRY_DSN = (Get-Content $envFile | Select-String "^SENTRY_DSN_FRONTEND=") -replace "^SENTRY_DSN_FRONTEND=", ""
}

# ── 3. Build de imágenes ─────────────────────────────────────────────────────

Step "3/7  Construyendo imágenes Docker"

if ($SkipBuild) {
    Log "SkipBuild activado — reutilizando imágenes existentes." "Yellow"
} else {
    RunOrDie "docker compose build --pull" { docker compose build --pull }
    Log "Build completado." "Green"
}

# ── 4. Migraciones de base de datos ─────────────────────────────────────────

Step "4/7  Aplicando migraciones (PostgreSQL)"

if ($SkipMigrations) {
    Log "SkipMigrations activado — omitiendo migrate." "Yellow"
} else {
    RunOrDie "python manage.py migrate" {
        docker compose run --rm backend python manage.py migrate --noinput
    }
    Log "Migraciones aplicadas." "Green"
}

# ── 5. Archivos estáticos ────────────────────────────────────────────────────

Step "5/7  Recolectando archivos estáticos"

RunOrDie "python manage.py collectstatic" {
    docker compose run --rm backend python manage.py collectstatic --noinput --clear
}
Log "Archivos estáticos recolectados." "Green"

# ── 6. Restart de servicios ──────────────────────────────────────────────────

Step "6/7  Reiniciando servicios"

# Redis primero (backend lo necesita para arrancar)
Log "Reiniciando redis..."
docker compose up -d redis
if ($LASTEXITCODE -ne 0) { Die "redis no pudo iniciar. Revisar: docker compose logs redis" }

# Backend: reiniciar y esperar que esté saludable antes de tocar el frontend
Log "Reiniciando backend..."
docker compose up -d --no-deps backend
if ($LASTEXITCODE -ne 0) { Die "backend no pudo iniciar. Revisar: docker compose logs backend" }

$backendOk = WaitForHttp -Url $BackendHealthUrl -MaxSeconds 90 -Label "backend"
if (-not $backendOk) {
    Die "El backend no respondió en 90 segundos.`n  Revisar: docker compose logs --tail=80 backend"
}

# Workers (dependen del backend y redis)
Log "Reiniciando workers (celery, celery-beat)..."
docker compose up -d --no-deps celery celery-beat
if ($LASTEXITCODE -ne 0) { Log "Advertencia: workers no pudieron iniciar. Revisar logs." "Yellow" }

# Frontend (Nginx + React SPA) — solo si el backend está OK
Log "Reiniciando frontend (Nginx)..."
docker compose up -d --no-deps frontend
if ($LASTEXITCODE -ne 0) { Die "frontend no pudo iniciar. Revisar: docker compose logs frontend" }

# Monitoring (no crítico para el negocio)
docker compose up -d prometheus pushgateway grafana redis_exporter > $null 2>&1

# ── 7. Health check final ────────────────────────────────────────────────────

Step "7/7  Verificando salud del sistema"

$finalOk = WaitForHttp -Url $HealthUrl -MaxSeconds 30 -Label "sistema completo"
if (-not $finalOk) {
    Log "Health check falló en $HealthUrl" "Red"
    Log "Revisar logs: docker compose logs --tail=50 backend" "Yellow"
    Log "Rollback disponible: git checkout $hashAntes && .\deploy.ps1 -SkipBuild" "Yellow"
    exit 1
}

# Smoke test extendido (verifica endpoints críticos — no bloquea el deploy)
$smokeScript = Join-Path $PSScriptRoot "scripts\smoke-test.ps1"
if (Test-Path $smokeScript) {
    Log "Ejecutando smoke test de endpoints..." "Cyan"
    $backendBase = $BackendHealthUrl -replace "/api/health/", ""
    & $smokeScript -BaseUrl "http://localhost" -ApiUrl $backendBase
    if ($LASTEXITCODE -ne 0) {
        Log "Smoke test reportó fallos — revisar antes de habilitar tráfico" "Yellow"
    }
}

# ── Resumen ───────────────────────────────────────────────────────────────────

Write-Host ""
docker compose ps

$segundos = [Math]::Round(((Get-Date) - $START).TotalSeconds)
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   DEPLOY COMPLETADO en ${segundos}s" -ForegroundColor Green
Write-Host "║   Commit:  $(git rev-parse --short HEAD)" -ForegroundColor Green
Write-Host "║   App:     http://localhost" -ForegroundColor Green
Write-Host "║   Admin:   http://localhost/admin/" -ForegroundColor Green
Write-Host "║   API:     http://localhost/api/v1/docs/" -ForegroundColor Green
Write-Host "║   Grafana: http://localhost:3000  (admin / tita2026)" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Para ver logs en vivo:" -ForegroundColor DarkGray
Write-Host "  docker compose logs -f backend" -ForegroundColor DarkGray
Write-Host "Para rollback:" -ForegroundColor DarkGray
Write-Host "  git checkout $($hashAntes.Substring(0,7)) && .\deploy.ps1 -SkipMigrations" -ForegroundColor DarkGray
Write-Host ""
