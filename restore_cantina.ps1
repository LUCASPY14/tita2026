# restore_cantina.ps1
# Restauracion de backup logico (pg_dump --format=custom) de cantina_tita.
# PostgreSQL corre en Docker -- usa docker exec para psql/pg_restore.
#
# Uso:
#   .\restore_cantina.ps1 -BackupFile "D:\produccion_tita\backups\cantina\cantina_20260726_0200.dump"
#
# ATENCION: este proceso elimina y recrea la base de datos.
# Asegurarse de que ningun usuario este usando la app antes de restaurar.

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,

    [string]$ProjectRoot = "D:\tita2026",
    [string]$DbName      = "cantina_tita"
)

# Leer credenciales desde .env.production
$envFile = Join-Path $ProjectRoot "backend\.env.production"
if (-not (Test-Path $envFile)) {
    Write-Error "No se encontro $envFile."
    exit 1
}
$envLines = Get-Content $envFile
function Get-EnvVar([string]$name) {
    $line = $envLines | Where-Object { $_ -match "^${name}=" } | Select-Object -First 1
    if ($line) { return ($line -split "=", 2)[1].Trim() }
    return ""
}
$DB_USER     = Get-EnvVar "DB_USER"
$DB_PASSWORD = Get-EnvVar "DB_PASSWORD"

if (-not $DB_USER -or -not $DB_PASSWORD) {
    Write-Error "Faltan DB_USER o DB_PASSWORD en $envFile."
    exit 1
}

if (-not (Test-Path $BackupFile)) {
    Write-Error "Archivo de backup no encontrado: $BackupFile"
    exit 1
}

# Verificar que el contenedor postgres esta corriendo
$CONTAINER = "tita2026-postgres-1"
$pgState = (docker inspect --format "{{.State.Running}}" $CONTAINER 2>$null)
if ($pgState -ne "true") {
    Write-Error "Contenedor '$CONTAINER' no esta corriendo. Verificar: docker compose ps"
    exit 1
}

# Manejar archivo cifrado GPG
$archivoParaRestaurar = $BackupFile
if ($BackupFile -like "*.gpg") {
    Write-Host "Detectado archivo GPG. Descifrando..." -ForegroundColor Yellow
    $archivoParaRestaurar = $BackupFile -replace "\.gpg$", ""
    & gpg --output $archivoParaRestaurar --decrypt $BackupFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error al descifrar el archivo GPG."
        exit 1
    }
    Write-Host "  Descifrado OK: $archivoParaRestaurar" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== RESTAURACION CANTINA TITA ===" -ForegroundColor Cyan
Write-Host "Archivo : $archivoParaRestaurar"
Write-Host "Base    : $DbName (en contenedor Docker 'postgres')"
Write-Host ""
Write-Host "ATENCION: Se eliminara y recreara la base '$DbName'." -ForegroundColor Yellow
$confirm = Read-Host "Escribir 'SI' para continuar"
if ($confirm -ne "SI") {
    Write-Host "Restauracion cancelada." -ForegroundColor Gray
    exit 0
}

$TMP_CONTAINER = "/tmp/cantina_restore.dump"

try {
    # 1. Detener backend y celery para liberar conexiones a la DB
    Write-Host ""
    Write-Host "1/6 Deteniendo backend y workers para liberar conexiones..." -ForegroundColor Yellow
    docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") stop backend celery celery-beat
    Write-Host "    OK" -ForegroundColor Green

    # 2. Copiar dump al contenedor
    Write-Host "2/6 Copiando backup al contenedor..." -ForegroundColor Yellow
    docker cp $archivoParaRestaurar "${CONTAINER}:${TMP_CONTAINER}"
    if ($LASTEXITCODE -ne 0) { throw "docker cp fallo." }
    Write-Host "    OK" -ForegroundColor Green

    # 3. Terminar conexiones activas y eliminar base
    Write-Host "3/6 Eliminando base existente..." -ForegroundColor Yellow
    docker exec -e "PGPASSWORD=$DB_PASSWORD" $CONTAINER psql -U $DB_USER -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DbName' AND pid <> pg_backend_pid();"
    docker exec -e "PGPASSWORD=$DB_PASSWORD" $CONTAINER psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DbName;"
    if ($LASTEXITCODE -ne 0) { throw "DROP DATABASE fallo." }
    Write-Host "    OK" -ForegroundColor Green

    # 4. Crear base vacia
    Write-Host "4/6 Creando base vacia..." -ForegroundColor Yellow
    docker exec -e "PGPASSWORD=$DB_PASSWORD" $CONTAINER psql -U $DB_USER -d postgres -c "CREATE DATABASE $DbName OWNER $DB_USER;"
    if ($LASTEXITCODE -ne 0) { throw "CREATE DATABASE fallo." }
    Write-Host "    OK" -ForegroundColor Green

    # 5. Restaurar dump
    Write-Host "5/6 Restaurando backup (puede tardar varios minutos)..." -ForegroundColor Yellow
    docker exec -e "PGPASSWORD=$DB_PASSWORD" $CONTAINER `
        pg_restore -U $DB_USER -d $DbName `
        --clean --if-exists --no-owner --no-privileges `
        $TMP_CONTAINER
    if ($LASTEXITCODE -ne 0) { throw "pg_restore fallo con codigo $LASTEXITCODE." }
    docker exec $CONTAINER rm -f $TMP_CONTAINER
    Write-Host "    OK" -ForegroundColor Green

    # 6. Levantar servicios y aplicar migraciones pendientes
    Write-Host "6/6 Levantando servicios y aplicando migraciones..." -ForegroundColor Yellow
    docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") start backend celery celery-beat
    Start-Sleep -Seconds 10
    docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") run --rm backend python manage.py migrate --noinput
    Write-Host "    OK" -ForegroundColor Green

    Write-Host ""
    Write-Host "=== RESTAURACION COMPLETADA ===" -ForegroundColor Green
    Write-Host "Verificar que la app responde: http://localhost/api/health/"

} catch {
    Write-Host ""
    Write-Host "=== RESTAURACION FALLIDA ===" -ForegroundColor Red
    Write-Error $_

    Write-Host ""
    Write-Host "Intentando levantar los servicios nuevamente..." -ForegroundColor Yellow
    docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") start backend celery celery-beat
    exit 1
} finally {
    # Limpiar archivo descifrado temporalmente si se genero
    if ($BackupFile -like "*.gpg" -and (Test-Path $archivoParaRestaurar)) {
        Remove-Item $archivoParaRestaurar -Force -ErrorAction SilentlyContinue
    }
}
