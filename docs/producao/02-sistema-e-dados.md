# Produção — 2. Instalar o sistema e trazer os dados

Pré-requisito: o [passo 1](01-postgresql.md) concluído. Isso quer dizer o PostgreSQL rodando, o projeto em `/opt/hybrazil-cases` e a linha `DATABASE_URL=...` do `criar-banco.sh` guardada.

## 1. Instalar o sistema no servidor

```bash
cd /opt/hybrazil-cases
sudo git pull                                   # traz os scripts mais novos
sudo bash scripts/producao/instalar.sh
```

O script pode ser rodado de novo sem problema. Ele faz o seguinte:

| Etapa | O que acontece |
|---|---|
| Python e Node | Instala o Python 3.12 e o Node.js 22, que só é usado para compilar a interface. |
| Usuário `hybrazil` | Cria o usuário de sistema que vai rodar o site, **sem login e sem senha**. Ninguém entra no servidor com ele. |
| Pasta dos anexos | Cria `/var/lib/hybrazil-cases/uploads`, com dono `hybrazil` e permissão `700`. Só o site lê e grava ali. |
| Dependências | Cria o ambiente Python (`backend/.venv`) e compila a interface (`frontend/dist`). |
| `.env` | Pede a linha `DATABASE_URL=...`. **Cole a linha e tecle Enter; ela não aparece na tela.** O script cria o `backend/.env`, que só o root e o `hybrazil` conseguem ler. |
| Teste | Sobe o site por alguns segundos com o usuário `hybrazil` e confere se conectou no banco e entregou a interface. |

O resultado esperado no final é `OK: o site subiu com o usuario hybrazil...`.

> Se o banco ainda estiver vazio, o teste cria um **admin provisório**. Ele some quando o backup for restaurado no item 2.

> **Se o `pip` ou o `npm` ficarem muito lentos ou travarem:** é o mesmo problema de IPv6 do `dnf`. Faça o servidor preferir IPv4 e rode o script de novo:
> ```bash
> echo "precedence ::ffff:0:0/96  100" | sudo tee -a /etc/gai.conf
> ```

## 2. Trazer o backup desta máquina

### 2.1 Fazer um backup novo (no Windows)

Use um backup feito **na hora**, para ir com tudo o que foi feito até agora. No PowerShell, na pasta do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1 -Nome producao
```

O backup fica em `runtime\backups\producao-<data-hora>\`, com `banco.dump`, `anexos\` e `info.txt`, cerca de 2 GB.

> **A partir daqui, não use mais o site local para trabalho de verdade.** O que for feito nele depois do backup não vai para a produção. Se precisar, dá para repetir os passos 2.1 a 2.3 depois: a restauração pode ser feita quantas vezes quiser.

### 2.2 Copiar para o servidor

O Windows já tem o `scp`. Troque `usuario` e `servidor` pelo seu login e pelo endereço do CentOS:

```powershell
scp -r runtime\backups\producao-AAAAMMDD-HHMMSS usuario@servidor:~/
```

Também dá para copiar pelo **WinSCP**, arrastando a pasta para a sua pasta pessoal no servidor.

### 2.3 Restaurar no servidor

```bash
cd /opt/hybrazil-cases
sudo bash scripts/producao/restaurar-backup.sh ~/producao-AAAAMMDD-HHMMSS
```

O script mostra o que tem no backup e pede para digitar `RESTAURAR`. Depois disso:

1. Para o site, se ele já estiver rodando como serviço.
2. Recria o banco a partir do backup, conectando como o **próprio usuário do site** (não precisa de superusuário).
3. Copia os anexos para `/var/lib/hybrazil-cases/uploads`, com dono `hybrazil` e acesso só dele.
4. Confere as contagens (projetos, tickets, comentários, anexos…) com as do `info.txt`. O resultado esperado é `Conferido: iguais as do momento do backup.`

As atualizações de banco que vieram depois do backup (por exemplo, os ícones de projeto) são aplicadas sozinhas quando o site sobe.

Depois de conferir, apague a cópia do backup da sua pasta pessoal. Ela tem todos os dados do sistema:

```bash
rm -rf ~/producao-AAAAMMDD-HHMMSS
```

> A restauração foi testada com o backup real (`pos-migracao-ora`) num PostgreSQL 18 e com o usuário restrito do site. As contagens bateram, e a atualização de banco que faltava (ícones) foi aplicada sozinha em seguida.

## 3. Ver o site antes de publicar (opcional)

O site ainda não está aberto na rede; isso vem no passo 3, com o nginx. Para olhar agora, suba o site à mão no servidor:

```bash
cd /opt/hybrazil-cases/backend
sudo -u hybrazil .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Num PowerShell desta máquina, abra um "túnel" até ele:

```powershell
ssh -L 8001:127.0.0.1:8000 usuario@servidor
```

Abra <http://localhost:8001> e entre com o seu usuário de sempre. Para parar, use `Ctrl+C` no servidor e feche o túnel.

## Próximo passo

3. Rodar o site como **serviço** (`systemd`, sobe sozinho com o servidor) e publicá-lo na rede pelo **nginx com HTTPS**.
