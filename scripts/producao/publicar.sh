#!/usr/bin/env bash
# Publica o HyBrazil Cases na rede como servico systemd, na porta 8093 (CentOS Stream 9 / RHEL 9).
# O HTTPS e o redirecionamento do dominio ficam no pfSense (HAProxy), fora deste servidor.
# Rode DEPOIS do instalar.sh (e da restauracao do backup). Pode ser rodado de novo sem problema.
#
#   cd /opt/hybrazil-cases && sudo bash scripts/producao/publicar.sh
#
# Opcoes:
#   --porta N      porta em que o site escuta (padrao: 8093)
#   --proxy IP     opcional: IP do pfSense visto por este servidor. Com ele, so o pfSense acessa a porta
#                  e o site registra o IP real de quem fez login (cabecalho X-Forwarded-For).
#
# O que faz:
#   1. liga COOKIE_SECURE=true no backend/.env (o navegador acessa por HTTPS, via pfSense);
#   2. servico 'hybrazil-cases': roda o site com o usuario hybrazil na porta escolhida, sobe com o servidor
#      e reinicia sozinho se cair;
#   3. firewall: libera a porta (para a rede, ou so para o --proxy).
set -euo pipefail

SERVICO=hybrazil-cases
APP_USER=hybrazil
DADOS=/var/lib/hybrazil-cases
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
ENV_ARQ=$RAIZ/backend/.env
UNIT=/etc/systemd/system/$SERVICO.service

PORTA=8093
PROXY=
while [ $# -gt 0 ]; do
    case "$1" in
        --porta) PORTA=$2; shift 2 ;;
        --proxy) PROXY=$2; shift 2 ;;
        *) echo "Opcao desconhecida: $1" >&2; exit 1 ;;
    esac
done

[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo: sudo bash $0" >&2; exit 1; }
[ -x "$RAIZ/backend/.venv/bin/uvicorn" ] && [ -f "$RAIZ/frontend/dist/index.html" ] && [ -f "$ENV_ARQ" ] \
    || { echo "Rode antes o scripts/producao/instalar.sh." >&2; exit 1; }
[[ "$PORTA" =~ ^[0-9]+$ ]] && [ "$PORTA" -ge 1024 ] && [ "$PORTA" -le 65535 ] \
    || { echo "Porta invalida: $PORTA (use de 1024 a 65535)." >&2; exit 1; }
if [ -n "$PROXY" ]; then
    [[ "$PROXY" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || { echo "IP do proxy invalido: $PROXY" >&2; exit 1; }
    CONFIAVEIS="127.0.0.1,$PROXY"
else
    CONFIAVEIS="127.0.0.1"
fi
passo() { echo; echo "== $*"; }

passo "1. Cookie de login so por HTTPS (COOKIE_SECURE=true)"
if grep -q '^COOKIE_SECURE=' "$ENV_ARQ"; then
    sed -i 's/^COOKIE_SECURE=.*/COOKIE_SECURE=true/' "$ENV_ARQ"
else
    echo "COOKIE_SECURE=true" >>"$ENV_ARQ"
fi
chown root:"$APP_USER" "$ENV_ARQ"; chmod 640 "$ENV_ARQ"
echo "Feito. O login passa a funcionar so pelo endereco https do pfSense."

passo "2. Servico '$SERVICO' na porta $PORTA"
cat >"$UNIT" <<EOF
# Gerado por scripts/producao/publicar.sh
[Unit]
Description=HyBrazil Cases
After=network-online.target postgresql-18.service
Wants=network-online.target postgresql-18.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$RAIZ/backend
Environment=PYTHONDONTWRITEBYTECODE=1
# um processo so: as atualizacoes de banco rodam na subida e nao podem rodar em paralelo.
# --forwarded-allow-ips: de quem o site aceita o IP real do usuario (X-Forwarded-For).
ExecStart=$RAIZ/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORTA --proxy-headers --forwarded-allow-ips $CONFIAVEIS --no-server-header --no-access-log --timeout-keep-alive 65
Restart=on-failure
RestartSec=5
TimeoutStopSec=20
# arquivos criados pelo site (anexos) ficam acessiveis so pelo usuario $APP_USER
UMask=0077
# protecoes: o site so consegue gravar na pasta de dados
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=$DADOS
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
if ! systemctl is-active --quiet "$SERVICO" && ss -ltn | grep -q ":$PORTA "; then
    echo "A porta $PORTA esta ocupada por outro programa. Libere-a ou escolha outra com --porta:" >&2
    ss -ltnp | grep ":$PORTA " >&2
    exit 1
fi
systemctl enable "$SERVICO" >/dev/null 2>&1
systemctl restart "$SERVICO"
ok=0
for _ in $(seq 1 60); do
    sleep 0.5
    if curl -fsS -m 3 "http://127.0.0.1:$PORTA/api/saude" >/dev/null 2>&1; then ok=1; break; fi
    systemctl is-failed --quiet "$SERVICO" && break
done
if [ $ok -ne 1 ]; then
    echo "O servico nao respondeu. Ultimas linhas do log:" >&2
    journalctl -u "$SERVICO" -n 30 --no-pager >&2
    exit 1
fi
echo "Rodando na porta $PORTA e ligado na subida do servidor."

passo "3. Firewall: porta $PORTA"
if systemctl is-active --quiet firewalld; then
    # tira regras antigas desta porta (ex.: de outro IP de proxy) e libera so para o proxy atual
    while IFS= read -r regra; do
        [ -n "$regra" ] && firewall-cmd -q --permanent --remove-rich-rule="$regra"
    done < <(firewall-cmd --permanent --list-rich-rules | grep "port=\"$PORTA\"" || true)
    firewall-cmd -q --permanent --remove-port="$PORTA/tcp" 2>/dev/null || true
    if [ -n "$PROXY" ]; then
        firewall-cmd -q --permanent --add-rich-rule="rule family=\"ipv4\" source address=\"$PROXY\" port port=\"$PORTA\" protocol=\"tcp\" accept"
        quem="so para $PROXY"
    else
        firewall-cmd -q --permanent --add-port="$PORTA/tcp"
        quem="para a rede"
    fi
    firewall-cmd -q --reload
    echo "Porta $PORTA liberada $quem (zona $(firewall-cmd --get-default-zone))."
else
    echo "ATENCAO: o firewalld nao esta rodando; a porta $PORTA fica aberta para toda a rede." >&2
fi

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo
echo "Site publicado em http://$IP:$PORTA  (verificacao de saude: /api/saude)"
echo "Aponte o HAProxy do pfSense para esse endereco. O login so funciona pelo endereco https do dominio."
echo "Comandos uteis: systemctl status $SERVICO  |  journalctl -u $SERVICO -f  |  sudo bash scripts/producao/atualizar.sh"
