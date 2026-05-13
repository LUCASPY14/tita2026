# start_celery.ps1
# Inicia el worker Celery y el beat scheduler para tita2026
# Prerequisito: Redis corriendo (ejecutar start_redis.ps1 primero)
# Uso: .\start_celery.ps1

param(
    [switch]$BeatOnly,    # Solo el beat scheduler (sin worker)
    [switch]$WorkerOnly   # Solo el worker (sin beat)
)

$BackendDir = Join-Path $PSScriptRoot "backend"

# Verificar que Redis esta disponible
Write-Host "=== Verificando Redis ===" -ForegroundColor Cyan
$ping = wsl -d Ubuntu -- bash -c "redis-cli ping 2>/dev/null" 2>&1
if ($ping -ne "PONG") {
    Write-Host "ADVERTENCIA: Redis no responde en localhost:6379" -ForegroundColor Yellow
    Write-Host "Ejecuta .\start_redis.ps1 primero" -ForegroundColor Yellow
    $confirm = Read-Host "Continuar de todos modos? (s/N)"
    if ($confirm -notmatch "^[sS]") { exit 1 }
}

Set-Location $BackendDir

# Activar virtualenv
$venvActivate = Join-Path $BackendDir "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
} else {
    Write-Host "ERROR: No se encontro el virtualenv en $BackendDir\venv" -ForegroundColor Red
    exit 1
}

Write-Host ""

if (-not $BeatOnly) {
    Write-Host "=== Iniciando Celery Worker ===" -ForegroundColor Cyan
    Write-Host "Comando: celery -A backend worker -l info -c 2" -ForegroundColor Gray
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$BackendDir'; . '$venvActivate'; celery -A backend worker -l info -c 2"
    ) -WindowStyle Normal
    Write-Host "Worker iniciado en nueva ventana" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

if (-not $WorkerOnly) {
    Write-Host ""
    Write-Host "=== Iniciando Celery Beat (scheduler) ===" -ForegroundColor Cyan
    Write-Host "Comando: celery -A backend beat -l info" -ForegroundColor Gray
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$BackendDir'; . '$venvActivate'; celery -A backend beat -l info"
    ) -WindowStyle Normal
    Write-Host "Beat scheduler iniciado en nueva ventana" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Celery en ejecucion ===" -ForegroundColor Green
Write-Host "Worker + Beat: 2 ventanas nuevas de PowerShell abiertas"
Write-Host ""
Write-Host "Tareas programadas (11 en total):"
Write-Host "  - expirar-recargas-pendientes    (diario 02:00)"
Write-Host "  - alertas-saldo-bajo             (diario 08:00)"
Write-Host "  - alertar-stock-minimo           (diario 07:00)"
Write-Host "  - verificar-vencimientos         (diario 09:00)"
Write-Host "  - resumen-diario-ventas          (diario 23:50)"
Write-Host "  - resumen-diario-stock           (diario 23:55)"
Write-Host "  - calcular-kpis-diarios          (diario 23:45)"
Write-Host "  - cierre-automatico-cajas        (cada hora)"
Write-Host "  - limpiar-notificaciones         (domingo 03:00)"
Write-Host "  - generar-cuentas-almuerzos      (1ro del mes 06:00)"
Write-Host "  - alertar-cuentas-vencidas       (dia 10 del mes 08:00)"
Write-Host ""
Write-Host "Para detener: cerrar las ventanas del worker y beat"
