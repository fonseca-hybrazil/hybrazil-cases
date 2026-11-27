# Passa o HyBrazil Cases a usar o PostgreSQL instalado no Windows (servico),
# em vez do PostgreSQL portatil de runtime\pgsql (porta 5433).
#
# O que faz:
#   1. pede a senha do superusuario (postgres) do servidor instalado - nao e gravada;
#   2. cria o usuario 'hyora' e os bancos 'hyora' e 'hyora_test', com as extensoes;
#   3. copia os dados do banco portatil para o banco novo;
#   4. atualiza backend\.env (as linhas antigas ficam comentadas para voltar atras).
#
# Uso: powershell -ExecutionPolicy Bypass -File scripts\usar-postgres-instalado.ps1
#      [-Porta 5432] [-Bin "C:\Program Files\PostgreSQL\18\bin"] [-Superusuario postgres] [-SemCopiarDados]
param(
    [int]$Porta = 5432,
    [string]$Bin = 'C:\Program Files\PostgreSQL\18\bin',
    [string]$Superusuario = 'postgres',
    [switch]$SemCopiarDados
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root 'backend\.env'
$binPortatil = Join-Path $root 'runtime\pgsql\bin'
$psql = Join-Path $Bin 'psql.exe'
if (-not (Test-Path $psql)) { throw "psql.exe nao encontrado em $Bin (use -Bin)" }
if (-not (Test-Path $envFile)) { throw "$envFile nao existe" }

function New-Secret { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ }) }

function Invoke-Psql([string]$Banco, [string]$Sql) {
    $out = & $psql -h localhost -p $Porta -U $Superusuario -d $Banco -v ON_ERROR_STOP=1 -tAc $Sql
    if ($LASTEXITCODE -ne 0) { throw "Falha no comando SQL: $Sql" }
    return $out
}

# --- senha do usuario administrador (digitada aqui, nunca gravada) ---
# Basta um usuario com CREATEROLE e CREATEDB; nao precisa ser superusuario.
if (-not $env:PGPASSWORD) {
    $seguro = Read-Host "Senha do usuario '$Superusuario' do PostgreSQL instalado (porta $Porta)" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro)
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

try {
    $versao = Invoke-Psql 'postgres' 'SHOW server_version'
    Write-Host "Conectado: PostgreSQL $versao na porta $Porta."

    # --- usuario e bancos ---
    $appPwd = New-Secret
    if (Invoke-Psql 'postgres' "SELECT 1 FROM pg_roles WHERE rolname='hyora'") {
        Invoke-Psql 'postgres' "ALTER ROLE hyora LOGIN PASSWORD '$appPwd'" | Out-Null
        Write-Host "Usuario 'hyora' ja existia: senha redefinida."
    } else {
        Invoke-Psql 'postgres' "CREATE ROLE hyora LOGIN PASSWORD '$appPwd'" | Out-Null
        Write-Host "Usuario 'hyora' criado."
    }
    # Sem superusuario, e preciso poder assumir o papel 'hyora' para criar os bancos
    # em nome dele e restaurar os dados como dono (PostgreSQL 16+).
    if ((Invoke-Psql 'postgres' 'SELECT rolsuper FROM pg_roles WHERE rolname = current_user') -ne 't') {
        Invoke-Psql 'postgres' 'GRANT hyora TO CURRENT_USER WITH SET TRUE, INHERIT FALSE' | Out-Null
    }

    $bancoJaTinhaDados = $false
    foreach ($db in 'hyora', 'hyora_test') {
        if (Invoke-Psql 'postgres' "SELECT 1 FROM pg_database WHERE datname='$db'") {
            Write-Host "Banco '$db' ja existe."
            if ($db -eq 'hyora') {
                $bancoJaTinhaDados = [bool](Invoke-Psql 'hyora' "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='schema_migrations'")
            }
        } else {
            Invoke-Psql 'postgres' "CREATE DATABASE $db OWNER hyora ENCODING 'UTF8' TEMPLATE template0" | Out-Null
            Write-Host "Banco '$db' criado."
        }
        # unaccent e pg_trgm sao extensoes "confiaveis": o dono do banco pode cria-las.
        Invoke-Psql $db 'SET ROLE hyora; CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm;' | Out-Null
    }

    # --- copia dos dados do banco portatil ---
    $envTexto = [IO.File]::ReadAllText($envFile)
    $urlAntiga = ([regex]::Match($envTexto, '(?m)^DATABASE_URL=(.+)$')).Groups[1].Value.Trim()
    if ($SemCopiarDados) {
        Write-Host 'Copia de dados ignorada (-SemCopiarDados). O sistema cria as tabelas ao iniciar.'
    } elseif ($bancoJaTinhaDados) {
        Write-Host "O banco 'hyora' ja tem tabelas do sistema: nada foi copiado para nao sobrescrever."
    } elseif ($urlAntiga -notmatch ':5433/') {
        Write-Host 'O .env nao aponta para o banco portatil: nada a copiar.'
    } else {
        $m = [regex]::Match($urlAntiga, '//(?<u>[^:]+):(?<p>[^@]+)@')
        & (Join-Path $PSScriptRoot 'db-start.ps1') -Portatil
        $dump = Join-Path ([IO.Path]::GetTempPath()) "hyora-$(Get-Date -Format yyyyMMddHHmmss).dump"
        $senhaSuper = $env:PGPASSWORD
        $env:PGPASSWORD = $m.Groups['p'].Value
        & "$binPortatil\pg_dump.exe" -h localhost -p 5433 -U $m.Groups['u'].Value -d hyora -Fc --no-owner --no-privileges -f $dump
        $env:PGPASSWORD = $senhaSuper
        if ($LASTEXITCODE -ne 0) { throw 'pg_dump do banco portatil falhou.' }
        & "$binPortatil\pg_restore.exe" -h localhost -p $Porta -U $Superusuario -d hyora --no-owner --role=hyora --no-comments --exit-on-error $dump
        if ($LASTEXITCODE -ne 0) { throw "pg_restore falhou. O arquivo da copia ficou em $dump" }
        Remove-Item $dump
        Write-Host 'Dados copiados do banco portatil.'
    }

    # --- atualiza o .env ---
    $novaUrl = "postgresql+psycopg://hyora:$appPwd@localhost:$Porta/hyora"
    $novaUrlTeste = "postgresql+psycopg://hyora:$appPwd@localhost:$Porta/hyora_test"
    $envTexto = [regex]::Replace($envTexto, '(?m)^(DATABASE_URL|TEST_DATABASE_URL)=', '# (banco portatil, antigo) $1=')
    $envTexto = $envTexto.TrimEnd() + "`r`n# PostgreSQL instalado (servico do Windows)`r`nDATABASE_URL=$novaUrl`r`nTEST_DATABASE_URL=$novaUrlTeste`r`n"
    [IO.File]::WriteAllText($envFile, $envTexto)
    Write-Host "backend\.env atualizado para a porta $Porta."
} finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

# O portatil nao e mais necessario; os dados dele continuam em runtime\pgdata.
& "$binPortatil\pg_ctl.exe" -D (Join-Path $root 'runtime\pgdata') status *> $null
if ($LASTEXITCODE -eq 0) { & "$binPortatil\pg_ctl.exe" -D (Join-Path $root 'runtime\pgdata') stop -m fast | Out-Null; Write-Host 'PostgreSQL portatil parado.' }

Write-Host ''
Write-Host 'Pronto. Inicie o sistema normalmente com scripts\iniciar.ps1'
