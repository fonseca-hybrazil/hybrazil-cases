"""Converte o Markdown simples do Ora (comentários e descrições) para o documento do editor (TipTap).

Cobre o que aparece nos dados do Ora: parágrafos e quebras de linha, ```código``` com linguagem,
títulos (#), citações (>), listas (-, *, 1.), listas de tarefas (- [ ] / - [x]), linha (---),
**negrito**, *itálico*, ~~riscado~~, `código`, [links](url) e endereços http(s) soltos.
"""
import re

LINGUAGENS = {  # nome no Ora/Markdown -> nome no editor
    "sql": "sql", "tsql": "sql", "mysql": "sql", "python": "python", "py": "python", "js": "javascript",
    "javascript": "javascript", "ts": "typescript", "typescript": "typescript", "c#": "csharp", "cs": "csharp",
    "csharp": "csharp", "c": "c", "cpp": "cpp", "c++": "cpp", "java": "java", "vb": "vbnet", "vbnet": "vbnet",
    "vb.net": "vbnet", "vbs": "vbscript", "vbscript": "vbscript", "json": "json", "xml": "xml", "html": "xml",
    "css": "css", "bash": "bash", "sh": "bash", "shell": "bash", "powershell": "bash", "ps1": "bash", "cmd": "bash",
    "bat": "bash", "ini": "ini", "yaml": "yaml", "yml": "yaml", "markdown": "markdown", "md": "markdown",
    "diff": "diff", "st": "st", "iecst": "st", "scl": "st", "text": "plaintext", "txt": "plaintext",
    "plaintext": "plaintext",
}

_FENCE = re.compile(r"^\s*(```|~~~)\s*([\w#+.\-]*)\s*$")
_TITULO = re.compile(r"^(#{1,6})\s+(.*)$")
_CITACAO = re.compile(r"^>\s?(.*)$")
_TAREFA = re.compile(r"^\s*[-*+]\s+\[( |x|X)\]\s+(.*)$")
_LISTA = re.compile(r"^\s*[-*+]\s+(.*)$")
_NUMERADA = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
_LINHA = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")

_INLINE = re.compile(
    r"(?P<code>`[^`\n]+`)"
    r"|(?P<link>\[(?P<lt>[^\]\n]+)\]\((?P<lu>https?://[^)\s]+|mailto:[^)\s]+)\))"
    r"|(?P<bold>\*\*(?P<bt>[^*\n]+?)\*\*|__(?P<bt2>[^_\n]+?)__)"
    r"|(?P<strike>~~(?P<st>[^~\n]+?)~~)"
    r"|(?P<ital>(?<![\w*])\*(?P<it>[^*\s][^*\n]*?)\*(?![\w*]))"
    r"|(?P<url>https?://[^\s<>()\[\]]+[^\s<>()\[\].,;:!?'\"])"
)


def _texto(t: str, marks: list | None = None) -> dict:
    n = {"type": "text", "text": t}
    if marks:
        n["marks"] = marks
    return n


def inline(s: str) -> list[dict]:
    """Texto com marcações -> nós de texto do TipTap."""
    out: list[dict] = []
    pos = 0
    for m in _INLINE.finditer(s):
        if m.start() > pos:
            out.append(_texto(s[pos:m.start()]))
        if m.group("code"):
            out.append(_texto(m.group("code")[1:-1], [{"type": "code"}]))
        elif m.group("link"):
            out.append(_texto(m.group("lt"), [{"type": "link", "attrs": {"href": m.group("lu")}}]))
        elif m.group("bold"):
            out.append(_texto(m.group("bt") or m.group("bt2"), [{"type": "bold"}]))
        elif m.group("strike"):
            out.append(_texto(m.group("st"), [{"type": "strike"}]))
        elif m.group("ital"):
            out.append(_texto(m.group("it"), [{"type": "italic"}]))
        elif m.group("url"):
            out.append(_texto(m.group("url"), [{"type": "link", "attrs": {"href": m.group("url")}}]))
        pos = m.end()
    if pos < len(s):
        out.append(_texto(s[pos:]))
    return [n for n in out if n["text"]]


