from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str
    test_database_url: str = ""
    upload_dir: Path = ROOT_DIR / "runtime" / "uploads"
    frontend_dist: Path = ROOT_DIR / "frontend" / "dist"

    # Senha inicial do usuário "admin" criado no primeiro start (troca obrigatória no 1º acesso)
    admin_initial_password: str = ""

    sessao_horas: int = 12            # sessão normal
    sessao_lembrar_dias: int = 30     # "manter conectado"
    max_tentativas_login: int = 5
    bloqueio_minutos: int = 5
    max_upload_mb: int = 1024
    cookie_secure: bool = False       # True quando servido por HTTPS


@lru_cache
def get_settings() -> Settings:
    return Settings()
