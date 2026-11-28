"""Categorias e labels."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Categoria, Label, Ticket, Usuario, ticket_labels
from ..schemas import (
    CategoriaEditarIn, CategoriaIn, CategoriaOut, LabelComUso, LabelEditarIn, LabelIn, LabelOut, MesclarIn,
    OrdemIn,
)
from ..security import exigir, usuario_logado

router = APIRouter(prefix="/api", tags=["catalogos"])
admin_cat = exigir("admin_categorias")
admin_lab = exigir("admin_labels")


# --------------------------------------------------------------- categorias
@router.get("/categorias", response_model=list[CategoriaOut])
def listar_categorias(_: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    return list(db.scalars(select(Categoria).order_by(Categoria.ordem, Categoria.id)))


@router.post("/categorias", response_model=CategoriaOut, status_code=201)
def criar_categoria(dados: CategoriaIn, _: Usuario = Depends(admin_cat), db: Session = Depends(get_db)):
    ordem = (db.scalar(select(func.max(Categoria.ordem))) or 0) + 1
    c = Categoria(nome=dados.nome.strip(), icone=dados.icone, cor=dados.cor.lower(), ordem=ordem)
    db.add(c)
    db.flush()
    return c


@router.patch("/categorias/{cat_id}", response_model=CategoriaOut)
def editar_categoria(cat_id: int, dados: CategoriaEditarIn, _: Usuario = Depends(admin_cat),
                     db: Session = Depends(get_db)):
    c = db.get(Categoria, cat_id)
    if c is None:
        raise HTTPException(404, "Categoria não encontrada.")
    if dados.nome is not None:
        c.nome = dados.nome.strip()
    if dados.icone is not None:
        c.icone = dados.icone
    if dados.cor is not None:
        c.cor = dados.cor.lower()
    if dados.ativa is not None:
        c.ativa = dados.ativa
    return c


@router.put("/categorias-ordem", response_model=list[CategoriaOut])
def ordenar_categorias(dados: OrdemIn, _: Usuario = Depends(admin_cat), db: Session = Depends(get_db)):
    for i, cid in enumerate(dados.ids):
        db.execute(update(Categoria).where(Categoria.id == cid).values(ordem=i))
    return list(db.scalars(select(Categoria).order_by(Categoria.ordem, Categoria.id)))


@router.delete("/categorias/{cat_id}", status_code=204)
def excluir_categoria(cat_id: int, _: Usuario = Depends(admin_cat), db: Session = Depends(get_db)):
    c = db.get(Categoria, cat_id)
    if c is None:
        raise HTTPException(404, "Categoria não encontrada.")
    if db.scalar(select(func.count()).select_from(Ticket).where(Ticket.categoria_id == cat_id)):
        raise HTTPException(409, "Categoria em uso. Desative-a em vez de excluir.")
    db.delete(c)


# ------------------------------------------------------------------- labels
@router.get("/labels", response_model=list[LabelOut])
def listar_labels(_: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    return list(db.scalars(select(Label).order_by(func.lower(Label.nome))))


@router.get("/labels-uso", response_model=list[LabelComUso])
def listar_labels_uso(
    projeto_id: int | None = Query(None, ge=1),   # informado: conta só os tickets deste projeto
    _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db),
):
    filtro = [Ticket.excluido_em.is_(None)]
    if projeto_id:
        filtro.append(Ticket.projeto_id == projeto_id)
    uso = (
        select(ticket_labels.c.label_id, func.count().label("n"))
        .join(Ticket, Ticket.id == ticket_labels.c.ticket_id)
        .where(*filtro)
        .group_by(ticket_labels.c.label_id).subquery()
    )
    q = select(Label, func.coalesce(uso.c.n, 0)).outerjoin(uso, uso.c.label_id == Label.id).order_by(
        func.lower(Label.nome))
    return [LabelComUso(id=l.id, nome=l.nome, cor=l.cor, uso=n) for l, n in db.execute(q)]


def _nome_label_livre(db: Session, nome: str, exceto_id: int | None = None) -> None:
    q = select(Label.id).where(func.lower(Label.nome) == nome.lower())
    if exceto_id:
        q = q.where(Label.id != exceto_id)
    if db.scalar(q):
        raise HTTPException(409, "Já existe uma label com este nome.")


@router.post("/labels", response_model=LabelOut, status_code=201)
def criar_label(dados: LabelIn, _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    _nome_label_livre(db, dados.nome)
    l = Label(nome=dados.nome, cor=dados.cor.lower())
    db.add(l)
    db.flush()
    return l


@router.patch("/labels/{label_id}", response_model=LabelOut)
def editar_label(label_id: int, dados: LabelEditarIn, _: Usuario = Depends(admin_lab),
                 db: Session = Depends(get_db)):
    l = db.get(Label, label_id)
    if l is None:
        raise HTTPException(404, "Label não encontrada.")
    if dados.nome is not None:
        nome = dados.nome.strip()
        _nome_label_livre(db, nome, exceto_id=l.id)
        l.nome = nome
    if dados.cor is not None:
        l.cor = dados.cor.lower()
    return l


@router.post("/labels/{label_id}/mesclar", status_code=204)
def mesclar_label(label_id: int, dados: MesclarIn, _: Usuario = Depends(admin_lab),
                  db: Session = Depends(get_db)):
    """Move todos os tickets da label `label_id` para `destino_id` e exclui a de origem."""
    origem, destino = db.get(Label, label_id), db.get(Label, dados.destino_id)
    if origem is None or destino is None or origem.id == destino.id:
        raise HTTPException(422, "Labels inválidas para mesclar.")
    db.execute(
        text("INSERT INTO ticket_labels (ticket_id, label_id) "
             "SELECT ticket_id, :destino FROM ticket_labels WHERE label_id = :origem ON CONFLICT DO NOTHING"),
        {"destino": destino.id, "origem": origem.id},
    )
    db.execute(delete(Label).where(Label.id == origem.id))


@router.delete("/labels/{label_id}", status_code=204)
def excluir_label(label_id: int, _: Usuario = Depends(admin_lab), db: Session = Depends(get_db)):
    l = db.get(Label, label_id)
    if l is None:
        raise HTTPException(404, "Label não encontrada.")
    db.delete(l)
