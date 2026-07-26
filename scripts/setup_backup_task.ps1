# setup_backup_task.ps1
# Instala las tareas programadas de backup diario de Cantina Tita.
# Ejecutar UNA VEZ en el servidor de produccion como Administrador.
#
# Uso:
#   .\scripts\setup_backup_task.ps1
#
# Que registra:
#   "Backup Cantina Local"  -- 02:00 diario -- pg_dump via docker exec
#   "Backup Cantina Nube"   -- 02:30 diario -- sube el dump a Google Drive (si rclone instalado)
#
# No se necesita -DbPassword: las credenciales se leen de backend\.env.production en cada backup.

param(
    [string]$ProjectRoot  = "D:\tita2026",
    [string]$BackupDir    = "D:\produccion_tita\backups\cantina",
    [string]$GpgRecipient = "",   # email GPG para cifrar el backup; vacio = sin cifrado
    [switch]$SkipNube
)

# -- Verificar que se ejecuta como administrador --
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Este script debe ejecutarse como Administrador."
    Write-Host  "Abrir PowerShell como Administrador y volver a ejecutar."
    exit 1
}

# -- Verificar que .env.production existe (backup_cantina.ps1 lo necesita) --
$envFile = Join-Path $ProjectRoot "backend\.env.production"
if (-not (Test-Path $envFile)) {
    Write-Error "No se encontro $envFile. Completar la configuracion de produccion primero."
    exit 1
}

Write-Host "=== INSTALACION DE BACKUPS AUTOMATICOS - CANTINA TITA ===" -ForegroundColor Cyan
Write-Host ""

# -- 1. Crear directorio de backups --
Write-Host "1/3 Creando directorio de backups: $BackupDir" -ForegroundColor Yellow
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "    Directorio creado." -ForegroundColor Green
} else {
    Write-Host "    Ya existe." -ForegroundColor Gray
}

# -- 2. Registrar tarea: Backup Local (02:00 diario) --
Write-Host "2/3 Registrando tarea 'Backup Cantina Local' (02:00 diario)..." -ForegroundColor Yellow

$backupScript = Join-Path $ProjectRoot "backup_cantina.ps1"
if (-not (Test-Path $backupScript)) {
    Write-Warning "No se encontro $backupScript."
}

$gpgArg = if ($GpgRecipient) { " -GpgRecipient `"$GpgRecipient`"" } else { "" }
$taskAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -NoProfile -ExecutionPolicy Bypass -File `"$backupScript`" -ProjectRoot `"$ProjectRoot`"$gpgArg"

$taskTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"

$taskSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable

$taskPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$existing = Get-ScheduledTask -TaskName "Backup Cantina Local" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "    Tarea ya existe -- actualizando..." -ForegroundColor Gray
    Set-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings | Out-Null
} else {
    Register-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -Principal $taskPrincipal `
        -Description "Backup diario de cantina_tita a $BackupDir via docker exec pg_dump" | Out-Null
}
Write-Host "    [OK] Tarea 'Backup Cantina Local' registrada." -ForegroundColor Green

# -- 3. Registrar tarea: Backup Nube (02:30 diario, opcional) --
if ($SkipNube) {
    Write-Host "3/3 Saltando backup a la nube (-SkipNube)." -ForegroundColor Gray
} else {
    Write-Host "3/3 Registrando tarea 'Backup Cantina Nube' (02:30 diario)..." -ForegroundColor Yellow

    $nubeScript = Join-Path $ProjectRoot "scripts\backup_nube.ps1"
    if (-not (Test-Path $nubeScript)) {
        Write-Warning "    No se encontro $nubeScript. Saltando tarea de nube."
    } else {
        $rcloneOk = $null
        try { $rcloneOk = Get-Command rclone -ErrorAction Stop } catch {}

        if (-not $rcloneOk) {
            Write-Warning "    rclone no encontrado en PATH."
            Write-Warning "    Instalar desde https://rclone.org y configurar remote 'gdrive'."
            Write-Warning "    Luego volver a ejecutar este script para registrar la tarea de nube."
        } else {
            $nubeArg = "-NonInteractive -NoProfile -ExecutionPolicy Bypass -File `"$nubeScript`" -SoloUltimo"
            if ($GpgRecipient) { $nubeArg += " -RequireEncrypted" }
            $actionNube  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $nubeArg
            $triggerNube = New-ScheduledTaskTrigger -Daily -At "02:30"

            $existingNube = Get-ScheduledTask -TaskName "Backup Cantina Nube" -ErrorAction SilentlyContinue
            if ($existingNube) {
                Set-ScheduledTask -TaskName "Backup Cantina Nube" `
                    -Action $actionNube -Trigger $triggerNube | Out-Null
            } else {
                Register-ScheduledTask -TaskName "Backup Cantina Nube" `
                    -Action $actionNube -Trigger $triggerNube -Settings $taskSettings -Principal $taskPrincipal `
                    -Description "Backup diario de cantina_tita a Google Drive via rclone" | Out-Null
            }
            Write-Host "    [OK] Tarea 'Backup Cantina Nube' registrada." -ForegroundColor Green
        }
    }
}

# -- Resumen --
Write-Host ""
Write-Host "=== INSTALACION COMPLETADA ===" -ForegroundColor Green
Write-Host ""
Write-Host "Tareas registradas en Task Scheduler:"
Write-Host "  - Backup Cantina Local  02:00 diario -> $BackupDir"
if (-not $SkipNube) {
    Write-Host "  - Backup Cantina Nube   02:30 diario -> gdrive:backups/cantina_tita (si rclone OK)"
}
Write-Host ""
Write-Host "Para ejecutar un backup ahora (prueba):"
Write-Host "  powershell -File `"$backupScript`""
Write-Host ""
Write-Host "Para restaurar desde un backup:"
Write-Host "  .\restore_cantina.ps1 -BackupFile `"$BackupDir\cantina_<fecha>.dump`""
