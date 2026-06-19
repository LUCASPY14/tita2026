# backup_cantina.ps1
# Backup lógico diario de cantina_tita (PostgreSQL)
# Configurar como tarea programada de Windows — ejecutar a las 02:00 diariamente.
#
# Para registrar la tarea:
#   schtasks /Create /TN "Backup Cantina" /TR "powershell -File C:\backups\backup_cantina.ps1" /SC DAILY /ST 02:00 /RU SYSTEM
#
# Cifrado GPG (opcional):
#   .\backup_cantina.ps1 -GpgRecipient "admin@cantina.edu.py"
#   Requiere: gpg instalado y la clave pública del destinatario importada.
#   El .dump se cifra y el original se elimina; sólo queda el .dump.gpg.
#   Para descifrar: gpg --output backup.dump --decrypt backup.dump.gpg

param(
    [string]$DbName      = "cantina_tita",
    [string]$PgUser      = "postgres",
    [string]$PgHost      = "localhost",
    [string]$PgPort      = "5432",
    [string]$PgBin       = "C:\Program Files\PostgreSQL\16\bin",
    [string]$BackupDir   = "C:\backups\cantina",
    [int]   $Keep        = 30,
    [string]$GpgRecipient = ""   # email o key-ID GPG; vacío = sin cifrado
)

$DIR     = $BackupDir
$KEEP    = $Keep
$FECHA   = Get-Date -Format "yyyyMMdd_HHmm"
$ARCHIVO = "$DIR\cantina_$FECHA.dump"
$LOG     = "$DIR\backup_$FECHA.log"

# Crear directorio si no existe
if (-not (Test-Path $DIR)) { New-Item -ItemType Directory -Path $DIR | Out-Null }

# Credenciales: configurar con scripts\setup_pgpass.ps1 antes del primer uso.
# El archivo pgpass.conf en %APPDATA%\postgresql\ permite autenticación sin contraseña en texto plano.
if ($env:PGPASSWORD) {
    Write-Host "Usando PGPASSWORD desde variable de entorno."
} elseif (-not (Test-Path (Join-Path $env:APPDATA "postgresql\pgpass.conf"))) {
    Write-Error "No hay credenciales configuradas. Ejecutar: scripts\setup_pgpass.ps1 -Password <password>"
    exit 1
}

try {
    # pg_dump formato custom (compatible con pg_restore y restore_cantina.ps1)
    & (Join-Path $PgBin "pg_dump.exe") `
        -h $PgHost -p $PgPort -U $PgUser `
        --format=custom --compress=9 `
        --file=$ARCHIVO `
        $DbName

    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump falló con código $LASTEXITCODE"
    }

    $size = [math]::Round((Get-Item $ARCHIVO).Length / 1MB, 2)
    "$(Get-Date) | OK | $ARCHIVO | $size MB" | Out-File $LOG

    # ── Cifrado GPG (opcional) ───────────────────────────────────────────────
    if ($GpgRecipient) {
        $gpgCmd = $null
        try { $gpgCmd = Get-Command gpg -ErrorAction Stop } catch {}

        if (-not $gpgCmd) {
            "$(Get-Date) | WARNING | GPG no disponible — backup queda sin cifrar" | Add-Content $LOG
            Write-Warning "gpg no está instalado. El backup quedó sin cifrar: $ARCHIVO"
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
                Write-Host "Backup cifrado con GPG: $ARCHIVO ($sizeGpg MB)"
            } else {
                "$(Get-Date) | WARNING | gpg falló — backup sin cifrar: $ARCHIVO" | Add-Content $LOG
                Write-Warning "Cifrado GPG falló (exit $LASTEXITCODE). El backup quedó sin cifrar."
            }
        }
    }

    # Rotación: eliminar backups con más de $KEEP días (.dump y .dump.gpg)
    Get-ChildItem "$DIR\cantina_*.dump", "$DIR\cantina_*.dump.gpg" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KEEP) } |
        Remove-Item -Force

    Write-Host "Backup OK: $ARCHIVO ($size MB)"

    # ── Backup a la nube (opcional) ──────────────────────────────────────────
    # Se activa automáticamente si existe scripts\backup_nube.ps1 y rclone está
    # disponible. Configura rclone con: rclone config → remote "gdrive"
    $scriptNube = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "scripts\backup_nube.ps1"
    if (Test-Path $scriptNube) {
        $rcloneOk = $null
        try { $rcloneOk = Get-Command rclone -ErrorAction Stop } catch {}
        if ($rcloneOk) {
            Write-Host "Iniciando backup a la nube..."
            & powershell -File $scriptNube -SoloUltimo
        }
    }

} catch {
    "$(Get-Date) | ERROR | $_" | Out-File $LOG
    Write-Error "Backup FALLIDO: $_"
    exit 1
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
