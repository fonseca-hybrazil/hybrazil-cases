import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .config import get_settings
from .migrate import aplicar_migracoes
from .routers import auth, catalogos, dashboard, grupos, icones, projetos, tickets, usuarios
from .seed import semear

log = logging.getLogger("hyora")


def inicializar_banco() -> None:
    aplicadas = aplicar_migracoes()
    if aplicadas:
        log.warning("Migrações aplicadas: %s", ", ".join(aplicadas))
    sessao = db.new_session()
    try:
        senha = semear(sessao)
        sessao.commit()
    finally:
        sessao.close()
    if senha:
        log.warning("Usuário inicial criado: login 'admin' (senha definida em ADMIN_INITIAL_PASSWORD "
                    "no backend/.env, ou gerada e mostrada a seguir). Troca obrigatória no 1º acesso.")
        if not get_settings().admin_initial_password:
            log.warning("Senha gerada para o admin: %s", senha)


@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializar_banco()
    yield


def criar_app(com_lifespan: bool = True) -> FastAPI:
    app = FastAPI(title="HyBrazil Cases", lifespan=lifespan if com_lifespan else None)
    for r in (auth.router, usuarios.router, grupos.router, catalogos.router, projetos.router, tickets.router, icones.router,
              dashboard.router):
        app.include_router(r)

    @app.exception_handler(HTTPException)
    async def http_erro(_: Request, exc: HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)

    @app.get("/api/saude")
    def saude():
        return {"ok": True}

    # Interface web compilada (frontend/dist), com fallback para o roteamento do React
    dist = Path(get_settings().frontend_dist)
    if (dist / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{caminho:path}", include_in_schema=False)
        def spa(caminho: str):
            if caminho.startswith("api/"):
                raise HTTPException(404, "Rota não encontrada.")
            arquivo = (dist / caminho).resolve()
            if caminho and arquivo.is_file() and dist.resolve() in arquivo.parents:
                return FileResponse(arquivo)
            return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})

    return app


app = criar_app()
