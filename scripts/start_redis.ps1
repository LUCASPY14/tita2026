# start_redis.ps1 — Inicia Redis en WSL2
# Uso: .\scripts\start_redis.ps1

Write-Host "Iniciando Redis en WSL2..." -ForegroundColor Cyan

# Verifica si Redis ya está corriendo
$running = wsl -- bash -c "redis-cli ping 2>/dev/null" 2>$null
if ($running -eq "PONG") {
    Write-Host "Redis ya está corriendo." -ForegroundColor Green
    exit 0
}

# Inicia el servicio
wsl -u root -- service redis-server start

Start-Sleep -Seconds 1

$check = wsl -- bash -c "redis-cli ping 2>/dev/null" 2>$null
if ($check -eq "PONG") {
    Write-Host "Redis iniciado correctamente en localhost:6379" -ForegroundColor Green
} else {
    Write-Host "Redis no responde. Verifica la instalacion en WSL2." -ForegroundColor Red
    Write-Host "  Instalar: wsl -- sudo apt install redis-server" -ForegroundColor Yellow
}