def _paragrafo(linhas: list[str]) -> dict:
    conteudo: list[dict] = []
    for i, linha in enumerate(linhas):
        if i:
            conteudo.append({"type": "hardBreak"})
        conteudo += inline(linha)
    return {"type": "paragraph", "content": conteudo} if conteudo else {"type": "paragraph"}


def _item(texto: str) -> dict:
    return {"type": "listItem", "content": [_paragrafo([texto])]}


def para_doc(md: str | None) -> dict | None:
    """Markdown -> documento. None se não houver texto."""
    if not md or not md.strip():
        return None
    linhas = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocos: list[dict] = []
    para: list[str] = []
    i = 0

    def fechar_paragrafo():
        if para:
            blocos.append(_paragrafo(para))
            para.clear()

    while i < len(linhas):
        linha = linhas[i]
        f = _FENCE.match(linha)
        if f:
            fechar_paragrafo()
            marca, lang = f.group(1), f.group(2).lower()
            codigo = []
            i += 1
            while i < len(linhas) and not linhas[i].strip().startswith(marca):
                codigo.append(linhas[i])
                i += 1
            i += 1  # pula o fechamento
            bloco = {"type": "codeBlock", "attrs": {"language": LINGUAGENS.get(lang)}}
            if "\n".join(codigo):
                bloco["content"] = [_texto("\n".join(codigo))]
            blocos.append(bloco)
            continue
        if not linha.strip():
            fechar_paragrafo()
            i += 1
            continue
        if _LINHA.match(linha):
            fechar_paragrafo()
            blocos.append({"type": "horizontalRule"})
            i += 1
            continue
        t = _TITULO.match(linha)
        if t:
            fechar_paragrafo()
            blocos.append({"type": "heading", "attrs": {"level": 2 if len(t.group(1)) <= 2 else 3},
                           "content": inline(t.group(2)) or [_texto(t.group(2) or " ")]})
            i += 1
            continue
        if _CITACAO.match(linha):
            fechar_paragrafo()
            citadas = []
            while i < len(linhas) and _CITACAO.match(linhas[i]):
                citadas.append(_CITACAO.match(linhas[i]).group(1))
                i += 1
            blocos.append({"type": "blockquote", "content": [_paragrafo(citadas)]})
            continue
        if _TAREFA.match(linha):
            fechar_paragrafo()
            itens = []
            while i < len(linhas) and _TAREFA.match(linhas[i]):
                m = _TAREFA.match(linhas[i])
                itens.append({"type": "taskItem", "attrs": {"checked": m.group(1).lower() == "x"},
                              "content": [_paragrafo([m.group(2)])]})
                i += 1
            blocos.append({"type": "taskList", "content": itens})
            continue
        if _NUMERADA.match(linha):
            fechar_paragrafo()
            inicio = int(_NUMERADA.match(linha).group(1))
            itens = []
            while i < len(linhas) and _NUMERADA.match(linhas[i]):
                itens.append(_item(_NUMERADA.match(linhas[i]).group(2)))
                i += 1
            no = {"type": "orderedList", "content": itens}
            if inicio != 1:
                no["attrs"] = {"start": inicio}
            blocos.append(no)
            continue
        if _LISTA.match(linha) and not linha.lstrip().startswith("**"):
            fechar_paragrafo()
            itens = []
            while i < len(linhas) and _LISTA.match(linhas[i]) and not _TAREFA.match(linhas[i]):
                itens.append(_item(_LISTA.match(linhas[i]).group(1)))
                i += 1
            blocos.append({"type": "bulletList", "content": itens})
            continue
        para.append(linha)
        i += 1
    fechar_paragrafo()
    return {"type": "doc", "content": blocos} if blocos else None
