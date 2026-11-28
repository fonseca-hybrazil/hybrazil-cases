#!/usr/bin/env bash
# Atualiza o HyBrazil Cases em producao com a versao mais nova do GitHub.
#
#   cd /opt/hybrazil-cases && sudo bash scripts/producao/atualizar.sh
#
# Baixa o codigo novo, reinstala dependencias, recompila a interface e reinicia o servico.
# As atualizacoes de banco (migracoes) sao aplicadas sozinhas quando o site sobe.
# Recomendado: fazer um backup antes de atualizacoes grandes.
set -euo pipefail

SERVICO=hybrazil-cases
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
UNIT=/etc/systemd/system/$SERVICO.service

[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo: sudo bash $0" >&2; exit 1; }
[ -f "$UNIT" ] || { echo "O servico ainda nao existe. Rode antes o scripts/producao/publicar.sh." >&2; exit 1; }
PORTA=$(grep -o -- '--port [0-9]*' "$UNIT" | awk '{print $2}')
PORTA=${PORTA:-8093}
cd "$RAIZ"

antes=$(git rev-parse --short HEAD)
echo "== Baixando a versao nova (atual: $antes)"
git pull --ff-only
depois=$(git rev-parse --short HEAD)
if [ "$antes" = "$depois" ]; then
    echo "Ja estava na versao mais nova ($depois)."
else
    git --no-pager log --oneline "$antes..$depois" | sed 's/^/  /'
fi

# reinstala dependencias e recompila a interface (o teste rapido e pulado com o servico no ar)
bash "$RAIZ/scripts/producao/instalar.sh"

echo
echo "== Reiniciando o servico"
systemctl restart "$SERVICO"
for _ in $(seq 1 60); do
    sleep 0.5
    if curl -fsS -m 3 "http://127.0.0.1:$PORTA/api/saude" >/dev/null 2>&1; then
        echo "OK: site atualizado para $depois e no ar."
        journalctl -u "$SERVICO" --since "-2min" --no-pager -q | grep -i 'migra' | sed 's/^/  /' || true
        exit 0
    fi
    systemctl is-failed --quiet "$SERVICO" && break
done
echo "FALHOU: o site nao voltou. Ultimas linhas do log:" >&2
journalctl -u "$SERVICO" -n 30 --no-pager >&2
echo "Para voltar o codigo a versao anterior:" >&2
echo "  sudo git reset --hard $antes && sudo bash scripts/producao/instalar.sh && sudo systemctl restart $SERVICO" >&2
exit 1
