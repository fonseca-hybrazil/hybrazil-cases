"""Conversão de modelos para as respostas da API."""
from .models import Anexo, Usuario
from .schemas import AnexoOut, UsuarioBasico


def avatar_url(u: Usuario) -> str | None:
    if not u.avatar_caminho:
        return None
    # o nome do arquivo (aleatório) muda quando o avatar é trocado, evitando cache antigo
    versao = u.avatar_caminho.replace("\\", "/").rsplit("/", 1)[-1].split(".")[0][:12]
    return f"/api/usuarios/{u.id}/avatar?v={versao}"


def usuario_basico(u: Usuario | None) -> UsuarioBasico | None:
    if u is None:
        return None
    return UsuarioBasico(id=u.id, nome=u.nome, login=u.login, avatar_url=avatar_url(u), ativo=u.ativo)


def anexo_out(a: Anexo) -> AnexoOut:
    return AnexoOut(
        id=a.id, nome=a.nome_original, tipo_mime=a.tipo_mime, tamanho=a.tamanho,
        url=f"/api/anexos/{a.id}/arquivo", criado_em=a.criado_em,
    )
