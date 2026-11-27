"""Monta a exportação do Ora a partir dos pacotes tirados da aba do app.ora.pm.

Na aba do Ora, a exportação fica na memória da página; cada pacote é uma string
"HYORA|<apelido>|<parte>|<total>|<base64 de gzip>" (pedaços de um JSON {projeto, tickets}).
Este script junta os pedaços e grava runtime/ora-export/<apelido>/projeto.json e tickets/<id>.json.

Uso:  python ora/receber.py <arquivo com pacotes> [<arquivo> ...]
      (aceita texto puro ou a saída de ferramenta em JSON [{type, text}])
"""
import base64
import gzip
import json
import re
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parents[2] / "runtime" / "ora-export"
PACOTE = re.compile(r"HYORA\|([a-z0-9_-]+)\|(\d+)\|(\d+)\|([A-Za-z0-9+/=]+)")
PEDACOS = PASTA / "_pedacos"


def textos(caminho: Path) -> list[str]:
    bruto = caminho.read_text(encoding="utf-8")
    try:
        dados = json.loads(bruto)
    except ValueError:
        return [bruto]
    saida = []
    for item in dados if isinstance(dados, list) else [dados]:
        t = item.get("text") if isinstance(item, dict) else item
        if isinstance(t, str):
            try:
                v = json.loads(t)
                saida.append(v if isinstance(v, str) else t)
            except ValueError:
                saida.append(t)
    return saida


def main(arquivos: list[str]) -> None:
    PEDACOS.mkdir(parents=True, exist_ok=True)
    recebidos: set[str] = set()
    for a in arquivos:
        for t in textos(Path(a)):
            for apelido, parte, total, dados in PACOTE.findall(t):
                (PEDACOS / f"{apelido}.{int(parte):04d}-de-{int(total):04d}").write_text(dados, encoding="ascii")
                recebidos.add(apelido)
                print(f"pedaço {apelido} {parte}/{total} ({len(dados)} caracteres)")
    # monta os projetos que estiverem completos
    por_apelido: dict[str, list[Path]] = {}
    for p in PEDACOS.iterdir():
        por_apelido.setdefault(p.name.split(".")[0], []).append(p)
    for apelido, partes in por_apelido.items():
        if apelido not in recebidos:  # só monta os projetos que chegaram agora
            continue
        total = int(partes[0].name.rsplit("-de-", 1)[1])
        if len(partes) != total:
            print(f"{apelido}: {len(partes)} de {total} pedaços; faltam os demais")
            continue
        b64 = "".join(p.read_text(encoding="ascii") for p in sorted(partes))
        exp = json.loads(gzip.decompress(base64.b64decode(b64)))
        base = PASTA / apelido
        (base / "tickets").mkdir(parents=True, exist_ok=True)
        (base / "projeto.json").write_text(json.dumps(exp["projeto"], ensure_ascii=False), encoding="utf-8")
        for tid, t in exp["tickets"].items():
            (base / "tickets" / f"{tid}.json").write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")
        (base / "estado.json").write_text(json.dumps(exp.get("estado"), ensure_ascii=False), encoding="utf-8")
        print(f"{apelido}: projeto + {len(exp['tickets'])} tickets gravados em {base}")


if __name__ == "__main__":
    main(sys.argv[1:])
