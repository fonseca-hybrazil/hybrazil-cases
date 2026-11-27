#!/usr/bin/env bash
# Cria o banco do HyBrazil Cases no PostgreSQL de PRODUCAO (CentOS / RHEL), com um usuario exclusivo do site.
#
# O usuario do site (padrao: hybrazil_cases):
#   - e dono apenas do banco do site (precisa disso para aplicar as migracoes do sistema);
#   - NAO e superusuario, NAO cria bancos nem usuarios, NAO faz replicacao;
#   - pelo pg_hba.conf, so conecta no banco dele, so pela propria maquina (TCP em localhost) e com senha;
#   - nenhum outro usuario comum consegue conectar no banco do site (REVOKE ... FROM PUBLIC).
# A senha do usuario do site e gerada aqui (32 caracteres) e mostrada uma unica vez, ja no formato do .env.
#
# Rode como o usuario 'postgres' do sistema (entra no banco sem senha e pode editar o pg_hba.conf):
#   sudo -u postgres bash scripts/producao/criar-banco.sh
# Opcoes:
#   --usuario NOME   --banco NOME   --porta 5432
#   --redefinir-senha      gera senha nova se o usuario ja existir
set -euo pipefail

USUARIO=hybrazil_cases
BANCO=hybrazil_cases
PORTA=5432
REDEFINIR=0
while [ $# -gt 0 ]; do
    case "$1" in
        --usuario) USUARIO="$2"; shift 2 ;;
        --banco) BANCO="$2"; shift 2 ;;
        --porta) PORTA="$2"; shift 2 ;;
        --redefinir-senha) REDEFINIR=1; shift ;;
        *) echo "Opcao desconhecida: $1" >&2; exit 2 ;;
    esac
done
for nome in "$USUARIO" "$BANCO"; do
    [[ "$nome" =~ ^[a-z_][a-z0-9_]{0,62}$ ]] || { echo "Use so letras minusculas, numeros e _ em '$nome'." >&2; exit 2; }
done

PSQL="${PSQL:-psql}"
export PGPORT="${PGPORT:-$PORTA}"
sql() {  # sql BANCO "comando"
    "$PSQL" -X -q -t -A -v ON_ERROR_STOP=1 -d "$1" -c "$2"
}

versao=$(sql postgres "SHOW server_version")
[ "$(sql postgres "SELECT rolsuper FROM pg_roles WHERE rolname = current_user")" = "t" ] || {
    echo "Rode como superusuario: sudo -u postgres bash $0" >&2; exit 1; }
echo "Conectado ao PostgreSQL $versao (porta $PGPORT)."

# --- 1. usuario do site ---
senha=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32 || true)
[ ${#senha} -eq 32 ] || { echo "Falha ao gerar a senha." >&2; exit 1; }
if [ -n "$(sql postgres "SELECT 1 FROM pg_roles WHERE rolname = '$USUARIO'")" ]; then
    if [ "$REDEFINIR" -ne 1 ]; then
        echo "O usuario '$USUARIO' ja existe. Rode de novo com --redefinir-senha para gerar uma senha nova." >&2
        exit 1
    fi
    sql postgres "ALTER ROLE $USUARIO PASSWORD '$senha'" >/dev/null
    echo "Usuario '$USUARIO' ja existia: senha redefinida."
else
    sql postgres "CREATE ROLE $USUARIO LOGIN PASSWORD '$senha'" >/dev/null
    echo "Usuario '$USUARIO' criado."
fi
sql postgres "ALTER ROLE $USUARIO NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS INHERIT CONNECTION LIMIT 50" >/dev/null

# --- 2. banco do site, com o usuario como dono ---
if [ -n "$(sql postgres "SELECT 1 FROM pg_database WHERE datname = '$BANCO'")" ]; then
    echo "Banco '$BANCO' ja existe (mantido como esta)."
    sql postgres "ALTER DATABASE $BANCO OWNER TO $USUARIO" >/dev/null
else
    sql postgres "CREATE DATABASE $BANCO OWNER $USUARIO ENCODING 'UTF8' TEMPLATE template0" >/dev/null
    echo "Banco '$BANCO' criado."
fi
# Ninguem alem do dono (e do superusuario) conecta ou cria objetos temporarios nesse banco.
sql postgres "REVOKE ALL ON DATABASE $BANCO FROM PUBLIC" >/dev/null
# Extensoes da busca, criadas em nome do usuario do site para que ele mesmo consiga restaurar backups.
# (no CentOS elas vem no pacote postgresql18-contrib)
sql "$BANCO" "SET client_min_messages TO warning; SET ROLE $USUARIO; CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm;" >/dev/null
echo "Extensoes unaccent e pg_trgm prontas."

# --- 3. pg_hba.conf: o usuario do site so entra no banco dele, pela propria maquina ---
hba=$(sql postgres "SHOW hba_file")
marca="# HyBrazil Cases: usuario $USUARIO"
if grep -qxF "$marca" "$hba"; then
    echo "pg_hba.conf ja tem as regras do usuario '$USUARIO'."
else
    copia="$hba.antes-hybrazil-$(date +%Y%m%d-%H%M%S)"
    cp -p "$hba" "$copia"
    regras=$(printf '%s\n' \
        "$marca" \
        "host    $BANCO    $USUARIO    127.0.0.1/32    scram-sha-256" \
        "host    $BANCO    $USUARIO    ::1/128         scram-sha-256" \
        "local   all    $USUARIO                  reject" \
        "host    all    $USUARIO    all           reject" \
        "# fim HyBrazil Cases" "")
    # As regras vao antes da primeira regra existente: o PostgreSQL usa a primeira linha que combinar.
    REGRAS="$regras" awk '
        !feito && /^[[:space:]]*(local|host)/ { print ENVIRON["REGRAS"]; feito = 1 }
        { print }
        END { if (!feito) print ENVIRON["REGRAS"] }
    ' "$copia" >"$hba"
    sql postgres "SELECT pg_reload_conf()" >/dev/null
    erros=$(sql postgres "SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL")
    if [ "$erros" != "0" ]; then
        cp -p "$copia" "$hba"
        sql postgres "SELECT pg_reload_conf()" >/dev/null
        echo "O pg_hba.conf ficaria com erro; o original foi restaurado. Confira $hba." >&2
        exit 1
    fi
    echo "pg_hba.conf atualizado (copia em $copia) e recarregado."
fi

# --- 4. resultado ---
echo
echo "Linha para o backend/.env do servidor (guarde: a senha nao sera mostrada de novo):"
echo "DATABASE_URL=postgresql+psycopg://$USUARIO:$senha@localhost:$PGPORT/$BANCO"
