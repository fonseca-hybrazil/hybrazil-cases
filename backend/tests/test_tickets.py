from .conftest import doc


def novo(c, projeto, titulo, **extra):
    r = c.post(f"/api/projetos/{projeto}/tickets", json={"titulo": titulo, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def quadro(c, projeto, **params):
    r = c.get(f"/api/projetos/{projeto}/quadro", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_projeto_somente_admin_cria(ana, admin):
    assert ana.post("/api/projetos", json={"nome": "X"}).status_code == 403
    assert admin.post("/api/projetos", json={"nome": "X"}).status_code == 201


def test_numeracao_por_projeto(admin, projeto):
    outro = admin.post("/api/projetos", json={"nome": "Elétrica"}).json()["id"]
    assert novo(admin, projeto, "a")["numero"] == 1
    assert novo(admin, projeto, "b")["numero"] == 2
    assert novo(admin, outro, "c")["numero"] == 1
    r = admin.get(f"/api/projetos/{projeto}/tickets/numero/2")
    assert r.status_code == 200 and r.json()["titulo"] == "b"
    assert admin.get(f"/api/projetos/{outro}/tickets/numero/2").status_code == 404


def test_novo_ticket_vai_para_o_topo_e_mover(admin, projeto):
    t1 = novo(admin, projeto, "primeiro")
    t2 = novo(admin, projeto, "segundo")
    t3 = novo(admin, projeto, "terceiro")
    col = quadro(admin, projeto)["pendente"]
    assert [t["titulo"] for t in col["tickets"]] == ["terceiro", "segundo", "primeiro"]

    # mover "terceiro" para depois de "primeiro" (fim)
    r = admin.post(f"/api/tickets/{t3['id']}/mover", json={"status": "pendente", "apos_id": t1["id"]})
    assert r.status_code == 200
    col = quadro(admin, projeto)["pendente"]
    assert [t["titulo"] for t in col["tickets"]] == ["segundo", "primeiro", "terceiro"]

    # mover "segundo" para Doing e depois completar
    admin.post(f"/api/tickets/{t2['id']}/mover", json={"status": "andamento"})
    r = admin.post(f"/api/tickets/{t2['id']}/mover", json={"status": "completado"})
    assert r.json()["concluido_em"] is not None
    q = quadro(admin, projeto)
    assert q["completado"]["total"] == 1 and q["pendente"]["total"] == 2
    tl = admin.get(f"/api/tickets/{t2['id']}/timeline").json()
    movimentos = [i["dados"] for i in tl if i["atividade"] == "moveu"]
    assert movimentos == [{"de": "pendente", "para": "andamento"}, {"de": "andamento", "para": "completado"}]


def test_mover_muitas_vezes_no_mesmo_lugar_renumera(admin, projeto):
    a = novo(admin, projeto, "a")
    b = novo(admin, projeto, "b")
    # ordem atual: b, a. Insere repetidamente logo após "b" para esgotar a precisão
    for i in range(70):
        t = novo(admin, projeto, f"x{i}")
        r = admin.post(f"/api/tickets/{t['id']}/mover", json={"status": "pendente", "apos_id": b["id"]})
        assert r.status_code == 200, r.text
    titulos = [t["titulo"] for t in quadro(admin, projeto, limite=500)["pendente"]["tickets"]]
    assert titulos[0] == "b" and titulos[1] == "x69" and titulos[-1] == "a"


def test_editar_ticket_registra_atividades(admin, ana, projeto):
    t = novo(admin, projeto, "Falha disjuntor")
    cats = admin.get("/api/categorias").json()
    lab = admin.post("/api/labels", json={"nome": "PLC", "cor": "#22aadd"}).json()
    ana_id = ana.get("/api/auth/me").json()["id"]
    r = admin.patch(f"/api/tickets/{t['id']}", json={
        "titulo": "Falha no disjuntor 52L1", "categoria_id": cats[0]["id"], "responsavel_id": ana_id,
        "label_ids": [lab["id"]], "descricao": doc("Abrir o painel")})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["responsavel"]["login"] == "ana" and d["label_ids"] == [lab["id"]] and d["tem_descricao"]
    tipos = [i["atividade"] for i in admin.get(f"/api/tickets/{t['id']}/timeline").json()]
    assert tipos == ["criou", "titulo", "descricao", "categoria", "responsavel", "label_add"]
    # limpar responsável com null
    r = admin.patch(f"/api/tickets/{t['id']}", json={"responsavel_id": None})
    assert r.json()["responsavel"] is None


def test_filtros(admin, ana, projeto):
    plc = admin.post("/api/labels", json={"nome": "PLC", "cor": "#22aadd"}).json()["id"]
    e3 = admin.post("/api/labels", json={"nome": "Elipse E3", "cor": "#1188ee"}).json()["id"]
    cats = {c["nome"]: c["id"] for c in admin.get("/api/categorias").json()}
    ana_id = ana.get("/api/auth/me").json()["id"]

    t1 = novo(admin, projeto, "Falha fechamento disjuntor 52L1", label_ids=[plc],
              categoria_id=cats["Problema"])
    t2 = novo(admin, projeto, "Implementação da lógica do GMG", label_ids=[plc, e3],
              categoria_id=cats["Implementação"], responsavel_id=ana_id)
    t3 = novo(admin, projeto, "Trocar sensor ultrassônico", descricao=doc("Sonda nova no medidor Kron"))
    admin.post(f"/api/tickets/{t3['id']}/comentarios", json={"conteudo": doc("Verificar telegramas Modbus")})

    def ids(**p):
        q = quadro(admin, projeto, **p)
        return sorted(t["numero"] for col in ("pendente", "andamento", "completado") for t in q[col]["tickets"])

    assert ids(label=plc) == [1, 2]
    assert ids(label=[plc, e3]) == [1, 2]
    assert ids(label=[plc, e3], labels_modo="todas") == [2]
    assert ids(categoria=cats["Problema"]) == [1]
    assert ids(categoria=0) == [3]
    assert ids(responsavel=ana_id) == [2]
    assert ids(responsavel=0) == [1, 3]
    assert ids(numero=2) == [2]
    # texto: título, sem acento, plural, trecho de código, descrição e comentários
    assert ids(q="disjuntores") == [1]
    assert ids(q="logica") == [2]
    assert ids(q="52L") == [1]
    assert ids(q="kron") == [3]
    assert ids(q="modbus") == [3]
    assert ids(q="100%") == []
    # combinação
    assert ids(label=plc, q="gmg") == [2]
    q = quadro(admin, projeto, label=plc)
    assert q["pendente"]["total"] == 2 and q["total_sem_filtro"]["pendente"] == 3


def test_comentario_excluido_nao_aparece_na_busca(ana, projeto, admin):
    t = novo(ana, projeto, "Ticket")
    c = ana.post(f"/api/tickets/{t['id']}/comentarios", json={"conteudo": doc("palavrasecreta")}).json()
    assert quadro(ana, projeto, q="palavrasecreta")["pendente"]["total"] == 1
    assert ana.delete(f"/api/comentarios/{c['id']}").status_code == 204
    assert quadro(ana, projeto, q="palavrasecreta")["pendente"]["total"] == 0


def test_permissoes_de_comentario(admin, ana, bruno, projeto):
    t = novo(ana, projeto, "Ticket da Ana")
    c = ana.post(f"/api/tickets/{t['id']}/comentarios", json={"conteudo": doc("oi")}).json()
    assert c["pode_editar"] and c["pode_excluir"]
    assert ana.post(f"/api/tickets/{t['id']}/comentarios",
                    json={"conteudo": {"type": "doc", "content": [{"type": "paragraph"}]}}).status_code == 422
    # Bruno (grupo Usuários) não edita nem exclui comentário alheio
    assert bruno.patch(f"/api/comentarios/{c['id']}", json={"conteudo": doc("x")}).status_code == 403
    assert bruno.delete(f"/api/comentarios/{c['id']}").status_code == 403
    tl = bruno.get(f"/api/tickets/{t['id']}/timeline").json()
    com = [i for i in tl if i["tipo"] == "comentario"][0]
    assert not com["pode_editar"] and not com["pode_excluir"]
    # autora edita
    r = ana.patch(f"/api/comentarios/{c['id']}", json={"conteudo": doc("olá editado")})
    assert r.status_code == 200 and r.json()["editado_em"]
    # admin exclui qualquer um
    assert admin.delete(f"/api/comentarios/{c['id']}").status_code == 204


def test_permissoes_de_exclusao_de_ticket(admin, ana, bruno, projeto):
    t = novo(ana, projeto, "da Ana")
    assert bruno.get(f"/api/tickets/{t['id']}").json()["pode_excluir"] is False
    assert bruno.delete(f"/api/tickets/{t['id']}").status_code == 403
    assert ana.delete(f"/api/tickets/{t['id']}").status_code == 204
    assert ana.get(f"/api/tickets/{t['id']}").status_code == 404
    t2 = novo(bruno, projeto, "do Bruno")
    assert admin.delete(f"/api/tickets/{t2['id']}").status_code == 204
    # número não é reaproveitado
    assert novo(admin, projeto, "novo")["numero"] == 3


def test_anexos(ana, projeto):
    t = novo(ana, projeto, "Com anexo")
    r = ana.post(f"/api/tickets/{t['id']}/anexos", files={"arquivo": ("foto.png", b"\x89PNG fake", "image/png")})
    assert r.status_code == 201, r.text
    a = r.json()
    r = ana.get(a["url"])
    assert r.status_code == 200 and r.content == b"\x89PNG fake"
    assert r.headers["content-type"] == "image/png" and r.headers["content-disposition"].startswith("inline")
    # HTML nunca é exibido inline (evita script malicioso)
    h = ana.post(f"/api/tickets/{t['id']}/anexos",
                 files={"arquivo": ("x.html", b"<script>alert(1)</script>", "text/html")}).json()
    r = ana.get(h["url"])
    assert r.headers["content-disposition"].startswith("attachment")
    assert r.headers["content-type"] == "application/octet-stream"
    # comentário com imagem anexada
    conteudo = {"type": "doc", "content": [{"type": "image", "attrs": {"src": a["url"], "anexoId": a["id"]}}]}
    assert ana.post(f"/api/tickets/{t['id']}/comentarios", json={"conteudo": conteudo}).status_code == 201
    # anexo de outro ticket não pode ser referenciado
    t2 = novo(ana, projeto, "Outro")
    assert ana.post(f"/api/tickets/{t2['id']}/comentarios", json={"conteudo": conteudo}).status_code == 422


def test_labels_globais_mesclar_e_categoria_em_uso(admin, ana, projeto):
    outro = admin.post("/api/projetos", json={"nome": "Outro"}).json()["id"]
    a = ana.post("/api/labels", json={"nome": "Lagoa Grande", "cor": "#ffcc00"}).json()
    assert ana.post("/api/labels", json={"nome": "lagoa grande", "cor": "#ffcc00"}).status_code == 409
    b = ana.post("/api/labels", json={"nome": "Lagoa Gde", "cor": "#ffcc00"}).json()
    novo(ana, projeto, "t1", label_ids=[a["id"]])
    novo(ana, outro, "t2", label_ids=[b["id"]])
    novo(ana, outro, "t3", label_ids=[a["id"], b["id"]])
    assert ana.post(f"/api/labels/{b['id']}/mesclar", json={"destino_id": a["id"]}).status_code == 403
    assert admin.post(f"/api/labels/{b['id']}/mesclar", json={"destino_id": a["id"]}).status_code == 204
    uso = {l["nome"]: l["uso"] for l in admin.get("/api/labels-uso").json()}
    assert uso == {"Lagoa Grande": 3}
    por_projeto = {l["nome"]: l["uso"] for l in admin.get("/api/labels-uso", params={"projeto_id": outro}).json()}
    assert por_projeto == {"Lagoa Grande": 2}

    cat = admin.get("/api/categorias").json()[0]
    novo(admin, projeto, "com categoria", categoria_id=cat["id"])
    assert admin.delete(f"/api/categorias/{cat['id']}").status_code == 409
    assert admin.patch(f"/api/categorias/{cat['id']}", json={"ativa": False}).json()["ativa"] is False
    # categoria inativa não pode ser atribuída a novos tickets
    r = admin.post(f"/api/projetos/{projeto}/tickets", json={"titulo": "x", "categoria_id": cat["id"]})
    assert r.status_code == 422


def test_conteudo_perigoso_e_removido(ana, projeto):
    t = novo(ana, projeto, "XSS")
    conteudo = {"type": "doc", "content": [
        {"type": "paragraph", "content": [
            {"type": "text", "text": "clique", "marks": [{"type": "link", "attrs": {"href": "javascript:alert(1)"}}]},
            {"type": "text", "text": " ok", "marks": [{"type": "link", "attrs": {"href": "https://exemplo.com"}}]},
            {"type": "text", "text": " cor", "marks": [{"type": "textStyle", "attrs": {"color": "red;background:url(x)"}}]},
        ]},
        {"type": "image", "attrs": {"src": "javascript:alert(1)"}},
    ]}
    c = ana.post(f"/api/tickets/{t['id']}/comentarios", json={"conteudo": conteudo}).json()
    p = c["conteudo"]["content"]
    assert len(p) == 1  # imagem removida
    marks = [n.get("marks") for n in p[0]["content"]]
    assert marks[0] == []
    assert marks[1][0]["attrs"]["href"] == "https://exemplo.com"
    assert marks[2][0]["attrs"]["color"] is None
    r = ana.patch(f"/api/tickets/{t['id']}", json={"descricao": conteudo}).json()
    assert r["descricao"]["content"][0]["content"][0]["marks"] == []


def test_favoritos_e_contagens(admin, projeto):
    novo(admin, projeto, "a")
    assert admin.put(f"/api/projetos/{projeto}/favorito").status_code == 204
    p = admin.get("/api/projetos").json()[0]
    assert p["favorito"] is True and p["contagem"]["pendente"] == 1


def test_video_permite_avancar_com_range(ana, projeto):
    """O player do navegador pede pedaços do vídeo (Range); sem 206 não dá para avançar/voltar."""
    t = novo(ana, projeto, "Com vídeo")
    conteudo = bytes(range(256)) * 40
    v = ana.post(f"/api/tickets/{t['id']}/anexos", files={"arquivo": ("teste.mp4", conteudo, "video/mp4")}).json()
    r = ana.get(v["url"], headers={"Range": "bytes=100-199"})
    assert r.status_code == 206
    assert r.content == conteudo[100:200]
    assert r.headers["content-type"] == "video/mp4"
    assert r.headers["content-range"] == f"bytes 100-199/{len(conteudo)}"


def test_visualizar_planilha(ana, projeto):
    import io
    from datetime import datetime
    import openpyxl
    t = novo(ana, projeto, "Com planilha")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Geração"
    ws.append(["Dia", "UG1", "Fator"])
    ws.append([datetime(2024, 8, 1), 886, 0.123456789])
    ws["C2"].number_format = "0.00%"
    ws["D2"] = 2.5
    ws["D2"].number_format = "0.00"
    wb.create_sheet("Resumo")["B3"] = "ok"
    buf = io.BytesIO()
    wb.save(buf)
    x = ana.post(f"/api/tickets/{t['id']}/anexos", files={"arquivo": (
        "dados.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}).json()
    r = ana.get(f"/api/anexos/{x['id']}/planilha")
    assert r.status_code == 200, r.text
    d = r.json()
    assert [a["nome"] for a in d["abas"]] == ["Geração", "Resumo"]
    assert d["linhas"] == [["Dia", "UG1", "Fator", None], ["01/08/2024", 886, "12,35%", 2.5]]
    d = ana.get(f"/api/anexos/{x['id']}/planilha?aba=1").json()
    assert d["aba"] == 1 and d["linhas"] == [[None, None], [None, None], [None, "ok"]]
    # CSV com ponto e vírgula e acentos em Windows-1252
    c = ana.post(f"/api/tickets/{t['id']}/anexos", files={"arquivo": (
        "medidas.csv", "Tag;Valor\nNível;1,5\n".encode("cp1252"), "text/csv")}).json()
    assert ana.get(f"/api/anexos/{c['id']}/planilha").json()["linhas"] == [["Tag", "Valor"], ["Nível", "1,5"]]
    # arquivo que não é planilha, ou xlsx corrompido
    p = ana.post(f"/api/tickets/{t['id']}/anexos", files={"arquivo": ("a.pdf", b"%PDF", "application/pdf")}).json()
    assert ana.get(f"/api/anexos/{p['id']}/planilha").status_code == 415
    z = ana.post(f"/api/tickets/{t['id']}/anexos", files={"arquivo": ("ruim.xlsx", b"nao e zip", "application/octet-stream")}).json()
    assert ana.get(f"/api/anexos/{z['id']}/planilha").status_code == 422


def _lista_tarefas(*itens: tuple[str, bool]) -> dict:
    return {"type": "taskList", "content": [
        {"type": "taskItem", "attrs": {"checked": feito},
         "content": [{"type": "paragraph", "content": [{"type": "text", "text": txt}]}]}
        for txt, feito in itens
    ]}


def test_lista_de_tarefas(ana, bruno, projeto):
    desc = {"type": "doc", "content": [_lista_tarefas(("Desligar disjuntor", True), ("Medir isolação", False))]}
    t = ana.post(f"/api/projetos/{projeto}/tickets", json={"titulo": "Procedimento", "descricao": desc}).json()
    assert (t["tarefas_feitas"], t["tarefas_total"]) == (1, 2)

    # comentário com mais 3 tarefas, uma delas com valor inválido em "checked" (vira False)
    lista = _lista_tarefas(("Passo A", False), ("Passo B", False), ("Passo C", True))
    lista["content"][0]["attrs"]["checked"] = "sim"
    c = ana.post(f"/api/tickets/{t['id']}/comentarios", json={"conteudo": {"type": "doc", "content": [lista]}}).json()
    assert ana.get(f"/api/tickets/{t['id']}").json()["tarefas_total"] == 5
    assert ana.get(f"/api/tickets/{t['id']}").json()["tarefas_feitas"] == 2

    # Bruno não é autor do comentário, mas pode marcar a tarefa (sem marcar o comentário como editado)
    r = bruno.post(f"/api/comentarios/{c['id']}/tarefas", json={"indice": 1, "feito": True})
    assert r.status_code == 200, r.text
    assert r.json()["editado_em"] is None
    assert r.json()["conteudo"]["content"][0]["content"][1]["attrs"]["checked"] is True
    # marcar a da descrição
    d = bruno.post(f"/api/tickets/{t['id']}/tarefas", json={"indice": 1, "feito": True}).json()
    assert (d["tarefas_feitas"], d["tarefas_total"]) == (4, 5)
    # posição inexistente
    assert bruno.post(f"/api/tickets/{t['id']}/tarefas", json={"indice": 9, "feito": True}).status_code == 404
    # fica registrado quem marcou e qual tarefa
    ativ = [i for i in ana.get(f"/api/tickets/{t['id']}/timeline").json() if i.get("atividade") == "tarefa"]
    assert [(a["usuario"]["login"], a["dados"]["texto"], a["dados"]["feito"]) for a in ativ] == [
        ("bruno", "Passo B", True), ("bruno", "Medir isolação", True)]
    # excluir o comentário tira as tarefas dele da conta
    assert ana.delete(f"/api/comentarios/{c['id']}").status_code == 204
    assert ana.get(f"/api/tickets/{t['id']}").json()["tarefas_total"] == 2
