# Script de verificación pre-importación
# Verifica que todo esté listo para importar la base de datos

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Verificación Pre-Importación" -ForegroundColor Cyan
Write-Host " Base de Datos: dbcantinatita" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# 1. Verificar archivo SQL
Write-Host "1. Verificando archivo SQL..." -ForegroundColor Yellow
$sqlFile = "database\dbcantinatita_schema.sql"
if (Test-Path $sqlFile) {
    $fileSize = (Get-Item $sqlFile).Length / 1KB
    Write-Host "   [OK] Archivo encontrado ($([math]::Round($fileSize, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Archivo NO encontrado: $sqlFile" -ForegroundColor Red
    $allGood = $false
}

# 2. Verificar MySQL
Write-Host ""
Write-Host "2. Verificando MySQL..." -ForegroundColor Yellow
$mysqlCommand = Get-Command mysql -ErrorAction SilentlyContinue
if ($mysqlCommand) {
    $mysqlVersion = mysql --version 2>&1
    Write-Host "   [OK] MySQL instalado" -ForegroundColor Green
    Write-Host "     $mysqlVersion" -ForegroundColor Gray
} else {
    Write-Host "   [ERROR] MySQL NO encontrado en PATH" -ForegroundColor Red
    $allGood = $false
}

# 3. Verificar configuración Django
Write-Host ""
Write-Host "3. Verificando configuración Django..." -ForegroundColor Yellow
$settingsFile = "backend\settings\development.py"
if (Test-Path $settingsFile) {
    $settingsContent = Get-Content $settingsFile -Raw
    if ($settingsContent -match "dbcantinatita") {
        Write-Host "   [OK] Configuración correcta (dbcantinatita)" -ForegroundColor Green
    } else {
        Write-Host "   [WARN] Advertencia: Verificar nombre de BD en settings" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [ERROR] Archivo de configuración NO encontrado" -ForegroundColor Red
    $allGood = $false
}

# 4. Verificar requirements.txt
Write-Host ""
Write-Host "4. Verificando dependencias Python..." -ForegroundColor Yellow
$requirementsFile = "requirements.txt"
if (Test-Path $requirementsFile) {
    $requirements = Get-Content $requirementsFile -Raw
    
    $checks = @{
        "Django" = $requirements -match "Django"
        "djangorestframework" = $requirements -match "djangorestframework"
        "mysqlclient" = $requirements -match "mysqlclient"
        "django-cors-headers" = $requirements -match "django-cors-headers"
    }
    
    $checksOk = $true
    foreach ($package in $checks.Keys) {
        if ($checks[$package]) {
            Write-Host "   [OK] $package" -ForegroundColor Green
        } else {
            Write-Host "   [ERROR] $package faltante" -ForegroundColor Red
            $checksOk = $false
        }
    }
    
    if (-not $checksOk) {
        $allGood = $false
    }
} else {
    Write-Host "   [ERROR] requirements.txt NO encontrado" -ForegroundColor Red
    $allGood = $false
}

# 5. Verificar estructura de directorios
Write-Host ""
Write-Host "5. Verificando estructura de directorios..." -ForegroundColor Yellow
$directories = @(
    "backend\apps",
    "backend\database",
    "backend\logs",
    "frontend\src"
)

foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "   [OK] $dir" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] $dir NO existe" -ForegroundColor Red
        $allGood = $false
    }
}

# Resumen final
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host " [OK] VERIFICACION EXITOSA" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Todo esta listo para importar la base de datos." -ForegroundColor Green
    Write-Host ""
    Write-Host "Proximo paso:" -ForegroundColor Cyan
    Write-Host "  .\database\import_database.ps1" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host " [ERROR] VERIFICACION FALLIDA" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Revisa los errores arriba y corrígelos antes de continuar." - ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Presione cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
