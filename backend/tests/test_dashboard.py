from sqlalchemy import update

from app import db
from app.models import Ticket

from .test_tickets import novo


def dash(c, **params):
    r = c.get("/api/dashboard", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_dashboard_contagens_e_filtros(admin, ana, projeto):
    ana_id = next(u["id"] for u in admin.get("/api/usuarios").json() if u["login"] == "ana")
    cats = {c["nome"]: c["id"] for c in admin.get("/api/categorias").json()}
    plc = admin.post("/api/labels", json={"nome": "PLC", "cor": "#22aadd"}).json()["id"]
    e3 = admin.post("/api/labels", json={"nome": "Elipse E3", "cor": "#1188ee"}).json()["id"]

    t1 = novo(admin, projeto, "A", categoria_id=cats["Problema"], responsavel_id=ana_id, label_ids=[plc, e3])
    novo(admin, projeto, "B", categoria_id=cats["Problema"], label_ids=[plc])
    t3 = novo(admin, projeto, "C")
    admin.post(f"/api/tickets/{t1['id']}/mover", json={"status": "completado", "apos_id": None})

    # datas fixas para conferir o mês a mês (horário de Brasília)
    with db.engine().begin() as conn:
        conn.execute(update(Ticket).where(Ticket.id == t1["id"]).values(
            criado_em="2026-01-10 12:00-03", concluido_em="2026-03-02 12:00-03"))
        conn.execute(update(Ticket).where(Ticket.id == t3["id"]).values(criado_em="2026-02-28 23:30-03"))

    d = dash(admin)
    assert d["totais"] == {"total": 3, "abertos": 2, "completados": 1, "dias_medio": 51.0, "dias_mediana": 51.0}
    meses = {m["mes"]: (m["criados"], m["concluidos"]) for m in d["por_mes"]}
    assert meses["2026-01"] == (1, 0) and meses["2026-02"] == (1, 0) and meses["2026-03"] == (0, 1)
    assert {c["nome"]: c["total"] for c in d["por_categoria"]} == {"Problema": 2, "Sem categoria": 1}
    assert [(l["nome"], l["total"]) for l in d["por_label"]["itens"]] == [("PLC", 2), ("Elipse E3", 1)]
    assert d["por_label"]["sem_label"] == 1
    resp = {r["nome"]: (r["id"], r["total"]) for r in d["por_responsavel"]}
    assert resp == {"Sem responsável": (None, 2), "Ana": (ana_id, 1)}

    # filtros
    assert dash(admin, responsavel_id=0)["totais"]["total"] == 2
    assert dash(admin, categoria_id=0)["totais"]["total"] == 1
    assert dash(admin, label_id=e3)["totais"]["total"] == 1
    assert dash(admin, status="abertos")["totais"]["total"] == 2
    assert dash(admin, status="completado")["totais"]["completados"] == 1
    # período pela data de criação (23:30 de 28/02 em Brasília ainda é fevereiro)
    fev = dash(admin, de="2026-02-01", ate="2026-02-28")
    assert fev["totais"]["total"] == 1 and [m["mes"] for m in fev["por_mes"]] == ["2026-02"]
    # concluídos contam pelo mês de conclusão
    marco = dash(admin, de="2026-03-01", ate="2026-03-31")
    assert marco["totais"]["total"] == 0 and marco["por_mes"] == [{"mes": "2026-03", "criados": 0, "concluidos": 1}]

    # qualquer usuário logado vê; datas invertidas dão erro
    assert ana.get("/api/dashboard").status_code == 200
    assert admin.get("/api/dashboard", params={"de": "2026-03-01", "ate": "2026-01-01"}).status_code == 422


def test_dashboard_exige_login(app):
    from fastapi.testclient import TestClient
    assert TestClient(app).get("/api/dashboard").status_code == 401
