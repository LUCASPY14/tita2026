# start_celery.ps1 — Inicia Celery worker para tareas async
# Uso: .\scripts\start_celery.ps1
# Prerequisito: Redis corriendo (.\scripts\start_redis.ps1)

param(
    # 4 workers: I/O-bound tasks (DB + email) no saturan CPU.
    # Con 14 tareas periódicas y dos cada 15 min en paralelo, 2 era el mínimo exacto.
    [string]$Concurrency = "4",
    [string]$LogLevel = "info"
)

$backendDir = Join-Path $PSScriptRoot "..\backend"
$venvPython = Join-Path $backendDir "venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "No se encontro el venv en $venvPython" -ForegroundColor Red
    exit 1
}

# Verifica que Redis responda antes de arrancar
$redisCheck = wsl -- bash -c "redis-cli ping 2>/dev/null" 2>$null
if ($redisCheck -ne "PONG") {
    Write-Host "Redis no esta corriendo. Ejecuta primero: .\scripts\start_redis.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Iniciando Celery worker..." -ForegroundColor Cyan
Write-Host "  Backend : $backendDir" -ForegroundColor Gray
Write-Host "  Workers : $Concurrency" -ForegroundColor Gray
Write-Host "  LogLevel: $LogLevel" -ForegroundColor Gray
Write-Host ""

Set-Location $backendDir

$env:DJANGO_SETTINGS_MODULE = "backend.settings.development"

& $venvPython -m celery -A backend.celery_app worker `
    --concurrency=$Concurrency `
    --loglevel=$LogLevel `
    --events
