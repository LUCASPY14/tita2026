# setup_pgpass.ps1
# Configura el archivo .pgpass de PostgreSQL para que backup_cantina.ps1
# y restore_cantina.ps1 puedan autenticarse sin contraseña en texto plano.
#
# Ejecutar UNA VEZ en el servidor de producción, como el mismo usuario que
# correrá la tarea programada (normalmente SYSTEM o el usuario administrador).
#
# Uso:
#   .\scripts\setup_pgpass.ps1 -Password "la_password_real"
#
# Para la cuenta SYSTEM (tarea programada):
#   Start-Process powershell -Verb RunAs -ArgumentList "-File scripts\setup_pgpass.ps1 -Password 'la_password_real'"

param(
    [Parameter(Mandatory=$true)]
    [string]$Password,

    [string]$PgHost = "localhost",
    [string]$PgPort = "5432",
    [string]$DbName = "cantina_tita",
    [string]$PgUser = "postgres"
)

# En Windows, PostgreSQL busca el archivo en %APPDATA%\postgresql\pgpass.conf
$pgPassDir  = Join-Path $env:APPDATA "postgresql"
$pgPassFile = Join-Path $pgPassDir "pgpass.conf"

if (-not (Test-Path $pgPassDir)) {
    New-Item -ItemType Directory -Path $pgPassDir | Out-Null
}

# Formato: hostname:port:database:username:password
# El asterisco (*) aplica a cualquier base de datos del mismo host/user
$entry = "$PgHost`:$PgPort`:*`:$PgUser`:$Password"

# Agregar solo si no existe ya esta combinación host:port:user
$existing = if (Test-Path $pgPassFile) { Get-Content $pgPassFile } else { @() }
$alreadyExists = $existing | Where-Object { $_ -like "$PgHost`:$PgPort`:*`:$PgUser`:*" }

if ($alreadyExists) {
    Write-Warning "Ya existe una entrada para $PgUser@$PgHost. Actualizando..."
    $existing = $existing | Where-Object { $_ -notlike "$PgHost`:$PgPort`:*`:$PgUser`:*" }
}

$existing + $entry | Set-Content $pgPassFile -Encoding UTF8

# En Windows, el archivo no necesita permisos 0600 como en Linux,
# pero restringir a solo el usuario actual es buena práctica.
$acl = Get-Acl $pgPassFile
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $env:USERNAME, "FullControl", "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl $pgPassFile $acl

Write-Host "pgpass.conf configurado en: $pgPassFile" -ForegroundColor Green
Write-Host "Verificar con: psql -U $PgUser -d $DbName -c 'SELECT 1'"
