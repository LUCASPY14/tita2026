# scripts/smoke-test.ps1 — Cantina Tita
#
# Verifica que los servicios críticos responden correctamente tras un deploy.
# Uso independiente:
#   .\scripts\smoke-test.ps1
#   .\scripts\smoke-test.ps1 -BaseUrl http://192.168.1.100 -ApiUrl http://192.168.1.100:8000
#
# También es llamado automáticamente por deploy.ps1 al final del paso 7.

param(
    [string]$BaseUrl    = "http://localhost",
    [string]$ApiUrl     = "http://localhost:8000",
    [int]   $TimeoutSec = 10
)

$ErrorActionPreference = "Continue"
$Passed = 0
$Failed = 0

function Test-Endpoint {
    param(
        [string]$Label,
        [string]$Url,
        [int[]] $Expected = @(200),
        [string]$MustContain = ""
    )

    $code = 0
    $ok   = $false
    $msg  = ""

    try {
        $resp = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        $code = [int]$resp.StatusCode
        if ($Expected -contains $code) {
            if ($MustContain -and ($resp.Content -notmatch [regex]::Escape($MustContain))) {
                $msg = "body no contiene '$MustContain'"
            } else {
                $ok = $true
            }
        } else {
            $msg = "esperado $($Expected -join ' o '), recibido $code"
        }
    } catch {
        $webResp = $_.Exception.Response
        if ($null -ne $webResp) {
            $code = [int]$webResp.StatusCode
            if ($Expected -contains $code) {
                $ok = $true
            } else {
                $msg = "HTTP $code — esperado $($Expected -join ' o ')"
            }
        } else {
            $code = 0
            $msg  = "sin respuesta: $($_.Exception.Message.Split([char]10)[0])"
        }
    }

    if ($ok) {
        Write-Host ("    [OK] {0,-46} {1}" -f $Label, $code) -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host ("   [ERR] {0,-46} {1}  {2}" -f $Label, $code, $msg) -ForegroundColor Red
        $script:Failed++
    }
}

# ── Encabezado ────────────────────────────────────────────────────
$line = "─" * 60
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  Smoke Test — Cantina Tita" -ForegroundColor Cyan
Write-Host "  Backend : $ApiUrl" -ForegroundColor DarkGray
Write-Host "  Frontend: $BaseUrl" -ForegroundColor DarkGray
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

# ── 1. Health ────────────────────────────────────────────────────
Write-Host "  Health checks" -ForegroundColor Yellow
Test-Endpoint "Backend /api/health/"        "$ApiUrl/api/health/"   @(200) '"status"'
Test-Endpoint "Frontend (Nginx) /"          "$BaseUrl/"             @(200)
Test-Endpoint "Nginx → backend /api/health/" "$BaseUrl/api/health/" @(200) '"status"'

# ── 2. API — debe responder 401 sin token (no 500) ────────────────
Write-Host ""
Write-Host "  API endpoints — requieren auth (401 esperado)" -ForegroundColor Yellow
Test-Endpoint "JWT token endpoint"           "$ApiUrl/api/v1/usuarios/token/"                @(400, 401, 405)
Test-Endpoint "Productos catálogo"           "$ApiUrl/api/v1/productos/productos/"           @(401, 403)
Test-Endpoint "Core tarjetas"               "$ApiUrl/api/v1/core/tarjetas/"                @(401, 403)
Test-Endpoint "Contabilidad cajas"          "$ApiUrl/api/v1/contabilidad/cajas/"            @(401, 403)
Test-Endpoint "Clientes"                    "$ApiUrl/api/v1/clientes/clientes/"             @(401, 403)
Test-Endpoint "Almuerzos menú diario"       "$ApiUrl/api/v1/almuerzos/menu-diario/"         @(401, 403)
Test-Endpoint "Ventas"                      "$ApiUrl/api/v1/ventas/ventas/"                 @(401, 403)
Test-Endpoint "Facturas"                    "$ApiUrl/api/v1/contabilidad/facturas/"         @(401, 403)
Test-Endpoint "Notificaciones"              "$ApiUrl/api/v1/notificaciones/notificaciones/" @(401, 403)

# ── 3. Inventario — alertas (endpoint nuevo) ─────────────────────
Write-Host ""
Write-Host "  Inventario — alertas" -ForegroundColor Yellow
Test-Endpoint "Alertas de stock"            "$ApiUrl/api/v1/inventario/alertas-stock/"       @(401, 403)
Test-Endpoint "Alertas de vencimiento"      "$ApiUrl/api/v1/inventario/alertas-vencimiento/" @(401, 403)

# ── 4. Bancard — requieren auth (401 sin token) ───────────────────
Write-Host ""
Write-Host "  Bancard vPOS (requieren auth)" -ForegroundColor Yellow
Test-Endpoint "Bancard iniciar"             "$ApiUrl/api/v1/core/bancard/iniciar/"            @(401, 403, 405)
Test-Endpoint "Bancard retorno (público)"   "$ApiUrl/api/v1/core/bancard/retorno/"            @(400, 404, 200)
Test-Endpoint "Bancard estado (sin ID)"     "$ApiUrl/api/v1/core/bancard/estado/no-existe/"   @(401, 403, 404)

# ── 5. Endpoints públicos / portal ───────────────────────────────
Write-Host ""
Write-Host "  Endpoints públicos" -ForegroundColor Yellow
Test-Endpoint "Portal frontend"             "$BaseUrl/portal/"      @(200)
Test-Endpoint "Admin Django"                "$ApiUrl/admin/"        @(200, 301, 302)
Test-Endpoint "API docs (Swagger)"          "$ApiUrl/api/v1/docs/"  @(200, 404)

# ── Resumen ───────────────────────────────────────────────────────
$Total = $Passed + $Failed
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
if ($Failed -eq 0) {
    Write-Host ("  RESULTADO: {0}/{1} checks pasaron" -f $Passed, $Total) -ForegroundColor Green
} else {
    Write-Host ("  RESULTADO: {0}/{1} checks fallaron" -f $Failed, $Total) -ForegroundColor Red
}
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

if ($Failed -gt 0) { exit 1 }
exit 0
