from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["pendente", "andamento", "completado"]
COR_REGEX = r"^#[0-9a-fA-F]{6}$"


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------- usuários
class UsuarioBasico(Base):
    id: int
    nome: str
    login: str
    avatar_url: str | None = None
    ativo: bool = True


class GrupoResumo(Base):
    id: int
    nome: str


class UsuarioAdmin(UsuarioBasico):
    email: str | None
    trocar_senha: bool
    ultimo_acesso: datetime | None
    bloqueado_ate: datetime | None
    criado_em: datetime
    grupos: list[GrupoResumo]


class Eu(UsuarioBasico):
    email: str | None
    trocar_senha: bool
    permissoes: list[str]


class LoginIn(BaseModel):
    login: str
    senha: str
    lembrar: bool = False


class TrocarSenhaIn(BaseModel):
    senha_atual: str
    nova_senha: str


class PerfilIn(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=120)
    email: str | None = Field(None, max_length=200)


class UsuarioCriarIn(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    login: str = Field(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9._@-]+$")
    email: str | None = Field(None, max_length=200)
    senha: str
    grupo_ids: list[int] = []


class UsuarioEditarIn(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=120)
    login: str | None = Field(None, min_length=2, max_length=60, pattern=r"^[A-Za-z0-9._@-]+$")
    email: str | None = Field(None, max_length=200)
    ativo: bool | None = None
    grupo_ids: list[int] | None = None


class RedefinirSenhaIn(BaseModel):
    nova_senha: str


# ------------------------------------------------------------------- grupos
class GrupoOut(Base):
    id: int
    nome: str
    descricao: str
    permissoes: list[str]
    sistema: bool
    usuario_ids: list[int]


class GrupoIn(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    descricao: str = Field("", max_length=300)
    permissoes: list[str] = []


class GrupoEditarIn(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=80)
    descricao: str | None = Field(None, max_length=300)
    permissoes: list[str] | None = None
    usuario_ids: list[int] | None = None


# ------------------------------------------------------ categorias e labels
class CategoriaOut(Base):
    id: int
    nome: str
    icone: str
    cor: str
    ordem: int
    ativa: bool


class CategoriaIn(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    icone: str = Field(min_length=1, max_length=60)
    cor: str = Field(pattern=COR_REGEX)


class CategoriaEditarIn(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=60)
    icone: str | None = Field(None, min_length=1, max_length=60)
    cor: str | None = Field(None, pattern=COR_REGEX)
    ativa: bool | None = None


class OrdemIn(BaseModel):
    ids: list[int]


class LabelOut(Base):
    id: int
    nome: str
    cor: str


class LabelComUso(LabelOut):
    uso: int


class LabelIn(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    cor: str = Field(pattern=COR_REGEX)

    @field_validator("nome")
    @classmethod
    def limpar(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome obrigatório")
        return v


class LabelEditarIn(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=60)
    cor: str | None = Field(None, pattern=COR_REGEX)


class MesclarIn(BaseModel):
    destino_id: int


# ----------------------------------------------------------------- projetos
class ContagemStatus(BaseModel):
    pendente: int = 0
    andamento: int = 0
    completado: int = 0


class ProjetoOut(Base):
    id: int
    nome: str
    descricao: str
    arquivado: bool
    favorito: bool = False
    contagem: ContagemStatus = ContagemStatus()
    icone: str | None = None
    icone_cor: str | None = None


ICONE_PADRAO = r"^(lucide:[a-z0-9-]{1,60}|lib:\d{1,9})$"
COR_HEX = r"^#[0-9a-fA-F]{6}$"


class ProjetoIn(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    descricao: str = Field("", max_length=2000)
    icone: str | None = Field(None, pattern=ICONE_PADRAO)
    icone_cor: str | None = Field(None, pattern=COR_HEX)


class ProjetoEditarIn(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=100)
    descricao: str | None = Field(None, max_length=2000)
    arquivado: bool | None = None
    # "" remove o ícone (volta ao padrão); None não mexe
    icone: str | None = Field(None, pattern=ICONE_PADRAO + "|^$")
    icone_cor: str | None = Field(None, pattern=COR_HEX + "|^$")


class IconeOut(BaseModel):
    id: int
    nome: str
    url: str
    tipo_mime: str
    tamanho: int
    em_uso: int = 0


# ------------------------------------------------------------------ tickets
class TicketResumo(BaseModel):
    id: int
    projeto_id: int
    numero: int
    titulo: str
    status: Status
    categoria_id: int | None
    responsavel: UsuarioBasico | None
    label_ids: list[int]
    qtd_comentarios: int
    tem_descricao: bool
    tarefas_total: int
    tarefas_feitas: int
    ordem: float
    criado_em: datetime
    concluido_em: datetime | None


class TicketDetalhe(TicketResumo):
    descricao: dict | None
    criado_por: UsuarioBasico | None
    atualizado_em: datetime
    pode_excluir: bool


class Coluna(BaseModel):
    total: int
    tickets: list[TicketResumo]


class Quadro(BaseModel):
    pendente: Coluna
    andamento: Coluna
    completado: Coluna
    total_sem_filtro: ContagemStatus


class TicketCriarIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=500)
    status: Status = "pendente"
    categoria_id: int | None = None
    responsavel_id: int | None = None
    label_ids: list[int] = []
    descricao: dict | None = None


class TicketEditarIn(BaseModel):
    """Campos ausentes não são alterados. Para limpar categoria/responsável envie null."""
    model_config = ConfigDict(extra="forbid")
    titulo: str | None = Field(None, min_length=1, max_length=500)
    descricao: dict | None = None
    categoria_id: int | None = None
    responsavel_id: int | None = None
    label_ids: list[int] | None = None


class MoverIn(BaseModel):
    status: Status
    apos_id: int | None = None  # None = topo da coluna


# -------------------------------------------------------------- comentários
class AnexoOut(Base):
    id: int
    nome: str
    tipo_mime: str
    tamanho: int
    url: str
    criado_em: datetime


class ComentarioIn(BaseModel):
    conteudo: dict


class TarefaIn(BaseModel):
    indice: int = Field(ge=0)  # posição da caixa no documento (ordem de leitura, começando em 0)
    feito: bool


class ItemTimeline(BaseModel):
    tipo: Literal["comentario", "atividade"]
    id: int
    criado_em: datetime
    usuario: UsuarioBasico | None
    # comentário
    conteudo: dict | None = None
    editado_em: datetime | None = None
    pode_editar: bool = False
    pode_excluir: bool = False
    # atividade
    atividade: str | None = None
    dados: dict[str, Any] | None = None


class PermissaoOut(BaseModel):
    chave: str
    descricao: str
