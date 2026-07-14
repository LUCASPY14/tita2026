# scripts/setup_wal_archiving.ps1 — Cantina Tita
#
# Configura WAL (Write-Ahead Logging) archiving en PostgreSQL 15/16 nativo
# en Windows. Con WAL archiving, la ventana de pérdida de datos pasa de
# hasta 24 horas (intervalo entre pg_dump) a minutos.
#
# ── Qué hace este script ──────────────────────────────────────────────────────
#   1. Crea el directorio de archivos WAL
#   2. Modifica postgresql.conf para activar archiving
#   3. Recarga la configuración de PostgreSQL (pg_reload_conf)
#   4. Verifica que el archiving quedó activo
#
# ── Uso ──────────────────────────────────────────────────────────────────────
#   .\scripts\setup_wal_archiving.ps1
#   .\scripts\setup_wal_archiving.ps1 -WalDir "D:\wal_archive" -PgVersion "16"
#
# ── IMPORTANTE ───────────────────────────────────────────────────────────────
#   Para restaurar a un punto en el tiempo (PITR) tras un desastre:
#     1. Restaurar el último pg_dump (restore_cantina.ps1)
#     2. Aplicar los archivos WAL hasta el momento del incidente usando pg_waldump
#      o configurando recovery.conf / postgresql.conf (recovery_target_time)
#   Ver: https://www.postgresql.org/docs/current/continuous-archiving.html

param(
    [string]$WalDir    = "C:\wal_archive\cantina",
    [string]$PgVersion = "16",
    [string]$PgData    = "C:\Program Files\PostgreSQL\$PgVersion\data",
    [string]$PgBin     = "C:\Program Files\PostgreSQL\$PgVersion\bin",
    [string]$PgUser    = "postgres",
    [string]$PgPort    = "5432",
    [switch]$DryRun    = $false
)

$ErrorActionPreference = "Stop"

$line = "─" * 62
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  WAL Archiving Setup — Cantina Tita PostgreSQL $PgVersion" -ForegroundColor Cyan
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

# ── 1. Crear directorio WAL ───────────────────────────────────────────────────
Write-Host "  [1/4] Directorio WAL: $WalDir" -ForegroundColor Yellow
if (-not (Test-Path $WalDir)) {
    if (-not $DryRun) { New-Item -ItemType Directory -Path $WalDir -Force | Out-Null }
    Write-Host "    Creado." -ForegroundColor Green
} else {
    Write-Host "    Ya existe." -ForegroundColor Gray
}

# ── 2. Generar parámetros de postgresql.conf ──────────────────────────────────
# El archive_command usa copy de Windows; rclone puede usarse además para nube.
$archiveCmd  = "copy `"%p`" `"$WalDir\%f`""    # %p = path WAL, %f = filename
$pgconf      = Join-Path $PgData "postgresql.conf"

Write-Host ""
Write-Host "  [2/4] Parámetros a agregar en postgresql.conf:" -ForegroundColor Yellow
$newParams = @"

# ── WAL Archiving — configurado por setup_wal_archiving.ps1 ──────────────────
wal_level           = replica           # habilita WAL para archiving y replicación
archive_mode        = on                # activa el archiving de segmentos WAL
archive_command     = '$archiveCmd'     # comando para copiar cada segmento WAL
archive_timeout     = 300               # forzar un nuevo segmento cada 5 minutos
# ─────────────────────────────────────────────────────────────────────────────
"@
Write-Host $newParams -ForegroundColor DarkGray

if (-not $DryRun) {
    if (-not (Test-Path $pgconf)) {
        Write-Host "  ERROR: No se encontró $pgconf" -ForegroundColor Red
        Write-Host "  Verificar -PgData y -PgVersion." -ForegroundColor DarkGray
        exit 1
    }

    # Verificar si ya está configurado
    $contenido = Get-Content $pgconf -Raw
    if ($contenido -match "archive_mode\s*=\s*on") {
        Write-Host "    WAL archiving ya está configurado en postgresql.conf." -ForegroundColor Gray
    } else {
        Add-Content -Path $pgconf -Value $newParams -Encoding utf8
        Write-Host "    Parámetros agregados a postgresql.conf." -ForegroundColor Green
    }
}

# ── 3. Recargar configuración PostgreSQL ──────────────────────────────────────
Write-Host ""
Write-Host "  [3/4] Recargando configuración PostgreSQL..." -ForegroundColor Yellow
if (-not $DryRun) {
    try {
        $result = & (Join-Path $PgBin "psql.exe") `
            -h localhost -p $PgPort -U $PgUser `
            -c "SELECT pg_reload_conf();" -t 2>&1
        if ($result -match "t") {
            Write-Host "    pg_reload_conf() OK" -ForegroundColor Green
        } else {
            Write-Host "    Recargar manualmente: net stop postgresql-x64-$PgVersion && net start postgresql-x64-$PgVersion" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "    No se pudo ejecutar pg_reload_conf. Reiniciar el servicio PostgreSQL manualmente." -ForegroundColor Yellow
    }
}

# ── 4. Verificar estado del archiving ─────────────────────────────────────────
Write-Host ""
Write-Host "  [4/4] Verificando estado del archiving..." -ForegroundColor Yellow
if (-not $DryRun) {
    try {
        $status = & (Join-Path $PgBin "psql.exe") `
            -h localhost -p $PgPort -U $PgUser `
            -c "SELECT archived_count, failed_count, last_archived_wal, last_failed_wal FROM pg_stat_archiver;" `
            -t 2>&1
        Write-Host $status -ForegroundColor DarkGray
    } catch {
        Write-Host "    Verificar manualmente: SELECT * FROM pg_stat_archiver;" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host ""
Write-Host "  PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Reiniciar PostgreSQL si wal_level cambió:" -ForegroundColor DarkGray
Write-Host "       net stop postgresql-x64-$PgVersion" -ForegroundColor DarkGray
Write-Host "       net start postgresql-x64-$PgVersion" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. Verificar que los archivos WAL se están copiando a $WalDir" -ForegroundColor DarkGray
Write-Host "     (deberían aparecer archivos .000000 dentro de 5 minutos)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. Opcional — subir WALs a la nube con rclone:" -ForegroundColor DarkGray
Write-Host "     Modificar archive_command en postgresql.conf:" -ForegroundColor DarkGray
Write-Host '     archive_command = '"'"'copy "%p" "C:\wal_archive\cantina\%f" && rclone copyto "C:\wal_archive\cantina\%f" "gdrive:wal_archive/%f"'"'" -ForegroundColor DarkGray
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

if ($DryRun) { Write-Host "  [DryRun] No se realizaron cambios." -ForegroundColor Yellow }
