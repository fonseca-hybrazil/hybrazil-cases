# Supervisor do HyBrazil Cases: mantem o site sempre no ar em http://localhost:8000.
#  - inicia o servidor web (uvicorn) escondido, com log em runtime\logs;
#  - se o servidor cair, inicia de novo (com espera crescente se cair seguidas vezes);
#  - enquanto existir runtime\servico.pausa (criado pelo atualizar.ps1), espera antes de reiniciar.
# Normalmente e iniciado pela tarefa agendada (instalar-servico.ps1), nao a mao.
param([switch]$Rede, [int]$Porta = 8000)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$logs = Join-Path $runtime 'logs'
$pausa = Join-Path $runtime 'servico.pausa'
$pidServidor = Join-Path $runtime 'servico-servidor.pid'
$pidSupervisor = Join-Path $runtime 'servico-supervisor.pid'
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
New-Item -ItemType Directory -Force $logs | Out-Null

function Write-Log([string]$msg) {
    $linha = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
    Add-Content -Path (Join-Path $logs 'servico.log') -Value $linha -Encoding utf8
}

function Rotate-Log([string]$nome) {
    $f = Join-Path $logs $nome
    if ((Test-Path $f) -and (Get-Item $f).Length -gt 5MB) { Move-Item -Force $f "$f.1" }
}

# Uma instancia so.
$mutex = New-Object Threading.Mutex($false, 'Local\HyBrazilCasesServico')
try { $dono = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $dono = $true }  # supervisor anterior foi encerrado a forca
if (-not $dono) { Write-Host 'O supervisor ja esta rodando.'; exit 0 }

try {
    Set-Content -Path $pidSupervisor -Value $PID -Encoding ascii
    Rotate-Log 'servico.log'
    Write-Log "Supervisor iniciado (PID $PID, porta $Porta, rede=$([bool]$Rede))."
    $hostIp = if ($Rede) { '0.0.0.0' } else { '127.0.0.1' }
    $espera = 2

    while ($true) {
        while (Test-Path $pausa) { Start-Sleep -Milliseconds 500 }

        try {
            & (Join-Path $PSScriptRoot 'db-start.ps1') *> $null
        } catch {
            Write-Log "Banco indisponivel: $($_.Exception.Message). Nova tentativa em 15 s."
            Start-Sleep -Seconds 15
            continue
        }

        if (-not (Test-Path (Join-Path $root 'frontend\dist\index.html'))) {
            Write-Log 'Interface nao compilada; compilando...'
            try { & (Join-Path $PSScriptRoot 'compilar-frontend.ps1') *>> (Join-Path $logs 'compilacao.log') }
            catch { Write-Log "Falha ao compilar a interface: $($_.Exception.Message)" }
        }

        Rotate-Log 'servidor.log'
        Rotate-Log 'servidor-erros.log'
        $inicio = Get-Date
        $proc = Start-Process -FilePath $python -PassThru -WindowStyle Hidden `
            -WorkingDirectory (Join-Path $root 'backend') `
            -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', $hostIp, '--port', "$Porta", '--no-access-log') `
            -RedirectStandardOutput (Join-Path $logs 'servidor.log') `
            -RedirectStandardError (Join-Path $logs 'servidor-erros.log')
        $null = $proc.Handle    # sem isso o ExitCode vem vazio
        Set-Content -Path $pidServidor -Value $proc.Id -Encoding ascii
        Write-Log "Servidor iniciado (PID $($proc.Id))."

        $proc.WaitForExit()
        $duracao = [int]((Get-Date) - $inicio).TotalSeconds
        Write-Log "Servidor parou (codigo $($proc.ExitCode), ficou $duracao s no ar)."
        Remove-Item $pidServidor -ErrorAction SilentlyContinue

        if (Test-Path $pausa) { $espera = 2; continue }    # reinicio pedido pelo atualizar.ps1
        if ($duracao -gt 60) { $espera = 2 } else { $espera = [Math]::Min($espera * 2, 60) }
        Write-Log "Reiniciando em $espera s."
        Start-Sleep -Seconds $espera
    }
} finally {
    Remove-Item $pidSupervisor -ErrorAction SilentlyContinue
    $mutex.ReleaseMutex()
}
