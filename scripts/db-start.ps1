# Inicia o PostgreSQL local (porta 5433) em segundo plano.
$root = Split-Path -Parent $PSScriptRoot
$bin = Join-Path $root 'runtime\pgsql\bin'
$data = Join-Path $root 'runtime\pgdata'
$log = Join-Path $root 'runtime\postgres.log'

& "$bin\pg_isready.exe" -q -h localhost -p 5433
if ($LASTEXITCODE -eq 0) { Write-Host 'PostgreSQL ja esta rodando.'; return }

# Start-Process evita que o processo do servidor herde a saida deste console.
Start-Process -FilePath "$bin\pg_ctl.exe" -ArgumentList @('-D', "`"$data`"", '-o', '"-p 5433"', '-l', "`"$log`"", 'start') -WindowStyle Hidden

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    & "$bin\pg_isready.exe" -q -h localhost -p 5433
    if ($LASTEXITCODE -eq 0) { Write-Host 'PostgreSQL iniciado na porta 5433.'; return }
}
throw "PostgreSQL nao iniciou. Veja $log"
