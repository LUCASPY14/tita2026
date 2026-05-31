# backup_cantina.ps1
# Backup lógico diario de cantina_tita (PostgreSQL)
# Configurar como tarea programada de Windows — ejecutar a las 02:00 diariamente.
#
# Para registrar la tarea:
#   schtasks /Create /TN "Backup Cantina" /TR "powershell -File C:\backups\backup_cantina.ps1" /SC DAILY /ST 02:00 /RU SYSTEM

$DB       = "cantina_tita_dev"
$USER     = "postgres"
$HOST     = "localhost"
$PORT     = "5432"
$DIR      = "C:\backups\cantina"
$KEEP     = 30            # días a conservar
$FECHA    = Get-Date -Format "yyyyMMdd_HHmm"
$ARCHIVO  = "$DIR\cantina_$FECHA.sql.gz"
$LOG      = "$DIR\backup_$FECHA.log"

# Crear directorio si no existe
if (-not (Test-Path $DIR)) { New-Item -ItemType Directory -Path $DIR | Out-Null }

$env:PGPASSWORD = "TU_PASSWORD_AQUI"   # <-- reemplazar o usar .pgpass

try {
    # pg_dump + compresión
    & "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" `
        -h $HOST -p $PORT -U $USER `
        --format=custom --compress=9 `
        --file=$ARCHIVO `
        $DB

    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump falló con código $LASTEXITCODE"
    }

    $size = [math]::Round((Get-Item $ARCHIVO).Length / 1MB, 2)
    "$(Get-Date) | OK | $ARCHIVO | $size MB" | Out-File $LOG

    # Rotación: eliminar backups con más de $KEEP días
    Get-ChildItem "$DIR\cantina_*.sql.gz" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KEEP) } |
        Remove-Item -Force

    Write-Host "Backup OK: $ARCHIVO ($size MB)"

} catch {
    "$(Get-Date) | ERROR | $_" | Out-File $LOG
    Write-Error "Backup FALLIDO: $_"
    exit 1
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
