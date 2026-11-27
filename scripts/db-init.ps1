# Cria o cluster PostgreSQL local (uma vez so) e o banco da aplicacao.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\db-init.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pg = Join-Path $root 'runtime\pgsql\bin'
$data = Join-Path $root 'runtime\pgdata'
$envFile = Join-Path $root 'backend\.env'
$port = 5433

if (Test-Path (Join-Path $data 'PG_VERSION')) {
    Write-Host "Cluster ja existe em $data"
    exit 0
}

function New-Secret { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ }) }
$superPwd = New-Secret
$appPwd = New-Secret
$jwtSecret = (New-Secret) + (New-Secret)

$pwFile = New-TemporaryFile
Set-Content -Path $pwFile -Value $superPwd -NoNewline -Encoding ascii
& "$pg\initdb.exe" -D $data -U postgres --pwfile=$pwFile -A scram-sha-256 -E UTF8 --locale-provider=builtin --builtin-locale=C.UTF-8 | Out-Host
Remove-Item $pwFile

& (Join-Path $PSScriptRoot 'db-start.ps1')

$env:PGPASSWORD = $superPwd
& "$pg\psql.exe" -h localhost -p $port -U postgres -v ON_ERROR_STOP=1 -c "CREATE ROLE hyora LOGIN PASSWORD '$appPwd';" | Out-Host
& "$pg\psql.exe" -h localhost -p $port -U postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE hyora OWNER hyora;" | Out-Host
& "$pg\psql.exe" -h localhost -p $port -U postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE hyora_test OWNER hyora;" | Out-Host
foreach ($db in 'hyora', 'hyora_test') {
    & "$pg\psql.exe" -h localhost -p $port -U postgres -d $db -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm;" | Out-Host
}
Remove-Item Env:\PGPASSWORD

New-Item -ItemType Directory -Force (Split-Path $envFile) | Out-Null
$envText = @"
# Gerado por scripts/db-init.ps1  NAO versionar
DATABASE_URL=postgresql+psycopg://hyora:$appPwd@localhost:$port/hyora
TEST_DATABASE_URL=postgresql+psycopg://hyora:$appPwd@localhost:$port/hyora_test
JWT_SECRET=$jwtSecret
UPLOAD_DIR=$(Join-Path $root 'runtime\uploads')
POSTGRES_SUPERUSER_PASSWORD=$superPwd
"@
[IO.File]::WriteAllText($envFile, $envText)

Write-Host "Banco criado. Configuracao gravada em $envFile"
