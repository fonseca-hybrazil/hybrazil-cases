from fastapi.testclient import TestClient

from .conftest import SENHA, criar_usuario, logar


def test_login_invalido_e_rotas_protegidas(app):
    c = TestClient(app)
    assert c.get("/api/projetos").status_code == 401
    criar_usuario("ana", ["Usuários"])
    assert c.post("/api/auth/login", json={"login": "ana", "senha": "errada"}).status_code == 401
    assert c.post("/api/auth/login", json={"login": "ninguem", "senha": SENHA}).status_code == 401


def test_login_ok_ignora_maiusculas_e_logout(app):
    criar_usuario("ana", ["Usuários"])
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"login": "ANA", "senha": SENHA})
    assert r.status_code == 200
    eu = r.json()
    assert eu["login"] == "ana"
    assert "comentario_excluir_proprio" in eu["permissoes"]
    assert "admin_usuarios" not in eu["permissoes"]
    assert c.get("/api/projetos").status_code == 200
    assert c.post("/api/auth/logout").status_code == 204
    assert c.get("/api/projetos").status_code == 401


def test_bloqueio_apos_varias_tentativas(app):
    criar_usuario("ana", ["Usuários"])
    c = TestClient(app)
    for _ in range(5):
        assert c.post("/api/auth/login", json={"login": "ana", "senha": "x"}).status_code == 401
    r = c.post("/api/auth/login", json={"login": "ana", "senha": SENHA})
    assert r.status_code == 429


def test_troca_de_senha_obrigatoria(app):
    criar_usuario("novo", ["Usuários"], trocar_senha=True)
    c = logar(app, "novo")
    assert c.get("/api/auth/me").json()["trocar_senha"] is True
    assert c.get("/api/projetos").status_code == 403
    r = c.post("/api/auth/trocar-senha", json={"senha_atual": SENHA, "nova_senha": "curta"})
    assert r.status_code == 422
    r = c.post("/api/auth/trocar-senha", json={"senha_atual": SENHA, "nova_senha": "uma-senha-nova"})
    assert r.status_code == 200
    assert c.get("/api/projetos").status_code == 200


def test_admin_cria_usuario_e_redefine_senha(app, admin, ana):
    r = admin.post("/api/admin/usuarios", json={
        "nome": "Carla", "login": "carla", "senha": "senha-inicial-1", "grupo_ids": [2]})
    assert r.status_code == 201, r.text
    uid = r.json()["id"]
    assert r.json()["trocar_senha"] is True
    assert admin.post("/api/admin/usuarios", json={
        "nome": "X", "login": "CARLA", "senha": "senha-inicial-1"}).status_code == 409
    # usuário comum não administra
    assert ana.get("/api/admin/usuarios").status_code == 403
    # desativar derruba o acesso
    assert admin.patch(f"/api/admin/usuarios/{uid}", json={"ativo": False}).status_code == 200
    c = TestClient(app)
    assert c.post("/api/auth/login", json={"login": "carla", "senha": "senha-inicial-1"}).status_code == 401


def test_admin_nao_remove_propria_permissao(admin):
    eu = admin.get("/api/auth/me").json()
    r = admin.patch(f"/api/admin/usuarios/{eu['id']}", json={"grupo_ids": [2]})
    assert r.status_code == 422
    r = admin.patch(f"/api/admin/usuarios/{eu['id']}", json={"ativo": False})
    assert r.status_code == 422


def test_grupos_personalizados(admin, app):
    perms = admin.get("/api/admin/permissoes").json()
    assert {p["chave"] for p in perms} >= {"ticket_excluir", "comentario_excluir"}
    r = admin.post("/api/admin/grupos", json={"nome": "Moderadores", "permissoes": ["comentario_excluir"]})
    assert r.status_code == 201
    gid = r.json()["id"]
    assert admin.post("/api/admin/grupos", json={"nome": "moderadores"}).status_code == 409
    assert admin.post("/api/admin/grupos", json={"nome": "Y", "permissoes": ["voar"]}).status_code == 422
    uid = criar_usuario("mod", ["Usuários"])
    assert admin.patch(f"/api/admin/grupos/{gid}", json={"usuario_ids": [uid]}).status_code == 200
    mod = logar(app, "mod")
    assert "comentario_excluir" in mod.get("/api/auth/me").json()["permissoes"]
    # grupos do sistema não podem ser excluídos
    assert admin.delete("/api/admin/grupos/1").status_code == 422
    assert admin.delete(f"/api/admin/grupos/{gid}").status_code == 204
