# backup_cantina.ps1
# Backup logico diario de cantina_tita (PostgreSQL)
# Configurar como tarea programada de Windows -- ejecutar a las 02:00 diariamente.
#
# Para registrar la tarea:
#   .\scripts\setup_backup_task.ps1 -DbPassword (Read-Host -AsSecureString) -GpgRecipient "admin@cantinatita.com"
#
# Cifrado GPG:
#   .\backup_cantina.ps1 -GpgRecipient "admin@cantinatita.com"
#   Requiere: gpg instalado y la clave publica importada.
#   Para descifrar: gpg --output backup.dump --decrypt backup.dump.gpg

param(
    [string]$DbName       = "cantina_tita",
    [string]$PgUser       = "postgres",
    [string]$PgHost       = "localhost",
    [string]$PgPort       = "5432",
    [string]$PgBin        = "C:\Program Files\PostgreSQL\16\bin",
    [string]$BackupDir    = "D:\produccion_tita\backups\cantina",
    [int]   $Keep         = 30,
    [string]$GpgRecipient = ""
)

$FECHA   = Get-Date -Format "yyyyMMdd_HHmm"
$ARCHIVO = "$BackupDir\cantina_$FECHA.dump"
$LOG     = "$BackupDir\backup_$FECHA.log"

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }

if (-not $env:PGPASSWORD) {
    $pgpass = Join-Path $env:APPDATA "postgresql\pgpass.conf"
    if (-not (Test-Path $pgpass)) {
        Write-Error "Sin credenciales. Ejecutar: scripts\setup_pgpass.ps1 -Password <password>"
        exit 1
    }
}

try {
    & (Join-Path $PgBin "pg_dump.exe") `
        -h $PgHost -p $PgPort -U $PgUser `
        --format=custom --compress=9 `
        --file=$ARCHIVO `
        $DbName

    if ($LASTEXITCODE -ne 0) { throw "pg_dump fallo con codigo $LASTEXITCODE" }

    $sizeMB = [math]::Round((Get-Item $ARCHIVO).Length / 1MB, 2)
    "$(Get-Date) | OK | $ARCHIVO | $sizeMB MB" | Out-File $LOG -Encoding utf8

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

    # Rotacion: eliminar backups con mas de $Keep dias
    Get-ChildItem "$BackupDir\cantina_*.dump", "$BackupDir\cantina_*.dump.gpg" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$Keep) } |
        Remove-Item -Force

    Write-Host "Backup OK: $ARCHIVO ($sizeMB MB)" -ForegroundColor Green

    # Backup a la nube (opcional - requiere rclone)
    $scriptNube = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "scripts\backup_nube.ps1"
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
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
