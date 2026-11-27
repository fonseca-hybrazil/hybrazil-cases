# Deixa o HyBrazil Cases sempre no ar: registra uma tarefa agendada que inicia o
# supervisor (servico.ps1) escondido toda vez que voce entra no Windows, e ja o inicia.
# Nao precisa de administrador.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts\instalar-servico.ps1           (so neste computador)
#   powershell -ExecutionPolicy Bypass -File scripts\instalar-servico.ps1 -Rede     (acessivel pela rede interna)
#   powershell -ExecutionPolicy Bypass -File scripts\instalar-servico.ps1 -Parar    (para o site agora)
#   powershell -ExecutionPolicy Bypass -File scripts\instalar-servico.ps1 -Remover  (para e tira do inicio automatico)
param([switch]$Rede, [int]$Porta = 8000, [switch]$Parar, [switch]$Remover)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$nome = 'HyBrazil Cases'
$atalho = Join-Path ([Environment]::GetFolderPath('Startup')) "$nome.lnk"
$servico = Join-Path $PSScriptRoot 'servico.ps1'

function Stop-Site {
    if (Get-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue) { Stop-ScheduledTask -TaskName $nome }
    foreach ($arq in 'servico-supervisor.pid', 'servico-servidor.pid') {
        $f = Join-Path $runtime $arq
        if (Test-Path $f) {
            $id = (Get-Content $f -Raw).Trim()
            if ($id) { cmd /c "taskkill /PID $id /T /F >nul 2>&1" }
            Remove-Item $f -ErrorAction SilentlyContinue
        }
    }
    Write-Host 'Site parado.'
}

if ($Parar -or $Remover) {
    Stop-Site
    if ($Remover) {
        if (Get-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $nome -Confirm:$false }
        Remove-Item $atalho -ErrorAction SilentlyContinue
        Write-Host 'Inicio automatico removido.'
    }
    exit 0
}

$argumentos = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$servico`" -Porta $Porta"
if ($Rede) { $argumentos += ' -Rede' }

Stop-Site
try {
    $acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argumentos -WorkingDirectory $root
    $gatilho = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    $config = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew `
        -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $nome -Action $acao -Trigger $gatilho -Settings $config -Principal $principal `
        -Description 'Mantem o HyBrazil Cases no ar em http://localhost (scripts\servico.ps1)' -Force | Out-Null
    Remove-Item $atalho -ErrorAction SilentlyContinue
    Start-ScheduledTask -TaskName $nome
    Write-Host "Tarefa agendada '$nome' registrada (inicia ao entrar no Windows)."
} catch {
    # Sem permissao para tarefas agendadas: usa um atalho na pasta Inicializar.
    Write-Host "Nao foi possivel registrar a tarefa agendada ($($_.Exception.Message)). Usando a pasta Inicializar."
    $ws = New-Object -ComObject WScript.Shell
    $lnk = $ws.CreateShortcut($atalho)
    $lnk.TargetPath = 'powershell.exe'
    $lnk.Arguments = $argumentos
    $lnk.WorkingDirectory = $root
    $lnk.WindowStyle = 7
    $lnk.Save()
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList $argumentos
    Write-Host "Atalho criado em $atalho"
}

for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        if ((Invoke-WebRequest "http://127.0.0.1:$Porta/api/saude" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) {
            Write-Host "Site no ar: http://localhost:$Porta"
            if ($Rede) { Write-Host "Na rede: http://$($env:COMPUTERNAME):$Porta" }
            exit 0
        }
    } catch { }
}
Write-Host "O site ainda nao respondeu. Veja os logs em $runtime\logs" -ForegroundColor Yellow
exit 1
