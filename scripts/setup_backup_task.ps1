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
#
# IMPORTANTE -- las tareas corren como el usuario indicado en -BackupUser (por defecto, el
# usuario que ejecuta este script), NO como SYSTEM. Docker Desktop en Windows expone su motor
# unicamente a la sesion de usuario que lo inicio -- una tarea corriendo como SYSTEM no puede
# ver los contenedores aunque esten sanos, y el backup falla todos los dias con "contenedor no
# esta corriendo" pese a que si lo esta. El script pide la contrasena de Windows de ese usuario
# una sola vez, al registrar la tarea (queda guardada de forma segura por Task Scheduler, para
# poder correr sin que haya nadie con sesion iniciada).

param(
    [string]$ProjectRoot  = "D:\tita2026",
    [string]$BackupDir    = "D:\produccion_tita\backups\cantina",
    [string]$GpgRecipient = "",   # email GPG para cifrar el backup; vacio = sin cifrado
    [string]$BackupUser   = "$env:USERDOMAIN\$env:USERNAME",
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

# -- 0. Contrasena del usuario que va a ejecutar las tareas --
# Se pide una sola vez aqui; Task Scheduler la guarda cifrada para poder correr
# la tarea sin que haya una sesion de Windows iniciada.
Write-Host "Las tareas van a correr como '$BackupUser' (necesario para que puedan ver Docker Desktop)." -ForegroundColor Yellow
$securePassword = Read-Host "Contrasena de Windows para $BackupUser" -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
if (-not $plainPassword) {
    Write-Error "No se ingreso una contrasena. Abortando."
    exit 1
}
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

# Corre como $BackupUser (no SYSTEM) -- Docker Desktop solo es visible para la
# sesion de usuario que lo inicio. "Run whether user is logged on or not" con
# contrasena guardada permite que funcione sin sesion interactiva abierta.
$existing = Get-ScheduledTask -TaskName "Backup Cantina Local" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "    Tarea ya existe -- actualizando..." -ForegroundColor Gray
    Set-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings `
        -User $BackupUser -Password $plainPassword | Out-Null
} else {
    Register-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings `
        -User $BackupUser -Password $plainPassword -RunLevel Highest `
        -Description "Backup diario de cantina_tita a $BackupDir via docker exec pg_dump" | Out-Null
}
Write-Host "    [OK] Tarea 'Backup Cantina Local' registrada (usuario: $BackupUser)." -ForegroundColor Green

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
                    -Action $actionNube -Trigger $triggerNube `
                    -User $BackupUser -Password $plainPassword | Out-Null
            } else {
                Register-ScheduledTask -TaskName "Backup Cantina Nube" `
                    -Action $actionNube -Trigger $triggerNube -Settings $taskSettings `
                    -User $BackupUser -Password $plainPassword -RunLevel Highest `
                    -Description "Backup diario de cantina_tita a Google Drive via rclone" | Out-Null
            }
            Write-Host "    [OK] Tarea 'Backup Cantina Nube' registrada (usuario: $BackupUser)." -ForegroundColor Green
        }
    }
}

# -- Limpiar la contrasena de la memoria del proceso --
$plainPassword = $null
[System.GC]::Collect()

# -- Resumen --
Write-Host ""
Write-Host "=== INSTALACION COMPLETADA ===" -ForegroundColor Green
Write-Host ""
Write-Host "Tareas registradas en Task Scheduler (usuario: $BackupUser):"
Write-Host "  - Backup Cantina Local  02:00 diario -> $BackupDir"
if (-not $SkipNube) {
    Write-Host "  - Backup Cantina Nube   02:30 diario -> gdrive:backups/cantina_tita (si rclone OK)"
}
Write-Host ""
Write-Host "IMPORTANTE: activar 'Start Docker Desktop when you sign in' en" -ForegroundColor Yellow
Write-Host "Docker Desktop > Settings > General, para que sobreviva a un reinicio del servidor." -ForegroundColor Yellow
Write-Host ""
Write-Host "Para ejecutar un backup ahora (prueba):"
Write-Host "  powershell -File `"$backupScript`""
Write-Host ""
Write-Host "Para restaurar desde un backup:"
Write-Host "  .\restore_cantina.ps1 -BackupFile `"$BackupDir\cantina_<fecha>.dump`""
