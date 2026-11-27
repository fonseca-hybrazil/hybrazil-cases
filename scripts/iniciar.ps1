# Inicia o HyBrazil Cases: banco de dados + servidor web (porta 8000).
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts\iniciar.ps1          (so neste computador)
#   powershell -ExecutionPolicy Bypass -File scripts\iniciar.ps1 -Rede    (acessivel pela rede interna)
param([switch]$Rede, [int]$Porta = 8000)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot 'db-start.ps1')

if (-not (Test-Path (Join-Path $root 'frontend\dist\index.html'))) {
    Write-Host 'Interface ainda nao compilada. Compilando...'
    & (Join-Path $PSScriptRoot 'compilar-frontend.ps1')
}

$hostIp = if ($Rede) { '0.0.0.0' } else { '127.0.0.1' }
Write-Host ""
Write-Host "HyBrazil Cases em http://localhost:$Porta  (Ctrl+C para parar)"
if ($Rede) { Write-Host "Na rede: http://$($env:COMPUTERNAME):$Porta" }
& (Join-Path $root 'backend\.venv\Scripts\python.exe') -m uvicorn app.main:app --app-dir (Join-Path $root 'backend') --host $hostIp --port $Porta
