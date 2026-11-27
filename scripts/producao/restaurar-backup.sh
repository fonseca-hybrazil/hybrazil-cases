#!/usr/bin/env bash
# Restaura no servidor de PRODUCAO um backup feito pelo scripts\backup.ps1 (Windows) ou pelo backup de producao:
# uma pasta com banco.dump, anexos/ e info.txt.
#
#   sudo bash scripts/producao/restaurar-backup.sh /caminho/da/pasta-do-backup
#
# O que faz:
#   1. confere o backup (banco.dump, anexos/, contagens no info.txt);
#   2. para o site, se ele ja estiver rodando como servico (hybrazil-cases);
#   3. apaga e recria o banco a partir do backup, conectando como o PROPRIO usuario do site
#      (que e dono do banco; nao precisa de superusuario);
#   4. copia os anexos para a pasta do site, com dono hybrazil e acesso so dele;
#   5. confere as contagens com as do info.txt e religa o site.
# ATENCAO: o que estiver no banco de producao agora e substituido pelo backup.
set -euo pipefail

APP_USER=hybrazil
SERVICO=hybrazil-cases
PG_BIN=/usr/pgsql-18/bin
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
ENV_ARQ=$RAIZ/backend/.env

[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo: sudo bash $0 <pasta-do-backup>" >&2; exit 1; }
[ $# -ge 1 ] || { echo "Uso: sudo bash $0 <pasta-do-backup> [--sim]" >&2; exit 2; }
BACKUP=$(cd "$1" && pwd)
SIM=${2:-}
DUMP=$BACKUP/banco.dump
[ -f "$DUMP" ] || { echo "Nao achei $DUMP." >&2; exit 1; }
[ -f "$ENV_ARQ" ] || { echo "Nao achei $ENV_ARQ. Rode antes o instalar.sh." >&2; exit 1; }

valor_env() { grep -m1 "^$1=" "$ENV_ARQ" | cut -d= -f2- | tr -d '\r'; }
URL=$(valor_env DATABASE_URL)
UPLOADS=$(valor_env UPLOAD_DIR)
[[ "$URL" =~ ^postgresql\+psycopg://([^:]+):([^@]+)@([^:/]+):([0-9]+)/([^?]+) ]] || { echo "DATABASE_URL em formato inesperado." >&2; exit 1; }
export PGUSER=${BASH_REMATCH[1]} PGPASSWORD=${BASH_REMATCH[2]} PGHOST=${BASH_REMATCH[3]} PGPORT=${BASH_REMATCH[4]}
BANCO=${BASH_REMATCH[5]}
[ -n "$UPLOADS" ] || { echo "UPLOAD_DIR nao definido no .env." >&2; exit 1; }

# contagens que o backup registrou (info.txt foi gravado no Windows: pode ter BOM e CRLF)
esperado=""
[ -f "$BACKUP/info.txt" ] && esperado=$(sed 's/\r$//; s/^\xEF\xBB\xBF//' "$BACKUP/info.txt" | grep -E '^[a-z_]+=[0-9]+$' || true)
n_anexos=0
[ -d "$BACKUP/anexos" ] && n_anexos=$(find "$BACKUP/anexos" -type f | wc -l)

echo "Backup:  $BACKUP"
echo "         banco.dump $(du -h "$DUMP" | cut -f1), anexos: $n_anexos arquivos ($(du -sh "$BACKUP/anexos" 2>/dev/null | cut -f1))"
[ -n "$esperado" ] && echo "$esperado" | sed 's/^/         /'
echo "Destino: banco '$BANCO' (usuario $PGUSER) + anexos em $UPLOADS"
if [ "$SIM" != "--sim" ]; then
    echo "O que estiver no banco de producao agora sera SUBSTITUIDO pelo backup."
    read -rp "Digite RESTAURAR para continuar: " resp
    [ "$resp" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }
fi

contagens() {
    "$PG_BIN/psql" -X -q -t -A -F= -d "$BANCO" -c "select 'projetos', count(*) from projetos union all select 'tickets', count(*) from tickets
        union all select 'comentarios', count(*) from comentarios union all select 'anexos', count(*) from anexos
        union all select 'atividades', count(*) from atividades union all select 'labels', count(*) from labels
        union all select 'usuarios', count(*) from usuarios"
}

ativo=0
if systemctl is-active --quiet "$SERVICO" 2>/dev/null; then
    ativo=1
    echo "Parando o site ($SERVICO)..."
    systemctl stop "$SERVICO"
fi
religar() { [ $ativo -eq 1 ] && { echo "Religando o site..."; systemctl start "$SERVICO"; } || true; }
trap religar EXIT

echo "Recriando o banco a partir do backup..."
"$PG_BIN/psql" -X -q -v ON_ERROR_STOP=1 -d "$BANCO" \
    -c "SET client_min_messages TO warning; DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# --no-owner/--no-privileges: os objetos ficam do usuario do site, sem depender dos usuarios da maquina de origem
"$PG_BIN/pg_restore" -d "$BANCO" --no-owner --no-privileges --no-comments --exit-on-error "$DUMP"

if [ -d "$BACKUP/anexos" ]; then
    echo "Copiando os anexos..."
    install -d -m 700 -o "$APP_USER" -g "$APP_USER" "$UPLOADS"
    # espelha: arquivos que nao estao no backup saem da pasta (como no restaurar.ps1)
    rsync -a --delete "$BACKUP/anexos/" "$UPLOADS/"
    chown -R "$APP_USER:$APP_USER" "$UPLOADS"
    find "$UPLOADS" -type d -exec chmod 700 {} +
    find "$UPLOADS" -type f -exec chmod 600 {} +
    command -v restorecon >/dev/null && restorecon -R "$UPLOADS" || true
fi

obtido=$(contagens)
echo "Contagens restauradas:"; echo "$obtido" | sed 's/^/  /'
if [ -n "$esperado" ]; then
    if [ "$obtido" = "$esperado" ]; then
        echo "Conferido: iguais as do momento do backup."
    else
        echo "ATENCAO: as contagens NAO batem com o info.txt do backup." >&2
        exit 1
    fi
fi
echo "Anexos na pasta do site: $(find "$UPLOADS" -type f | wc -l) arquivos."
echo "Restauracao concluida."
