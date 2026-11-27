# Compila a interface web (frontend\dist), que o servidor Python entrega.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$env:PATH = (Join-Path $root 'runtime\node') + ';' + $env:PATH
Push-Location (Join-Path $root 'frontend')
try {
    if (-not (Test-Path 'node_modules')) { npm install --no-fund --no-audit }
    npx tsc -p tsconfig.json
    if ($LASTEXITCODE -ne 0) { throw 'Erros de tipo no frontend.' }
    npx vite build
} finally { Pop-Location }
