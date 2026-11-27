# Publica as mudancas no site que esta no ar (http://localhost:8000):
#   1. compila a interface numa pasta separada (o site continua no ar enquanto isso);
#   2. confere se o backend importa sem erro (e roda os testes com -Testes);
#   3. so entao reinicia o servidor, troca a interface e espera o site responder.
# Se a compilacao ou a conferencia falhar, nada e trocado: o site segue na versao anterior.
#
# Uso: powershell -ExecutionPolicy Bypass -File scripts\atualizar.ps1 [-Testes] [-SemInterface]
param([switch]$Testes, [switch]$SemInterface, [int]$Porta = 8000)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$logs = Join-Path $runtime 'logs'
$pausa = Join-Path $runtime 'servico.pausa'
$pidServidor = Join-Path $runtime 'servico-servidor.pid'
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
$frontend = Join-Path $root 'frontend'
$distNovo = Join-Path $frontend 'dist-novo'
$inicio = Get-Date

function Test-Supervisor {
    try { [Threading.Mutex]::OpenExisting('Local\HyBrazilCasesServico').Dispose(); return $true } catch { return $false }
}

# --- 1. interface ---
if (-not $SemInterface) {
    Write-Host 'Compilando a interface...'
    $env:PATH = (Join-Path $runtime 'node') + ';' + $env:PATH
    Push-Location $frontend
    try {
        if (-not (Test-Path 'node_modules')) { npm install --no-fund --no-audit | Out-Host }
        npx tsc -p tsconfig.json | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Erros de tipo no frontend. O site NAO foi atualizado.' }
        npx vite build --outDir dist-novo --emptyOutDir --logLevel warn | Out-Host
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $distNovo 'index.html'))) { throw 'Falha no build do frontend. O site NAO foi atualizado.' }
    } finally { Pop-Location }
}

# --- 2. backend ---
Write-Host 'Conferindo o backend...'
Push-Location (Join-Path $root 'backend')
try {
    & $python -c "import app.main" | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'O backend tem erro de importacao. O site NAO foi atualizado.' }
    if ($Testes) {
        & (Join-Path $PSScriptRoot 'db-start.ps1') | Out-Null
        & $python -m pytest -q -p no:cacheprovider | Select-Object -Last 3 | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Testes falharam. O site NAO foi atualizado.' }
    }
} finally { Pop-Location }

# --- 3. troca e reinicio ---
$pidAntigo = if (Test-Path $pidServidor) { (Get-Content $pidServidor -Raw).Trim() } else { '' }
New-Item -ItemType File -Force $pausa | Out-Null
try {
    if ($pidAntigo) {
        # taskkill /T: o python.exe do venv e um lancador com um processo filho.
        cmd /c "taskkill /PID $pidAntigo /T /F >nul 2>&1"
        for ($i = 0; $i -lt 40 -and (Get-Process -Id $pidAntigo -ErrorAction SilentlyContinue); $i++) { Start-Sleep -Milliseconds 250 }
    }
    if (-not $SemInterface) {
        $dist = Join-Path $frontend 'dist'
        $distVelho = Join-Path $frontend 'dist-velho'
        if (Test-Path $distVelho) { Remove-Item -Recurse -Force $distVelho }
        if (Test-Path $dist) { Rename-Item $dist 'dist-velho' }
        Rename-Item $distNovo 'dist'
        Remove-Item -Recurse -Force $distVelho -ErrorAction SilentlyContinue
    }
} finally {
    Remove-Item $pausa -ErrorAction SilentlyContinue
}

if (-not (Test-Supervisor)) {
    Write-Host 'O supervisor nao estava rodando; iniciando...'
    if (Get-ScheduledTask -TaskName 'HyBrazil Cases' -ErrorAction SilentlyContinue) {
        Start-ScheduledTask -TaskName 'HyBrazil Cases'
    } else {
        Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'servico.ps1'), '-Porta', "$Porta")
    }
}

# --- 4. espera o site responder ---
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $pidNovo = if (Test-Path $pidServidor) { (Get-Content $pidServidor -Raw).Trim() } else { '' }
    if (-not $pidNovo -or $pidNovo -eq $pidAntigo) { continue }
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$Porta/api/saude" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            $s = [int]((Get-Date) - $inicio).TotalSeconds
            Write-Host "Site atualizado e no ar: http://localhost:$Porta  (servidor PID $pidNovo, $s s)"
            exit 0
        }
    } catch { }
}
Write-Host 'O site NAO voltou em 30 s. Ultimas linhas do log de erros:' -ForegroundColor Red
Get-Content (Join-Path $logs 'servidor-erros.log') -Tail 25 -ErrorAction SilentlyContinue | Out-Host
exit 1
