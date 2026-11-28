"""Redefine a senha de um usuário direto no banco (para quando ninguém consegue entrar como administrador).

Uso (na pasta backend):
    python redefinir_senha.py            lista os usuários ativos que administram usuários
    python redefinir_senha.py <login>    gera uma senha provisória para <login>

A senha provisória aparece só na tela. No primeiro acesso o sistema exige trocá-la.
Também desbloqueia o usuário (tentativas erradas), reativa se estiver inativo e encerra as sessões abertas dele.
Em produção use scripts/producao/redefinir-senha.sh, que roda isto com o usuário do site.
"""
import secrets
import sys

from sqlalchemy import func, select

from app import db
from app.models import Usuario
from app.security import encerrar_sessoes_do_usuario, hash_senha


def listar_admins(sessao) -> None:
    usuarios = sessao.scalars(select(Usuario).where(Usuario.ativo.is_(True)).order_by(Usuario.login)).all()
    admins = [u for u in usuarios if "admin_usuarios" in u.permissoes]
    if not admins:
        print("Nenhum usuário ativo administra usuários.")
    else:
        print("Usuários ativos que administram usuários:")
        for u in admins:
            print(f"  {u.login:<20} {u.nome}")
    print("\nPara redefinir: informe o login (qualquer usuário, não só os da lista).")


def redefinir(sessao, login: str) -> int:
    u = sessao.scalar(select(Usuario).where(func.lower(Usuario.login) == login.lower()))
    if u is None:
        print(f"Usuário '{login}' não encontrado.", file=sys.stderr)
        return 1
    senha = secrets.token_urlsafe(9)
    u.senha_hash = hash_senha(senha)
    u.trocar_senha = True
    u.tentativas_falhas = 0
    u.bloqueado_ate = None
    reativado = not u.ativo
    u.ativo = True
    encerrar_sessoes_do_usuario(sessao, u.id)
    sessao.commit()
    print(f"Senha provisória de '{u.login}' ({u.nome}): {senha}")
    print("No primeiro acesso o sistema pede uma senha nova.")
    if reativado:
        print("O usuário estava inativo e foi reativado.")
    return 0


def main() -> int:
    sessao = db.new_session()
    try:
        if len(sys.argv) < 2:
            listar_admins(sessao)
            return 0
        return redefinir(sessao, sys.argv[1].strip())
    finally:
        sessao.close()


if __name__ == "__main__":
    sys.exit(main())
