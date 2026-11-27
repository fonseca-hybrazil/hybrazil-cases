"""Backup do banco do sistema (pg_dump, formato custom) em runtime/backups/, sem mostrar a senha.

Uso:  python ora/backup.py [nome]
Restaurar: pg_restore -h localhost -p <porta> -U hyora -d hyora --clean <arquivo>
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import get_settings  # noqa: E402

PG_DUMP = [Path(r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"),
           Path(__file__).resolve().parents[2] / "runtime" / "pgsql" / "bin" / "pg_dump.exe"]

u = urlparse(get_settings().database_url.replace("postgresql+psycopg", "postgresql"))
destino = Path(__file__).resolve().parents[2] / "runtime" / "backups"
destino.mkdir(parents=True, exist_ok=True)
arq = destino / f"{(sys.argv[1] if len(sys.argv) > 1 else 'hyora')}-{datetime.now():%Y%m%d-%H%M%S}.dump"
exe = next(p for p in PG_DUMP if p.exists())
subprocess.run([str(exe), "-h", u.hostname, "-p", str(u.port), "-U", u.username, "-Fc", "-f", str(arq), u.path.lstrip("/")],
               check=True, env={**os.environ, "PGPASSWORD": u.password or ""})
print(f"backup: {arq} ({arq.stat().st_size // 1024} KB)")
