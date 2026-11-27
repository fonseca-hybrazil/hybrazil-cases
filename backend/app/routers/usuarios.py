from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .. import arquivos
from ..db import get_db
from ..models import Grupo, Usuario
from ..schemas import (
    Eu, GrupoResumo, RedefinirSenhaIn, UsuarioAdmin, UsuarioBasico, UsuarioCriarIn, UsuarioEditarIn,
)
from ..security import (
    encerrar_sessoes_do_usuario, exigir, hash_senha, usuario_logado, validar_nova_senha,
)
from ..serial import avatar_url, usuario_basico
from .auth import eu_out

router = APIRouter(tags=["usuarios"])


def admin_out(u: Usuario) -> UsuarioAdmin:
    return UsuarioAdmin(
        id=u.id, nome=u.nome, login=u.login, avatar_url=avatar_url(u), ativo=u.ativo, email=u.email,
        trocar_senha=u.trocar_senha, ultimo_acesso=u.ultimo_acesso, bloqueado_ate=u.bloqueado_ate,
        criado_em=u.criado_em, grupos=[GrupoResumo(id=g.id, nome=g.nome) for g in u.grupos],
    )


def _grupos(db: Session, ids: list[int]) -> list[Grupo]:
    grupos = list(db.scalars(select(Grupo).where(Grupo.id.in_(ids)))) if ids else []
    if len(grupos) != len(set(ids)):
        raise HTTPException(422, "Grupo inválido.")
    return grupos


def _login_livre(db: Session, login: str, exceto_id: int | None = None) -> None:
    q = select(Usuario.id).where(func.lower(Usuario.login) == login.lower())
    if exceto_id:
        q = q.where(Usuario.id != exceto_id)
    if db.scalar(q):
        raise HTTPException(409, "Já existe um usuário com este login.")


