PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40
SVG_OK = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="#1e88e5"/></svg>'


def test_icone_padrao_no_projeto(admin, projeto):
    r = admin.patch(f"/api/projetos/{projeto}", json={"icone": "lucide:zap", "icone_cor": "#f59e0b"})
    assert r.status_code == 200, r.text
    assert (r.json()["icone"], r.json()["icone_cor"]) == ("lucide:zap", "#f59e0b")
    # formatos inválidos são recusados
    assert admin.patch(f"/api/projetos/{projeto}", json={"icone": "<script>"}).status_code == 422
    assert admin.patch(f"/api/projetos/{projeto}", json={"icone_cor": "red"}).status_code == 422
    # "" remove
    r = admin.patch(f"/api/projetos/{projeto}", json={"icone": ""})
    assert r.json()["icone"] is None


def test_biblioteca_de_icones(admin, ana, projeto):
    # só quem administra projetos envia
    assert ana.post("/api/icones", files={"arquivo": ("a.png", PNG, "image/png")}).status_code == 403
    r = admin.post("/api/icones", files={"arquivo": ("Usina Solar.png", PNG, "application/octet-stream")})
    assert r.status_code == 201, r.text
    png = r.json()
    assert png["nome"] == "Usina Solar" and png["tipo_mime"] == "image/png"
    svg = admin.post("/api/icones", files={"arquivo": ("logo.svg", SVG_OK, "image/svg+xml")}).json()

    # qualquer usuário logado vê a lista e a imagem; SVG vai com CSP que impede scripts
    assert [i["nome"] for i in ana.get("/api/icones").json()] == ["logo", "Usina Solar"]
    r = ana.get(svg["url"])
    assert r.status_code == 200 and r.content == SVG_OK
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert "sandbox" in r.headers["content-security-policy"]

    # usar no projeto; ícone inexistente é recusado
    assert admin.patch(f"/api/projetos/{projeto}", json={"icone": f"lib:{png['id']}"}).status_code == 200
    assert admin.patch(f"/api/projetos/{projeto}", json={"icone": "lib:999999"}).status_code == 422
    assert [i["em_uso"] for i in admin.get("/api/icones").json()] == [0, 1]

    # excluir da biblioteca: o projeto volta ao ícone padrão
    assert ana.delete(f"/api/icones/{png['id']}").status_code == 403
    assert admin.delete(f"/api/icones/{png['id']}").status_code == 204
    assert admin.get(f"/api/projetos/{projeto}").json()["icone"] is None
    assert admin.get(png["url"]).status_code == 404


def test_icone_recusa_arquivos_perigosos_ou_invalidos(admin):
    def enviar(nome, dados):
        return admin.post("/api/icones", files={"arquivo": (nome, dados, "image/svg+xml")}).status_code

    assert enviar("x.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>') == 422
    assert enviar("x.svg", b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>') == 422
    assert enviar("x.svg", b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:x="http://www.w3.org/1999/xlink">'
                           b'<image x:href="https://exemplo.com/a.png"/></svg>') == 422
    assert enviar("x.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject/></svg>') == 422
    bomba = (b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;">]>'
             b'<svg xmlns="http://www.w3.org/2000/svg"><text>&b;</text></svg>')
    assert enviar("x.svg", bomba) == 422
    assert enviar("x.png", b"isto nao e imagem") == 415
    assert enviar("grande.png", PNG + b"\x00" * 600 * 1024) == 413
