# Roda os testes automatizados do backend (usa o banco hyora_test).
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'db-start.ps1')
Push-Location (Join-Path $root 'backend')
try { & .\.venv\Scripts\python.exe -m pytest -q } finally { Pop-Location }
