# Backup completo do sistema: banco de dados + anexos, numa pasta so.
#   runtime\backups\<nome>-<data-hora>\
#       banco.dump   banco inteiro (pg_dump, formato custom)
#       anexos\      copia dos arquivos anexados (UPLOAD_DIR)
#       info.txt     data, versao do codigo (commit) e contagens, para conferir
# O site continua no ar durante o backup.
#
# Uso: powershell -ExecutionPolicy Bypass -File scripts\backup.ps1 [-Nome pos-migracao] [-SemAnexos]
# Para voltar a um backup: scripts\restaurar.ps1 -Backup <pasta>
param([string]$Nome = 'backup', [switch]$SemAnexos)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_banco.ps1')

$banco = Get-Banco
$destino = Join-Path $PastaBackups ("{0}-{1:yyyyMMdd-HHmmss}" -f $Nome, (Get-Date))
New-Item -ItemType Directory -Force $destino | Out-Null

Write-Host "Copiando o banco '$($banco.Nome)'..."
Invoke-Pg $banco 'pg_dump' @('-Fc', '-f', (Join-Path $destino 'banco.dump'), $banco.Nome)

$anexos = Get-PastaAnexos
if (-not $SemAnexos) {
    Write-Host "Copiando os anexos de $anexos..."
    robocopy $anexos (Join-Path $destino 'anexos') /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Falha ao copiar os anexos (robocopy $LASTEXITCODE)." }
}

$commit = try { (git -C $Raiz log -1 --format='%h %s' 2>$null) } catch { '' }
$arquivos = if ($SemAnexos) { 'nao copiados (-SemAnexos)' } else {
    $f = Get-ChildItem (Join-Path $destino 'anexos') -Recurse -File -ErrorAction SilentlyContinue
    '{0} arquivos, {1:N0} MB' -f @($f).Count, (($f | Measure-Object Length -Sum).Sum / 1MB)
}
@"
Backup do HyBrazil Cases
Data:    $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')
Banco:   $($banco.Nome) em $($banco.Host):$($banco.Porta)
Codigo:  $commit
Anexos:  $arquivos (origem: $anexos)

Contagens no momento do backup:
$(Get-Contagens $banco)
"@ | Set-Content -Encoding utf8 (Join-Path $destino 'info.txt')

$tam = (Get-ChildItem $destino -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Write-Host ("Backup pronto: {0} ({1:N0} MB)" -f $destino, $tam) -ForegroundColor Green
