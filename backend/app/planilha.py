"""Leitura de planilhas anexadas (xlsx/xlsm/csv) para o visualizador do site, sem baixar o arquivo.

Só lê valores (o resultado salvo das fórmulas), uma aba por vez e com limite de linhas/colunas,
para que arquivos grandes não pesem no servidor nem no navegador.
"""
import csv
import io
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import HTTPException

LIMITE_LINHAS = 1000
LIMITE_COLUNAS = 60
LIMITE_MB = 25
EXT_EXCEL = {".xlsx", ".xlsm"}
EXT_CSV = {".csv"}


def suportada(nome: str) -> bool:
    return Path(nome).suffix.lower() in EXT_EXCEL | EXT_CSV


def _valor(v, formato: str | None = None):
    """Valor pronto para exibir: números ficam números (o navegador formata), o resto vira texto."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "VERDADEIRO" if v else "FALSO"
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y") if v.time() == time(0) else v.strftime("%d/%m/%Y %H:%M:%S").removesuffix(":00")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, time):
        return v.strftime("%H:%M:%S").removesuffix(":00") if v.second == 0 else v.strftime("%H:%M:%S")
    if isinstance(v, timedelta):
        s = int(v.total_seconds())
        return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"
    if isinstance(v, (int, float)):
        casas = _casas(formato)
        if formato and "%" in formato:
            return f"{v * 100:.{casas or 0}f}%".replace(".", ",")
        if isinstance(v, float):
            v = round(v, 6 if casas is None else casas)
            return int(v) if v.is_integer() and casas in (None, 0) else v
        return v
    return str(v)


def _casas(formato: str | None) -> int | None:
    """Casas decimais pedidas pelo formato da célula (ex.: '0.00' -> 2); None para 'Geral'."""
    if not formato or formato == "General":
        return None
    parte = formato.split(";")[0]
    if "." not in parte:
        return 0
    return len(re.match(r"[0#?]*", parte.split(".", 1)[1]).group())


def _aparar(linhas: list[list]) -> list[list]:
    """Remove linhas vazias do fim e colunas vazias da direita."""
    while linhas and all(c in (None, "") for c in linhas[-1]):
        linhas.pop()
    largura = max((i + 1 for ln in linhas for i, c in enumerate(ln) if c not in (None, "")), default=0)
    return [ln[:largura] + [None] * (largura - len(ln)) for ln in linhas]


def _excel(caminho: Path, aba: int) -> dict:
    import openpyxl  # importado só aqui: o restante do sistema não depende dele
    try:
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    except Exception:
        raise HTTPException(422, "Não foi possível ler esta planilha. Baixe o arquivo para abrir no Excel.")
    try:
        folhas = wb.worksheets
        if not folhas:
            raise HTTPException(422, "A planilha não tem abas com dados.")
        abas = [{"nome": ws.title, "oculta": ws.sheet_state != "visible"} for ws in folhas]
        if not 0 <= aba < len(folhas):
            aba = 0
        ws = folhas[aba]
        linhas, mais_linhas, mais_colunas = [], False, False
        for i, row in enumerate(ws.iter_rows()):
            if i >= LIMITE_LINHAS:
                mais_linhas = True
                break
            celulas = list(row)
            if len(celulas) > LIMITE_COLUNAS:
                mais_colunas = mais_colunas or any(getattr(c, "value", None) is not None for c in celulas[LIMITE_COLUNAS:])
                celulas = celulas[:LIMITE_COLUNAS]
            linhas.append([_valor(getattr(c, "value", None), getattr(c, "number_format", None)) for c in celulas])
        total = ws.max_row if isinstance(ws.max_row, int) else None
        return {"abas": abas, "aba": aba, "linhas": _aparar(linhas), "total_linhas": total,
                "mais_linhas": mais_linhas, "mais_colunas": mais_colunas}
    finally:
        wb.close()


def _csv(caminho: Path) -> dict:
    bruto = caminho.read_bytes()
    for cod in ("utf-8-sig", "cp1252"):
        try:
            texto = bruto.decode(cod)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialeto = csv.Sniffer().sniff(texto[:20000], delimiters=";,\t|")
    except csv.Error:
        dialeto = csv.excel
    linhas, mais_linhas, mais_colunas = [], False, False
    for i, row in enumerate(csv.reader(io.StringIO(texto), dialeto)):
        if i >= LIMITE_LINHAS:
            mais_linhas = True
            break
        if len(row) > LIMITE_COLUNAS:
            mais_colunas = True
            row = row[:LIMITE_COLUNAS]
        linhas.append(row)
    total = texto.count("\n") + (0 if texto.endswith("\n") else 1)
    return {"abas": [{"nome": caminho.stem[:31] or "CSV", "oculta": False}], "aba": 0, "linhas": _aparar(linhas),
            "total_linhas": total, "mais_linhas": mais_linhas, "mais_colunas": mais_colunas}


def ler(caminho: Path, nome: str, aba: int = 0) -> dict:
    if not suportada(nome):
        raise HTTPException(415, "Este tipo de arquivo não tem visualização. Baixe o arquivo.")
    if not caminho.is_file():
        raise HTTPException(404, "Arquivo não encontrado no servidor.")
    if caminho.stat().st_size > LIMITE_MB * 1024 * 1024:
        raise HTTPException(413, f"Planilha grande demais para visualizar (mais de {LIMITE_MB} MB). Baixe o arquivo.")
    if Path(nome).suffix.lower() in EXT_CSV:
        return _csv(caminho)
    return _excel(caminho, aba)
