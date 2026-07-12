# setup_firewall.ps1
# Configura el firewall de Windows para proteger los servicios internos de Docker.
# Ejecutar como Administrador una sola vez en el servidor de produccion.
#
# Uso:
#   .\scripts\setup_firewall.ps1
#   .\scripts\setup_firewall.ps1 -LanCidr "10.0.0.0/8"

param(
    [string]$LanCidr = "192.168.100.0/24"
)

$ErrorActionPreference = "Stop"

function New-FwRule {
    param([string]$Name, [int]$Port, [string]$Desc)

    $nameBlock = "$Name - BLOQUEAR externo"
    $nameLan   = "$Name - PERMITIR LAN"

    Get-NetFirewallRule -DisplayName $nameBlock -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue
    Get-NetFirewallRule -DisplayName $nameLan -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue

    New-NetFirewallRule `
        -DisplayName  $nameBlock `
        -Direction    Inbound `
        -Protocol     TCP `
        -LocalPort    $Port `
        -Action       Block `
        -Profile      Any `
        -Description  "Bloquea $Desc desde internet" | Out-Null

    New-NetFirewallRule `
        -DisplayName   $nameLan `
        -Direction     Inbound `
        -Protocol      TCP `
        -LocalPort     $Port `
        -RemoteAddress $LanCidr `
        -Action        Allow `
        -Profile       Any `
        -Description   "Permite $Desc solo desde LAN $LanCidr" | Out-Null

    Write-Host "  [OK] Puerto $Port ($Desc) solo LAN $LanCidr" -ForegroundColor Green
}

Write-Host ""
Write-Host "Configurando firewall para Cantina Tita..." -ForegroundColor Cyan
Write-Host "LAN permitida: $LanCidr" -ForegroundColor Cyan
Write-Host ""

New-FwRule -Name "CantinaTita-Grafana"     -Port 3000 -Desc "Grafana dashboards"
New-FwRule -Name "CantinaTita-Prometheus"  -Port 9090 -Desc "Prometheus metrics"
New-FwRule -Name "CantinaTita-PushGateway" -Port 9091 -Desc "Prometheus PushGateway"
New-FwRule -Name "CantinaTita-WAHA"        -Port 3001 -Desc "WAHA WhatsApp API"

# PostgreSQL: solo localhost y Docker bridge
$pgBlock = "CantinaTita-PostgreSQL - BLOQUEAR externo"
$pgAllow = "CantinaTita-PostgreSQL - PERMITIR local"

Get-NetFirewallRule -DisplayName $pgBlock -ErrorAction SilentlyContinue |
    Remove-NetFirewallRule -ErrorAction SilentlyContinue
Get-NetFirewallRule -DisplayName $pgAllow -ErrorAction SilentlyContinue |
    Remove-NetFirewallRule -ErrorAction SilentlyContinue

New-NetFirewallRule `
    -DisplayName  $pgBlock `
    -Direction    Inbound -Protocol TCP -LocalPort 5432 `
    -Action       Block -Profile Any `
    -Description  "Bloquea PostgreSQL desde cualquier IP remota" | Out-Null

New-NetFirewallRule `
    -DisplayName   $pgAllow `
    -Direction     Inbound -Protocol TCP -LocalPort 5432 `
    -RemoteAddress @("127.0.0.1", "172.16.0.0/12", "10.0.0.0/8") `
    -Action        Allow -Profile Any `
    -Description   "Permite PostgreSQL solo desde localhost y Docker bridge" | Out-Null

Write-Host "  [OK] Puerto 5432 (PostgreSQL) solo localhost + Docker" -ForegroundColor Green

Write-Host ""
Write-Host "Puerto 80 (app): accesible publicamente via Cloudflare Tunnel" -ForegroundColor Yellow
Write-Host ""
Write-Host "Firewall configurado correctamente." -ForegroundColor Green
Write-Host "Verificar con: netstat -ano"
Write-Host ""
