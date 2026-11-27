# Produção — 1. Instalar o PostgreSQL (CentOS)

Este guia instala o PostgreSQL 18 no servidor **CentOS** e cria o banco do HyBrazil Cases. O site usa um **usuário exclusivo**, que só consegue mexer no banco dele.

> O site e o banco ficam na **mesma máquina**. Por isso o banco não aceita conexões pela rede.

Todos os comandos são rodados no servidor, por SSH, com um usuário que tenha `sudo`.

## 0. Conferir a versão do sistema

```bash
cat /etc/os-release
```

| `VERSION_ID` | Situação |
|---|---|
| **9** ou **10** (CentOS Stream 9/10, Rocky, Alma, RHEL) | Siga este guia. |
| **8** | Funciona com os mesmos comandos. Mas o CentOS 8 está **sem atualizações de segurança** desde 2021; se possível, use uma versão 9 ou 10. |
| **7** | **Não dá.** O CentOS 7 está sem suporte desde junho de 2024, e o repositório oficial não tem PostgreSQL 18 para ele. É preciso atualizar o sistema (ou trocar por Rocky/Alma 9) antes. |

## 1. Instalar o PostgreSQL 18

O CentOS traz versões antigas do PostgreSQL. Por isso usamos o **repositório oficial do PostgreSQL** (PGDG):

```bash
# repositório oficial (detecta sozinho se o sistema é 8, 9 ou 10)
sudo dnf install -y "https://download.postgresql.org/pub/repos/yum/reporpms/EL-$(rpm -E %{rhel})-$(uname -m)/pgdg-redhat-repo-latest.noarch.rpm"

# SÓ NO CENTOS STREAM: o repositório monta o endereço com a versão "menor" do sistema (ex.: rhel-9.7-...),
# que o Stream não tem. Troca pelo endereço sem versão menor (ex.: rhel-9-x86_64), que existe no servidor do PostgreSQL.
sudo sed -i "s/rhel-\$releasever_major\.\$releasever_minor-/rhel-$(rpm -E %{rhel})-/" /etc/yum.repos.d/pgdg-redhat-all.repo
sudo dnf clean all

# só no 8 e no 9: desliga o PostgreSQL antigo do sistema, para não haver conflito (é uma precaução)
sudo dnf -qy module disable postgresql

# servidor + extensões (a busca do sistema usa unaccent e pg_trgm, que vêm no "contrib")
# glibc-langpack-en garante o locale en_US.UTF-8 (num sistema em inglês normalmente já está instalado)
sudo dnf install -y postgresql18-server postgresql18-contrib glibc-langpack-en
```

### Se aparecer "No match for argument: postgresql18-server"

O `dnf` não está enxergando o repositório do PostgreSQL 18. Confira:

```bash
rpm -q pgdg-redhat-repo                 # o repositório oficial está instalado? qual versão?
dnf repolist all | grep -i pgdg         # deve aparecer "pgdg18 ... enabled"
```

- **`pgdg-redhat-repo` não instalado:** o primeiro comando do passo 1 falhou. Rode de novo e veja a mensagem de erro. Normalmente é falta de acesso a `download.postgresql.org`, por proxy ou firewall da rede.
- **Instalado, mas sem `pgdg18` na lista:** é uma versão antiga do pacote, de antes do PostgreSQL 18. Atualize e limpe o cache:

  ```bash
  sudo dnf upgrade -y pgdg-redhat-repo
  sudo dnf clean all && sudo dnf makecache
  ```

- **`pgdg18` aparece como `disabled`:** `sudo dnf config-manager --set-enabled pgdg18`.

Depois, `dnf list postgresql18-server` deve mostrar o pacote. Então rode de novo o `dnf install` acima.

### Se aparecer "Failed to download metadata for repo 'pgdg-...'"

O repositório está configurado, mas o servidor não consegue baixar de `download.postgresql.org`:

```bash
curl -sSI https://download.postgresql.org/pub/repos/yum/common/redhat/rhel-9-x86_64/repodata/repomd.xml | head -1
getent hosts download.postgresql.org                      # o nome resolve?
env | grep -i proxy; grep -i proxy /etc/dnf/dnf.conf      # a rede usa proxy?
```

| O `curl` respondeu… | Causa e solução |
|---|---|
| `HTTP/... 200` | A rede funciona; o problema é o endereço que o `dnf` monta. Veja com `grep -m2 baseurl /etc/yum.repos.d/pgdg-redhat-all.repo`. Se aparecer `$releasever_major.$releasever_minor`, é o caso do **CentOS Stream**: aplique o comando `sed` do passo 1. Se a rede não tiver IPv6 (`curl -6 ...` falha e `curl -4 ...` dá 200), também force IPv4 no dnf: `echo "ip_resolve=4" \| sudo tee -a /etc/dnf/dnf.conf`. |
| `Could not resolve host` | DNS. Confira `/etc/resolv.conf` com o pessoal de rede. |
| `Connection timed out` / `Failed to connect` | Firewall ou proxy. Se a empresa usa proxy, coloque `proxy=http://endereco:porta` em `/etc/dnf/dnf.conf`. Senão, peça a liberação de `download.postgresql.org` (porta 443). |
| `SSL certificate problem` | O proxy da empresa inspeciona HTTPS. Instale o certificado da empresa em `/etc/pki/ca-trust/source/anchors/` e rode `sudo update-ca-trust`. |

