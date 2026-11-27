# Volta o sistema ao estado de um backup feito pelo backup.ps1 (banco + anexos).
#   - Antes, faz um backup do estado atual ("antes-restauracao"), para poder desfazer.
#   - Para o site, apaga e recria o banco a partir do backup, espelha os anexos e religa o site.
#   - Migracoes do banco mais novas que o backup sao reaplicadas sozinhas quando o site volta.
#
# Uso:
#   scripts\restaurar.ps1 -Backup pos-migracao-ora        (nome ou inicio do nome; pega o mais recente)
#   scripts\restaurar.ps1 -Backup runtime\backups\<pasta>  (caminho da pasta)
#   -Teste  restaura so o banco no banco de TESTES (hyora_test) e confere as contagens; o site nao e tocado.
#   -Sim    nao pede confirmacao.   -SemBackupAntes  pula o backup de seguranca.
param([Parameter(Mandatory = $true)][string]$Backup, [switch]$Teste, [switch]$Sim, [switch]$SemBackupAntes)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_banco.ps1')

# --- localiza o backup ---
$pasta = if (Test-Path (Join-Path $Backup 'banco.dump')) { (Resolve-Path $Backup).Path } else {
    Get-ChildItem $PastaBackups -Directory | Where-Object { $_.Name -like "$Backup*" -and (Test-Path (Join-Path $_.FullName 'banco.dump')) } |
        Sort-Object Name | Select-Object -Last 1 -ExpandProperty FullName
}
if (-not $pasta) { throw "Backup '$Backup' nao encontrado em $PastaBackups." }
$dump = Join-Path $pasta 'banco.dump'
$anexosBackup = Join-Path $pasta 'anexos'
$banco = Get-Banco -Teste:$Teste

Write-Host "Backup:  $pasta"
Write-Host "Destino: banco '$($banco.Nome)'$(if (-not $Teste) { ' + anexos em ' + (Get-PastaAnexos) })"
if (-not $Teste -and -not $Sim) {
    Write-Host 'Tudo o que foi feito no site depois desse backup sera desfeito (fica guardado no backup de seguranca).' -ForegroundColor Yellow
    if ((Read-Host 'Digite RESTAURAR para continuar') -ne 'RESTAURAR') { Write-Host 'Cancelado.'; exit 1 }
}

if (-not $Teste -and -not $SemBackupAntes) {
    & (Join-Path $PSScriptRoot 'backup.ps1') -Nome 'antes-restauracao'
}

function Restore-Banco {
    Write-Host "Recriando o banco '$($banco.Nome)' a partir do backup..."
    Invoke-Pg $banco 'psql' @('-q', '-d', $banco.Nome, '-v', 'ON_ERROR_STOP=1', '-c',
        'SET client_min_messages TO warning; DROP SCHEMA public CASCADE; CREATE SCHEMA public;') | Out-Null
    Invoke-Pg $banco 'pg_restore' @('-d', $banco.Nome, '--no-owner', '--no-comments', '--exit-on-error', $dump)
}

if ($Teste) {
    Restore-Banco
    $esperado = [regex]::Match((Get-Content (Join-Path $pasta 'info.txt') -Raw), '(?s)backup:\s*\r?\n(.+)$').Groups[1].Value.Trim() -replace '\r', ''
    $obtido = Get-Contagens $banco
    Write-Host "Contagens restauradas:`n$obtido"
    if ($esperado -and $esperado -eq $obtido) { Write-Host 'Conferido: iguais as do momento do backup.' -ForegroundColor Green; exit 0 }
    Write-Host 'As contagens NAO batem com o info.txt do backup.' -ForegroundColor Red; exit 1
}

Stop-Site
try {
    Restore-Banco
    if (Test-Path $anexosBackup) {
        Write-Host 'Espelhando os anexos...'
        robocopy $anexosBackup (Get-PastaAnexos) /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "Falha ao copiar os anexos (robocopy $LASTEXITCODE)." }
    } else {
        Write-Host 'Esse backup nao tem anexos; a pasta de anexos ficou como estava.' -ForegroundColor Yellow
    }
} finally {
    $noAr = Start-Site
}
Write-Host "Contagens agora:`n$(Get-Contagens $banco)"
if ($noAr) { Write-Host 'Restaurado. Site no ar: http://localhost:8000' -ForegroundColor Green }
else { Write-Host 'Restaurado, mas o site nao respondeu em 30 s. Veja runtime\logs.' -ForegroundColor Yellow }
