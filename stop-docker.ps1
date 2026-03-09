# ========================================
# SCRIPT DE DETENCIÓN - CANTINA TITA
# ========================================

Write-Host "🛑 Deteniendo Sistema Cantina TITA..." -ForegroundColor Cyan
Write-Host ""

# Navegar al directorio del proyecto
$scriptPath = $PSScriptRoot
Set-Location $scriptPath

# Mostrar contenedores corriendo
Write-Host "📊 Contenedores activos:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Preguntar si quiere eliminar volúmenes
Write-Host "¿Quieres eliminar también los datos (base de datos, redis)? (y/n): " -ForegroundColor Yellow -NoNewline
$eliminarDatos = Read-Host

if ($eliminarDatos -eq "y" -or $eliminarDatos -eq "Y" -or $eliminarDatos -eq "s" -or $eliminarDatos -eq "S") {
    Write-Host ""
    Write-Host "⚠️  ADVERTENCIA: Se eliminarán TODOS los datos!" -ForegroundColor Red
    Write-Host "¿Estás seguro? (y/n): " -ForegroundColor Red -NoNewline
    $confirmacion = Read-Host
    
    if ($confirmacion -eq "y" -or $confirmacion -eq "Y" -or $confirmacion -eq "s" -or $confirmacion -eq "S") {
        Write-Host ""
        Write-Host "🗑️  Deteniendo y eliminando contenedores y volúmenes..." -ForegroundColor Red
        docker-compose down -v
    } else {
        Write-Host ""
        Write-Host "✋ Operación cancelada" -ForegroundColor Yellow
        pause
        exit
    }
} else {
    Write-Host ""
    Write-Host "🛑 Deteniendo contenedores (los datos se preservarán)..." -ForegroundColor Cyan
    docker-compose down
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Sistema detenido correctamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para volver a iniciar, ejecuta: .\start-docker.ps1" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Ocurrió un error al detener el sistema" -ForegroundColor Red
}

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
