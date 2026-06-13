# setup_backup_task.ps1
# Instala las tareas programadas de backup diario de Cantina Tita.
# Ejecutar UNA VEZ en el servidor de producción como Administrador.
#
# Uso:
#   .\scripts\setup_backup_task.ps1 -DbPassword "password_de_postgres"
#
# Qué registra:
#   "Backup Cantina Local"  — 02:00 diario — pg_dump a C:\backups\cantina\
#   "Backup Cantina Nube"   — 02:30 diario — sube el dump a Google Drive (si rclone instalado)
#
# Pre-requisitos:
#   - PostgreSQL 16 instalado (ajustar -PgBin si es otra versión)
#   - Usuario SYSTEM con acceso a pg_dump (pgpass.conf en perfil SYSTEM)
#   - rclone configurado con remote "gdrive" (opcional, solo para nube)

param(
    [Parameter(Mandatory=$true)]
    [string]$DbPassword,

    [string]$ProjectRoot = "C:\tita2026",
    [string]$BackupDir   = "C:\backups\cantina",
    [string]$PgBin       = "C:\Program Files\PostgreSQL\16\bin",
    [string]$PgUser      = "cantina_user",
    [string]$PgHost      = "localhost",
    [string]$PgPort      = "5432",
    [switch]$SkipNube    = $false
)

# ── Verificar que se ejecuta como administrador ───────────────────────────────
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Este script debe ejecutarse como Administrador."
    Write-Host  "Abrir PowerShell como Administrador y volver a ejecutar."
    exit 1
}

Write-Host "=== INSTALACION DE BACKUPS AUTOMÁTICOS - CANTINA TITA ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Crear directorio de backups ────────────────────────────────────────────
Write-Host "1/4 Creando directorio de backups: $BackupDir" -ForegroundColor Yellow
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "    Directorio creado." -ForegroundColor Green
} else {
    Write-Host "    Ya existe." -ForegroundColor Gray
}

# ── 2. Configurar pgpass.conf para la cuenta SYSTEM ──────────────────────────
Write-Host "2/4 Configurando pgpass.conf para la cuenta SYSTEM..." -ForegroundColor Yellow

$pgpassScript = Join-Path $ProjectRoot "scripts\setup_pgpass.ps1"
if (-not (Test-Path $pgpassScript)) {
    Write-Error "No se encontró $pgpassScript. Verificar que ProjectRoot sea correcto."
    exit 1
}

# Configurar pgpass para el usuario actual (quien ejecuta el script)
& powershell -File $pgpassScript -Password $DbPassword -PgUser $PgUser -PgHost $PgHost -PgPort $PgPort
if ($LASTEXITCODE -ne 0) {
    Write-Error "setup_pgpass.ps1 falló."
    exit 1
}

# Configurar también para la cuenta SYSTEM (la que ejecuta las tareas programadas)
$pgpassSystemDir  = "C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql"
$pgpassSystemFile = Join-Path $pgpassSystemDir "pgpass.conf"
if (-not (Test-Path $pgpassSystemDir)) {
    New-Item -ItemType Directory -Path $pgpassSystemDir -Force | Out-Null
}
$entry = "$PgHost`:$PgPort`:*`:$PgUser`:$DbPassword"
$entry | Out-File -FilePath $pgpassSystemFile -Encoding UTF8 -Force
Write-Host "    pgpass.conf configurado para SYSTEM: $pgpassSystemFile" -ForegroundColor Green

# ── 3. Registrar tarea: Backup Local (02:00 diario) ──────────────────────────
Write-Host "3/4 Registrando tarea 'Backup Cantina Local' (02:00 diario)..." -ForegroundColor Yellow

$backupScript = Join-Path $ProjectRoot "backup_cantina.ps1"
if (-not (Test-Path $backupScript)) {
    Write-Error "No se encontró $backupScript. Verificar -ProjectRoot."
    exit 1
}

$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NonInteractive -NoProfile -File `"$backupScript`" -PgBin `"$PgBin`" -PgUser `"$PgUser`" -PgHost `"$PgHost`" -PgPort `"$PgPort`""
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$existingTask = Get-ScheduledTask -TaskName "Backup Cantina Local" -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "    Tarea ya existe — actualizando..." -ForegroundColor Gray
    Set-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $action -Trigger $trigger -Settings $settings | Out-Null
} else {
    Register-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
        -Description "Backup diario de cantina_tita a $BackupDir (pg_dump format custom)" | Out-Null
}
Write-Host "    ✓ Tarea 'Backup Cantina Local' registrada." -ForegroundColor Green

# ── 4. Registrar tarea: Backup Nube (02:30 diario, opcional) ─────────────────
if (-not $SkipNube) {
    Write-Host "4/4 Registrando tarea 'Backup Cantina Nube' (02:30 diario)..." -ForegroundColor Yellow

    $nubeScript = Join-Path $ProjectRoot "scripts\backup_nube.ps1"
    if (-not (Test-Path $nubeScript)) {
        Write-Warning "    No se encontró $nubeScript. Saltando tarea de nube."
    } else {
        $rcloneOk = $null
        try { $rcloneOk = Get-Command rclone -ErrorAction Stop } catch {}

        if (-not $rcloneOk) {
            Write-Warning "    rclone no encontrado. Instalar desde https://rclone.org y ejecutar:"
            Write-Warning "    rclone config  →  nuevo remote 'gdrive' (Google Drive)"
            Write-Warning "    Luego volver a ejecutar este script o crear la tarea manualmente."
        } else {
            $actionNube = New-ScheduledTaskAction -Execute "powershell.exe" `
                -Argument "-NonInteractive -NoProfile -File `"$nubeScript`" -SoloUltimo"
            $triggerNube = New-ScheduledTaskTrigger -Daily -At "02:30"

            $existingNube = Get-ScheduledTask -TaskName "Backup Cantina Nube" -ErrorAction SilentlyContinue
            if ($existingNube) {
                Set-ScheduledTask -TaskName "Backup Cantina Nube" `
                    -Action $actionNube -Trigger $triggerNube | Out-Null
            } else {
                Register-ScheduledTask -TaskName "Backup Cantina Nube" `
                    -Action $actionNube -Trigger $triggerNube -Settings $settings -Principal $principal `
                    -Description "Backup diario de cantina_tita a Google Drive via rclone" | Out-Null
            }
            Write-Host "    ✓ Tarea 'Backup Cantina Nube' registrada." -ForegroundColor Green
        }
    }
} else {
    Write-Host "4/4 Saltando backup a la nube (-SkipNube)." -ForegroundColor Gray
}

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== INSTALACION COMPLETADA ===" -ForegroundColor Green
Write-Host ""
Write-Host "Tareas registradas (ver en Task Scheduler):"
Write-Host "  - Backup Cantina Local  02:00 diario → $BackupDir"
if (-not $SkipNube) {
    Write-Host "  - Backup Cantina Nube   02:30 diario → gdrive:backups/cantina_tita"
}
Write-Host ""
Write-Host "Ejecutar backup ahora para verificar:"
Write-Host "  powershell -File `"$backupScript`""
Write-Host ""
Write-Host "Restaurar desde un backup:"
Write-Host "  .\restore_cantina.ps1 -BackupFile `"$BackupDir\cantina_<fecha>.dump`""
