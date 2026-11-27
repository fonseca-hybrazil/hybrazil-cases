# Garante que o banco de dados esta no ar.
# - Se o backend\.env aponta para o PostgreSQL portatil (porta 5433), inicia-o em segundo plano.
# - Se aponta para outro servidor (ex.: o PostgreSQL instalado como servico), so confere se responde.
# -Portatil forca o uso do portatil (usado pelo script de migracao).
param([switch]$Portatil)
$root = Split-Path -Parent $PSScriptRoot
$bin = Join-Path $root 'runtime\pgsql\bin'
$data = Join-Path $root 'runtime\pgdata'
$log = Join-Path $root 'runtime\postgres.log'
$envFile = Join-Path $root 'backend\.env'

$url = ''
if (Test-Path $envFile) {
    $url = ([regex]::Match([IO.File]::ReadAllText($envFile), '(?m)^DATABASE_URL=(.+)$')).Groups[1].Value.Trim()
}
$m = [regex]::Match($url, '@(?<h>[^:/]+):(?<p>\d+)/')
$dbHost = if ($m.Success) { $m.Groups['h'].Value } else { 'localhost' }
$dbPort = if ($m.Success) { [int]$m.Groups['p'].Value } else { 5433 }

$isready = Join-Path $bin 'pg_isready.exe'
if (-not (Test-Path $isready)) { $isready = 'C:\Program Files\PostgreSQL\18\bin\pg_isready.exe' }

if (-not $Portatil -and $dbPort -ne 5433) {
    & $isready -q -h $dbHost -p $dbPort
    if ($LASTEXITCODE -eq 0) { Write-Host "PostgreSQL respondendo em ${dbHost}:$dbPort."; return }
    throw "O PostgreSQL em ${dbHost}:$dbPort nao responde. Verifique se o servico (postgresql-x64-18) esta iniciado."
}

& $isready -q -h localhost -p 5433
if ($LASTEXITCODE -eq 0) { Write-Host 'PostgreSQL portatil ja esta rodando.'; return }

# Start-Process evita que o processo do servidor herde a saida deste console.
Start-Process -FilePath "$bin\pg_ctl.exe" -ArgumentList @('-D', "`"$data`"", '-o', '"-p 5433"', '-l', "`"$log`"", 'start') -WindowStyle Hidden

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    & $isready -q -h localhost -p 5433
    if ($LASTEXITCODE -eq 0) { Write-Host 'PostgreSQL portatil iniciado na porta 5433.'; return }
}
throw "PostgreSQL nao iniciou. Veja $log"
