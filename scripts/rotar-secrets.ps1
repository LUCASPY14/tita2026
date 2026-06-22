# scripts/rotar-secrets.ps1 — Cantina Tita
#
# Rota la SECRET_KEY de Django en .env.production.
# Hace backup del .env actual antes de modificar.
# Reinicia el backend para que la nueva clave tome efecto.
#
# Uso:
#   .\scripts\rotar-secrets.ps1
#   .\scripts\rotar-secrets.ps1 -EnvFile backend\.env.staging -SkipRestart
#
# NOTA: Las claves de Bancard (BANCARD_PUBLIC_KEY, BANCARD_PRIVATE_KEY) son
# emitidas por Bancard y deben rotarse manualmente contactando a su soporte.
# Este script NO las modifica.

param(
    [string]$EnvFile     = "backend\.env.production",
    [switch]$SkipRestart = $false,
    [switch]$DryRun      = $false
)

$ErrorActionPreference = "Stop"

$line = "─" * 60
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  Rotación de SECRET_KEY — Cantina Tita" -ForegroundColor Cyan
Write-Host $line -ForegroundColor DarkGray

# ── 1. Verificar que el archivo existe ───────────────────────────
$envPath = Join-Path (Split-Path $PSScriptRoot) $EnvFile
if (-not (Test-Path $envPath)) {
    Write-Host ""
    Write-Host "  ERROR: No se encontró $envPath" -ForegroundColor Red
    Write-Host "  Creá el archivo desde: backend\.env.production.example" -ForegroundColor DarkGray
    exit 1
}

Write-Host ""
Write-Host "  Archivo  : $envPath" -ForegroundColor DarkGray

# ── 2. Leer contenido actual ──────────────────────────────────────
$content = Get-Content $envPath -Raw -Encoding utf8

# Extraer SECRET_KEY actual para mostrarla (solo primeros 12 chars)
$currentMatch = [regex]::Match($content, 'SECRET_KEY\s*=\s*(.+)')
$currentKey   = if ($currentMatch.Success) { $currentMatch.Groups[1].Value.Trim() } else { "(no encontrada)" }
$currentPreview = if ($currentKey.Length -ge 12) { $currentKey.Substring(0, 12) + "..." } else { $currentKey }
Write-Host "  Clave actual : $currentPreview" -ForegroundColor DarkGray

# ── 3. Generar nueva SECRET_KEY ───────────────────────────────────
Write-Host ""
Write-Host "  Generando nueva SECRET_KEY con Python..." -ForegroundColor Yellow

$newKey = & python -c "import secrets; print(secrets.token_urlsafe(50))" 2>&1
if ($LASTEXITCODE -ne 0 -or -not $newKey) {
    Write-Host "  ERROR: Python no disponible o falló al generar la clave." -ForegroundColor Red
    Write-Host "  Generá manualmente con:" -ForegroundColor DarkGray
    Write-Host '    python -c "import secrets; print(secrets.token_urlsafe(50))"' -ForegroundColor DarkGray
    exit 1
}

$newKey      = $newKey.Trim()
$newPreview  = $newKey.Substring(0, 12) + "..."
Write-Host "  Clave nueva  : $newPreview" -ForegroundColor Green

if ($DryRun) {
    Write-Host ""
    Write-Host "  [DryRun] No se realizaron cambios." -ForegroundColor Yellow
    Write-Host "  Nueva clave completa: $newKey" -ForegroundColor DarkGray
    exit 0
}

# ── 4. Backup del .env actual ─────────────────────────────────────
$timestamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$envPath.backup.$timestamp"
Copy-Item $envPath $backupPath
Write-Host "  Backup creado: $backupPath" -ForegroundColor DarkGray

# ── 5. Reemplazar SECRET_KEY en el archivo ────────────────────────
if ($content -match 'SECRET_KEY\s*=\s*.+') {
    $newContent = [regex]::Replace($content, '(SECRET_KEY\s*=\s*).+', "`${1}$newKey")
} else {
    # No existe la línea — agregarla al final
    $newContent = $content.TrimEnd() + "`nSECRET_KEY=$newKey`n"
    Write-Host "  ADVERTENCIA: SECRET_KEY no estaba en el archivo, se agregó al final." -ForegroundColor Yellow
}

Set-Content -Path $envPath -Value $newContent -Encoding utf8 -NoNewline

Write-Host ""
Write-Host "  SECRET_KEY actualizada correctamente." -ForegroundColor Green

# ── 6. Reiniciar backend ──────────────────────────────────────────
if (-not $SkipRestart) {
    Write-Host ""
    Write-Host "  Reiniciando backend para aplicar la nueva clave..." -ForegroundColor Yellow
    try {
        docker compose restart backend 2>&1 | Out-Null
        Start-Sleep 5

        # Verificar que el backend respondió
        $health = Invoke-WebRequest -Uri "http://localhost:8000/api/health/ready/" `
            -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $body = $health.Content | ConvertFrom-Json
        if ($body.status -eq "ready") {
            Write-Host "  Backend reiniciado y saludable." -ForegroundColor Green
        } else {
            Write-Host "  ADVERTENCIA: Backend respondió con status=$($body.status). Revisar logs." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ADVERTENCIA: No se pudo verificar el health check del backend." -ForegroundColor Yellow
        Write-Host "  Verificar manualmente: docker compose logs --tail=30 backend" -ForegroundColor DarkGray
    }
} else {
    Write-Host ""
    Write-Host "  (SkipRestart activo) Reiniciá el backend manualmente:" -ForegroundColor DarkGray
    Write-Host "    docker compose restart backend" -ForegroundColor DarkGray
}

# ── 7. Advertencias importantes ───────────────────────────────────
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  IMPORTANTE tras rotar la SECRET_KEY:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Todos los tokens JWT activos quedan invalidados." -ForegroundColor DarkGray
Write-Host "     Los usuarios deberán iniciar sesión nuevamente." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. Los tokens de recuperación de contraseña en curso" -ForegroundColor DarkGray
Write-Host "     quedarán inválidos." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. Las sesiones del Django Admin quedan cerradas." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Backup guardado en: $backupPath" -ForegroundColor DarkGray
Write-Host $line -ForegroundColor DarkGray
Write-Host ""
