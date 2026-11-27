from datetime import datetime

from sqlalchemy import (
    ARRAY, BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, Table, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

grupo_usuarios = Table(
    "grupo_usuarios", Base.metadata,
    Column("grupo_id", ForeignKey("grupos.id", ondelete="CASCADE"), primary_key=True),
    Column("usuario_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
)

ticket_labels = Table(
    "ticket_labels", Base.metadata,
    Column("ticket_id", ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)

favoritos = Table(
    "favoritos", Base.metadata,
    Column("usuario_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("projeto_id", ForeignKey("projetos.id", ondelete="CASCADE"), primary_key=True),
)

TS = DateTime(timezone=True)


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(Text)
    login: Mapped[str] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    avatar_caminho: Mapped[str | None] = mapped_column(Text)
    senha_hash: Mapped[str] = mapped_column(Text)
    trocar_senha: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_acesso: Mapped[datetime | None] = mapped_column(TS)
    tentativas_falhas: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(TS)
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    ora_id: Mapped[str | None] = mapped_column(Text)

    grupos: Mapped[list["Grupo"]] = relationship(secondary=grupo_usuarios, back_populates="usuarios")

    @property
    def permissoes(self) -> set[str]:
        return {p for g in self.grupos for p in g.permissoes}


class Grupo(Base):
    __tablename__ = "grupos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str] = mapped_column(Text, default="")
    permissoes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    sistema: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())

    usuarios: Mapped[list[Usuario]] = relationship(secondary=grupo_usuarios, back_populates="grupos")


class Sessao(Base):
    __tablename__ = "sessoes"
    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    expira_em: Mapped[datetime] = mapped_column(TS)
    ip: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)

    usuario: Mapped[Usuario] = relationship()


class Projeto(Base):
    __tablename__ = "projetos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str] = mapped_column(Text, default="")
    proximo_numero: Mapped[int] = mapped_column(Integer, default=1)
    arquivado: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    ora_id: Mapped[str | None] = mapped_column(Text)


class Categoria(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(Text)
    icone: Mapped[str] = mapped_column(Text)
    cor: Mapped[str] = mapped_column(Text)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)


class Label(Base):
    __tablename__ = "labels"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(Text)
    cor: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    ora_id: Mapped[str | None] = mapped_column(Text)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(Text)
    descricao: Mapped[dict | None] = mapped_column(JSONB)
    descricao_texto: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, default="pendente")
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    criado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    ordem: Mapped[float] = mapped_column(Float, default=0)
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    concluido_em: Mapped[datetime | None] = mapped_column(TS)
    excluido_em: Mapped[datetime | None] = mapped_column(TS)
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    ora_id: Mapped[str | None] = mapped_column(Text)

    labels: Mapped[list[Label]] = relationship(secondary=ticket_labels, order_by=Label.nome)
    responsavel: Mapped[Usuario | None] = relationship(foreign_keys=[responsavel_id])
    autor: Mapped[Usuario | None] = relationship(foreign_keys=[criado_por])


class Comentario(Base):
    __tablename__ = "comentarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    autor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    conteudo: Mapped[dict] = mapped_column(JSONB)
    texto: Mapped[str] = mapped_column(Text, default="")
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    editado_em: Mapped[datetime | None] = mapped_column(TS)
    excluido_em: Mapped[datetime | None] = mapped_column(TS)
    excluido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    ora_id: Mapped[str | None] = mapped_column(Text)

    autor: Mapped[Usuario | None] = relationship(foreign_keys=[autor_id])


class Anexo(Base):
    __tablename__ = "anexos"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    comentario_id: Mapped[int | None] = mapped_column(ForeignKey("comentarios.id", ondelete="SET NULL"))
    nome_original: Mapped[str] = mapped_column(Text)
    tipo_mime: Mapped[str] = mapped_column(Text)
    tamanho: Mapped[int] = mapped_column(BigInteger)
    caminho: Mapped[str] = mapped_column(Text)
    enviado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    ora_id: Mapped[str | None] = mapped_column(Text)


class Atividade(Base):
    __tablename__ = "atividades"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    tipo: Mapped[str] = mapped_column(Text)
    dados: Mapped[dict] = mapped_column(JSONB, default=dict)
    criado_em: Mapped[datetime] = mapped_column(TS, server_default=func.now())

    usuario: Mapped[Usuario | None] = relationship()
