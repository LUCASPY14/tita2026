-- ==========================================
-- PROCEDIMIENTO DE RECOVERY/RESTORE
-- CANTINA TITA - SQL SERVER
-- ==========================================
-- Este script permite restaurar la base de datos titadb desde backups
-- Incluye varios escenarios de recovery
--
-- IMPORTANTE: Adaptar las rutas y nombres de archivo según tu entorno
-- ==========================================

USE master;
GO

-- ==========================================
-- ESCENARIO 1: RESTORE COMPLETO DESDE ÚLTIMO BACKUP FULL
-- ==========================================
-- Usar cuando: Necesitas restaurar a la última versión disponible

PRINT '==========================================';
PRINT 'ESCENARIO 1: Restore desde último FULL';
PRINT '==========================================';

-- 1. Obtener el último backup FULL
DECLARE @LastFullBackup NVARCHAR(500);

SELECT TOP 1 @LastFullBackup = physical_device_name
FROM msdb.dbo.backupset bs
INNER JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
WHERE bs.database_name = 'titadb'
  AND bs.type = 'D'  -- Full backup
ORDER BY bs.backup_finish_date DESC;

PRINT 'Último backup FULL: ' + ISNULL(@LastFullBackup, 'NO ENCONTRADO');

-- 2. Poner la BD en modo SINGLE_USER para evitar conexiones activas
ALTER DATABASE titadb SET SINGLE_USER WITH ROLLBACK IMMEDIATE;

-- 3. Restaurar el backup FULL con NORECOVERY (para poder aplicar logs después)
RESTORE DATABASE titadb
FROM DISK = @LastFullBackup
WITH NORECOVERY,
     REPLACE,
     STATS = 10;

PRINT '✅ Backup FULL restaurado';
GO

-- ==========================================
-- ESCENARIO 2: APLICAR TRANSACTION LOGS
-- ==========================================
-- Aplicar todos los transaction logs después del backup FULL

PRINT '==========================================';
PRINT 'ESCENARIO 2: Aplicando Transaction Logs';
PRINT '==========================================';

-- Cursor para iterar sobre todos los logs en orden
DECLARE @LogFile NVARCHAR(500);
DECLARE @LogBackupDate DATETIME;

DECLARE log_cursor CURSOR FOR
SELECT physical_device_name, backup_start_date
FROM msdb.dbo.backupset bs
INNER JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
WHERE bs.database_name = 'titadb'
  AND bs.type = 'L'  -- Log backup
  AND bs.backup_start_date > (
      SELECT MAX(backup_start_date)
      FROM msdb.dbo.backupset
      WHERE database_name = 'titadb' AND type = 'D'
  )
ORDER BY bs.backup_start_date ASC;

OPEN log_cursor;
FETCH NEXT FROM log_cursor INTO @LogFile, @LogBackupDate;

WHILE @@FETCH_STATUS = 0
BEGIN
    PRINT 'Aplicando log: ' + @LogFile + ' (Fecha: ' + CONVERT(VARCHAR, @LogBackupDate, 120) + ')';
    
    RESTORE LOG titadb
    FROM DISK = @LogFile
    WITH NORECOVERY,
         STATS = 10;
    
    FETCH NEXT FROM log_cursor INTO @LogFile, @LogBackupDate;
END;

CLOSE log_cursor;
DEALLOCATE log_cursor;

PRINT '✅ Transaction Logs aplicados';
GO

-- ==========================================
-- ESCENARIO 3: FINALIZAR RECOVERY
-- ==========================================

PRINT '==========================================';
PRINT 'ESCENARIO 3: Finalizando Recovery';
PRINT '==========================================';

-- Finalizar la restauración (poner BD en estado ONLINE)
RESTORE DATABASE titadb WITH RECOVERY;

-- Volver a modo MULTI_USER
ALTER DATABASE titadb SET MULTI_USER;

PRINT '✅ Recovery completado';
PRINT '✅ Base de datos titadb restaurada y ONLINE';
GO

-- ==========================================
-- ESCENARIO 4: POINT-IN-TIME RECOVERY
-- ==========================================
-- Comentar arriba y usar este script para restaurar a un punto específico en el tiempo

/*
PRINT '==========================================';
PRINT 'ESCENARIO 4: Point-in-Time Recovery';
PRINT '==========================================';

DECLARE @RestoreToDate DATETIME;
SET @RestoreToDate =  '2026-04-12 14:30:00';  -- CAMBIAR A LA FECHA DESEADA

PRINT 'Restaurando a: ' + CONVERT(VARCHAR, @RestoreToDate, 120);

-- 1. Poner en SINGLE_USER
ALTER DATABASE titadb SET SINGLE_USER WITH ROLLBACK IMMEDIATE;

-- 2. Restaurar último FULL antes de la fecha objetivo
DECLARE @FullBackupFile NVARCHAR(500);

SELECT TOP 1 @FullBackupFile = physical_device_name
FROM msdb.dbo.backupset bs
INNER JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
WHERE bs.database_name = 'titadb'
  AND bs.type = 'D'
  AND bs.backup_finish_date <= @RestoreToDate
ORDER BY bs.backup_finish_date DESC;

RESTORE DATABASE titadb
FROM DISK = @FullBackupFile
WITH NORECOVERY,
     REPLACE,
     STATS = 10;

-- 3. Aplicar logs hasta la fecha objetivo
DECLARE @LogCursor CURSOR;
DECLARE @CurrentLogFile NVARCHAR(500);

SET @LogCursor = CURSOR FOR
SELECT physical_device_name
FROM msdb.dbo.backupset bs
INNER JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
WHERE bs.database_name = 'titadb'
  AND bs.type = 'L'
  AND bs.backup_start_date >= (SELECT backup_finish_date FROM msdb.dbo.backupset WHERE physical_device_name = @FullBackupFile)
  AND bs.backup_start_date <= @RestoreToDate
ORDER BY bs.backup_start_date ASC;

OPEN @LogCursor;
FETCH NEXT FROM @LogCursor INTO @CurrentLogFile;

WHILE @@FETCH_STATUS = 0
BEGIN
    RESTORE LOG titadb
    FROM DISK = @CurrentLogFile
    WITH NORECOVERY,
         STOPAT = @RestoreToDate,
         STATS = 10;
    
    FETCH NEXT FROM @LogCursor INTO @CurrentLogFile;
END;

CLOSE @LogCursor;
DEALLOCATE @LogCursor;

-- 4. Finalizar
RESTORE DATABASE titadb WITH RECOVERY;
ALTER DATABASE titadb SET MULTI_USER;

PRINT '✅ Point-in-Time Recovery completado';
*/

-- ==========================================
-- VERIFICAR ESTADO DE LA BASE DE DATOS
-- ==========================================

PRINT '';
PRINT '====================================';
PRINT 'VERIFICACIÓN FINAL';
PRINT '====================================';

SELECT 
    name,
    state_desc AS 'Estado',
    recovery_model_desc AS 'Recovery Model',
    user_access_desc AS 'User Access'
FROM sys.databases
WHERE name = 'titadb';

-- Verificar integridad
DBCC CHECKDB(titadb) WITH NO_INFOMSGS;

PRINT '';
PRINT '✅ Proceso de restauración completado exitosamente';
PRINT '';
GO
