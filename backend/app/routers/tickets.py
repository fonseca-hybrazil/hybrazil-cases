from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import and_, exists, func, or_, select, text, update
from sqlalchemy.orm import Session, selectinload

from .. import arquivos, planilha
from ..db import get_db
from ..models import (
    Anexo, Atividade, Categoria, Comentario, Label, Projeto, Ticket, Usuario, ticket_labels,
)
from ..richtext import (
    anexos_referenciados, contar_tarefas, documento_vazio, extrair_texto, marcar_tarefa, sanitizar,
)
from ..schemas import (
    AnexoOut, Coluna, ComentarioIn, ContagemStatus, ItemTimeline, MoverIn, Quadro, TarefaIn, TicketCriarIn,
    TicketDetalhe, TicketEditarIn, TicketResumo,
)
from ..security import agora, tem, usuario_logado
from ..serial import anexo_out, usuario_basico
from .projetos import obter_projeto

router = APIRouter(prefix="/api", tags=["tickets"])

STATUS = ("pendente", "andamento", "completado")
PASSO_ORDEM = 1024.0


# =============================================================== filtros
class Filtros:
    def __init__(
        self,
        label: list[int] = Query(default=[]),
        labels_modo: Literal["qualquer", "todas"] = "qualquer",
        categoria: list[int] = Query(default=[], description="0 = sem categoria"),
        responsavel: list[int] = Query(default=[], description="0 = sem responsável"),
        q: str | None = Query(default=None, max_length=200),
        numero: int | None = None,
    ):
        self.label, self.labels_modo = label, labels_modo
        self.categoria, self.responsavel = categoria, responsavel
        self.q = (q or "").strip() or None
        self.numero = numero

    def ativos(self) -> bool:
        return bool(self.label or self.categoria or self.responsavel or self.q or self.numero)

    def condicoes(self) -> list:
        conds = []
        if self.numero is not None:
            conds.append(Ticket.numero == self.numero)
        if self.label:
            ids = sorted(set(self.label))
            if self.labels_modo == "todas":
                for lid in ids:
                    conds.append(exists().where(ticket_labels.c.ticket_id == Ticket.id,
                                                ticket_labels.c.label_id == lid))
            else:
                conds.append(exists().where(ticket_labels.c.ticket_id == Ticket.id,
                                            ticket_labels.c.label_id.in_(ids)))
        for valores, coluna in ((self.categoria, Ticket.categoria_id), (self.responsavel, Ticket.responsavel_id)):
            if valores:
                ids = [v for v in valores if v != 0]
                partes = []
                if ids:
                    partes.append(coluna.in_(ids))
                if 0 in valores:
                    partes.append(coluna.is_(None))
                conds.append(or_(*partes))
        if self.q:
            conds.append(condicao_texto(self.q))
        return conds


