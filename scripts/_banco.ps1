# Funcoes comuns aos scripts de backup e restauracao (carregado com ". _banco.ps1").
$script:Raiz = Split-Path -Parent $PSScriptRoot
$script:PgBin = @('C:\Program Files\PostgreSQL\18\bin', (Join-Path $Raiz 'runtime\pgsql\bin')) |
    Where-Object { Test-Path (Join-Path $_ 'pg_dump.exe') } | Select-Object -First 1
$script:PastaBackups = Join-Path $Raiz 'runtime\backups'

function Get-EnvValor([string]$chave) {
    $arq = Join-Path $Raiz 'backend\.env'
    $m = [regex]::Match([IO.File]::ReadAllText($arq), "(?m)^$chave=(.+)$")
    if (-not $m.Success) { throw "$chave nao encontrado em backend\.env" }
    $m.Groups[1].Value.Trim()
}

# Le a conexao do .env. -Teste usa o banco de testes (TEST_DATABASE_URL).
function Get-Banco([switch]$Teste) {
    $url = Get-EnvValor $(if ($Teste) { 'TEST_DATABASE_URL' } else { 'DATABASE_URL' })
    $m = [regex]::Match($url, '//(?<u>[^:]+):(?<s>[^@]*)@(?<h>[^:/]+):(?<p>\d+)/(?<d>[^?]+)')
    if (-not $m.Success) { throw 'DATABASE_URL em formato inesperado.' }
    [pscustomobject]@{
        Host = $m.Groups['h'].Value; Porta = $m.Groups['p'].Value; Usuario = $m.Groups['u'].Value
        Senha = [uri]::UnescapeDataString($m.Groups['s'].Value); Nome = $m.Groups['d'].Value
    }
}

function Get-PastaAnexos {
    try { Get-EnvValor 'UPLOAD_DIR' } catch { Join-Path $Raiz 'runtime\uploads' }
}

# Roda um executavel do PostgreSQL com a senha so na variavel de ambiente deste processo.
function Invoke-Pg($banco, [string]$exe, [string[]]$argumentos) {
    $env:PGPASSWORD = $banco.Senha
    try {
        & (Join-Path $PgBin "$exe.exe") -h $banco.Host -p $banco.Porta -U $banco.Usuario @argumentos
        if ($LASTEXITCODE -ne 0) { throw "$exe terminou com erro ($LASTEXITCODE)." }
    } finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
}

function Get-Contagens($banco) {
    $sql = "select 'projetos', count(*) from projetos union all select 'tickets', count(*) from tickets " +
           "union all select 'comentarios', count(*) from comentarios union all select 'anexos', count(*) from anexos " +
           "union all select 'atividades', count(*) from atividades union all select 'labels', count(*) from labels " +
           "union all select 'usuarios', count(*) from usuarios"
    $linhas = Invoke-Pg $banco 'psql' @('-d', $banco.Nome, '-AtF', '=', '-c', $sql)
    $linhas -join "`n"
}

# Pede ao supervisor do site que espere e derruba o servidor (mesmo esquema do atualizar.ps1).
function Stop-Site {
    $runtime = Join-Path $Raiz 'runtime'
    New-Item -ItemType File -Force (Join-Path $runtime 'servico.pausa') | Out-Null
    $arqPid = Join-Path $runtime 'servico-servidor.pid'
    if (Test-Path $arqPid) {
        $p = (Get-Content $arqPid -Raw).Trim()
        cmd /c "taskkill /PID $p /T /F >nul 2>&1"
        for ($i = 0; $i -lt 40 -and (Get-Process -Id $p -ErrorAction SilentlyContinue); $i++) { Start-Sleep -Milliseconds 250 }
    }
}

function Start-Site([int]$Porta = 8000) {
    Remove-Item (Join-Path $Raiz 'runtime\servico.pausa') -ErrorAction SilentlyContinue
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            if ((Invoke-WebRequest "http://127.0.0.1:$Porta/api/saude" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { return $true }
        } catch { }
    }
    $false
}
