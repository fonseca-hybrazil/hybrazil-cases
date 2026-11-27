"""Biblioteca de ícones enviados (PNG, SVG, ICO, JPG, WebP, GIF), usados como ícone de projeto."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from .. import arquivos
from ..db import get_db
from ..models import Icone, Projeto, Usuario
from ..schemas import IconeOut
from ..security import exigir, usuario_logado

router = APIRouter(prefix="/api/icones", tags=["icones"])
admin = exigir("admin_projetos")

LIMITE_KB = 512
# extensão de gravação e tipo servido, identificados pelo conteúdo (não pelo nome do arquivo)
TIPOS = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp",
         "ico": "image/x-icon", "svg": "image/svg+xml"}
# Um SVG é um documento: só aceitamos desenho, sem nada que execute código ou busque conteúdo externo.
SVG_PROIBIDOS = {"script", "foreignobject", "iframe", "embed", "object", "audio", "video", "handler", "listener"}
# Servido com CSP restrita: mesmo aberto direto na aba, um SVG não executa scripts.
CABECALHOS = {"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox",
              "X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=604800, immutable"}


def _tipo(dados: bytes) -> str | None:
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if dados[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "webp"
    if dados[:4] == b"\x00\x00\x01\x00":
        return "ico"
    inicio = dados[:1024].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if inicio.startswith((b"<?xml", b"<svg", b"<!--", b"<!doctype svg")) and b"<svg" in dados[:4096].lower():
        return "svg"
    return None


def _validar_svg(dados: bytes) -> None:
    from defusedxml import ElementTree as ET  # bloqueia entidades XML maliciosas
    try:
        raiz = ET.fromstring(dados)
    except Exception:
        raise HTTPException(422, "SVG inválido (não foi possível ler o arquivo).")
    if raiz.tag.rsplit("}", 1)[-1].lower() != "svg":
        raise HTTPException(422, "O arquivo não é um SVG.")
    for el in raiz.iter():
        tag = el.tag.rsplit("}", 1)[-1].lower() if isinstance(el.tag, str) else ""
        if tag in SVG_PROIBIDOS:
            raise HTTPException(422, f"SVG com conteúdo não permitido (<{tag}>). Use um SVG só com desenho.")
        for nome, valor in el.attrib.items():
            nome = nome.rsplit("}", 1)[-1].lower()
            v = valor.strip().lower()
            if nome.startswith("on"):
                raise HTTPException(422, "SVG com script (atributo de evento) não é permitido.")
            if nome == "href" and not (v.startswith("#") or v.startswith("data:image/")):
                raise HTTPException(422, "SVG com link para conteúdo externo não é permitido.")
            if "javascript:" in v or ("url(" in v and "url(#" not in v.replace(" ", "")):
                raise HTTPException(422, "SVG com referência externa não é permitido.")


def _out(i: Icone, em_uso: int = 0) -> IconeOut:
    return IconeOut(id=i.id, nome=i.nome, url=f"/api/icones/{i.id}/arquivo", tipo_mime=i.tipo_mime,
                    tamanho=i.tamanho, em_uso=em_uso)


@router.get("", response_model=list[IconeOut])
def listar(_: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    uso = dict(db.execute(select(Projeto.icone, func.count()).where(Projeto.icone.like("lib:%"))
                          .group_by(Projeto.icone)).all())
    return [_out(i, uso.get(f"lib:{i.id}", 0)) for i in db.scalars(select(Icone).order_by(func.lower(Icone.nome)))]


@router.post("", response_model=IconeOut, status_code=201)
def enviar(arquivo: UploadFile = File(...), eu: Usuario = Depends(admin), db: Session = Depends(get_db)):
    dados = arquivo.file.read(LIMITE_KB * 1024 + 1)
    if len(dados) > LIMITE_KB * 1024:
        raise HTTPException(413, f"Ícone maior que {LIMITE_KB} KB. Use uma imagem menor (ícones ficam bem com 64 a 256 px).")
    ext = _tipo(dados)
    if ext is None:
        raise HTTPException(415, "Formato não suportado. Envie PNG, SVG, ICO, JPG, WebP ou GIF.")
    if ext == "svg":
        _validar_svg(dados)
    rel = Path("icones") / f"{uuid.uuid4().hex}.{ext}"
    destino = arquivos.raiz() / rel
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(dados)
    nome = Path(arquivo.filename or "icone").stem.strip()[:80] or "icone"
    i = Icone(nome=nome, tipo_mime=TIPOS[ext], tamanho=len(dados), caminho=rel.as_posix(), enviado_por=eu.id)
    db.add(i)
    db.flush()
    return _out(i)


@router.get("/{icone_id}/arquivo")
def arquivo(icone_id: int, _: Usuario = Depends(usuario_logado), db: Session = Depends(get_db)):
    i = db.get(Icone, icone_id)
    if i is None:
        raise HTTPException(404, "Ícone não encontrado.")
    p = arquivos.caminho_absoluto(i.caminho)
    if not p.is_file():
        raise HTTPException(404, "Arquivo do ícone não encontrado no servidor.")
    return FileResponse(p, media_type=i.tipo_mime, headers=CABECALHOS)


@router.delete("/{icone_id}", status_code=204)
def excluir(icone_id: int, _: Usuario = Depends(admin), db: Session = Depends(get_db)):
    """Remove da biblioteca; projetos que o usavam voltam ao ícone padrão."""
    i = db.get(Icone, icone_id)
    if i is None:
        raise HTTPException(404, "Ícone não encontrado.")
    db.execute(update(Projeto).where(Projeto.icone == f"lib:{i.id}").values(icone=None))
    caminho = i.caminho
    db.delete(i)
    db.flush()
    arquivos.remover(caminho)
