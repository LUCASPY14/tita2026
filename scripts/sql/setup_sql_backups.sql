-- ==========================================
-- CONFIGURACIÓN DE BACKUPS AUTOMÁTICOS
-- CANTINA TITA - SQL SERVER
-- ==========================================
-- Este script configura backups automáticos para la base de datos titadb
-- Incluye: Backups FULL diarios, backups de LOG cada 15 minutos, y limpieza automática
--
-- PRERREQUISITOS:
-- 1. SQL Server Agent debe estar corriendo
-- 2. Permisos de sysadmin o db_backupoperator
-- 3. Carpetas de backup deben existir
--
-- EJECUCIÓN:
-- sqlcmd -S localhost -U sa -P <password> -i setup_sql_backups.sql
-- ==========================================

USE master;
GO

-- ==========================================
-- 1. CREAR CARPETAS DE BACKUP
-- ==========================================
PRINT '🔧 Creando carpetas de backup...';

DECLARE @BackupPath NVARCHAR(500) = 'D:\SQLBackups\titadb\';

-- Crear carpetas si no existen
EXEC master.dbo.xp_create_subdir @BackupPath;
EXEC master.dbo.xp_create_subdir CONCAT(@BackupPath, 'Full');
EXEC master.dbo.xp_create_subdir CONCAT(@BackupPath, 'Log');
EXEC master.dbo.xp_create_subdir CONCAT(@BackupPath, 'Diff');

PRINT '✅ Carpetas creadas';
GO

-- ==========================================
-- 2. CONFIGURAR RECOVERY MODEL
-- ==========================================
PRINT '🔧 Configurando recovery model...';

USE master;
GO

IF EXISTS (SELECT 1 FROM sys.databases WHERE name = 'titadb')
BEGIN
    ALTER DATABASE titadb SET RECOVERY FULL;
    PRINT '✅ Recovery model configurado a FULL';
END
ELSE
BEGIN
    PRINT '❌ ERROR: Base de datos titadb no existe';
    RAISERROR('Database titadb does not exist', 16, 1);
END
GO

-- ==========================================
-- 3. BACKUP INICIAL FULL
-- ==========================================
PRINT '🔧 Creando backup inicial...';

DECLARE @InitialBackup NVARCHAR(500);
SET @InitialBackup = 'D:\SQLBackups\titadb\Full\titadb_initial_' + 
                     CONVERT(VARCHAR(8), GETDATE(), 112) + '_' +
                     REPLACE(CONVERT(VARCHAR(8), GETDATE(), 108), ':', '') + '.bak';

BACKUP DATABASE titadb 
TO DISK = @InitialBackup
WITH INIT, 
     COMPRESSION,
     STATS = 10,
     CHECKSUM,
     NAME = 'titadb Initial Full Backup';

PRINT '✅ Backup inicial creado: ' + @InitialBackup;
GO

-- ==========================================
-- 4. JOB: BACKUP FULL DIARIO (2 AM)
-- ==========================================
PRINT '🔧 Creando job de backup FULL diario...';

USE msdb;
GO

-- Eliminar job si existe
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = 'titadb_backup_full_daily')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = 'titadb_backup_full_daily';
    PRINT '  - Job anterior eliminado';
END

-- Crear job
EXEC msdb.dbo.sp_add_job
    @job_name = N'titadb_backup_full_daily',
    @enabled = 1,
    @description = N'Backup FULL diario de titadb a las 2 AM',
    @category_name = N'Database Maintenance',
    @owner_login_name = N'sa';

-- Agregar step
EXEC msdb.dbo.sp_add_jobstep
    @job_name = N'titadb_backup_full_daily',
    @step_name = N'Backup Full Database',
    @subsystem = N'TSQL',
    @command = N'
DECLARE @BackupFile NVARCHAR(500);
DECLARE @BackupDate VARCHAR(17);
DECLARE @OldDate VARCHAR(10);

