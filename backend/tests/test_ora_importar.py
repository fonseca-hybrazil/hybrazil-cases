import json

from sqlalchemy import select

from app import db as banco
from app.models import Anexo, Atividade, Comentario, Label, Projeto, Ticket, Usuario
from ora import importar as imp


def _projeto(pid, titulo, labels, tarefas, extras=None):
    return {"data": {
        "project": {"id": pid, "title": titulo, "description": "", "owner": 1, "tasks": 10,
                    "created_at": "2024-01-01T10:00:00Z", "archived": False},
        "lists": [{"id": pid * 10 + 1, "title": "Pendências", "list_type": 1},
                  {"id": pid * 10 + 2, "title": "Doing", "list_type": 1},
                  {"id": pid * 10 + 3, "title": "Completadas", "list_type": 2}],
        "task_types": [{"id": 7, "name": "Problem"}, {"id": 8, "name": "epic"}],
        "labels": labels, "tasks": tarefas,
        "developers": [{"dev_id": 1, "full_name": "Felipe F", "username": "felipe", "email": "felipe@hybrazil.com",
                        "active": True}, {"dev_id": 2, "full_name": "Ana", "username": "ana.ora", "active": False}],
        **(extras or {}),
    }}


def _tarefa(tid, num, lista, **k):
    return {"id": tid, "second_id": num, "title": f"T{num}", "description": k.get("desc"), "list_id": lista,
            "task_type": k.get("tipo", 7), "creator": 1, "position": k.get("pos", 0), "archived": k.get("arq", False),
            "deleted": False, "created_at": "2024-02-01T10:00:00Z", "updated_at": "2024-02-02T10:00:00Z",
            "complete_at": "2024-02-03T10:00:00Z"}


