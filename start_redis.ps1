# start_redis.ps1
# Inicia Redis en WSL2 Ubuntu y verifica que esta escuchando en localhost:6379
# Uso: .\start_redis.ps1

Write-Host "=== Iniciando Redis via WSL2 ===" -ForegroundColor Cyan

# 1. Verificar que WSL2 / Ubuntu esta disponible
$wslStatus = wsl -d Ubuntu -- echo "ok" 2>&1
if ($wslStatus -ne "ok") {
    Write-Host "ERROR: WSL2 Ubuntu no responde. Asegurate de que WSL2 este instalado." -ForegroundColor Red
    exit 1
}

# 2. Verificar que redis-server esta instalado
$redisPath = wsl -d Ubuntu -- which redis-server 2>&1
if (-not $redisPath) {
    Write-Host "Redis no instalado. Instalando como root..." -ForegroundColor Yellow
    wsl -d Ubuntu -u root -- apt-get install -y redis-server 2>&1
}

# 3. Detener servicio systemd y cualquier instancia previa
#    El servicio systemd de Redis usa --bind 127.0.0.1 por defecto (no accesible desde Windows)
wsl -d Ubuntu -u root -- bash -c "systemctl stop redis-server 2>/dev/null; systemctl disable redis-server 2>/dev/null; redis-cli shutdown nosave 2>/dev/null; sleep 1" | Out-Null

# 4. Iniciar Redis vinculado a 0.0.0.0 para que sea accesible desde Windows
Write-Host "Iniciando redis-server en WSL2 (bind 0.0.0.0)..." -ForegroundColor Yellow
wsl -d Ubuntu -u root -- bash -c "redis-server --daemonize yes --loglevel notice --logfile /tmp/redis.log --bind 0.0.0.0 --port 6379 --protected-mode no 2>&1"

Start-Sleep -Seconds 2

# 5. Verificar que Redis responde desde WSL2
$ping = wsl -d Ubuntu -- bash -c "redis-cli ping 2>/dev/null"
if ($ping -ne "PONG") {
    Write-Host "ERROR: Redis no responde en WSL2. Revisar /tmp/redis.log" -ForegroundColor Red
    wsl -d Ubuntu -- bash -c "cat /tmp/redis.log 2>/dev/null | tail -20"
    exit 1
}

# 6. Verificar acceso desde Windows (donde corre Celery)
$venvPython = Join-Path $PSScriptRoot "backend\venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $winPing = & $venvPython -c "import redis; r=redis.Redis('localhost',6379); print(r.ping())" 2>&1
    if ($winPing -match "True") {
        Write-Host "Redis accesible desde Windows en localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "ADVERTENCIA: Redis no accesible desde Windows. Celery puede fallar." -ForegroundColor Yellow
    }
} else {
    Write-Host "Redis iniciado correctamente en 0.0.0.0:6379" -ForegroundColor Green
}

Write-Host ""
Write-Host "Para iniciar el worker Celery, ejecuta start_celery.ps1" -ForegroundColor Cyan
