# Script para ejecutar el servidor de desarrollo React
# Rama: desarrollo
# Uso: .\run-dev-frontend.ps1

Write-Host "⚛️  Iniciando servidor React (rama desarrollo)..." -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path ".\package.json")) {
    Write-Host "❌ Error: package.json no encontrado en el directorio actual" -ForegroundColor Red
    Write-Host "   Asegúrate de ejecutar este script desde: D:\tita2026\frontend\" -ForegroundColor Yellow
    exit 1
}

# Verificar que node_modules existe
if (-not (Test-Path ".\node_modules")) {
    Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
    npm install
}

Write-Host ""
Write-Host "🌐 Iniciando servidor en http://localhost:3000" -ForegroundColor Green
Write-Host "   Presiona Ctrl+C para detener el servidor" -ForegroundColor Gray
Write-Host ""

# Ejecutar servidor
npm start