def test_importacao(tmp_path, monkeypatch):
    pasta = tmp_path / "export"
    monkeypatch.setattr(imp, "PASTA", pasta)
    # projeto A: 3 tickets; label "PLC" também existe no projeto B (com outro id e cor)
    a = _projeto(100, "Automação", [{"id": 501, "title": "PLC", "color": "#111111"}, {"id": 502, "title": "E3", "color": "#222"}], [
        _tarefa(1, 5, 1001, desc="Passos:\n```st\nIF x THEN\n```", pos=2),
        _tarefa(2, 7, 1001, pos=1),
        _tarefa(3, 9, 1003, arq=True, tipo=8),
    ], {"tasks_labels": [{"task_id": 1, "label_id": 501}, {"task_id": 2, "label_id": 502}],
        "tasks_developers": [{"task_id": 1, "dev_id": 1, "updated_at": "a"}, {"task_id": 1, "dev_id": 2, "updated_at": "b"}]})
    b = _projeto(200, "Mikrotik", [{"id": 601, "title": "plc ", "color": "#333"}], [_tarefa(4, 1, 2002)],
                 {"tasks_labels": [{"task_id": 4, "label_id": 601}]})
    for apelido, proj, tickets in [("a", a, {
        1: {"task_id": 1, "second_id": 5, "detalhe": {
            "discussionThread": {"id": 9}, "files": [],
            "checklists": [{"id": 70, "title": "Usinas", "position": 1},
                           {"id": 71, "main_id": 70, "title": "Muriaé", "checked": True, "position": 1},
                           {"id": 72, "main_id": 70, "title": "Pardo", "checked": False, "position": 2}]},
            "mensagens": [
                {"id": 900, "type": 1, "user_id": 1, "created_at": "2024-02-01T10:00:00Z"},
                {"id": 901, "type": 11, "user_id": 1, "created_at": "2024-02-01T11:00:00Z",
                 "category_old_title": "Pendências", "category_new_title": "Doing"},
                {"id": 902, "type": 1, "discussion_thread": 9, "user_id": 2, "text": "Veja **isso** #7",
                 "created_at": "2024-02-01T12:00:00Z", "edited_at": "2024-02-01T12:05:00Z",
                 "attachments": [{"id": 77, "url": "foto.png", "file_title": "foto.png", "file_type": "image/png",
                                  "file_size": 4}]},
                {"id": 903, "type": 1, "discussion_thread": 9, "user_id": 1, "text": "apagado", "deleted": True,
                 "created_at": "2024-02-01T13:00:00Z"},
            ]}}), ("b", b, {})]:
        base = pasta / apelido
        (base / "tickets").mkdir(parents=True)
        (base / "arquivos").mkdir()
        (base / "projeto.json").write_text(json.dumps(proj), encoding="utf-8")
        for tid, t in tickets.items():
            (base / "tickets" / f"{tid}.json").write_text(json.dumps(t), encoding="utf-8")
    (pasta / "a" / "arquivos" / "foto.png").write_bytes(b"\x89PNG")

    with banco.new_session() as s:
        i = imp.Importador(s, tmp_path / "uploads")
        ra = i.importar("a")
        rb = i.importar("b")
        s.commit()
    assert ra["tickets"] == 3 and ra["arquivados"] == 1 and ra["comentarios"] == 1 and ra["anexos"] == 1
    assert rb["tickets"] == 1

    with banco.new_session() as s:
        pa = s.scalar(select(Projeto).where(Projeto.ora_id == "100"))
        assert pa.proximo_numero == 11
        ts = {t.numero: t for t in s.scalars(select(Ticket).where(Ticket.projeto_id == pa.id))}
        assert ts[5].status == "pendente" and ts[9].status == "completado" and ts[9].excluido_em is not None
        assert ts[9].categoria_id is None  # "epic" não tem categoria
        assert ts[7].ordem < ts[5].ordem  # posição do Ora
        # descrição: código ST + checklist virou lista de tarefas + outro responsável citado
        tipos = [b["type"] for b in ts[5].descricao["content"]]
        assert "codeBlock" in tipos and "taskList" in tipos
        assert (ts[5].tarefas_feitas, ts[5].tarefas_total) == (1, 2)
        assert "Outros responsáveis no Ora: Ana" in ts[5].descricao_texto
        # labels globais: "PLC" e "plc " são a mesma
        plc = s.scalars(select(Label).where(Label.nome.ilike("plc"))).all()
        assert len(plc) == 1
        tb = s.scalar(select(Ticket).where(Ticket.ora_id == "4"))
        assert [lab.id for lab in tb.labels] == [plc[0].id] and [lab.id for lab in ts[5].labels] == [plc[0].id]
        # comentário: Markdown + imagem anexada; o apagado não vem
        cs = s.scalars(select(Comentario).where(Comentario.ticket_id == ts[5].id)).all()
        assert len(cs) == 1 and cs[0].editado_em is not None and "isso" in cs[0].texto
        assert cs[0].conteudo["content"][-1]["type"] == "image"
        an = s.scalar(select(Anexo).where(Anexo.comentario_id == cs[0].id))
        assert (tmp_path / "uploads" / an.caminho).read_bytes() == b"\x89PNG"
        # histórico
        tipos_at = sorted(a.tipo for a in s.scalars(select(Atividade).where(Atividade.ticket_id == ts[5].id)))
        assert tipos_at == ["criou", "moveu"]
        # usuários: senha bloqueada; inativo no Ora continua inativo; dono @hybrazil.com é admin
        felipe = s.scalar(select(Usuario).where(Usuario.ora_id == "1"))
        ana = s.scalar(select(Usuario).where(Usuario.ora_id == "2"))
        assert felipe.trocar_senha and "Administradores" in {g.nome for g in felipe.grupos}
        assert not ana.ativo

    # reimportar não duplica
    with banco.new_session() as s:
        imp.Importador(s, tmp_path / "uploads").importar("a")
        s.commit()
    with banco.new_session() as s:
        assert len(s.scalars(select(Projeto).where(Projeto.ora_id == "100")).all()) == 1
        assert len(s.scalars(select(Ticket).where(Ticket.ora_id == "1")).all()) == 1
