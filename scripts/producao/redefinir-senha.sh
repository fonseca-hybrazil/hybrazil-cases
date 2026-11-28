#!/usr/bin/env bash
# Redefine a senha de um usuario do HyBrazil Cases direto no banco de producao.
#
#   cd /opt/hybrazil-cases
#   sudo bash scripts/producao/redefinir-senha.sh            # lista os administradores
#   sudo bash scripts/producao/redefinir-senha.sh <login>    # gera uma senha provisoria (troca obrigatoria no 1o acesso)
set -euo pipefail

RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo: sudo bash $0 [login]" >&2; exit 1; }
cd "$RAIZ/backend"
# roda com o usuario do site, que e quem le o backend/.env
exec sudo -u hybrazil env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python redefinir_senha.py "$@"