def _escapar_like(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def condicao_texto(q: str):
    """Título, descrição ou comentários: full-text em português OU trecho (sem acentos)."""
    padrao = "%" + _escapar_like(q) + "%"
    return text(
        "("
        " tickets.busca @@ websearch_to_tsquery('pt_unaccent', :q_txt)"
        " OR (f_norm(tickets.titulo) || ' ' || f_norm(tickets.descricao_texto)) LIKE f_norm(:q_like)"
        " OR EXISTS (SELECT 1 FROM comentarios c WHERE c.ticket_id = tickets.id AND c.excluido_em IS NULL"
        "   AND (c.busca @@ websearch_to_tsquery('pt_unaccent', :q_txt) OR f_norm(c.texto) LIKE f_norm(:q_like)))"
        ")"
    ).bindparams(q_txt=q, q_like=padrao)


# ============================================================ serialização
def resumos(db: Session, tickets: list[Ticket]) -> list[TicketResumo]:
    ids = [t.id for t in tickets]
    labels: dict[int, list[int]] = {}
    qtd: dict[int, int] = {}
    if ids:
        for tid, lid in db.execute(
            select(ticket_labels.c.ticket_id, ticket_labels.c.label_id)
            .join(Label, Label.id == ticket_labels.c.label_id)
            .where(ticket_labels.c.ticket_id.in_(ids)).order_by(func.lower(Label.nome))
        ):
            labels.setdefault(tid, []).append(lid)
        qtd = dict(db.execute(
            select(Comentario.ticket_id, func.count()).where(
                Comentario.ticket_id.in_(ids), Comentario.excluido_em.is_(None)
            ).group_by(Comentario.ticket_id)
        ).all())
    return [
        TicketResumo(
            id=t.id, projeto_id=t.projeto_id, numero=t.numero, titulo=t.titulo, status=t.status,
            categoria_id=t.categoria_id, responsavel=usuario_basico(t.responsavel),
            label_ids=labels.get(t.id, []), qtd_comentarios=qtd.get(t.id, 0),
            tem_descricao=bool(t.descricao_texto) or t.descricao is not None,
            tarefas_total=t.tarefas_total, tarefas_feitas=t.tarefas_feitas,
            ordem=t.ordem, criado_em=t.criado_em, concluido_em=t.concluido_em,
        )
        for t in tickets
    ]


def pode_excluir_ticket(eu: Usuario, t: Ticket) -> bool:
    return tem(eu, "ticket_excluir") or (tem(eu, "ticket_excluir_proprio") and t.criado_por == eu.id)


def detalhe(db: Session, eu: Usuario, t: Ticket) -> TicketDetalhe:
    r = resumos(db, [t])[0]
    return TicketDetalhe(
        **r.model_dump(), descricao=t.descricao, criado_por=usuario_basico(t.autor),
        atualizado_em=t.atualizado_em, pode_excluir=pode_excluir_ticket(eu, t),
    )


def _carregar(db: Session, ticket_id: int) -> Ticket:
    t = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.excluido_em.is_(None))
        .options(selectinload(Ticket.responsavel), selectinload(Ticket.autor), selectinload(Ticket.labels))
    )
    if t is None:
        raise HTTPException(404, "Ticket não encontrado.")
    return t


def registrar(db: Session, t: Ticket, eu: Usuario, tipo: str, **dados) -> None:
    db.add(Atividade(ticket_id=t.id, usuario_id=eu.id, tipo=tipo, dados=dados))


def recalcular_tarefas(db: Session, t: Ticket) -> None:
    """Soma as caixas de tarefa da descrição e dos comentários (não excluídos) no ticket."""
    db.flush()
    feitas, total = contar_tarefas(t.descricao)
    for conteudo in db.scalars(select(Comentario.conteudo).where(
            Comentario.ticket_id == t.id, Comentario.excluido_em.is_(None))):
        f, n = contar_tarefas(conteudo)
        feitas, total = feitas + f, total + n
    t.tarefas_feitas, t.tarefas_total = feitas, total


# ================================================================ quadro
def _base(projeto_id: int, filtros: Filtros):
    return select(Ticket).where(Ticket.projeto_id == projeto_id, Ticket.excluido_em.is_(None),
                                *filtros.condicoes())


@router.get("/projetos/{projeto_id}/quadro", response_model=Quadro)
def quadro(
    projeto_id: int, filtros: Filtros = Depends(), limite: int = Query(50, ge=1, le=500),
    _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db),
):
    obter_projeto(db, projeto_id)
    base = _base(projeto_id, filtros).subquery()
    totais = dict(db.execute(select(base.c.status, func.count()).group_by(base.c.status)).all())
    sem_filtro = ContagemStatus(**dict(db.execute(
        select(Ticket.status, func.count()).where(Ticket.projeto_id == projeto_id, Ticket.excluido_em.is_(None))
        .group_by(Ticket.status)).all()))
    colunas = {}
    for status in STATUS:
        tickets = list(db.scalars(
            _base(projeto_id, filtros).where(Ticket.status == status)
            .options(selectinload(Ticket.responsavel)).order_by(Ticket.ordem, Ticket.id).limit(limite)
        ))
        colunas[status] = Coluna(total=totais.get(status, 0), tickets=resumos(db, tickets))
    return Quadro(**colunas, total_sem_filtro=sem_filtro)


