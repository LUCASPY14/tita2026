# setup_backup_task.ps1
# Instala las tareas programadas de backup diario de Cantina Tita.
# Ejecutar UNA VEZ en el servidor de produccion como Administrador.
#
# Uso:
#   .\scripts\setup_backup_task.ps1 -DbPassword "password_de_postgres"
#
# Que registra:
#   "Backup Cantina Local"  -- 02:00 diario -- pg_dump a C:\backups\cantina\
#   "Backup Cantina Nube"   -- 02:30 diario -- sube el dump a Google Drive (si rclone instalado)

param(
    [Parameter(Mandatory=$true)]
    [SecureString]$DbPassword,

    [string]$ProjectRoot = "C:\tita2026",
    [string]$BackupDir   = "C:\backups\cantina",
    [string]$PgBin       = "C:\Program Files\PostgreSQL\16\bin",
    [string]$PgUser      = "postgres",
    [string]$PgHost      = "localhost",
    [string]$PgPort      = "5432",
    [switch]$SkipNube
)

# Convertir SecureString a plain text para pgpass.conf (necesario para el archivo de credenciales de PostgreSQL)
$DbPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($DbPassword)
)

# -- Verificar que se ejecuta como administrador --
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Este script debe ejecutarse como Administrador."
    Write-Host  "Abrir PowerShell como Administrador y volver a ejecutar."
    exit 1
}

Write-Host "=== INSTALACION DE BACKUPS AUTOMATICOS - CANTINA TITA ===" -ForegroundColor Cyan
Write-Host ""

# -- 1. Crear directorio de backups --
Write-Host "1/4 Creando directorio de backups: $BackupDir" -ForegroundColor Yellow
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "    Directorio creado." -ForegroundColor Green
} else {
    Write-Host "    Ya existe." -ForegroundColor Gray
}

# -- 2. Configurar pgpass.conf para la cuenta SYSTEM --
Write-Host "2/4 Configurando pgpass.conf para la cuenta SYSTEM..." -ForegroundColor Yellow

$pgpassScript = Join-Path $ProjectRoot "scripts\setup_pgpass.ps1"
if (Test-Path $pgpassScript) {
    & powershell -File $pgpassScript -Password $DbPasswordPlain -PgUser $PgUser -PgHost $PgHost -PgPort $PgPort
    if ($LASTEXITCODE -ne 0) {
        Write-Error "setup_pgpass.ps1 fallo."
        exit 1
    }
}

$pgpassSystemDir  = "C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql"
$pgpassSystemFile = Join-Path $pgpassSystemDir "pgpass.conf"
if (-not (Test-Path $pgpassSystemDir)) {
    New-Item -ItemType Directory -Path $pgpassSystemDir -Force | Out-Null
}
$entry = "${PgHost}:${PgPort}:*:${PgUser}:${DbPasswordPlain}"
$entry | Out-File -FilePath $pgpassSystemFile -Encoding ascii -Force
Write-Host "    pgpass.conf configurado para SYSTEM: $pgpassSystemFile" -ForegroundColor Green

# -- 3. Registrar tarea: Backup Local (02:00 diario) --
Write-Host "3/4 Registrando tarea 'Backup Cantina Local' (02:00 diario)..." -ForegroundColor Yellow

$backupScript = Join-Path $ProjectRoot "backup_cantina.ps1"
if (-not (Test-Path $backupScript)) {
    Write-Warning "No se encontro $backupScript. La tarea se registrara igual; crear el script antes del primer backup."
}

$taskAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -NoProfile -File `"$backupScript`" -PgBin `"$PgBin`" -PgUser `"$PgUser`" -PgHost `"$PgHost`" -PgPort `"$PgPort`""

$taskTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"

$taskSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable

$taskPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$existingLocal = Get-ScheduledTask -TaskName "Backup Cantina Local" -ErrorAction SilentlyContinue
if ($existingLocal) {
    Write-Host "    Tarea ya existe -- actualizando..." -ForegroundColor Gray
    Set-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings | Out-Null
} else {
    Register-ScheduledTask -TaskName "Backup Cantina Local" `
        -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -Principal $taskPrincipal `
        -Description "Backup diario de cantina_tita a $BackupDir (pg_dump format custom)" | Out-Null
}
Write-Host "    [OK] Tarea 'Backup Cantina Local' registrada." -ForegroundColor Green

# -- 4. Registrar tarea: Backup Nube (02:30 diario, opcional) --
if ($SkipNube) {
    Write-Host "4/4 Saltando backup a la nube (-SkipNube)." -ForegroundColor Gray
} else {
    Write-Host "4/4 Registrando tarea 'Backup Cantina Nube' (02:30 diario)..." -ForegroundColor Yellow

    $nubeScript = Join-Path $ProjectRoot "scripts\backup_nube.ps1"
    if (-not (Test-Path $nubeScript)) {
        Write-Warning "    No se encontro $nubeScript. Saltando tarea de nube."
    } else {
        $rcloneOk = $null
        try {
            $rcloneOk = Get-Command rclone -ErrorAction Stop
        } catch {
            $rcloneOk = $null
        }

        if (-not $rcloneOk) {
            Write-Warning "    rclone no encontrado. Instalar desde https://rclone.org y configurar remote 'gdrive'."
            Write-Warning "    Luego volver a ejecutar este script para registrar la tarea de nube."
        } else {
            $actionNube  = New-ScheduledTaskAction -Execute "powershell.exe" `
                -Argument "-NonInteractive -NoProfile -File `"$nubeScript`" -SoloUltimo"
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
Write-Host "Para ejecutar un backup ahora:"
Write-Host "  powershell -File `"$backupScript`""
Write-Host ""
Write-Host "Para restaurar desde un backup:"
Write-Host "  .\restore_cantina.ps1 -BackupFile `"$BackupDir\cantina_<fecha>.dump`""
