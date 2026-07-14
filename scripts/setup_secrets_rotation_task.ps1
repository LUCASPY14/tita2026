# scripts/setup_secrets_rotation_task.ps1 — Cantina Tita
#
# Registra una tarea programada de Windows para rotar la SECRET_KEY de Django
# mensualmente (día 1 de cada mes a las 03:00), usando rotar-secrets.ps1.
#
# Ejecutar UNA VEZ como Administrador en el servidor de producción.
#
# ── Uso ──────────────────────────────────────────────────────────────────────
#   .\scripts\setup_secrets_rotation_task.ps1
#   .\scripts\setup_secrets_rotation_task.ps1 -RotationDay 15 -RotationHour "04:00"

param(
    [string]$ProjectRoot    = "C:\tita2026",
    [int]   $RotationDay    = 1,       # día del mes para rotar
    [string]$RotationHour   = "03:00", # hora de rotación (fuera del horario escolar)
    [switch]$SkipRestart    = $false   # pasar -SkipRestart si se prefiere reinicio manual
)

$ErrorActionPreference = "Stop"

$line = "─" * 62
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  Rotación automática de secrets — Task Scheduler" -ForegroundColor Cyan
Write-Host $line -ForegroundColor DarkGray

# ── Verificar Administrador ───────────────────────────────────────────────────
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host ""
    Write-Host "  ERROR: Ejecutar como Administrador." -ForegroundColor Red
    exit 1
}

$rotarScript = Join-Path $ProjectRoot "scripts\rotar-secrets.ps1"
if (-not (Test-Path $rotarScript)) {
    Write-Host "  ERROR: No se encontró $rotarScript" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Script    : $rotarScript" -ForegroundColor DarkGray
Write-Host "  Día       : $RotationDay de cada mes a las $RotationHour" -ForegroundColor DarkGray
Write-Host ""

$skipArg   = if ($SkipRestart) { " -SkipRestart" } else { "" }
$taskAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -NoProfile -File `"$rotarScript`"$skipArg"

# Trigger: mensual, día $RotationDay, a las $RotationHour
$taskTrigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth $RotationDay -At $RotationHour

$taskSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -RestartCount 1 `
    -RestartInterval (New-TimeSpan -Minutes 15) `
    -StartWhenAvailable

$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$taskName = "Cantina Tita — Rotación de Secrets"

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Tarea ya existe — actualizando..." -ForegroundColor Gray
    Set-ScheduledTask -TaskName $taskName `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings | Out-Null
} else {
    Register-ScheduledTask -TaskName $taskName `
        -Action $taskAction -Trigger $taskTrigger `
        -Settings $taskSettings -Principal $taskPrincipal `
        -Description "Rotación mensual de SECRET_KEY de Django. Todos los JWT activos se invalidan tras la rotación." | Out-Null
}

Write-Host ""
Write-Host "  [OK] Tarea registrada: '$taskName'" -ForegroundColor Green
Write-Host "       Próxima ejecución: día $RotationDay del mes siguiente a las $RotationHour" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Para ejecutar ahora manualmente:" -ForegroundColor DarkGray
Write-Host "    powershell -File `"$rotarScript`"" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  IMPORTANTE: La rotación invalida TODOS los JWT activos." -ForegroundColor Yellow
Write-Host "  Programar en horario de mínima actividad (madrugada)." -ForegroundColor DarkGray
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host ""
