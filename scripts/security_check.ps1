# security_check.ps1
# Verifica el estado de seguridad del servidor de producción de Cantina Tita.
# Ejecutar periódicamente o tras cada deploy.
#
# Uso:
#   .\scripts\security_check.ps1

$ErrorActionPreference = "SilentlyContinue"
$OK   = "[OK]  "
$WARN = "[WARN]"
$FAIL = "[FAIL]"
$pass = 0; $warns = 0; $fails = 0

function Check { param($label, $ok, $msg)
    if ($ok) { Write-Host "$OK  $label" -ForegroundColor Green; $script:pass++ }
    else      { Write-Host "$FAIL $label — $msg" -ForegroundColor Red; $script:fails++ }
}
function Warn { param($label, $msg)
    Write-Host "$WARN $label — $msg" -ForegroundColor Yellow; $script:warns++
}

Write-Host ""
Write-Host "=== Verificacion de seguridad — Cantina Tita ===" -ForegroundColor Cyan
Write-Host ""

# ── Docker ───────────────────────────────────────────────────────────────────
Write-Host "[ Docker ]" -ForegroundColor DarkGray

$containers = docker ps --format "{{.Names}}" 2>$null
$required = @("frontend","backend","redis","celery","celery-beat","grafana","prometheus","pushgateway","waha")
foreach ($svc in $required) {
    $running = $containers -like "*$svc*"
    Check "Contenedor '$svc' corriendo" ($running.Count -gt 0) "no está en docker ps"
}

# ── Cloudflare Tunnel ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ Cloudflare Tunnel ]" -ForegroundColor DarkGray

$tunnelSvc = Get-Service -Name "cloudflared" -ErrorAction SilentlyContinue
Check "cloudflared service Running" ($tunnelSvc -and $tunnelSvc.Status -eq "Running") "ejecutar: Start-Service cloudflared"

# ── Puertos internos — NO deben escuchar en 0.0.0.0 desde exterior ────────────
Write-Host ""
Write-Host "[ Firewall / puertos internos ]" -ForegroundColor DarkGray

$netstat = netstat -ano 2>$null
$internalPorts = @(3000, 9090, 9091, 3001, 5432)
foreach ($port in $internalPorts) {
    $listening = $netstat | Select-String ":$port\s"
    if ($listening) {
        # Verificar si hay regla de bloqueo en el firewall
        $blockRule = Get-NetFirewallRule -DisplayName "CantinaTita*$port*BLOQUEAR*" -ErrorAction SilentlyContinue
        if ($blockRule) {
            Check "Puerto $port bloqueado por firewall" $true ""
        } else {
            Warn "Puerto $port escucha pero sin regla de bloqueo" "ejecutar: .\scripts\setup_firewall.ps1"
        }
    } else {
        Check "Puerto $port no expuesto" $true ""
    }
}

# ── PostgreSQL ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ Base de datos ]" -ForegroundColor DarkGray

$pgSvc = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Where-Object {$_.Status -eq "Running"}
Check "PostgreSQL service Running" ($pgSvc.Count -gt 0) "iniciar el servicio postgresql"

# ── Backups ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ Backups ]" -ForegroundColor DarkGray

$backupDir = "C:\backups\cantina"
if (Test-Path $backupDir) {
    $lastBackup = Get-ChildItem "$backupDir\cantina_*.dump","$backupDir\cantina_*.dump.gpg" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($lastBackup) {
        $age = (Get-Date) - $lastBackup.LastWriteTime
        Check "Backup reciente (< 25 horas)" ($age.TotalHours -lt 25) "ultimo: $($lastBackup.Name) — hace $([math]::Round($age.TotalHours,1)) horas"
        $encrypted = $lastBackup.Name -like "*.gpg"
        if ($encrypted) { Check "Backup cifrado con GPG" $true "" }
        else             { Warn  "Backup sin cifrado GPG" "usar -GpgRecipient al configurar tarea" }
    } else {
        Check "Backup reciente existe" $false "no hay dumps en $backupDir"
    }
} else {
    Check "Directorio de backups existe" $false "ejecutar: .\scripts\setup_backup_task.ps1"
}

$backupTask = Get-ScheduledTask -TaskName "Backup Cantina Local" -ErrorAction SilentlyContinue
Check "Tarea programada backup registrada" ($null -ne $backupTask) "ejecutar: .\scripts\setup_backup_task.ps1"

# ── Variables de entorno críticas ─────────────────────────────────────────────
Write-Host ""
Write-Host "[ Variables de entorno — .env.production ]" -ForegroundColor DarkGray

$envFile = "D:\tita2026\backend\.env.production"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw

    $placeholders = @("RESEND_API_KEY_AQUI","PUBLIC_KEY_DE_BANCARD","PRIVATE_KEY_DE_BANCARD","MERCHANT_ID_DE_BANCARD","<key>","<key2>")
    foreach ($ph in $placeholders) {
        if ($envContent -like "*$ph*") {
            Warn "Placeholder sin reemplazar: $ph" "actualizar .env.production"
        }
    }

    $hasSecret = $envContent -match "SECRET_KEY=[A-Za-z0-9_\-]{30,}"
    Check "SECRET_KEY configurado" $hasSecret "generar con: python -c 'import secrets; print(secrets.token_urlsafe(50))'"

    $debugFalse = $envContent -match "DEBUG=False"
    Check "DEBUG=False" $debugFalse "DEBUG debe ser False en produccion"
} else {
    Check ".env.production existe" $false "crear desde .env.production.example"
}

# ── HTTPS / TLS ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ HTTPS ]" -ForegroundColor DarkGray

try {
    $resp = Invoke-WebRequest -Uri "https://cantinatita.com/api/health/" -TimeoutSec 10 -UseBasicParsing
    Check "HTTPS cantinatita.com responde" ($resp.StatusCode -eq 200) "verificar tunnel y contenedores"

    $csp = $resp.Headers["Content-Security-Policy"]
    Check "Header CSP presente" ($null -ne $csp) "agregar CSP en nginx.conf"

    $xframe = $resp.Headers["X-Frame-Options"]
    Check "Header X-Frame-Options presente" ($null -ne $xframe) "agregar en nginx.conf"
} catch {
    Warn "No se pudo conectar a cantinatita.com" "verificar cloudflared y docker"
}

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Resultado: $pass OK  |  $warns advertencias  |  $fails fallos" -ForegroundColor $(
    if ($fails -gt 0) { "Red" } elseif ($warns -gt 0) { "Yellow" } else { "Green" }
)
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

if ($fails -gt 0) { exit 1 }
