#!/usr/bin/env bash
# Instala (ou reinstala) o HyBrazil Cases no servidor de PRODUCAO (CentOS Stream 9 / RHEL 9).
# Pode ser rodado de novo sem problema: so faz o que estiver faltando e recompila.
#
#   cd /opt/hybrazil-cases && sudo bash scripts/producao/instalar.sh
#
# O que faz:
#   1. instala Python 3.12 e Node.js 22 (para compilar a interface);
#   2. cria o usuario de sistema 'hybrazil', que vai rodar o site (sem login, sem senha);
#   3. cria a pasta dos anexos /var/lib/hybrazil-cases/uploads, acessivel SO pelo usuario hybrazil;
#   4. cria o ambiente Python (backend/.venv) e compila a interface (frontend/dist);
#   5. cria o backend/.env (pede a linha DATABASE_URL gerada pelo criar-banco.sh), legivel so pelo hybrazil;
#   6. testa: sobe o site por alguns segundos em 127.0.0.1:8000 com o usuario hybrazil e confere se responde.
set -euo pipefail

APP_USER=hybrazil
DADOS=/var/lib/hybrazil-cases
UPLOADS=$DADOS/uploads
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
ENV_ARQ=$RAIZ/backend/.env
PY=python3.12

[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo: sudo bash $0" >&2; exit 1; }
[ -f "$RAIZ/backend/requirements.txt" ] || { echo "Nao achei o projeto em $RAIZ." >&2; exit 1; }
passo() { echo; echo "== $*"; }

passo "1. Python 3.12 e Node.js 22"
command -v $PY >/dev/null || dnf install -y python3.12 python3.12-pip
command -v rsync >/dev/null || dnf install -y rsync   # usado na restauracao dos anexos
node_ok() { command -v node >/dev/null && node -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit(a>22||(a===22&&b>=12)||(a===20&&b>=19)?0:1)'; }
if ! node_ok; then
    dnf module reset -y nodejs || true
    dnf module install -y nodejs:22/common
fi
echo "Python: $($PY --version)  |  Node: $(node --version)"

passo "2. Usuario de sistema '$APP_USER'"
if id "$APP_USER" >/dev/null 2>&1; then
    echo "Ja existe."
else
    useradd --system --home-dir "$DADOS" --no-create-home --shell /sbin/nologin "$APP_USER"
    echo "Criado (sem login e sem senha)."
fi

passo "3. Pasta dos anexos: $UPLOADS"
install -d -m 700 -o "$APP_USER" -g "$APP_USER" "$DADOS" "$UPLOADS"
echo "Dono $APP_USER, permissao 700 (ninguem mais le)."

passo "4. Ambiente Python e interface"
cd "$RAIZ/backend"
[ -x .venv/bin/python ] || $PY -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -m compileall -q app >/dev/null
echo "Dependencias do Python instaladas."
cd "$RAIZ/frontend"
npm ci --no-fund --no-audit --loglevel=error
npx vite build --outDir dist-novo --emptyOutDir --logLevel warn
rm -rf dist && mv dist-novo dist
echo "Interface compilada em frontend/dist."

passo "5. Configuracao (backend/.env)"
if [ -f "$ENV_ARQ" ] && grep -q '^DATABASE_URL=' "$ENV_ARQ"; then
    echo "Ja existe com DATABASE_URL (mantido)."
else
    echo "Cole a linha DATABASE_URL=... mostrada pelo criar-banco.sh e tecle Enter (nao aparece na tela):"
    read -rs linha; echo
    linha=${linha#"${linha%%[![:space:]]*}"}; linha=${linha%"${linha##*[![:space:]]}"}
    [[ "$linha" == DATABASE_URL=postgresql+psycopg://* ]] || { echo "Linha invalida (deve comecar com DATABASE_URL=postgresql+psycopg://)." >&2; exit 1; }
    umask 027
    cat >"$ENV_ARQ" <<EOF
# HyBrazil Cases - producao (criado por scripts/producao/instalar.sh)
$linha
UPLOAD_DIR=$UPLOADS
# Mude para true quando o site estiver atras do HTTPS (nginx):
COOKIE_SECURE=false
EOF
    echo "Criado."
fi
chown root:"$APP_USER" "$ENV_ARQ"
chmod 640 "$ENV_ARQ"
echo "Permissao: root le e escreve, $APP_USER so le, mais ninguem."

passo "6. Teste rapido (127.0.0.1:8000)"
if ss -ltn | grep -q ':8000 '; then
    echo "A porta 8000 ja esta em uso (o servico ja deve estar rodando). Teste pulado."
else
    log=$(mktemp)
    cd "$RAIZ/backend"
    sudo -u "$APP_USER" env PYTHONDONTWRITEBYTECODE=1 .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 >"$log" 2>&1 &
    pid=$!
    ok=0
    for _ in $(seq 1 40); do
        sleep 0.5
        if curl -fsS http://127.0.0.1:8000/api/saude >/dev/null 2>&1; then ok=1; break; fi
        kill -0 $pid 2>/dev/null || break
    done
    tela=$(curl -fsS http://127.0.0.1:8000/ 2>/dev/null | grep -c '<div id="root">' || true)
    kill $pid 2>/dev/null || true; wait $pid 2>/dev/null || true
    if [ $ok -eq 1 ] && [ "$tela" -ge 1 ]; then
        echo "OK: o site subiu com o usuario $APP_USER, conectou no banco e entregou a interface."
        grep -i 'senha gerada' "$log" >/dev/null && echo "(Banco vazio: foi criado um admin provisorio. Ele some quando o backup for restaurado.)"
    else
        echo "FALHOU. Ultimas linhas do log:" >&2
        tail -25 "$log" >&2
        rm -f "$log"; exit 1
    fi
    rm -f "$log"
fi

echo
echo "Instalacao concluida. Proximo passo: restaurar o backup (scripts/producao/restaurar-backup.sh)."
