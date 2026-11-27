"""Utilidades para o conteúdo do editor (documento JSON do TipTap/ProseMirror)."""
import copy
import re
from typing import Any

BLOCOS = {"paragraph", "heading", "blockquote", "codeBlock", "listItem", "taskItem", "horizontalRule"}
MAX_PROFUNDIDADE = 60


def extrair_texto(doc: Any) -> str:
    """Texto puro do documento, usado na busca."""
    partes: list[str] = []

    def visitar(no: Any, prof: int) -> None:
        if prof > MAX_PROFUNDIDADE or not isinstance(no, dict):
            return
        tipo = no.get("type")
        if tipo == "text":
            partes.append(str(no.get("text", "")))
        elif tipo == "hardBreak":
            partes.append("\n")
        elif tipo in ("arquivo", "video", "image"):
            nome = (no.get("attrs") or {}).get("nome") or (no.get("attrs") or {}).get("alt")
            if nome:
                partes.append(f" {nome} ")
        for filho in no.get("content") or []:
            visitar(filho, prof + 1)
        if tipo in BLOCOS:
            partes.append("\n")

    visitar(doc, 0)
    return "".join(partes).strip()


def anexos_referenciados(doc: Any) -> set[int]:
    """IDs de anexos usados no documento (atributo anexoId de imagens, vídeos e arquivos)."""
    ids: set[int] = set()

    def visitar(no: Any, prof: int) -> None:
        if prof > MAX_PROFUNDIDADE or not isinstance(no, dict):
            return
        anexo_id = (no.get("attrs") or {}).get("anexoId")
        if isinstance(anexo_id, int):
            ids.add(anexo_id)
        for filho in no.get("content") or []:
            visitar(filho, prof + 1)

    visitar(doc, 0)
    return ids


_URL_ANEXO = re.compile(r"^/api/anexos/\d+/arquivo$")
_COR = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgba?\([\d\s.,%]+\))$")


def _url_ok(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    u = url.strip()
    return bool(_URL_ANEXO.match(u)) or u.lower().startswith(("http://", "https://", "mailto:"))


def sanitizar(doc: Any) -> Any:
    """Remove links/mídias com endereços perigosos (ex.: javascript:) e cores inválidas."""
    def limpar(no: Any, prof: int) -> Any:
        if prof > MAX_PROFUNDIDADE or not isinstance(no, dict):
            return None
        tipo = no.get("type")
        attrs = no.get("attrs") or {}
        if tipo in ("image", "video", "arquivo") and not _url_ok(attrs.get("src")):
            return None
        if tipo == "taskItem":
            no = {**no, "attrs": {**attrs, "checked": attrs.get("checked") is True}}
        if "marks" in no:
            marks = []
            for m in no.get("marks") or []:
                if not isinstance(m, dict):
                    continue
                mattrs = m.get("attrs") or {}
                if m.get("type") == "link" and not _url_ok(mattrs.get("href")):
                    continue
                if m.get("type") == "textStyle" and mattrs.get("color") and not _COR.match(str(mattrs["color"])):
                    m = {**m, "attrs": {**mattrs, "color": None}}
                marks.append(m)
            no = {**no, "marks": marks}
        if "content" in no:
            no = {**no, "content": [f for f in (limpar(c, prof + 1) for c in no.get("content") or []) if f]}
        return no

    return limpar(doc, 0)


def _itens_tarefa(doc: Any) -> list[dict]:
    """Itens de lista de tarefas (taskItem) na ordem de leitura; um item pai vem antes dos subitens."""
    itens: list[dict] = []

    def visitar(no: Any, prof: int) -> None:
        if prof > MAX_PROFUNDIDADE or not isinstance(no, dict):
            return
        if no.get("type") == "taskItem":
            itens.append(no)
        for filho in no.get("content") or []:
            visitar(filho, prof + 1)

    visitar(doc, 0)
    return itens


def contar_tarefas(doc: Any) -> tuple[int, int]:
    """(feitas, total) das caixas de tarefa do documento."""
    itens = _itens_tarefa(doc)
    return sum(1 for i in itens if (i.get("attrs") or {}).get("checked") is True), len(itens)


def marcar_tarefa(doc: Any, indice: int, feito: bool) -> tuple[dict, str] | None:
    """Cópia do documento com a tarefa `indice` marcada/desmarcada, e o texto da tarefa.
    None se não existir tarefa nessa posição."""
    novo = copy.deepcopy(doc)
    itens = _itens_tarefa(novo)
    if not 0 <= indice < len(itens):
        return None
    item = itens[indice]
    item["attrs"] = {**(item.get("attrs") or {}), "checked": feito}
    primeiro = (item.get("content") or [None])[0]  # o texto do item, sem os subitens
    return novo, extrair_texto(primeiro)[:200]


def documento_vazio(doc: Any) -> bool:
    return not extrair_texto(doc) and not anexos_referenciados(doc)


def doc_de_texto(texto: str) -> dict:
    """Documento simples a partir de texto puro (útil para testes e importação)."""
    paragrafos = [
        {"type": "paragraph", "content": [{"type": "text", "text": linha}]} if linha else {"type": "paragraph"}
        for linha in texto.split("\n")
    ]
    return {"type": "doc", "content": paragrafos}
