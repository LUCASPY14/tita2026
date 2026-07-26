# backup_cantina.ps1
# Backup logico diario de cantina_tita via docker exec (PostgreSQL en Docker).
# Configurar como tarea programada de Windows -- ejecutar a las 02:00 diariamente.
#
# Para registrar la tarea:
#   .\scripts\setup_backup_task.ps1
#
# Para ejecutar manualmente:
#   .\backup_cantina.ps1
#
# Cifrado GPG (opcional):
#   .\backup_cantina.ps1 -GpgRecipient "admin@cantinatita.com"
#   Requiere: gpg instalado y la clave publica importada.
#   Para descifrar: gpg --output backup.dump --decrypt backup.dump.gpg

param(
    [string]$ProjectRoot  = "D:\tita2026",
    [string]$BackupDir    = "D:\produccion_tita\backups\cantina",
    [int]   $Keep         = 30,
    [string]$GpgRecipient = ""
)

$FECHA   = Get-Date -Format "yyyyMMdd_HHmm"
$ARCHIVO = "$BackupDir\cantina_$FECHA.dump"
$LOG     = "$BackupDir\backup_$FECHA.log"
$TMP     = "/tmp/cantina_backup_$FECHA.dump"

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }

# Leer credenciales desde .env.production (nunca se guardan en el script)
$envFile = Join-Path $ProjectRoot "backend\.env.production"
if (-not (Test-Path $envFile)) {
    Write-Error "No se encontro $envFile. Verificar que el proyecto esta en $ProjectRoot."
    exit 1
}
$envLines = Get-Content $envFile
function Get-EnvVar([string]$name) {
    $line = $envLines | Where-Object { $_ -match "^${name}=" } | Select-Object -First 1
    if ($line) { return ($line -split "=", 2)[1].Trim() }
    return ""
}
$DB_NAME     = Get-EnvVar "DB_NAME"
$DB_USER     = Get-EnvVar "DB_USER"
$DB_PASSWORD = Get-EnvVar "DB_PASSWORD"

if (-not $DB_NAME -or -not $DB_USER -or -not $DB_PASSWORD) {
    Write-Error "Faltan DB_NAME, DB_USER o DB_PASSWORD en $envFile."
    exit 1
}

# Verificar que el contenedor postgres esta corriendo
$CONTAINER = "tita2026-postgres-1"
$pgState = (docker inspect --format "{{.State.Running}}" $CONTAINER 2>$null)
if ($pgState -ne "true") {
    "$(Get-Date) | ERROR | Contenedor '$CONTAINER' no esta corriendo" | Out-File $LOG -Encoding utf8
    Write-Error "Contenedor '$CONTAINER' no esta corriendo. Verificar: docker compose ps"
    exit 1
}

try {
    # 1. pg_dump dentro del contenedor → archivo temporal en /tmp del contenedor
    docker exec -e "PGPASSWORD=$DB_PASSWORD" $CONTAINER `
        pg_dump -U $DB_USER --format=custom --compress=9 -f $TMP $DB_NAME

    if ($LASTEXITCODE -ne 0) { throw "pg_dump fallo con codigo $LASTEXITCODE" }

    # 2. Copiar dump desde el contenedor al host
    docker cp "${CONTAINER}:${TMP}" $ARCHIVO
    if ($LASTEXITCODE -ne 0) { throw "docker cp fallo al copiar el dump al host" }

    # 3. Limpiar archivo temporal del contenedor
    docker exec $CONTAINER rm -f $TMP

    $sizeMB = [math]::Round((Get-Item $ARCHIVO).Length / 1MB, 2)
    "$(Get-Date) | OK | $ARCHIVO | $sizeMB MB" | Out-File $LOG -Encoding utf8

    # 4. Cifrado GPG (opcional)
    if ($GpgRecipient) {
        $gpgCmd = $null
        try { $gpgCmd = Get-Command gpg -ErrorAction Stop } catch {}

        if (-not $gpgCmd) {
            "$(Get-Date) | WARNING | GPG no disponible - backup sin cifrar" | Add-Content $LOG
            Write-Warning "gpg no esta instalado. Backup sin cifrar: $ARCHIVO"
        } else {
            $archivoGpg = "$ARCHIVO.gpg"
            & gpg --batch --yes --trust-model always `
                  --recipient $GpgRecipient `
                  --output $archivoGpg `
                  --encrypt $ARCHIVO

            if ($LASTEXITCODE -eq 0) {
                Remove-Item $ARCHIVO -Force
                $ARCHIVO = $archivoGpg
                $sizeGpg = [math]::Round((Get-Item $ARCHIVO).Length / 1MB, 2)
                "$(Get-Date) | GPG OK | $ARCHIVO | $sizeGpg MB" | Add-Content $LOG
                Write-Host "Backup cifrado GPG: $ARCHIVO ($sizeGpg MB)" -ForegroundColor Green
            } else {
                "$(Get-Date) | WARNING | gpg fallo - backup sin cifrar: $ARCHIVO" | Add-Content $LOG
                Write-Warning "Cifrado GPG fallo. Backup sin cifrar: $ARCHIVO"
            }
        }
    }

    # 5. Rotacion: eliminar backups con mas de $Keep dias
    Get-ChildItem "$BackupDir\cantina_*.dump", "$BackupDir\cantina_*.dump.gpg" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$Keep) } |
        Remove-Item -Force

    Write-Host "Backup OK: $ARCHIVO ($sizeMB MB)" -ForegroundColor Green

    # 6. Backup a la nube (opcional - requiere rclone)
    $scriptNube = Join-Path $ProjectRoot "scripts\backup_nube.ps1"
    if (Test-Path $scriptNube) {
        $rcloneOk = $null
        try { $rcloneOk = Get-Command rclone -ErrorAction Stop } catch {}
        if ($rcloneOk) {
            Write-Host "Subiendo a la nube..."
            & powershell -File $scriptNube -SoloUltimo
        }
    }

} catch {
    "$(Get-Date) | ERROR | $_" | Out-File $LOG -Encoding utf8
    Write-Error "Backup FALLIDO: $_"
    exit 1
}
