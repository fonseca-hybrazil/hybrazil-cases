import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .db import get_db
from .models import Sessao, Usuario

COOKIE_NAME = "hyora_sessao"
_ph = PasswordHasher()


def agora() -> datetime:
    return datetime.now(timezone.utc)


def hash_senha(senha: str) -> str:
    return _ph.hash(senha)


def verificar_senha(hash_: str, senha: str) -> bool:
    try:
        return _ph.verify(hash_, senha)
    except (VerificationError, InvalidHashError):
        return False


def validar_nova_senha(senha: str) -> None:
    if len(senha) < 8:
        raise HTTPException(422, "A senha deve ter pelo menos 8 caracteres.")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def criar_sessao(db: Session, usuario: Usuario, lembrar: bool, request: Request) -> tuple[str, datetime]:
    s = get_settings()
    token = secrets.token_urlsafe(32)
    duracao = timedelta(days=s.sessao_lembrar_dias) if lembrar else timedelta(hours=s.sessao_horas)
    expira = agora() + duracao
    db.add(Sessao(
        token_hash=_hash_token(token),
        usuario_id=usuario.id,
        expira_em=expira,
        ip=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:300],
    ))
    return token, expira


def encerrar_sessao(db: Session, token: str | None) -> None:
    if token:
        db.execute(delete(Sessao).where(Sessao.token_hash == _hash_token(token)))


def encerrar_sessoes_do_usuario(db: Session, usuario_id: int, exceto_token: str | None = None) -> None:
    q = delete(Sessao).where(Sessao.usuario_id == usuario_id)
    if exceto_token:
        q = q.where(Sessao.token_hash != _hash_token(exceto_token))
    db.execute(q)


def _usuario_da_sessao(request: Request, db: Session) -> Usuario:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Não autenticado.")
    sessao = db.scalar(
        select(Sessao)
        .where(Sessao.token_hash == _hash_token(token))
        .options(selectinload(Sessao.usuario).selectinload(Usuario.grupos))
    )
    if sessao is None or sessao.expira_em <= agora() or not sessao.usuario.ativo:
        raise HTTPException(401, "Sessão expirada. Entre novamente.")
    return sessao.usuario


def usuario_logado_sem_checar_senha(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Para os endpoints de autenticação (me, logout, trocar senha)."""
    return _usuario_da_sessao(request, db)


def usuario_logado(request: Request, db: Session = Depends(get_db)) -> Usuario:
    usuario = _usuario_da_sessao(request, db)
    if usuario.trocar_senha:
        raise HTTPException(403, "Troque sua senha para continuar.")
    return usuario


def exigir(permissao: str):
    def dep(usuario: Usuario = Depends(usuario_logado)) -> Usuario:
        if permissao not in usuario.permissoes:
            raise HTTPException(403, "Você não tem permissão para esta ação.")
        return usuario
    return dep


def tem(usuario: Usuario, permissao: str) -> bool:
    return permissao in usuario.permissoes
