# restore_cantina.ps1
# Restauración de backup lógico (pg_dump --format=custom) de cantina_tita.
# Usar para la prueba mensual o ante un desastre real.
#
# Uso:
#   .\restore_cantina.ps1 -BackupFile "C:\backups\cantina\cantina_20260531_0200.sql.gz"
#
# Prerequisito: el archivo fue generado por backup_cantina.ps1 con --format=custom

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,

    [string]$DbName   = "cantina_tita",
    [string]$PgUser   = "postgres",
    [string]$PgHost   = "localhost",
    [string]$PgPort   = "5432",
    [string]$PgBin    = "C:\Program Files\PostgreSQL\16\bin"
)

$psql         = Join-Path $PgBin "psql.exe"
$pgRestore    = Join-Path $PgBin "pg_restore.exe"
$setupSql     = Join-Path $PSScriptRoot "scripts\setup_autovacuum.sql"
$dropLikeSql  = Join-Path $PSScriptRoot "scripts\drop_like_fk_indexes.sql"

# --- validaciones previas -------------------------------------------------------

if (!(Test-Path $BackupFile)) {
    Write-Error "Archivo de backup no encontrado: $BackupFile"
    exit 1
}

if (!(Test-Path $psql)) {
    Write-Error "psql.exe no encontrado en $PgBin. Ajustar -PgBin."
    exit 1
}

Write-Host "=== RESTAURACION CANTINA TITA ===" -ForegroundColor Cyan
Write-Host "Archivo : $BackupFile"
Write-Host "Base    : $DbName en $PgHost`:$PgPort"
Write-Host ""

# Credenciales: configurar con scripts\setup_pgpass.ps1 antes del primer uso.
if ($env:PGPASSWORD) {
    Write-Host "Usando PGPASSWORD desde variable de entorno."
} elseif (-not (Test-Path (Join-Path $env:APPDATA "postgresql\pgpass.conf"))) {
    Write-Error "No hay credenciales configuradas. Ejecutar: scripts\setup_pgpass.ps1 -Password <password>"
    exit 1
}

try {
    # 1. Terminar conexiones activas a la base objetivo
    Write-Host "1/5 Terminando conexiones activas..." -ForegroundColor Yellow
    & $psql -h $PgHost -p $PgPort -U $PgUser -d postgres -c @"
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DbName' AND pid <> pg_backend_pid();
"@
    if ($LASTEXITCODE -ne 0) { throw "No se pudo terminar conexiones activas." }

    # 2. Eliminar base existente
    Write-Host "2/5 Eliminando base existente..." -ForegroundColor Yellow
    & $psql -h $PgHost -p $PgPort -U $PgUser -d postgres -c "DROP DATABASE IF EXISTS $DbName;"
    if ($LASTEXITCODE -ne 0) { throw "DROP DATABASE falló." }

    # 3. Crear base vacía
    Write-Host "3/5 Creando base vacía..." -ForegroundColor Yellow
    & $psql -h $PgHost -p $PgPort -U $PgUser -d postgres -c "CREATE DATABASE $DbName OWNER $PgUser;"
    if ($LASTEXITCODE -ne 0) { throw "CREATE DATABASE falló." }

    # 4. Restaurar dump
    Write-Host "4/5 Restaurando backup (puede tardar varios minutos)..." -ForegroundColor Yellow
    & $pgRestore -h $PgHost -p $PgPort -U $PgUser -d $DbName `
        --clean --if-exists --no-owner --no-privileges --verbose `
        $BackupFile
    if ($LASTEXITCODE -ne 0) { throw "pg_restore falló con código $LASTEXITCODE." }

    # 5. Re-aplicar autovacuum tuning (se pierde al recrear la BD)
    if (Test-Path $setupSql) {
        Write-Host "5/6 Aplicando configuracion de autovacuum..." -ForegroundColor Yellow
        & $psql -h $PgHost -p $PgPort -U $PgUser -d $DbName -f $setupSql
        if ($LASTEXITCODE -ne 0) { throw "setup_autovacuum.sql falló." }
    } else {
        Write-Warning "5/6 setup_autovacuum.sql no encontrado en $setupSql — aplicar manualmente."
    }

    # 6. Eliminar índices _like sobre FK columns (Django los recrea en cada migrate)
    if (Test-Path $dropLikeSql) {
        Write-Host "6/6 Eliminando indices _like sobre FK columns..." -ForegroundColor Yellow
        & $psql -h $PgHost -p $PgPort -U $PgUser -d $DbName -f $dropLikeSql
        if ($LASTEXITCODE -ne 0) { throw "drop_like_fk_indexes.sql falló." }
    } else {
        Write-Warning "6/6 drop_like_fk_indexes.sql no encontrado en $dropLikeSql — aplicar manualmente."
    }

    Write-Host ""
    Write-Host "=== RESTAURACION COMPLETADA ===" -ForegroundColor Green
    Write-Host "Pasos manuales post-restauracion:"
    Write-Host "  1. python manage.py migrate          (migraciones pendientes)"
    Write-Host "  2. python manage.py check --deploy   (validar config de produccion)"
    Write-Host "  3. Verificar logs: db_health_check.sql seccion 2 y 3"

} catch {
    Write-Host ""
    Write-Host "=== RESTAURACION FALLIDA ===" -ForegroundColor Red
    Write-Error $_
    exit 1
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
