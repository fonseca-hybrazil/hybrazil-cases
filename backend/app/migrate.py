"""Aplica os arquivos migrations/NNN_*.sql ainda não aplicados, em ordem."""
from pathlib import Path

from sqlalchemy import text

from . import db

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def aplicar_migracoes() -> list[str]:
    aplicadas: list[str] = []
    with db.engine().begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " nome text PRIMARY KEY, aplicada_em timestamptz NOT NULL DEFAULT now())"
        ))
        feitas = {r[0] for r in conn.execute(text("SELECT nome FROM schema_migrations"))}
        for arquivo in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if arquivo.name in feitas:
                continue
            conn.exec_driver_sql(arquivo.read_text(encoding="utf-8"))
            conn.execute(text("INSERT INTO schema_migrations (nome) VALUES (:n)"), {"n": arquivo.name})
            aplicadas.append(arquivo.name)
    return aplicadas