@router.get("/projetos/{projeto_id}/tickets", response_model=Coluna)
def listar_tickets(
    projeto_id: int, status: Literal["pendente", "andamento", "completado"],
    filtros: Filtros = Depends(), offset: int = Query(0, ge=0), limite: int = Query(50, ge=1, le=500),
    _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db),
):
    q = _base(projeto_id, filtros).where(Ticket.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    tickets = list(db.scalars(q.options(selectinload(Ticket.responsavel))
                              .order_by(Ticket.ordem, Ticket.id).offset(offset).limit(limite)))
    return Coluna(total=total, tickets=resumos(db, tickets))


# ============================================================ ordenação
def _ordem_no_topo(db: Session, projeto_id: int, status: str, exceto: int | None = None) -> float:
    q = select(func.min(Ticket.ordem)).where(
        Ticket.projeto_id == projeto_id, Ticket.status == status, Ticket.excluido_em.is_(None))
    if exceto:
        q = q.where(Ticket.id != exceto)
    m = db.scalar(q)
    return 0.0 if m is None else m - PASSO_ORDEM


def _renumerar(db: Session, projeto_id: int, status: str) -> None:
    db.execute(text(
        "UPDATE tickets t SET ordem = s.rn * :passo FROM ("
        " SELECT id, row_number() OVER (ORDER BY ordem, id) AS rn FROM tickets"
        " WHERE projeto_id = :p AND status = :s AND excluido_em IS NULL) s WHERE t.id = s.id"
    ), {"passo": PASSO_ORDEM, "p": projeto_id, "s": status})
    db.expire_all()


def _ordem_apos(db: Session, t: Ticket, status: str, apos_id: int, tentativa: int = 0) -> float:
    apos = db.get(Ticket, apos_id)
    if apos is None or apos.projeto_id != t.projeto_id or apos.status != status or apos.excluido_em:
        raise HTTPException(422, "Posição inválida.")
    prox = db.scalar(select(func.min(Ticket.ordem)).where(
        Ticket.projeto_id == t.projeto_id, Ticket.status == status, Ticket.excluido_em.is_(None),
        Ticket.id != t.id, Ticket.ordem > apos.ordem))
    if prox is None:
        return apos.ordem + PASSO_ORDEM
    if prox - apos.ordem < 1e-6 and tentativa == 0:
        _renumerar(db, t.projeto_id, status)
        return _ordem_apos(db, t, status, apos_id, 1)
    return (apos.ordem + prox) / 2


# ================================================================ tickets
def _validar_refs(db: Session, categoria_id: int | None, responsavel_id: int | None) -> None:
    if categoria_id is not None:
        c = db.get(Categoria, categoria_id)
        if c is None or not c.ativa:
            raise HTTPException(422, "Categoria inválida.")
    if responsavel_id is not None:
        u = db.get(Usuario, responsavel_id)
        if u is None or not u.ativo:
            raise HTTPException(422, "Responsável inválido.")


def _descricao(doc: dict | None) -> dict | None:
    if doc is None or doc.get("type") != "doc":
        return None
    doc = sanitizar(doc)
    return None if documento_vazio(doc) else doc


def _labels(db: Session, ids: list[int]) -> list[Label]:
    labels = list(db.scalars(select(Label).where(Label.id.in_(ids)))) if ids else []
    if len(labels) != len(set(ids)):
        raise HTTPException(422, "Label inválida.")
    return labels


@router.post("/projetos/{projeto_id}/tickets", response_model=TicketDetalhe, status_code=201)
def criar_ticket(projeto_id: int, dados: TicketCriarIn, eu: Usuario = Depends(usuario_logado),
                 db: Session = Depends(get_db)):
    projeto = obter_projeto(db, projeto_id)
    if projeto.arquivado:
        raise HTTPException(422, "Projeto arquivado.")
    _validar_refs(db, dados.categoria_id, dados.responsavel_id)
    numero = db.scalar(
        update(Projeto).where(Projeto.id == projeto_id)
        .values(proximo_numero=Projeto.proximo_numero + 1).returning(Projeto.proximo_numero - 1)
    )
    desc = _descricao(dados.descricao)
    t = Ticket(
        projeto_id=projeto_id, numero=numero, titulo=dados.titulo.strip(), status=dados.status,
        categoria_id=dados.categoria_id, responsavel_id=dados.responsavel_id, criado_por=eu.id,
        descricao=desc, descricao_texto=extrair_texto(desc) if desc else "",
        ordem=_ordem_no_topo(db, projeto_id, dados.status),
        concluido_em=agora() if dados.status == "completado" else None,
    )
    t.labels = _labels(db, dados.label_ids)
    t.tarefas_feitas, t.tarefas_total = contar_tarefas(desc)
    db.add(t)
    db.flush()
    registrar(db, t, eu, "criou")
    return detalhe(db, eu, _carregar(db, t.id))


@router.get("/tickets/{ticket_id}", response_model=TicketDetalhe)
def obter_ticket(ticket_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    return detalhe(db, eu, _carregar(db, ticket_id))


@router.get("/projetos/{projeto_id}/tickets/numero/{numero}", response_model=TicketDetalhe)
def obter_por_numero(projeto_id: int, numero: int, eu: Usuario = Depends(usuario_logado),
                     db: Session = Depends(get_db)):
    tid = db.scalar(select(Ticket.id).where(Ticket.projeto_id == projeto_id, Ticket.numero == numero,
                                            Ticket.excluido_em.is_(None)))
    if tid is None:
        raise HTTPException(404, f"Ticket #{numero} não encontrado neste projeto.")
    return detalhe(db, eu, _carregar(db, tid))


@router.patch("/tickets/{ticket_id}", response_model=TicketDetalhe)
def editar_ticket(ticket_id: int, dados: TicketEditarIn, eu: Usuario = Depends(usuario_logado),
                  db: Session = Depends(get_db)):
    t = _carregar(db, ticket_id)
    campos = dados.model_fields_set
    if "titulo" in campos and dados.titulo is not None and dados.titulo.strip() != t.titulo:
        registrar(db, t, eu, "titulo", de=t.titulo, para=dados.titulo.strip())
        t.titulo = dados.titulo.strip()
    if "descricao" in campos:
        desc = _descricao(dados.descricao)
        if desc != t.descricao:
            t.descricao = desc
            t.descricao_texto = extrair_texto(desc) if desc else ""
            registrar(db, t, eu, "descricao")
            recalcular_tarefas(db, t)
    if "categoria_id" in campos and dados.categoria_id != t.categoria_id:
        _validar_refs(db, dados.categoria_id, None)
        registrar(db, t, eu, "categoria", de=t.categoria_id, para=dados.categoria_id)
        t.categoria_id = dados.categoria_id
    if "responsavel_id" in campos and dados.responsavel_id != t.responsavel_id:
        _validar_refs(db, None, dados.responsavel_id)
        registrar(db, t, eu, "responsavel", de=t.responsavel_id, para=dados.responsavel_id)
        t.responsavel_id = dados.responsavel_id
    if "label_ids" in campos and dados.label_ids is not None:
        novas = _labels(db, dados.label_ids)
        antes = {l.id for l in t.labels}
        depois = {l.id for l in novas}
        for lid in sorted(depois - antes):
            registrar(db, t, eu, "label_add", label_id=lid)
        for lid in sorted(antes - depois):
            registrar(db, t, eu, "label_rem", label_id=lid)
        t.labels = novas
    t.atualizado_em = agora()
    db.flush()
    db.expire(t)
    return detalhe(db, eu, _carregar(db, t.id))


@router.post("/tickets/{ticket_id}/mover", response_model=TicketDetalhe)
def mover_ticket(ticket_id: int, dados: MoverIn, eu: Usuario = Depends(usuario_logado),
                 db: Session = Depends(get_db)):
    t = _carregar(db, ticket_id)
    if dados.apos_id == t.id:
        raise HTTPException(422, "Posição inválida.")
    nova_ordem = (_ordem_no_topo(db, t.projeto_id, dados.status, exceto=t.id) if dados.apos_id is None
                  else _ordem_apos(db, t, dados.status, dados.apos_id))
    t = _carregar(db, ticket_id)  # pode ter sido expirado por uma renumeração
    if dados.status != t.status:
        registrar(db, t, eu, "moveu", de=t.status, para=dados.status)
        t.concluido_em = agora() if dados.status == "completado" else None
        t.status = dados.status
    t.ordem = nova_ordem
    t.atualizado_em = agora()
    db.flush()
    return detalhe(db, eu, t)


@router.delete("/tickets/{ticket_id}", status_code=204)
def excluir_ticket(ticket_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    t = _carregar(db, ticket_id)
    if not pode_excluir_ticket(eu, t):
        raise HTTPException(403, "Você não tem permissão para excluir este ticket.")
    t.excluido_em = agora()
    t.excluido_por = eu.id


# ============================================================== timeline
def _pode_editar_com(eu: Usuario, c: Comentario) -> bool:
    return c.autor_id == eu.id or tem(eu, "comentario_editar")


def _pode_excluir_com(eu: Usuario, c: Comentario) -> bool:
    return tem(eu, "comentario_excluir") or (c.autor_id == eu.id and tem(eu, "comentario_excluir_proprio"))


def item_comentario(eu: Usuario, c: Comentario) -> ItemTimeline:
    return ItemTimeline(
        tipo="comentario", id=c.id, criado_em=c.criado_em, usuario=usuario_basico(c.autor),
        conteudo=c.conteudo, editado_em=c.editado_em,
        pode_editar=_pode_editar_com(eu, c), pode_excluir=_pode_excluir_com(eu, c),
    )


@router.get("/tickets/{ticket_id}/timeline", response_model=list[ItemTimeline])
def timeline(ticket_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    _carregar(db, ticket_id)
    itens = [item_comentario(eu, c) for c in db.scalars(
        select(Comentario).where(Comentario.ticket_id == ticket_id, Comentario.excluido_em.is_(None))
        .options(selectinload(Comentario.autor)))]
    itens += [
        ItemTimeline(tipo="atividade", id=a.id, criado_em=a.criado_em, usuario=usuario_basico(a.usuario),
                     atividade=a.tipo, dados=a.dados)
        for a in db.scalars(select(Atividade).where(Atividade.ticket_id == ticket_id)
                            .options(selectinload(Atividade.usuario)))
    ]
    itens.sort(key=lambda i: (i.criado_em, 0 if i.tipo == "atividade" else 1, i.id))
    return itens


# ============================================================ comentários
def _validar_conteudo(db: Session, ticket_id: int, conteudo: dict) -> str:
    """Valida o documento (já sanitizado) e devolve o texto puro para a busca."""
    if conteudo.get("type") != "doc":
        raise HTTPException(422, "Conteúdo inválido.")
    if documento_vazio(conteudo):
        raise HTTPException(422, "O comentário está vazio.")
    refs = anexos_referenciados(conteudo)
    if refs:
        validos = set(db.scalars(select(Anexo.id).where(Anexo.id.in_(refs), Anexo.ticket_id == ticket_id)))
        if refs - validos:
            raise HTTPException(422, "Anexo inválido no comentário.")
    return extrair_texto(conteudo)


def _vincular_anexos(db: Session, ticket_id: int, comentario_id: int, conteudo: dict) -> None:
    refs = anexos_referenciados(conteudo)
    if refs:
        db.execute(update(Anexo).where(Anexo.id.in_(refs), Anexo.ticket_id == ticket_id,
                                       Anexo.comentario_id.is_(None)).values(comentario_id=comentario_id))


@router.post("/tickets/{ticket_id}/comentarios", response_model=ItemTimeline, status_code=201)
def comentar(ticket_id: int, dados: ComentarioIn, eu: Usuario = Depends(usuario_logado),
             db: Session = Depends(get_db)):
    t = _carregar(db, ticket_id)
    conteudo = sanitizar(dados.conteudo)
    texto_ = _validar_conteudo(db, t.id, conteudo)
    c = Comentario(ticket_id=t.id, autor_id=eu.id, conteudo=conteudo, texto=texto_)
    db.add(c)
    t.atualizado_em = agora()
    db.flush()
    _vincular_anexos(db, t.id, c.id, conteudo)
    recalcular_tarefas(db, t)
    db.refresh(c)
    return item_comentario(eu, c)


def _comentario(db: Session, comentario_id: int) -> Comentario:
    c = db.scalar(select(Comentario).where(Comentario.id == comentario_id, Comentario.excluido_em.is_(None))
                  .options(selectinload(Comentario.autor)))
    if c is None:
        raise HTTPException(404, "Comentário não encontrado.")
    _carregar(db, c.ticket_id)  # ticket precisa existir
    return c


@router.patch("/comentarios/{comentario_id}", response_model=ItemTimeline)
def editar_comentario(comentario_id: int, dados: ComentarioIn, eu: Usuario = Depends(usuario_logado),
                      db: Session = Depends(get_db)):
    c = _comentario(db, comentario_id)
    if not _pode_editar_com(eu, c):
        raise HTTPException(403, "Você não pode editar este comentário.")
    conteudo = sanitizar(dados.conteudo)
    c.texto = _validar_conteudo(db, c.ticket_id, conteudo)
    c.conteudo = conteudo
    c.editado_em = agora()
    db.flush()
    _vincular_anexos(db, c.ticket_id, c.id, conteudo)
    recalcular_tarefas(db, _carregar(db, c.ticket_id))
    return item_comentario(eu, c)


@router.delete("/comentarios/{comentario_id}", status_code=204)
def excluir_comentario(comentario_id: int, eu: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    c = _comentario(db, comentario_id)
    if not _pode_excluir_com(eu, c):
        raise HTTPException(403, "Você não tem permissão para excluir este comentário.")
    c.excluido_em = agora()
    c.excluido_por = eu.id
    recalcular_tarefas(db, _carregar(db, c.ticket_id))


# ================================================================ tarefas
# Qualquer usuário logado pode marcar/desmarcar uma tarefa (ex.: quem executa o procedimento),
# mesmo sem poder editar o texto. Fica registrado na linha do tempo quem marcou.
@router.post("/tickets/{ticket_id}/tarefas", response_model=TicketDetalhe)
def marcar_tarefa_descricao(ticket_id: int, dados: TarefaIn, eu: Usuario = Depends(usuario_logado),
                            db: Session = Depends(get_db)):
    t = _carregar(db, ticket_id)
    r = marcar_tarefa(t.descricao, dados.indice, dados.feito)
    if r is None:
        raise HTTPException(404, "Tarefa não encontrada (a descrição pode ter sido alterada).")
    novo, texto_ = r
    if novo != t.descricao:
        t.descricao = novo
        registrar(db, t, eu, "tarefa", texto=texto_, feito=dados.feito)
        recalcular_tarefas(db, t)
    db.flush()
    db.expire(t)
    return detalhe(db, eu, _carregar(db, t.id))


@router.post("/comentarios/{comentario_id}/tarefas", response_model=ItemTimeline)
def marcar_tarefa_comentario(comentario_id: int, dados: TarefaIn, eu: Usuario = Depends(usuario_logado),
                             db: Session = Depends(get_db)):
    c = _comentario(db, comentario_id)
    r = marcar_tarefa(c.conteudo, dados.indice, dados.feito)
    if r is None:
        raise HTTPException(404, "Tarefa não encontrada (o comentário pode ter sido alterado).")
    novo, texto_ = r
    if novo != c.conteudo:
        c.conteudo = novo   # sem marcar "editado": o texto não mudou
        t = _carregar(db, c.ticket_id)
        registrar(db, t, eu, "tarefa", texto=texto_, feito=dados.feito, comentario_id=c.id)
        recalcular_tarefas(db, t)
    db.flush()
    return item_comentario(eu, c)


# ================================================================= anexos
@router.post("/tickets/{ticket_id}/anexos", response_model=AnexoOut, status_code=201)
def enviar_anexo(ticket_id: int, arquivo: UploadFile = File(...), eu: Usuario = Depends(usuario_logado),
                 db: Session = Depends(get_db)):
    t = _carregar(db, ticket_id)
    rel, tamanho, mime = arquivos.salvar_upload(arquivo, f"anexos/{t.projeto_id}/{t.id}")
    a = Anexo(ticket_id=t.id, nome_original=(arquivo.filename or "arquivo")[:255], tipo_mime=mime,
              tamanho=tamanho, caminho=rel, enviado_por=eu.id)
    db.add(a)
    db.flush()
    db.refresh(a)
    return anexo_out(a)


@router.get("/tickets/{ticket_id}/anexos", response_model=list[AnexoOut])
def listar_anexos(ticket_id: int, _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    _carregar(db, ticket_id)
    q = select(Anexo).where(Anexo.ticket_id == ticket_id).order_by(Anexo.criado_em)
    return [anexo_out(a) for a in db.scalars(q)]


@router.get("/anexos/{anexo_id}/arquivo")
def baixar_anexo(anexo_id: int, download: bool = False, _: Usuario = Depends(usuario_logado),
                 db: Session = Depends(get_db)):
    a = db.get(Anexo, anexo_id)
    if a is None:
        raise HTTPException(404, "Anexo não encontrado.")
    return arquivos.resposta_arquivo(a.caminho, a.nome_original, a.tipo_mime, forcar_download=download)


@router.get("/anexos/{anexo_id}/planilha")
def ver_planilha(anexo_id: int, aba: int = Query(0, ge=0), _: Usuario = Depends(usuario_logado),
                 db: Session = Depends(get_db)):
    """Conteúdo de uma aba de planilha anexada (xlsx/xlsm/csv), para o visualizador."""
    a = db.get(Anexo, anexo_id)
    if a is None:
        raise HTTPException(404, "Anexo não encontrado.")
    return planilha.ler(arquivos.caminho_absoluto(a.caminho), a.nome_original, aba)
