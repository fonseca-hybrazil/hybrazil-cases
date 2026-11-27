from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import Grupo, Usuario
from ..permissoes import PERMISSOES
from ..schemas import GrupoEditarIn, GrupoIn, GrupoOut, PermissaoOut
from ..security import exigir

router = APIRouter(prefix="/api/admin", tags=["grupos"])
admin = exigir("admin_usuarios")


def grupo_out(g: Grupo) -> GrupoOut:
    return GrupoOut(
        id=g.id, nome=g.nome, descricao=g.descricao, permissoes=sorted(g.permissoes), sistema=g.sistema,
        usuario_ids=sorted(u.id for u in g.usuarios),
    )


def _validar_permissoes(perms: list[str]) -> list[str]:
    invalidas = set(perms) - set(PERMISSOES)
    if invalidas:
        raise HTTPException(422, f"Permissões inválidas: {', '.join(sorted(invalidas))}")
    return sorted(set(perms))


def _nome_livre(db: Session, nome: str, exceto_id: int | None = None) -> None:
    q = select(Grupo.id).where(func.lower(Grupo.nome) == nome.strip().lower())
    if exceto_id:
        q = q.where(Grupo.id != exceto_id)
    if db.scalar(q):
        raise HTTPException(409, "Já existe um grupo com este nome.")


@router.get("/permissoes", response_model=list[PermissaoOut])
def listar_permissoes(_: Usuario = Depends(admin)):
    return [PermissaoOut(chave=k, descricao=v) for k, v in PERMISSOES.items()]


@router.get("/grupos", response_model=list[GrupoOut])
def listar(_: Usuario = Depends(admin), db: Session = Depends(get_db)):
    q = select(Grupo).options(selectinload(Grupo.usuarios)).order_by(Grupo.id)
    return [grupo_out(g) for g in db.scalars(q)]


@router.post("/grupos", response_model=GrupoOut, status_code=201)
def criar(dados: GrupoIn, _: Usuario = Depends(admin), db: Session = Depends(get_db)):
    _nome_livre(db, dados.nome)
    g = Grupo(nome=dados.nome.strip(), descricao=dados.descricao.strip(),
              permissoes=_validar_permissoes(dados.permissoes))
    g.usuarios = []
    db.add(g)
    db.flush()
    return grupo_out(g)


@router.patch("/grupos/{grupo_id}", response_model=GrupoOut)
def editar(grupo_id: int, dados: GrupoEditarIn, eu: Usuario = Depends(admin), db: Session = Depends(get_db)):
    g = db.get(Grupo, grupo_id)
    if g is None:
        raise HTTPException(404, "Grupo não encontrado.")
    if dados.nome is not None:
        _nome_livre(db, dados.nome, exceto_id=g.id)
        g.nome = dados.nome.strip()
    if dados.descricao is not None:
        g.descricao = dados.descricao.strip()
    if dados.permissoes is not None:
        if g.sistema and g.nome == "Administradores":
            raise HTTPException(422, "As permissões do grupo Administradores não podem ser alteradas.")
        g.permissoes = _validar_permissoes(dados.permissoes)
    if dados.usuario_ids is not None:
        usuarios = list(db.scalars(select(Usuario).where(Usuario.id.in_(dados.usuario_ids))))
        if len(usuarios) != len(set(dados.usuario_ids)):
            raise HTTPException(422, "Usuário inválido.")
        g.usuarios = usuarios
    db.flush()
    db.expire(eu, ["grupos"])
    if "admin_usuarios" not in eu.permissoes:
        raise HTTPException(422, "Esta alteração removeria sua própria permissão de administrar usuários.")
    return grupo_out(g)


@router.delete("/grupos/{grupo_id}", status_code=204)
def excluir(grupo_id: int, eu: Usuario = Depends(admin), db: Session = Depends(get_db)):
    g = db.get(Grupo, grupo_id)
    if g is None:
        raise HTTPException(404, "Grupo não encontrado.")
    if g.sistema:
        raise HTTPException(422, "Grupos padrão do sistema não podem ser excluídos.")
    db.delete(g)
    db.flush()
    db.expire(eu, ["grupos"])
    if "admin_usuarios" not in eu.permissoes:
        raise HTTPException(422, "Esta exclusão removeria sua própria permissão de administrar usuários.")