**Sem acesso à internet:** baixe numa máquina com acesso os pacotes `postgresql18`, `postgresql18-libs`, `postgresql18-server` e `postgresql18-contrib` da pasta <https://download.postgresql.org/pub/repos/yum/18/redhat/rhel-9-x86_64/>, todos da mesma versão. Copie para o servidor e rode `sudo dnf install -y ./postgresql18-*.rpm`. As outras dependências vêm dos repositórios do CentOS.

## 2. Criar o cluster e ligar o serviço

```bash
# cria a pasta de dados em UTF-8, no mesmo idioma do servidor (inglês)
sudo PGSETUP_INITDB_OPTIONS="--encoding=UTF8 --locale=en_US.UTF-8" /usr/pgsql-18/bin/postgresql-18-setup initdb

# inicia agora e a cada boot
sudo systemctl enable --now postgresql-18
systemctl status postgresql-18 --no-pager
```

O status deve mostrar `active (running)`. Os dados ficam em `/var/lib/pgsql/18/data/`.

> **Por que `en_US.UTF-8`:** o locale do banco só define a ordenação de textos e o idioma das mensagens do próprio PostgreSQL. Com `en_US.UTF-8`, os logs do banco ficam em inglês como o resto do servidor. Os nomes com acento continuam em ordem (Ágata junto com A). A busca do sistema não depende disso: ela usa o dicionário `portuguese` e o `unaccent`, definidos pelo próprio sistema. O importante é ser **UTF-8**.

> **Disco separado para os dados:** se o servidor tiver um disco só para dados, prefira montá-lo em `/var/lib/pgsql` **antes** do passo 2. Mudar a pasta de dados depois exige ajustar o serviço e o SELinux.

## 3. Conferir que o banco não está aberto para a rede

No repositório oficial, o PostgreSQL já vem ouvindo **somente localhost** e com senha `scram-sha-256`. Confira:

```bash
sudo -u postgres psql -c "SHOW listen_addresses"   # deve ser: localhost
sudo ss -ltnp | grep 5432                          # deve mostrar só 127.0.0.1 e ::1
sudo firewall-cmd --list-all                       # a porta 5432 / "postgresql" NÃO deve aparecer
```

O superusuário `postgres` não tem senha. Ele só entra no banco pelo próprio servidor, com `sudo -u postgres` (autenticação "peer"). Assim, não existe senha de administrador do banco que possa vazar.

## 4. Criar o banco e o usuário do site

Coloque o projeto no servidor, por exemplo com `git clone https://github.com/fonseca-hybrazil/hybrazil-cases.git` (o passo de instalar o sistema detalha isso). Depois, na pasta do projeto:

```bash
sudo -u postgres bash scripts/producao/criar-banco.sh
```

O script:

1. Cria o usuário **`hybrazil_cases`** com uma senha aleatória de 32 caracteres. Esse usuário não é superusuário, não cria bancos nem usuários e não faz replicação.
2. Cria o banco **`hybrazil_cases`** com esse usuário como dono. O site precisa ser dono para aplicar sozinho as atualizações do esquema.
3. Bloqueia o banco para os outros usuários comuns (`REVOKE ALL ... FROM PUBLIC`).
4. Cria as extensões de busca (`unaccent` e `pg_trgm`) em nome do usuário do site. Assim ele mesmo consegue restaurar backups.
5. Coloca regras no **topo do `pg_hba.conf`**, que é o controle de acesso do PostgreSQL. O arquivo original ganha uma cópia ao lado. Com essas regras, o `hybrazil_cases` **só conecta no banco `hybrazil_cases`, só pela própria máquina e só com senha**. Depois o script recarrega a configuração e confere se ela ficou válida; se não ficou, volta o arquivo original.
6. Mostra a linha `DATABASE_URL=...` para o `backend/.env` do servidor. **Guarde essa linha:** a senha não aparece de novo. Se ela se perder, rode o script outra vez com `--redefinir-senha`.

Outros nomes ou porta: `--usuario`, `--banco`, `--porta`.

### O que o usuário do site pode e não pode fazer

| Ação | Resultado |
|---|---|
| Conectar no banco `hybrazil_cases` pela própria máquina, com a senha | permitido |
| Criar, alterar e apagar tabelas e dados **no próprio banco** (migrações, restauração de backup) | permitido |
| Conectar em qualquer outro banco (`postgres` ou outros) | recusado pelo `pg_hba.conf` |
| Conectar de outra máquina | recusado (o banco nem escuta a rede) |
| Criar bancos ou usuários, virar superusuário | recusado |
| Outros usuários comuns conectarem no banco do site | recusado |

O script foi testado num PostgreSQL 18.6. Foram verificados cada item da tabela, as 3 migrações do sistema rodando com esse usuário e a recriação do esquema que a restauração de backup faz.

## 5. Conferir

```bash
/usr/pgsql-18/bin/psql "postgresql://hybrazil_cases@localhost/hybrazil_cases" -c "select current_user"   # pede a senha; mostra hybrazil_cases
/usr/pgsql-18/bin/psql "postgresql://hybrazil_cases@localhost/postgres" -c "select 1"                    # deve dar: pg_hba.conf rejects connection
```

## Próximos passos

2. Instalar o sistema no servidor: Python, a pasta do projeto, o `backend/.env` com a `DATABASE_URL` acima e a pasta dos anexos (`UPLOAD_DIR`).
3. Levar os dados atuais desta máquina para o servidor (banco + anexos).
4. Rodar o site como serviço (`systemd`), com um usuário próprio do sistema e com a pasta de anexos acessível só por ele, atrás do nginx com HTTPS.
5. Configurar o backup semanal para o SharePoint, mantendo os 2 últimos.
