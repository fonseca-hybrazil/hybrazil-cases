"""Baixa os arquivos referenciados na exportação do Ora (anexos de tickets e de comentários e
fotos dos membros) para runtime/ora-export/<projeto>/arquivos/. Os arquivos do Ora ficam no
Amazon S3 com endereço público, então não precisa de login. Pula os já baixados.

Uso:  python ora/baixar_arquivos.py automacao mikrotik resolucao
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PASTA = Path(__file__).resolve().parents[2] / "runtime" / "ora-export"
URL_ANEXO_TICKET = "https://ora-attachments.s3.amazonaws.com/"
URL_ANEXO_MSG = "https://message-attachments.s3.amazonaws.com/"


def nome_local(ref: str) -> str:
    """Alguns anexos guardam a URL completa em vez do nome; o arquivo local usa só o nome."""
    return ref.rstrip("/").rsplit("/", 1)[-1] if ref.startswith(("http://", "https://")) else ref


def url_de(ref: str, base: str) -> str:
    return ref if ref.startswith(("http://", "https://")) else base + ref


def urls_do_projeto(base: Path) -> dict[str, str]:
    urls: dict[str, str] = {}
    for arq in (base / "tickets").glob("*.json"):
        t = json.loads(arq.read_text(encoding="utf-8"))
        detalhe = t.get("detalhe") if isinstance(t.get("detalhe"), dict) else {}
        for f in detalhe.get("files") or []:
            if not f.get("deleted") and f.get("data_path"):
                urls[nome_local(f["data_path"])] = url_de(f["data_path"], URL_ANEXO_TICKET)
        for m in t.get("mensagens") or []:
            if m.get("deleted"):
                continue
            for a in m.get("attachments") or []:
                if a.get("url"):
                    urls[nome_local(a["url"])] = url_de(a["url"], URL_ANEXO_MSG)
    projeto = json.loads((base / "projeto.json").read_text(encoding="utf-8"))
    for d in projeto["data"].get("developers") or []:
        foto = (d.get("profile_picture") or "").split("?")[0]
        if foto.startswith("https://") and not foto.endswith("default.png"):
            urls[f"avatar-{d['dev_id']}"] = foto
    return urls


def baixar(apelido: str) -> None:
    base = PASTA / apelido
    destino = base / "arquivos"
    destino.mkdir(parents=True, exist_ok=True)
    urls = urls_do_projeto(base)
    faltam = {n: u for n, u in urls.items() if not (destino / n).exists()}
    print(f"[{apelido}] {len(urls)} arquivos, faltam {len(faltam)}", flush=True)
    erros = []

    def um(item):
        nome, url = item
        tmp = destino / (nome + ".tmp")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HyBrazilCases-migracao"})
            with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
                while bloco := r.read(1 << 20):
                    f.write(bloco)
            tmp.replace(destino / nome)
        except Exception as e:  # noqa: BLE001 - registra e segue; rodar de novo tenta só os que faltam
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            erros.append([nome, url, repr(e)[:200]])

    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, _ in enumerate(ex.map(um, faltam.items()), 1):
            if i % 100 == 0 or i == len(faltam):
                print(f"[{apelido}] {i}/{len(faltam)} ({len(erros)} erros)", flush=True)
    (base / "erros-arquivos.json").write_text(json.dumps(erros, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    for apelido in sys.argv[1:] or ["automacao", "mikrotik", "resolucao"]:
        baixar(apelido)
