"""Gravação e leitura de arquivos enviados (anexos e avatares)."""
import mimetypes
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from .config import get_settings

# Tipos que o navegador pode exibir com segurança dentro da página
INLINE_SEGUROS = ("image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp", "application/pdf",
                  "video/", "audio/", "text/plain")
CHUNK = 1024 * 1024


def raiz() -> Path:
    return Path(get_settings().upload_dir)


def salvar_upload(arquivo: UploadFile, subpasta: str, limite_mb: int | None = None) -> tuple[str, int, str]:
    """Grava o arquivo em disco. Retorna (caminho relativo, tamanho, tipo mime)."""
    limite = (limite_mb or get_settings().max_upload_mb) * 1024 * 1024
    nome = arquivo.filename or "arquivo"
    ext = Path(nome).suffix.lower()[:12]
    if ext and not all(c.isalnum() or c == "." for c in ext):
        ext = ""
    rel = Path(subpasta) / f"{uuid.uuid4().hex}{ext}"
    destino = raiz() / rel
    destino.parent.mkdir(parents=True, exist_ok=True)
    tamanho = 0
    try:
        with destino.open("wb") as f:
            while bloco := arquivo.file.read(CHUNK):
                tamanho += len(bloco)
                if tamanho > limite:
                    raise HTTPException(413, f"Arquivo maior que o limite de {limite // (1024 * 1024)} MB.")
                f.write(bloco)
    except BaseException:
        destino.unlink(missing_ok=True)
        raise
    mime = arquivo.content_type or mimetypes.guess_type(nome)[0] or "application/octet-stream"
    if mime == "application/octet-stream":
        mime = mimetypes.guess_type(nome)[0] or mime
    return rel.as_posix(), tamanho, mime


def caminho_absoluto(rel: str) -> Path:
    base = raiz().resolve()
    p = (base / rel).resolve()
    if base not in p.parents:
        raise HTTPException(404, "Arquivo não encontrado.")
    return p


def resposta_arquivo(rel: str, nome: str, mime: str, forcar_download: bool = False) -> FileResponse:
    p = caminho_absoluto(rel)
    if not p.is_file():
        raise HTTPException(404, "Arquivo não encontrado no servidor.")
    inline = not forcar_download and mime.startswith(INLINE_SEGUROS)
    return FileResponse(
        p,
        media_type=mime if inline else "application/octet-stream",
        filename=nome,
        content_disposition_type="inline" if inline else "attachment",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
            "Cache-Control": "private, max-age=86400",
        },
    )


def remover(rel: str | None) -> None:
    if rel:
        try:
            caminho_absoluto(rel).unlink(missing_ok=True)
        except HTTPException:
            pass
