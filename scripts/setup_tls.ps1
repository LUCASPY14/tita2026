# scripts/setup_tls.ps1 — Cantina Tita
#
# Genera un certificado TLS self-signed para la LAN escolar y configura
# Nginx para escuchar en HTTPS (443). HTTP (80) redirige automáticamente a HTTPS.
#
# ── Requisitos ───────────────────────────────────────────────────────────────
#   - OpenSSL instalado (viene con Git for Windows: C:\Program Files\Git\usr\bin\openssl.exe)
#   - Docker Desktop corriendo
#   - Ejecutar como Administrador
#
# ── Uso ──────────────────────────────────────────────────────────────────────
#   .\scripts\setup_tls.ps1
#   .\scripts\setup_tls.ps1 -ServerIP "192.168.1.100" -ServerName "cantina.local"
#
# ── Distribución del CA a las PCs clientes ───────────────────────────────────
#   Tras ejecutar este script, en cada PC cajero/admin/comedor:
#     1. Copiar C:\tita2026\certs\cantina-ca.crt
#     2. Doble clic → Instalar certificado → Equipo local → Entidades de
#        certificación raíz de confianza
#   O por GPO si hay dominio de Active Directory.

param(
    [string]$ServerIP    = "192.168.1.100",          # IP del servidor en la LAN
    [string]$ServerName  = "cantina.local",           # hostname opcional (agregar en hosts de cada PC)
    [string]$CertsDir    = "C:\tita2026\certs",
    [string]$OpenSSL     = "C:\Program Files\Git\usr\bin\openssl.exe",
    [int]   $ValidDays   = 825                        # ~2 años y 3 meses (límite Safari)
)

$ErrorActionPreference = "Stop"

$line = "─" * 62
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  TLS Self-Signed Setup — Cantina Tita LAN" -ForegroundColor Cyan
Write-Host $line -ForegroundColor DarkGray

# ── Verificar openssl ─────────────────────────────────────────────────────────
if (-not (Test-Path $OpenSSL)) {
    $OpenSSL = (Get-Command openssl -ErrorAction SilentlyContinue)?.Source
    if (-not $OpenSSL) {
        Write-Host ""
        Write-Host "  ERROR: openssl no encontrado." -ForegroundColor Red
        Write-Host "  Instalar Git for Windows (incluye openssl) o especificar -OpenSSL <ruta>" -ForegroundColor DarkGray
        exit 1
    }
}
Write-Host "  openssl : $OpenSSL" -ForegroundColor DarkGray
Write-Host "  ServerIP: $ServerIP" -ForegroundColor DarkGray
Write-Host ""

# ── Crear directorio de certificados ─────────────────────────────────────────
if (-not (Test-Path $CertsDir)) { New-Item -ItemType Directory -Path $CertsDir | Out-Null }

$caKey   = Join-Path $CertsDir "cantina-ca.key"
$caCert  = Join-Path $CertsDir "cantina-ca.crt"
$srvKey  = Join-Path $CertsDir "cantina.key"
$srvCsr  = Join-Path $CertsDir "cantina.csr"
$srvCert = Join-Path $CertsDir "cantina.crt"
$srvExt  = Join-Path $CertsDir "cantina-ext.cnf"

# ── 1. Generar CA privada ─────────────────────────────────────────────────────
Write-Host "  [1/5] Generando CA privada..." -ForegroundColor Yellow
& $OpenSSL genrsa -out $caKey 4096 2>&1 | Out-Null
& $OpenSSL req -new -x509 -days $ValidDays -key $caKey -out $caCert `
    -subj "/C=PY/ST=Asuncion/O=Cantina Tita/CN=Cantina Tita CA" 2>&1 | Out-Null
Write-Host "    OK → $caCert" -ForegroundColor Green

# ── 2. Generar clave del servidor ─────────────────────────────────────────────
Write-Host "  [2/5] Generando clave del servidor..." -ForegroundColor Yellow
& $OpenSSL genrsa -out $srvKey 2048 2>&1 | Out-Null
Write-Host "    OK → $srvKey" -ForegroundColor Green

# ── 3. Generar CSR ────────────────────────────────────────────────────────────
Write-Host "  [3/5] Generando CSR..." -ForegroundColor Yellow
& $OpenSSL req -new -key $srvKey -out $srvCsr `
    -subj "/C=PY/ST=Asuncion/O=Cantina Tita/CN=$ServerName" 2>&1 | Out-Null
Write-Host "    OK → $srvCsr" -ForegroundColor Green

# ── 4. Firmar con la CA (SAN para IP y hostname) ──────────────────────────────
Write-Host "  [4/5] Firmando certificado del servidor..." -ForegroundColor Yellow
@"
[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
IP.1  = $ServerIP
IP.2  = 127.0.0.1
DNS.1 = $ServerName
DNS.2 = localhost
"@ | Out-File $srvExt -Encoding ascii

& $OpenSSL x509 -req -days $ValidDays `
    -in $srvCsr -CA $caCert -CAkey $caKey -CAcreateserial `
    -out $srvCert -extfile $srvExt -extensions v3_req 2>&1 | Out-Null
Write-Host "    OK → $srvCert" -ForegroundColor Green

# ── 5. Actualizar docker-compose para montar los certs ────────────────────────
Write-Host "  [5/5] Instrucciones para activar HTTPS en docker-compose..." -ForegroundColor Yellow

Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Certificados generados en: $CertsDir" -ForegroundColor Green
Write-Host ""
Write-Host "  PASO 1 — Activar HTTPS en docker-compose.yml:" -ForegroundColor Cyan
Write-Host "    En el servicio 'frontend', agregar:" -ForegroundColor DarkGray
Write-Host '      ports:'                                    -ForegroundColor DarkGray
Write-Host '        - "80:80"'                               -ForegroundColor DarkGray
Write-Host '        - "443:443"'                             -ForegroundColor DarkGray
Write-Host '      volumes:'                                  -ForegroundColor DarkGray
Write-Host '        - ./certs/cantina.crt:/etc/nginx/ssl/cantina.crt:ro' -ForegroundColor DarkGray
Write-Host '        - ./certs/cantina.key:/etc/nginx/ssl/cantina.key:ro' -ForegroundColor DarkGray
Write-Host ""
Write-Host "  PASO 2 — nginx.conf ya tiene el bloque HTTPS (listen 443 ssl)." -ForegroundColor Cyan
Write-Host "    Descomentar la sección '# HTTPS' si está comentada." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  PASO 3 — Distribuir el CA a cada PC de la LAN:" -ForegroundColor Cyan
Write-Host "    Archivo: $caCert" -ForegroundColor DarkGray
Write-Host "    Instalar en cada PC: doble clic → Equipo local →" -ForegroundColor DarkGray
Write-Host "    Entidades de certificación raíz de confianza" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  PASO 4 — Reiniciar el stack:" -ForegroundColor Cyan
Write-Host "    docker compose up -d --force-recreate frontend" -ForegroundColor DarkGray
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

# ── Verificar el certificado generado ────────────────────────────────────────
Write-Host "  Verificación del certificado:" -ForegroundColor DarkGray
& $OpenSSL x509 -noout -text -in $srvCert 2>&1 |
    Select-String "Subject:|DNS:|IP Address:|Not After" |
    ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
Write-Host ""