-- Formato: titadb_YYYYMMDD_HHMMSS.bak
SET @BackupDate = CONVERT(VARCHAR(8), GETDATE(), 112) + ''_'' + 
                  REPLACE(CONVERT(VARCHAR(8), GETDATE(), 108), '':'', '''');
SET @BackupFile = ''D:\SQLBackups\titadb\Full\titadb_'' + @BackupDate + ''.bak'';

-- Realizar backup
PRINT ''Iniciando backup FULL: '' + @BackupFile;

BACKUP DATABASE titadb 
TO DISK = @BackupFile
WITH INIT, 
     COMPRESSION,
     STATS = 10,
     CHECKSUM,
     NAME = ''titadb Full Backup'',
     DESCRIPTION = ''Backup automático diario'';

PRINT ''✅ Backup FULL completado'';

-- Borrar backups de más de 7 días
SET @OldDate = CONVERT(VARCHAR(10), DATEADD(DAY, -7, GETDATE()), 112);

EXECUTE master.dbo.xp_delete_file 
    0,
    N''D:\SQLBackups\titadb\Full'',
    N''bak'',
    @OldDate;

PRINT ''✅ Backups antiguos eliminados (>7 días)'';
',
    @database_name = N'master',
    @on_success_action = 1,  -- Quit with success
    @on_fail_action = 2;     -- Quit with failure

-- Crear schedule (diario a las 2 AM)
EXEC msdb.dbo.sp_add_schedule
    @schedule_name = N'Daily_2AM',
    @freq_type = 4,              -- Daily
    @freq_interval = 1,          -- Every day
    @active_start_time = 020000; -- 2:00 AM

-- Attach schedule to job
EXEC msdb.dbo.sp_attach_schedule
    @job_name = N'titadb_backup_full_daily',
    @schedule_name = N'Daily_2AM';

-- Agregar job al servidor local
EXEC msdb.dbo.sp_add_jobserver
    @job_name = N'titadb_backup_full_daily',
    @server_name = N'(LOCAL)';

PRINT '✅ Job de backup FULL creado';
GO

-- ==========================================
-- 5. JOB: BACKUP LOG CADA 15 MINUTOS
-- ==========================================
PRINT '🔧 Creando job de backup LOG cada 15 min...';

-- Eliminar job si existe
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = 'titadb_backup_log_every15min')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = 'titadb_backup_log_every15min';
    PRINT '  - Job anterior eliminado';
END

-- Crear job
EXEC msdb.dbo.sp_add_job
    @job_name = N'titadb_backup_log_every15min',
    @enabled = 1,
    @description = N'Backup de transaction log de titadb cada 15 minutos',
    @category_name = N'Database Maintenance',
    @owner_login_name = N'sa';

-- Agregar step
EXEC msdb.dbo.sp_add_jobstep
    @job_name = N'titadb_backup_log_every15min',
    @step_name = N'Backup Transaction Log',
    @subsystem = N'TSQL',
    @command = N'
DECLARE @BackupFile NVARCHAR(500);
DECLARE @BackupDate VARCHAR(17);
DECLARE @OldDate VARCHAR(10);

-- Formato: titadb_log_YYYYMMDD_HHMMSS.trn
SET @BackupDate = CONVERT(VARCHAR(8), GETDATE(), 112) + ''_'' +
                  REPLACE(CONVERT(VARCHAR(8), GETDATE(), 108), '':'', '''');
SET @BackupFile = ''D:\SQLBackups\titadb\Log\titadb_log_'' + @BackupDate + ''.trn'';

-- Realizar backup del log
BACKUP LOG titadb
TO DISK = @BackupFile
WITH COMPRESSION,
     STATS = 10,
     CHECKSUM,
     NAME = ''titadb Transaction Log Backup'';

-- Borrar logs de más de 2 días
SET @OldDate = CONVERT(VARCHAR(10), DATEADD(DAY, -2, GETDATE()), 112);

EXECUTE master.dbo.xp_delete_file 
    0,
    N''D:\SQLBackups\titadb\Log'',
    N''trn'',
    @OldDate;
',
    @database_name = N'master',
    @on_success_action = 1,
    @on_fail_action = 2;

-- Crear schedule (cada 15 minutos)
EXEC msdb.dbo.sp_add_schedule
    @schedule_name = N'Every15Min',
    @freq_type = 4,                  -- Daily
    @freq_interval = 1,              -- Every day
    @freq_subday_type = 4,           -- Minutes
    @freq_subday_interval = 15,      -- Every 15 minutes
    @active_start_time = 000000,     -- Start at midnight
    @active_end_time = 235959;       -- End at 23:59:59

-- Attach schedule to job
EXEC msdb.dbo.sp_attach_schedule
    @job_name = N'titadb_backup_log_every15min',
    @schedule_name = N'Every15Min';

-- Agregar job al servidor local
EXEC msdb.dbo.sp_add_jobserver
    @job_name = N'titadb_backup_log_every15min',
    @server_name = N'(LOCAL)';

PRINT '✅ Job de backup LOG creado';
GO

-- ==========================================
-- 6. JOB: BACKUP DIFERENCIAL CADA 6 HORAS
-- ==========================================
PRINT '🔧 Creando job de backup DIFERENCIAL cada 6 horas...';

-- Eliminar job si existe
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = 'titadb_backup_diff_every6h')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = 'titadb_backup_diff_every6h';
    PRINT '  - Job anterior eliminado';