# ------------------------------------------------------- para todos logados
@router.get("/api/usuarios", response_model=list[UsuarioBasico])
def listar_basico(_: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    """Usuários (inclusive inativos, para exibir autores antigos). A tela filtra os ativos."""
    return [usuario_basico(u) for u in db.scalars(select(Usuario).order_by(func.lower(Usuario.nome)))]


AVATAR_TIPOS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def _trocar_avatar(u: Usuario, arquivo: UploadFile | None) -> None:
    """Grava a nova foto (ou remove, se arquivo=None) e apaga a anterior do disco."""
    rel = None
    if arquivo is not None:
        if (arquivo.content_type or "") not in AVATAR_TIPOS:
            raise HTTPException(422, "Envie uma imagem PNG, JPEG ou WebP.")
        rel, _, _ = arquivos.salvar_upload(arquivo, "avatares", limite_mb=5)
    arquivos.remover(u.avatar_caminho)
    u.avatar_caminho = rel


@router.get("/api/usuarios/{usuario_id}/avatar")
def avatar(usuario_id: int, _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    u = db.get(Usuario, usuario_id)
    if not u or not u.avatar_caminho:
        raise HTTPException(404, "Sem avatar.")
    ext = "." + u.avatar_caminho.rsplit(".", 1)[-1].lower()
    mime = next((m for m, e in AVATAR_TIPOS.items() if e == ext or (ext == ".jpeg" and m == "image/jpeg")), "image/jpeg")
    return arquivos.resposta_arquivo(u.avatar_caminho, "avatar", mime)


@router.post("/api/auth/avatar", response_model=Eu)
def enviar_avatar(arquivo: UploadFile = File(...), usuario: Usuario = Depends(usuario_logado)):
    _trocar_avatar(usuario, arquivo)
    return eu_out(usuario)


@router.delete("/api/auth/avatar", response_model=Eu)
def remover_avatar(usuario: Usuario = Depends(usuario_logado)):
    _trocar_avatar(usuario, None)
    return eu_out(usuario)


# ------------------------------------------------------------- administração
admin = exigir("admin_usuarios")


@router.get("/api/admin/usuarios", response_model=list[UsuarioAdmin])
def listar(_: Usuario = Depends(admin), db: Session = Depends(get_db)):
    q = select(Usuario).options(selectinload(Usuario.grupos)).order_by(func.lower(Usuario.nome))
    return [admin_out(u) for u in db.scalars(q)]


@router.post("/api/admin/usuarios", response_model=UsuarioAdmin, status_code=201)
def criar(dados: UsuarioCriarIn, _: Usuario = Depends(admin), db: Session = Depends(get_db)):
    _login_livre(db, dados.login)
    validar_nova_senha(dados.senha)
    u = Usuario(
        nome=dados.nome.strip(), login=dados.login.strip(), email=(dados.email or "").strip() or None,
        senha_hash=hash_senha(dados.senha), trocar_senha=True,
    )
    u.grupos = _grupos(db, dados.grupo_ids)
    db.add(u)
    db.flush()
    db.refresh(u)
    return admin_out(u)


@router.patch("/api/admin/usuarios/{usuario_id}", response_model=UsuarioAdmin)
def editar(
    usuario_id: int, dados: UsuarioEditarIn, eu: Usuario = Depends(admin), db: Session = Depends(get_db),
):
    u = db.get(Usuario, usuario_id)
    if u is None:
        raise HTTPException(404, "Usuário não encontrado.")
    if dados.login is not None:
        _login_livre(db, dados.login, exceto_id=u.id)
        u.login = dados.login.strip()
    if dados.nome is not None:
        u.nome = dados.nome.strip()
    if "email" in dados.model_fields_set:
        u.email = (dados.email or "").strip() or None
    if dados.ativo is not None:
        if u.id == eu.id and not dados.ativo:
            raise HTTPException(422, "Você não pode desativar a si mesmo.")
        u.ativo = dados.ativo
        if not u.ativo:
            encerrar_sessoes_do_usuario(db, u.id)
    if dados.grupo_ids is not None:
        novos = _grupos(db, dados.grupo_ids)
        if u.id == eu.id and "admin_usuarios" not in {p for g in novos for p in g.permissoes}:
            raise HTTPException(422, "Você não pode remover sua própria permissão de administrar usuários.")
        u.grupos = novos
    db.flush()
    return admin_out(u)


def _usuario(db: Session, usuario_id: int) -> Usuario:
    u = db.get(Usuario, usuario_id)
    if u is None:
        raise HTTPException(404, "Usuário não encontrado.")
    return u


@router.post("/api/admin/usuarios/{usuario_id}/avatar", response_model=UsuarioAdmin)
def admin_enviar_avatar(
    usuario_id: int, arquivo: UploadFile = File(...), _: Usuario = Depends(admin), db: Session = Depends(get_db),
):
    u = _usuario(db, usuario_id)
    _trocar_avatar(u, arquivo)
    db.flush()
    return admin_out(u)


@router.delete("/api/admin/usuarios/{usuario_id}/avatar", response_model=UsuarioAdmin)
def admin_remover_avatar(usuario_id: int, _: Usuario = Depends(admin), db: Session = Depends(get_db)):
    u = _usuario(db, usuario_id)
    _trocar_avatar(u, None)
    db.flush()
    return admin_out(u)


@router.post("/api/admin/usuarios/{usuario_id}/redefinir-senha", status_code=204)
def redefinir_senha(
    usuario_id: int, dados: RedefinirSenhaIn, _: Usuario = Depends(admin), db: Session = Depends(get_db),
):
    u = db.get(Usuario, usuario_id)
    if u is None:
        raise HTTPException(404, "Usuário não encontrado.")
    validar_nova_senha(dados.nova_senha)
    u.senha_hash = hash_senha(dados.nova_senha)
    u.trocar_senha = True
    u.tentativas_falhas = 0
    u.bloqueado_ate = None
    encerrar_sessoes_do_usuario(db, u.id)
