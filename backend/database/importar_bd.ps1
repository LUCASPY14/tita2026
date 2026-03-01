# Script para importar el esquema de la base de datos dbcantinatita
# Version: 3.0 - Con ruta completa de MySQL
# Fecha: Febrero 2026

param(
    [string]$MySQLUser = "root",
    [string]$MySQLHost = "localhost",
    [int]$MySQLPort = 3306
)

# Buscar MySQL
$mysqlPaths = @(
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
    "C:\xampp\mysql\bin\mysql.exe",
    "C:\wamp64\bin\mysql\mysql8.0.39\bin\mysql.exe"
)

$mysqlExe = $null
foreach ($path in $mysqlPaths) {
    if (Test-Path $path) {
        $mysqlExe = $path
        break
    }
}

if (-not $mysqlExe) {
    # Intentar buscar en PATH
    $mysqlCmd = Get-Command mysql -ErrorAction SilentlyContinue
    if ($mysqlCmd) {
        $mysqlExe = $mysqlCmd.Source
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Importador de Base de Datos" -ForegroundColor Cyan
Write-Host "  dbcantinatita - Cantina Tita" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si el archivo SQL existe
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$sqlFile = Join-Path $scriptPath "dbcantinatita_schema.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Host "[ERROR] No se encontro el archivo SQL:" -ForegroundColor Red
    Write-Host "   $sqlFile" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Archivo SQL encontrado" -ForegroundColor Green
$fileSize = (Get-Item $sqlFile).Length / 1KB
Write-Host "  Tamano: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Gray
Write-Host ""

if (-not $mysqlExe) {
    Write-Host "[ERROR] MySQL no encontrado" -ForegroundColor Red
    Write-Host ""
    Write-Host "Instale MySQL desde: https://dev.mysql.com/downloads/mysql/" -ForegroundColor Yellow
    Write-Host "O use MySQL Workbench para importar el archivo SQL manualmente" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Archivo a importar: $sqlFile" -ForegroundColor Cyan
    Write-Host ""
    pause
    exit 1
}

Write-Host "[OK] MySQL encontrado" -ForegroundColor Green
Write-Host "  Ruta: $mysqlExe" -ForegroundColor Gray
Write-Host ""

# Solicitar contrasena de MySQL
Write-Host "Ingrese la contrasena de MySQL para '$MySQLUser'@'$MySQLHost':" -ForegroundColor Cyan
Write-Host "(Dejar vacio si no tiene contrasena)" -ForegroundColor Gray
$MySQLPassword = Read-Host -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($MySQLPassword)
$MySQLPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

Write-Host ""
Write-Host "Conectando a MySQL..." -ForegroundColor Yellow

# Probar conexion
try {
    if ($MySQLPasswordPlain) {
        $testCmd = "& `"$mysqlExe`" -u $MySQLUser -p`"$MySQLPasswordPlain`" -h $MySQLHost -P $MySQLPort -e `"SELECT 1`" 2>&1"
    } else {
        $testCmd = "& `"$mysqlExe`" -u $MySQLUser -h $MySQLHost -P $MySQLPort -e `"SELECT 1`" 2>&1"
    }
    
    $testResult = Invoke-Expression $testCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudo conectar a MySQL" -ForegroundColor Red
        Write-Host "Error: $testResult" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error al conectar: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Conexion exitosa" -ForegroundColor Green
Write-Host ""

# Verificar si la base de datos ya existe
Write-Host "Verificando base de datos 'dbcantinatita'..." -ForegroundColor Yellow

if ($MySQLPasswordPlain) {
    $checkCmd = "& `"$mysqlExe`" -u $MySQLUser -p`"$MySQLPasswordPlain`" -h $MySQLHost -P $MySQLPort -e `"SHOW DATABASES LIKE 'dbcantinatita'`" -N 2>&1"
} else {
    $checkCmd = "& `"$mysqlExe`" -u $MySQLUser -h $MySQLHost -P $MySQLPort -e `"SHOW DATABASES LIKE 'dbcantinatita'`" -N 2>&1"
}

$dbExists = Invoke-Expression $checkCmd

if ($dbExists -match "dbcantinatita") {
    Write-Host ""
    Write-Host "[ADVERTENCIA] La base de datos ya existe!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Desea ELIMINARLA y recrearla? Se perderan TODOS los datos!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  [S] Si, eliminar y recrear" -ForegroundColor Gray
    Write-Host "  [N] No, cancelar (predeterminado)" -ForegroundColor Gray
    Write-Host ""
    $confirm = Read-Host "Opcion [S/N]"
    
    if ($confirm -ne "S" -and $confirm -ne "s") {
        Write-Host ""
        Write-Host "[CANCELADO] Operacion cancelada" -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host ""
    Write-Host "Eliminando base de datos..." -ForegroundColor Yellow
    
    if ($MySQLPasswordPlain) {
        $dropCmd = "& `"$mysqlExe`" -u $MySQLUser -p`"$MySQLPasswordPlain`" -h $MySQLHost -P $MySQLPort -e `"DROP DATABASE dbcantinatita`" 2>&1"
    } else {
        $dropCmd = "& `"$mysqlExe`" -u $MySQLUser -h $MySQLHost -P $MySQLPort -e `"DROP DATABASE dbcantinatita`" 2>&1"
    }
    
    $dropResult = Invoke-Expression $dropCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Base de datos eliminada" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] No se pudo eliminar: $dropResult" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IMPORTANDO ESQUEMA SQL..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esto puede tomar varios minutos..." -ForegroundColor Yellow
Write-Host "Por favor espere..." -ForegroundColor Yellow
Write-Host ""

# Importar el esquema SQL  
Write-Host "Ejecutando import..." -ForegroundColor Gray

# Usar el metodo source de MySQL (mas robusto)
$sourceCmd = "source $($sqlFile -replace '\\', '/')"

if ($MySQLPasswordPlain) {
    $importErrors = & $mysqlExe -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort -e $sourceCmd 2>&1
} else {
    $importErrors = & $mysqlExe -u $MySQLUser -h $MySQLHost -P $MySQLPort -e $sourceCmd 2>&1
}

# Filtrar solo errores reales (ignoring warnings de password)
$realErrors = $importErrors | Where-Object { $_ -match "ERROR" -and $_ -notmatch "Warning" }

$importSuccess = ($realErrors.Count -eq 0)

if ($importSuccess) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BASE DE DATOS CREADA EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Obtener estadisticas
    $countTablesQuery = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dbcantinatita' AND table_type = 'BASE TABLE'"
    
    if ($MySQLPasswordPlain) {
        $countCmd = "& `"$mysqlExe`" -u $MySQLUser -p`"$MySQLPasswordPlain`" -h $MySQLHost -P $MySQLPort -e `"$countTablesQuery`" -N 2>&1"
    } else {
        $countCmd = "& `"$mysqlExe`" -u $MySQLUser -h $MySQLHost -P $MySQLPort -e `"$countTablesQuery`" -N 2>&1"
    }
    
    $tableCount = Invoke-Expression $countCmd
    
    Write-Host "Base de datos: dbcantinatita" -ForegroundColor Cyan
    Write-Host "Tablas creadas: $tableCount" -ForegroundColor Gray
    Write-Host "Servidor: $MySQLHost`:$MySQLPort" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "[PROXIMOS PASOS]" -ForegroundColor Yellow
    Write-Host "1. python manage.py inspectdb > database/generated_models.py" -ForegroundColor Gray
    Write-Host "2. Separar modelos por app" -ForegroundColor Gray
    Write-Host "3. python manage.py migrate --fake-initial" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "[ERROR] Error al importar el esquema" -ForegroundColor Red
    Write-Host ""
    Write-Host "Errores encontrados:" -ForegroundColor Yellow
    $realErrors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    Write-Host ""
    Write-Host "Archivo: $sqlFile" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "Presione cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
