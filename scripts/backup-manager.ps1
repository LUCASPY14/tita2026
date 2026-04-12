# ==========================================
# CANTINA TITA - BACKUP MANAGER
# ==========================================
# Script PowerShell para gestionar backups de SQL Server
# Uso: .\backup-manager.ps1 -Action [setup|backup|restore|verify]
# ==========================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('setup', 'backup', 'restore', 'verify', 'list')]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$ServerName = "localhost",
    
    [Parameter(Mandatory=$false)]
    [string]$DatabaseName = "titadb",
    
    [Parameter(Mandatory=$false)]
    [string]$BackupType = "FULL",  # FULL, DIFF, LOG
    
    [Parameter(Mandatory=$false)]
    [string]$RestoreDate = $null
)

$ErrorActionPreference = "Stop"

# ==========================================
# FUNCIONES
# ==========================================

function Write-Header {
    param([string]$Title)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Test-SqlServerConnection {
    Write-Host "🔌 Verificando conexión a SQL Server..." -ForegroundColor Yellow
    
    try {
        $query = "SELECT @@VERSION"
        $result = Invoke-Sqlcmd -ServerInstance $ServerName -Query $query -TrustServerCertificate
        Write-Host "✅ Conexión exitosa" -ForegroundColor Green
        Write-Host "   Versión: $($result.Column1.Split("`n")[0])" -ForegroundColor Gray
        return $true
    }
    catch {
        Write-Host "❌ Error de conexión: $_" -ForegroundColor Red
        return $false
    }
}

function Setup-Backups {
    Write-Header "CONFIGURAR BACKUPS AUTOMÁTICOS"
    
    if (-not (Test-SqlServerConnection)) {
        throw "No se pudo conectar al servidor SQL"
    }
    
    $scriptPath = Join-Path $PSScriptRoot "sql\setup_sql_backups.sql"
    
    if (-not (Test-Path $scriptPath)) {
        throw "No se encontró el script: $scriptPath"
    }
    
    Write-Host "📄 Ejecutando script de configuración..." -ForegroundColor Yellow
    Write-Host "   Script: $scriptPath" -ForegroundColor Gray
    
    try {
        Invoke-Sqlcmd -ServerInstance $ServerName -InputFile $scriptPath -TrustServerCertificate -Verbose
        
        Write-Host "`n✅ Backups automáticos configurados correctamente" -ForegroundColor Green
        Write-Host "`nJobs creados:" -ForegroundColor Cyan
        Write-Host "  ✓ titadb_backup_full_daily    (Diario 2:00 AM)" -ForegroundColor Gray
        Write-Host "  ✓ titadb_backup_diff_every6h  (Cada 6 horas)" -ForegroundColor Gray
        Write-Host "  ✓ titadb_backup_log_every15min (Cada 15 min)" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Error al configurar backups: $_" -ForegroundColor Red
        throw
    }
}

function Run-ManualBackup {
    Write-Header "EJECUTAR BACKUP MANUAL"
    
    if (-not (Test-SqlServerConnection)) {
        throw "No se pudo conectar al servidor SQL"
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "D:\SQLBackups\$DatabaseName\Manual\"
    
    # Crear carpeta si no existe
    if (-not (Test-Path $backupPath)) {
        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    }
    
    $backupFile = Join-Path $backupPath "${DatabaseName}_manual_${timestamp}.bak"
    
    Write-Host "🔧 Tipo de backup: $BackupType" -ForegroundColor Yellow
    Write-Host "📁 Destino: $backupFile" -ForegroundColor Yellow
    
    $query = @"
DECLARE @StartTime DATETIME = GETDATE();

BACKUP DATABASE [$DatabaseName]
TO DISK = '$backupFile'
WITH COMPRESSION,
     STATS = 10,
     CHECKSUM,
     NAME = '$DatabaseName Manual Backup';

DECLARE @Duration INT = DATEDIFF(SECOND, @StartTime, GETDATE());
PRINT 'Backup completado en ' + CAST(@Duration AS VARCHAR) + ' segundos';
"@
    
    try {
        Invoke-Sqlcmd -ServerInstance $ServerName -Query $query -TrustServerCertificate -QueryTimeout 3600
        
        $fileInfo = Get-Item $backupFile
        $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        
        Write-Host "`n✅ Backup completado exitosamente" -ForegroundColor Green
        Write-Host "   Archivo: $backupFile" -ForegroundColor Gray
        Write-Host "   Tamaño: $sizeMB MB" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Error al ejecutar backup: $_" -ForegroundColor Red
        throw
    }
}

function Verify-Backups {
    Write-Header "VERIFICAR HISTORIAL DE BACKUPS"
    
    if (-not (Test-SqlServerConnection)) {
        throw "No se pudo conectar al servidor SQL"
    }
    
    $query = @"
SELECT TOP 20
    database_name AS 'Database',
    CASE type
        WHEN 'D' THEN 'Full'
        WHEN 'I' THEN 'Differential'
        WHEN 'L' THEN 'Transaction Log'
    END AS 'Type',
    backup_start_date AS 'Start',
    backup_finish_date AS 'Finish',
    DATEDIFF(SECOND, backup_start_date, backup_finish_date) AS 'Duration (s)',
    CAST(backup_size / 1024 / 1024 AS DECIMAL(10,2)) AS 'Size (MB)',
    CAST(compressed_backup_size / 1024 / 1024 AS DECIMAL(10,2)) AS 'Compressed (MB)',
    bmf.physical_device_name AS 'File'
FROM msdb.dbo.backupset bs
INNER JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
WHERE database_name = '$DatabaseName'
ORDER BY backup_start_date DESC;
"@
    
    try {
        $results = Invoke-Sqlcmd -ServerInstance $ServerName -Query $query -TrustServerCertificate
        
        Write-Host "📊 Últimos 20 backups de $DatabaseName :`n" -ForegroundColor Cyan
        $results | Format-Table -AutoSize
        
        # Estadísticas
        $lastFull = $results | Where-Object Type -eq 'Full' | Select-Object -First 1
        $lastLog = $results | Where-Object Type -eq 'Transaction Log' | Select-Object -First 1
        
        Write-Host "`n📈 Estadísticas:" -ForegroundColor Cyan
        if ($lastFull) {
            Write-Host "  Último FULL: $($lastFull.Finish)" -ForegroundColor Gray
        }
        if ($lastLog) {
            Write-Host "  Último LOG:  $($lastLog.Finish)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ Error al verificar backups: $_" -ForegroundColor Red
        throw
    }
}

function List-BackupFiles {
    Write-Header "LISTAR ARCHIVOS DE BACKUP"
    
    $basePath = "D:\SQLBackups\$DatabaseName\"
    
    if (-not (Test-Path $basePath)) {
        Write-Host "⚠️  La carpeta de backups no existe: $basePath" -ForegroundColor Yellow
        return
    }
    
    Write-Host "📁 Carpeta: $basePath`n" -ForegroundColor Cyan
   
    # Backups FULL
    $fullPath = Join-Path $basePath "Full"
    if (Test-Path $fullPath) {
        $fullFiles = Get-ChildItem $fullPath -Filter "*.bak" | Sort-Object LastWriteTime -Descending
        Write-Host "  FULL ($($fullFiles.Count) archivos):" -ForegroundColor Yellow
        $fullFiles | ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "    - $($_.Name) ($sizeMB MB) - $($_.LastWriteTime)" -ForegroundColor Gray
        }
    }
    
    # Backups LOG
    $logPath = Join-Path $basePath "Log"
    if (Test-Path $logPath) {
        $logFiles = Get-ChildItem $logPath -Filter "*.trn" | Sort-Object LastWriteTime -Descending | Select-Object -First 10
        Write-Host "`n  TRANSACTION LOG (últimos 10):" -ForegroundColor Yellow
        $logFiles | ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "    - $($_.Name) ($sizeMB MB) - $($_.LastWriteTime)" -ForegroundColor Gray
        }
    }
    
    # Calcular espacio total
    $totalSize = (Get-ChildItem $basePath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "`n  Espacio total: $([math]::Round($totalSize, 2)) GB" -ForegroundColor Cyan
}

function Restore-Database {
    Write-Header "RESTAURAR BASE DE DATOS"
    
    Write-Host "⚠️  ADVERTENCIA: Esta operación sobrescribirá la base de datos actual!" -ForegroundColor Red
    Write-Host "   Base de datos: $DatabaseName" -ForegroundColor Yellow
    
    $confirmation = Read-Host "`n¿Desea continuar? (escriba 'SI' para confirmar)"
    
    if ($confirmation -ne "SI") {
        Write-Host "❌ Operación cancelada" -ForegroundColor Yellow
        return
    }
    
    $scriptPath = Join-Path $PSScriptRoot "sql\restore_database.sql"
    
    if (-not (Test-Path $scriptPath)) {
        throw "No se encontró el script de restauración: $scriptPath"
    }
    
    Write-Host "`n📄 Ejecutando script de restauración..." -ForegroundColor Yellow
    
    try {
        Invoke-Sqlcmd -ServerInstance $ServerName -InputFile $scriptPath -TrustServerCertificate -QueryTimeout 7200 -Verbose
        
        Write-Host "`n✅ Base de datos restaurada correctamente" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error al restaurar: $_" -ForegroundColor Red
        throw
    }
}

# ==========================================
# MAIN
# ==========================================

Write-Host "`n🚀 CANTINA TITA - Backup Manager" -ForegroundColor Magenta
Write-Host "   Servidor: $ServerName" -ForegroundColor Gray
Write-Host "   Base de datos: $DatabaseName`n" -ForegroundColor Gray

try {
    switch ($Action) {
        'setup' {
            Setup-Backups
        }
        'backup' {
            Run-ManualBackup
        }
        'restore' {
            Restore-Database
        }
        'verify' {
            Verify-Backups
        }
        'list' {
            List-BackupFiles
        }
    }
    
    Write-Host "`n✅ Operación completada exitosamente`n" -ForegroundColor Green
}
catch {
    Write-Host "`n❌ Error: $_`n" -ForegroundColor Red
    exit 1
}
