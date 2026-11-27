import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app import db
from app.config import get_settings
from app.main import criar_app
from app.migrate import aplicar_migracoes
from app.models import Grupo, Usuario
from app.security import hash_senha
from app.seed import semear

SENHA = "senha-de-teste-123"
TABELAS = ("atividades, anexos, comentarios, ticket_labels, tickets, labels, categorias, favoritos, projetos, icones, "
           "sessoes, grupo_usuarios, grupos, usuarios")


@pytest.fixture(scope="session", autouse=True)
def banco_de_teste():
    url = get_settings().test_database_url
    assert url, "TEST_DATABASE_URL não configurada no backend/.env"
    db.configure(url)
    aplicar_migracoes()
    yield


@pytest.fixture(autouse=True)
def limpar(tmp_path):
    with db.engine().begin() as conn:
        conn.execute(text(f"TRUNCATE {TABELAS} RESTART IDENTITY CASCADE"))
    s = db.new_session()
    semear(s)
    s.commit()
    s.close()
    get_settings().upload_dir = tmp_path / "uploads"
    yield


@pytest.fixture
def app():
    return criar_app(com_lifespan=False)


def criar_usuario(login: str, grupos: list[str], nome: str | None = None, trocar_senha: bool = False) -> int:
    s = db.new_session()
    u = Usuario(nome=nome or login.title(), login=login, senha_hash=hash_senha(SENHA), trocar_senha=trocar_senha)
    u.grupos = list(s.scalars(select(Grupo).where(Grupo.nome.in_(grupos))))
    s.add(u)
    s.commit()
    uid = u.id
    s.close()
    return uid


def logar(app, login: str) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"login": login, "senha": SENHA})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture
def admin(app) -> TestClient:
    criar_usuario("chefe", ["Administradores"], nome="Chefe")
    return logar(app, "chefe")


@pytest.fixture
def ana(app) -> TestClient:
    criar_usuario("ana", ["Usuários"], nome="Ana")
    return logar(app, "ana")


@pytest.fixture
def bruno(app) -> TestClient:
    criar_usuario("bruno", ["Usuários"], nome="Bruno")
    return logar(app, "bruno")


@pytest.fixture
def projeto(admin) -> int:
    r = admin.post("/api/projetos", json={"nome": "Automação"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def doc(texto: str) -> dict:
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": texto}]}]}
