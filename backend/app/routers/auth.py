from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..db import get_db
from ..models import Usuario
from ..schemas import Eu, LoginIn, PerfilIn, TrocarSenhaIn
from ..security import (
    COOKIE_NAME, agora, criar_sessao, encerrar_sessao, encerrar_sessoes_do_usuario, hash_senha,
    usuario_logado, usuario_logado_sem_checar_senha, validar_nova_senha, verificar_senha,
)
from ..serial import avatar_url

router = APIRouter(prefix="/api/auth", tags=["auth"])


def eu_out(u: Usuario) -> Eu:
    return Eu(
        id=u.id, nome=u.nome, login=u.login, avatar_url=avatar_url(u), ativo=u.ativo,
        email=u.email, trocar_senha=u.trocar_senha, permissoes=sorted(u.permissoes),
    )


@router.post("/login", response_model=Eu)
def login(dados: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    usuario = db.scalar(
        select(Usuario).where(func.lower(Usuario.login) == dados.login.strip().lower())
        .options(selectinload(Usuario.grupos))
    )
    erro = HTTPException(401, "Usuário ou senha inválidos.")
    if usuario is None or not usuario.ativo:
        raise erro
    if usuario.bloqueado_ate and usuario.bloqueado_ate > agora():
        raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos e tente novamente.")
    if not verificar_senha(usuario.senha_hash, dados.senha):
        usuario.tentativas_falhas += 1
        if usuario.tentativas_falhas >= s.max_tentativas_login:
            usuario.bloqueado_ate = agora() + timedelta(minutes=s.bloqueio_minutos)
            usuario.tentativas_falhas = 0
        db.commit()
        raise erro

    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate = None
    usuario.ultimo_acesso = agora()
    token, expira = criar_sessao(db, usuario, dados.lembrar, request)
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax", secure=s.cookie_secure, path="/",
        max_age=int((expira - agora()).total_seconds()) if dados.lembrar else None,
    )
    return eu_out(usuario)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    encerrar_sessao(db, request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=Eu)
def me(usuario: Usuario = Depends(usuario_logado_sem_checar_senha)):
    return eu_out(usuario)


@router.post("/trocar-senha", response_model=Eu)
def trocar_senha(
    dados: TrocarSenhaIn, request: Request,
    usuario: Usuario = Depends(usuario_logado_sem_checar_senha), db: Session = Depends(get_db),
):
    if not verificar_senha(usuario.senha_hash, dados.senha_atual):
        raise HTTPException(400, "Senha atual incorreta.")
    validar_nova_senha(dados.nova_senha)
    if dados.nova_senha == dados.senha_atual:
        raise HTTPException(422, "A nova senha deve ser diferente da atual.")
    usuario.senha_hash = hash_senha(dados.nova_senha)
    usuario.trocar_senha = False
    # derruba as outras sessões abertas deste usuário
    encerrar_sessoes_do_usuario(db, usuario.id, exceto_token=request.cookies.get(COOKIE_NAME))
    return eu_out(usuario)


@router.patch("/perfil", response_model=Eu)
def editar_perfil(dados: PerfilIn, usuario: Usuario = Depends(usuario_logado)):
    if dados.nome is not None:
        usuario.nome = dados.nome.strip()
    if "email" in dados.model_fields_set:
        usuario.email = (dados.email or "").strip() or None
    return eu_out(usuario)
