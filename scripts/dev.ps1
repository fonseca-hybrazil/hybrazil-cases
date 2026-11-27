# Modo desenvolvimento: API com recarga automatica (porta 8000) + Vite (porta 5173).
# Abra http://localhost:5173 . Ctrl+C encerra os dois.
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'db-start.ps1')
$api = Start-Process -PassThru -NoNewWindow -FilePath (Join-Path $root 'backend\.venv\Scripts\python.exe') `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--app-dir', (Join-Path $root 'backend'), '--reload', '--port', '8000')
try {
    $env:PATH = (Join-Path $root 'runtime\node') + ';' + $env:PATH
    Push-Location (Join-Path $root 'frontend')
    npx vite
} finally {
    Pop-Location
    Stop-Process -Id $api.Id -ErrorAction SilentlyContinue
}