END

-- Crear job
EXEC msdb.dbo.sp_add_job
    @job_name = N'titadb_backup_diff_every6h',
    @enabled = 1,
    @description = N'Backup diferencial de titadb cada 6 horas',
    @category_name = N'Database Maintenance',
    @owner_login_name = N'sa';

-- Agregar step
EXEC msdb.dbo.sp_add_jobstep
    @job_name = N'titadb_backup_diff_every6h',
    @step_name = N'Backup Differential',
    @subsystem = N'TSQL',
    @command = N'
DECLARE @BackupFile NVARCHAR(500);
DECLARE @BackupDate VARCHAR(17);
DECLARE @OldDate VARCHAR(10);

SET @BackupDate = CONVERT(VARCHAR(8), GETDATE(), 112) + ''_'' +
                  REPLACE(CONVERT(VARCHAR(8), GETDATE(), 108), '':'', '''');
SET @BackupFile = ''D:\SQLBackups\titadb\Diff\titadb_diff_'' + @BackupDate + ''.bak'';

BACKUP DATABASE titadb
TO DISK = @BackupFile
WITH DIFFERENTIAL,
     COMPRESSION,
     STATS = 10,
     CHECKSUM,
     NAME = ''titadb Differential Backup'';

-- Borrar backups diferenciales de más de 3 días
SET @OldDate = CONVERT(VARCHAR(10), DATEADD(DAY, -3, GETDATE()), 112);

EXECUTE master.dbo.xp_delete_file 
    0,
    N''D:\SQLBackups\titadb\Diff'',
    N''bak'',
    @OldDate;
',
    @database_name = N'master',
    @on_success_action = 1,
    @on_fail_action = 2;

-- Crear schedule (cada 6 horas)
EXEC msdb.dbo.sp_add_schedule
    @schedule_name = N'Every6Hours',
    @freq_type = 4,
    @freq_interval = 1,
    @freq_subday_type = 8,           -- Hours
    @freq_subday_interval = 6,       -- Every 6 hours
    @active_start_time = 000000;

-- Attach schedule to job
EXEC msdb.dbo.sp_attach_schedule
    @job_name = N'titadb_backup_diff_every6h',
    @schedule_name = N'Every6Hours';

-- Agregar job al servidor local
EXEC msdb.dbo.sp_add_jobserver
    @job_name = N'titadb_backup_diff_every6h',
    @server_name = N'(LOCAL)';

PRINT '✅ Job de backup DIFERENCIAL creado';
GO

-- ==========================================
-- 7. VERIFICAR JOBS CREADOS
-- ==========================================
PRINT '';
PRINT '📋 RESUMEN DE JOBS CREADOS:';
PRINT '====================================';

SELECT 
    name AS 'Job Name',
    enabled AS 'Enabled',
    date_created AS 'Created',
    description AS 'Description'
FROM msdb.dbo.sysjobs
WHERE name LIKE 'titadb_backup%'
ORDER BY name;

PRINT '';
PRINT '====================================';
PRINT '✅ CONFIGURACIÓN COMPLETADA';
PRINT '====================================';
PRINT '';
PRINT 'Backups configurados:';
PRINT '  ✓ FULL:         Diario a las 2:00 AM (retención: 7 días)';
PRINT '  ✓ DIFERENCIAL:  Cada 6 horas (retención: 3 días)';
PRINT '  ✓ LOG:          Cada 15 minutos (retención: 2 días)';
PRINT '';
PRINT 'Carpetas de backup:';
PRINT '  📁 D:\SQLBackups\titadb\Full\';
PRINT '  📁 D:\SQLBackups\titadb\Diff\';
PRINT '  📁 D:\SQLBackups\titadb\Log\';
PRINT '';
PRINT 'Para verificar el estado de los jobs:';
PRINT '  EXEC msdb.dbo.sp_help_job @job_name = ''titadb_backup_full_daily'';';
PRINT '';
PRINT 'Para ejecutar un backup manualmente:';
PRINT '  EXEC msdb.dbo.sp_start_job @job_name = ''titadb_backup_full_daily'';';
PRINT '';
GO
