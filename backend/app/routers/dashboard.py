"""Dashboard: contagens de cases por mês, categoria, label e responsável, com filtros.

Regras:
- Período (de/até, datas locais de Brasília): vale para a data de CRIAÇÃO do case, exceto na série
  "concluídos por mês", que usa a data de conclusão.
- Os outros filtros (projeto, status, categoria, label, responsável) valem para tudo.
- categoria_id=0 / responsavel_id=0 filtram "sem categoria" / "sem responsável".
- Um case com várias labels conta em cada uma delas.
"""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Categoria, Label, Ticket, Usuario, ticket_labels
from ..security import usuario_logado

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

FUSO = "America/Sao_Paulo"
TOP_LABELS = 15


class Totais(BaseModel):
    total: int
    abertos: int
    completados: int
    dias_medio: float | None      # tempo médio entre criação e conclusão (dos completados)
    dias_mediana: float | None


class Mes(BaseModel):
    mes: str                      # "AAAA-MM"
    criados: int
    concluidos: int


class Fatia(BaseModel):
    id: int | None                # None = sem categoria / sem responsável / "outras" labels
    nome: str
    cor: str | None = None
    total: int


class LabelsOut(BaseModel):
    itens: list[Fatia]
    outras: int                   # soma das labels fora do top
    qtd_outras: int               # quantas labels ficaram em "outras"
    sem_label: int


class Dashboard(BaseModel):
    totais: Totais
    por_mes: list[Mes]
    por_categoria: list[Fatia]
    por_label: LabelsOut
    por_responsavel: list[Fatia]


def _local(col):
    return func.timezone(FUSO, col)


def _dia(col):
    return cast(_local(col), Date)


def _mes(col):
    return func.to_char(_local(col), "YYYY-MM")


def _meses(inicio: str, fim: str) -> list[str]:
    a, m = map(int, inicio.split("-"))
    fa, fm = map(int, fim.split("-"))
    saida = []
    while (a, m) <= (fa, fm):
        saida.append(f"{a:04d}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return saida


@router.get("", response_model=Dashboard)
def dashboard(
    projeto_id: int | None = Query(None, ge=1),
    de: date | None = None,
    ate: date | None = None,
    status: Literal["todos", "abertos", "pendente", "andamento", "completado"] = "todos",
    categoria_id: int | None = Query(None, ge=0),
    label_id: int | None = Query(None, ge=1),
    responsavel_id: int | None = Query(None, ge=0),
    _: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    if de and ate and de > ate:
        raise HTTPException(422, "A data inicial é depois da data final.")

    # filtros comuns (sem período)
    base = [Ticket.excluido_em.is_(None)]
    if projeto_id:
        base.append(Ticket.projeto_id == projeto_id)
    if status == "abertos":
        base.append(Ticket.status != "completado")
    elif status != "todos":
        base.append(Ticket.status == status)
    if categoria_id is not None:
        base.append(Ticket.categoria_id.is_(None) if categoria_id == 0 else Ticket.categoria_id == categoria_id)
    if responsavel_id is not None:
        base.append(Ticket.responsavel_id.is_(None) if responsavel_id == 0 else Ticket.responsavel_id == responsavel_id)
    if label_id:
        base.append(Ticket.id.in_(select(ticket_labels.c.ticket_id).where(ticket_labels.c.label_id == label_id)))

    def periodo(col) -> list:
        c = []
        if de:
            c.append(_dia(col) >= de)
        if ate:
            c.append(_dia(col) <= ate)
        return c

    criados = base + periodo(Ticket.criado_em)

    # --- totais
    completado = Ticket.status == "completado"
    duracao = func.extract("epoch", Ticket.concluido_em - Ticket.criado_em) / 86400
    valida = [completado, Ticket.concluido_em.is_not(None), Ticket.concluido_em >= Ticket.criado_em]
    total, abertos, completados = db.execute(
        select(func.count(), func.count().filter(~completado), func.count().filter(completado)).where(*criados)
    ).one()
    medio, mediana = db.execute(
        select(func.avg(duracao), func.percentile_cont(0.5).within_group(duracao)).where(*criados, *valida)
    ).one()

    # --- por mês (criados pela data de criação; concluídos pela data de conclusão)
    mes_criacao = _mes(Ticket.criado_em)
    por_criacao = dict(db.execute(
        select(mes_criacao, func.count()).where(*criados).group_by(mes_criacao)
    ).all())
    mes_conclusao = _mes(Ticket.concluido_em)
    por_conclusao = dict(db.execute(
        select(mes_conclusao, func.count())
        .where(*base, *periodo(Ticket.concluido_em), Ticket.concluido_em.is_not(None)).group_by(mes_conclusao)
    ).all())
    hoje = db.scalar(select(_mes(func.now())))
    inicio = f"{de.year:04d}-{de.month:02d}" if de else min([*por_criacao, *por_conclusao], default=hoje)
    fim = f"{ate.year:04d}-{ate.month:02d}" if ate else max([hoje, *por_criacao, *por_conclusao])
    por_mes = [Mes(mes=m, criados=por_criacao.get(m, 0), concluidos=por_conclusao.get(m, 0))
               for m in _meses(inicio, fim)]

    # --- por categoria
    por_categoria = [
        Fatia(id=cid, nome=nome or "Sem categoria", cor=cor, total=n)
        for cid, nome, cor, n in db.execute(
            select(Ticket.categoria_id, Categoria.nome, Categoria.cor, func.count())
            .select_from(Ticket).outerjoin(Categoria, Categoria.id == Ticket.categoria_id)
            .where(*criados).group_by(Ticket.categoria_id, Categoria.nome, Categoria.cor)
            .order_by(func.count().desc(), Categoria.nome)
        )
    ]

    # --- por label (top + outras + sem label)
    contagem_labels = db.execute(
        select(Label.id, Label.nome, Label.cor, func.count())
        .select_from(ticket_labels).join(Ticket, Ticket.id == ticket_labels.c.ticket_id)
        .join(Label, Label.id == ticket_labels.c.label_id)
        .where(*criados).group_by(Label.id, Label.nome, Label.cor).order_by(func.count().desc(), Label.nome)
    ).all()
    resto = contagem_labels[TOP_LABELS:]
    sem_label = db.scalar(
        select(func.count()).select_from(Ticket)
        .where(*criados, ~Ticket.id.in_(select(ticket_labels.c.ticket_id)))
    )
    por_label = LabelsOut(
        itens=[Fatia(id=i, nome=n, cor=c, total=t) for i, n, c, t in contagem_labels[:TOP_LABELS]],
        outras=sum(r[3] for r in resto), qtd_outras=len(resto), sem_label=sem_label or 0,
    )

    # --- por responsável
    por_responsavel = [
        Fatia(id=uid, nome=nome or "Sem responsável", total=n)
        for uid, nome, n in db.execute(
            select(Ticket.responsavel_id, Usuario.nome, func.count())
            .select_from(Ticket).outerjoin(Usuario, Usuario.id == Ticket.responsavel_id)
            .where(*criados).group_by(Ticket.responsavel_id, Usuario.nome)
            .order_by(func.count().desc(), Usuario.nome)
        )
    ]

    return Dashboard(
        totais=Totais(
            total=total, abertos=abertos, completados=completados,
            dias_medio=round(float(medio), 1) if medio is not None else None,
            dias_mediana=round(float(mediana), 1) if mediana is not None else None,
        ),
        por_mes=por_mes,
        por_categoria=por_categoria,
        por_label=por_label,
        por_responsavel=por_responsavel,
    )
