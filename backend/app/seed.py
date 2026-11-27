"""Dados iniciais: grupos padrão, usuário admin e categorias."""
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Categoria, Grupo, Usuario
from .permissoes import GRUPOS_PADRAO, PERMISSOES
from .security import hash_senha

CATEGORIAS_PADRAO = [
    ("Problema", "triangle-alert", "#e5484d"),
    ("Implementação", "rocket", "#3e63dd"),
    ("Modificação", "wrench", "#f76b15"),
    ("Estudo", "book-open", "#8e4ec6"),
    ("Verificação", "circle-check", "#30a46c"),
    ("Documentação", "file-text", "#687076"),
]


def semear(db: Session) -> str | None:
    """Cria o que faltar. Retorna a senha do admin se ele foi criado agora."""
    grupos: dict[str, Grupo] = {}
    for g in GRUPOS_PADRAO:
        grupo = db.scalar(select(Grupo).where(func.lower(Grupo.nome) == g["nome"].lower()))
        if grupo is None:
            grupo = Grupo(nome=g["nome"], descricao=g["descricao"], permissoes=g["permissoes"], sistema=True)
            db.add(grupo)
        grupos[g["nome"]] = grupo

    # O grupo Administradores sempre tem todas as permissões (inclusive novas)
    admins = grupos["Administradores"]
    if set(admins.permissoes) != set(PERMISSOES):
        admins.permissoes = list(PERMISSOES)

    senha_criada = None
    if db.scalar(select(func.count()).select_from(Usuario)) == 0:
        senha_criada = get_settings().admin_initial_password or secrets.token_urlsafe(9)
        admin = Usuario(
            nome="Administrador", login="admin", senha_hash=hash_senha(senha_criada), trocar_senha=True,
        )
        admin.grupos = [admins]
        db.add(admin)

    if db.scalar(select(func.count()).select_from(Categoria)) == 0:
        for i, (nome, icone, cor) in enumerate(CATEGORIAS_PADRAO):
            db.add(Categoria(nome=nome, icone=icone, cor=cor, ordem=i))

    db.flush()
    return senha_criada
