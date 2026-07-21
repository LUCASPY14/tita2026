#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Descarga e instala windows_exporter como servicio de Windows.
  Expone métricas de CPU, RAM y disco en http://localhost:9182/metrics
  para que Prometheus (en Docker) las recolecte via host.docker.internal:9182.

.NOTES
  Ejecutar como Administrador en el servidor físico (fuera de Docker).
  Una sola vez; no reejecutar si el servicio ya existe.
#>

$VERSION  = "0.27.2"
$ARCH     = "amd64"
$MSI_URL  = "https://github.com/prometheus-community/windows_exporter/releases/download/v$VERSION/windows_exporter-$VERSION-$ARCH.msi"
$MSI_FILE = "$env:TEMP\windows_exporter.msi"

# Colectores habilitados: CPU, memoria, disco lógico, OS, red
$COLLECTORS = "cpu,memory,logical_disk,os,net"

Write-Host "=== Instalando windows_exporter v$VERSION ===" -ForegroundColor Cyan

# 1. Verificar si ya está instalado
$svc = Get-Service -Name "windows_exporter" -ErrorAction SilentlyContinue
if ($svc) {
    Write-Host "AVISO: El servicio 'windows_exporter' ya existe (estado: $($svc.Status))." -ForegroundColor Yellow
    Write-Host "Si querés actualizar, detené el servicio y desinstalá el MSI anterior primero."
    exit 0
}

# 2. Descargar MSI
Write-Host "Descargando desde $MSI_URL ..."
Invoke-WebRequest -Uri $MSI_URL -OutFile $MSI_FILE -UseBasicParsing
if (-not (Test-Path $MSI_FILE)) {
    Write-Error "No se pudo descargar el MSI."
    exit 1
}

# 3. Instalar silenciosamente con los colectores correctos
Write-Host "Instalando (silencioso)..."
$msiArgs = @(
    "/i", $MSI_FILE,
    "/quiet",
    "ENABLED_COLLECTORS=$COLLECTORS",
    "LISTEN_PORT=9182"
)
$proc = Start-Process msiexec.exe -ArgumentList $msiArgs -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Error "msiexec terminó con código $($proc.ExitCode)."
    exit 1
}

# 4. Verificar que el servicio quedó corriendo
Start-Sleep -Seconds 3
$svc = Get-Service -Name "windows_exporter" -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq "Running") {
    Write-Host "Servicio 'windows_exporter' corriendo." -ForegroundColor Green
} else {
    Write-Warning "El servicio no está corriendo. Verificar con: Get-Service windows_exporter"
}

# 5. Verificar endpoint
Write-Host "Verificando endpoint http://localhost:9182/metrics ..."
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:9182/metrics" -TimeoutSec 5 -UseBasicParsing
    if ($resp.StatusCode -eq 200) {
        Write-Host "OK — métricas disponibles ($([int]($resp.Content.Length/1024)) KB)." -ForegroundColor Green
    }
} catch {
    Write-Warning "El endpoint no respondió: $_"
    Write-Warning "Revisar: Get-Service windows_exporter | Start-Service"
}

# 6. Abrir firewall (solo tráfico desde la red local)
Write-Host "Configurando regla de firewall (entrada, puerto 9182, red local)..."
$rule = Get-NetFirewallRule -DisplayName "windows_exporter Prometheus" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule `
        -DisplayName "windows_exporter Prometheus" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 9182 `
        -RemoteAddress "127.0.0.1,172.16.0.0/12,192.168.0.0/16" `
        -Action Allow `
        -Profile Any | Out-Null
    Write-Host "Regla de firewall creada (acepta 127.0.0.1 y redes 172.x / 192.168.x)." -ForegroundColor Green
} else {
    Write-Host "Regla de firewall ya existe, sin cambios." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Listo ===" -ForegroundColor Green
Write-Host "windows_exporter v$VERSION instalado como servicio de Windows."
Write-Host "Prometheus lo va a leer desde Docker via host.docker.internal:9182"
Write-Host "El job 'windows_host' ya está configurado en monitoring/prometheus.yml"
Write-Host ""
Write-Host "Para verificar métricas en Prometheus:"
Write-Host "  http://localhost:9090/targets  (buscar job=windows_host)"
