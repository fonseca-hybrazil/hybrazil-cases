from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Icone, Projeto, Ticket, Usuario, favoritos
from ..schemas import ContagemStatus, ProjetoEditarIn, ProjetoIn, ProjetoOut
from ..security import exigir, usuario_logado

router = APIRouter(prefix="/api/projetos", tags=["projetos"])
admin = exigir("admin_projetos")


def _contagens(db: Session, ids: list[int] | None = None) -> dict[int, ContagemStatus]:
    q = (select(Ticket.projeto_id, Ticket.status, func.count())
         .where(Ticket.excluido_em.is_(None)).group_by(Ticket.projeto_id, Ticket.status))
    if ids is not None:
        q = q.where(Ticket.projeto_id.in_(ids))
    res: dict[int, ContagemStatus] = {}
    for pid, status, n in db.execute(q):
        setattr(res.setdefault(pid, ContagemStatus()), status, n)
    return res


def _favoritos(db: Session, usuario_id: int) -> set[int]:
    return set(db.scalars(select(favoritos.c.projeto_id).where(favoritos.c.usuario_id == usuario_id)))


def projeto_out(p: Projeto, favs: set[int], contagens: dict[int, ContagemStatus]) -> ProjetoOut:
    return ProjetoOut(id=p.id, nome=p.nome, descricao=p.descricao, arquivado=p.arquivado,
                      favorito=p.id in favs, contagem=contagens.get(p.id, ContagemStatus()),
                      icone=p.icone, icone_cor=p.icone_cor)


def _conferir_icone(db: Session, icone: str | None) -> str | None:
    """'' ou None -> sem ícone; 'lib:<id>' precisa existir na biblioteca."""
    if not icone:
        return None
    if icone.startswith("lib:") and db.get(Icone, int(icone[4:])) is None:
        raise HTTPException(422, "Ícone da biblioteca não encontrado.")
    return icone


def obter_projeto(db: Session, projeto_id: int) -> Projeto:
    p = db.get(Projeto, projeto_id)
    if p is None:
        raise HTTPException(404, "Projeto não encontrado.")
    return p


@router.get("", response_model=list[ProjetoOut])
def listar(eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    projetos = list(db.scalars(select(Projeto).order_by(func.lower(Projeto.nome))))
    favs, cont = _favoritos(db, eu.id), _contagens(db)
    return [projeto_out(p, favs, cont) for p in projetos]


@router.get("/{projeto_id}", response_model=ProjetoOut)
def obter(projeto_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    p = obter_projeto(db, projeto_id)
    return projeto_out(p, _favoritos(db, eu.id), _contagens(db, [p.id]))


@router.post("", response_model=ProjetoOut, status_code=201)
def criar(dados: ProjetoIn, eu: Usuario = Depends(admin), db: Session = Depends(get_db)):
    p = Projeto(nome=dados.nome.strip(), descricao=dados.descricao.strip(), criado_por=eu.id,
                icone=_conferir_icone(db, dados.icone), icone_cor=dados.icone_cor)
    db.add(p)
    db.flush()
    return projeto_out(p, set(), {})


@router.patch("/{projeto_id}", response_model=ProjetoOut)
def editar(projeto_id: int, dados: ProjetoEditarIn, eu: Usuario = Depends(admin), db: Session = Depends(get_db)):
    p = obter_projeto(db, projeto_id)
    if dados.nome is not None:
        p.nome = dados.nome.strip()
    if dados.descricao is not None:
        p.descricao = dados.descricao.strip()
    if dados.arquivado is not None:
        p.arquivado = dados.arquivado
    if dados.icone is not None:
        p.icone = _conferir_icone(db, dados.icone)
    if dados.icone_cor is not None:
        p.icone_cor = dados.icone_cor or None
    return projeto_out(p, _favoritos(db, eu.id), _contagens(db, [p.id]))


@router.put("/{projeto_id}/favorito", status_code=204)
def favoritar(projeto_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    obter_projeto(db, projeto_id)
    db.execute(insert(favoritos).values(usuario_id=eu.id, projeto_id=projeto_id).on_conflict_do_nothing())


@router.delete("/{projeto_id}/favorito", status_code=204)
def desfavoritar(projeto_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    db.execute(delete(favoritos).where(favoritos.c.usuario_id == eu.id, favoritos.c.projeto_id == projeto_id))
