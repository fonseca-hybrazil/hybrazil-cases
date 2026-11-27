"""Importa a exportação do Ora (runtime/ora-export/<apelido>/) para o HyBrazil Cases.

- Cada projeto do Ora vira um projeto daqui, com os mesmos números de ticket (#123).
- As labels são globais: labels de projetos diferentes com o mesmo nome viram uma só.
- Os tipos de tarefa do Ora viram as categorias (Problem -> Problema, Add -> Implementação...).
- As listas viram os status pelo nome: Pendências, Doing e Completadas.
- Comentários (Markdown) viram texto rico; anexos são copiados para a pasta de uploads.
- Tickets arquivados no Ora são importados como excluídos (ficam guardados, mas ocultos).
- Os membros viram usuários com senha bloqueada; o administrador libera o acesso em
  Usuários > Redefinir senha.
- Rodar de novo é seguro: o projeto já importado (mesmo ora_id) é apagado e importado outra vez.

Uso:  python ora/importar.py [--banco teste] automacao mikrotik resolucao
"""
import argparse
import json
import mimetypes
import secrets
import shutil
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select, text  # noqa: E402

from app import db as banco  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.migrate import aplicar_migracoes  # noqa: E402
from app.models import (  # noqa: E402
    Anexo, Atividade, Categoria, Comentario, Grupo, Label, Projeto, Ticket, Usuario,
)
from app.richtext import contar_tarefas, extrair_texto  # noqa: E402
from app.security import hash_senha  # noqa: E402
from app.seed import semear  # noqa: E402
from ora.markdown import para_doc  # noqa: E402

PASTA = Path(__file__).resolve().parents[2] / "runtime" / "ora-export"
CATEGORIA_POR_TIPO = {
    "problem": "Problema", "bug": "Problema", "fix": "Problema", "problema": "Problema",
    "add": "Implementação", "feature": "Implementação", "implementação": "Implementação",
    "modification": "Modificação", "chore": "Modificação", "modificação": "Modificação",
    "study": "Estudo", "estudo": "Estudo",
    "check": "Verificação", "test": "Verificação", "verificação": "Verificação",
    "docs": "Documentação", "documentação": "Documentação",
}
VIDEO_TOCAVEL = ("video/mp4", "video/webm", "video/ogg")


def nome_local(ref: str) -> str:
    """Nome do arquivo baixado: alguns anexos guardam no Ora a URL completa em vez do nome."""
    return ref.rstrip("/").rsplit("/", 1)[-1] if ref.startswith(("http://", "https://")) else ref


def data(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def status_da_lista(titulo: str, tipo: int | None) -> str:
    t = (titulo or "").lower()
    if "pend" in t or "todo" in t or "to do" in t or "backlog" in t:
        return "pendente"
    if "doing" in t or "andamento" in t or "progress" in t or "fazendo" in t:
        return "andamento"
    if "complet" in t or "conclu" in t or "done" in t or "feito" in t or "finaliz" in t:
        return "completado"
    return {2: "completado", 3: "andamento"}.get(tipo or 0, "pendente")


class Importador:
    def __init__(self, db, upload_dir: Path):
        self.db = db
        self.upload_dir = upload_dir
        self.usuarios: dict[int, int] = {}          # id Ora -> id daqui
        self.labels_por_nome: dict[str, Label] = {}
        self.categorias = {c.nome: c.id for c in db.scalars(select(Categoria))}
        self.grupo_usuarios = db.scalar(select(Grupo).where(Grupo.nome == "Usuários"))
        self.grupo_admin = db.scalar(select(Grupo).where(Grupo.nome == "Administradores"))
        for lab in db.scalars(select(Label)):
            self.labels_por_nome.setdefault(lab.nome.strip().lower(), lab)
        self.avisos: list[str] = []

    # ------------------------------------------------------------ usuários
    def usuario(self, ora_id: int | None, info: dict | None = None, ativo: bool = True, avatar: Path | None = None):
        if not ora_id:
            return None
        if ora_id in self.usuarios:
            return self.usuarios[ora_id]
        u = self.db.scalar(select(Usuario).where(Usuario.ora_id == str(ora_id)))
        info = info or {}
        email = (info.get("email") or "").strip() or None
        if u is None and email:
            u = self.db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))
        if u is None:
            login = (info.get("username") or f"ora{ora_id}").strip().lower()
            if self.db.scalar(select(Usuario.id).where(func.lower(Usuario.login) == login)):
                login = f"{login}-ora"
            u = Usuario(
                nome=(info.get("full_name") or info.get("username") or f"Usuário Ora {ora_id}").strip(),
                login=login, email=email, ativo=ativo, trocar_senha=True,
                senha_hash=hash_senha(secrets.token_urlsafe(32)),  # ninguém sabe: o admin redefine
            )
            u.grupos = [self.grupo_usuarios] if self.grupo_usuarios else []
            if email and email.lower().endswith("@hybrazil.com") and info.get("is_owner") and self.grupo_admin:
                u.grupos.append(self.grupo_admin)
            self.db.add(u)
        if not u.ora_id:
            u.ora_id = str(ora_id)
        if avatar and avatar.exists() and not u.avatar_caminho:
            cab = avatar.read_bytes()[:4]
            ext = ".png" if cab.startswith(b"\x89PNG") else ".webp" if cab.startswith(b"RIFF") else ".jpg"
            rel = f"avatares/{uuid.uuid4().hex}{ext}"
            (self.upload_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(avatar, self.upload_dir / rel)
            u.avatar_caminho = rel
        self.db.flush()
        self.usuarios[ora_id] = u.id
        return u.id

    # -------------------------------------------------------------- labels
    def label(self, titulo: str, cor: str, ora_id: int) -> Label:
        chave = titulo.strip().lower()
        lab = self.labels_por_nome.get(chave)
        if lab is not None and not lab.ora_id:  # label criada aqui (ex.: demonstração): adota a cor e o id do Ora
            if not self.db.scalar(select(Label.id).where(Label.ora_id == str(ora_id))):
                lab.cor, lab.ora_id = cor or lab.cor, str(ora_id)
        if lab is None:
            usado = self.db.scalar(select(Label.id).where(Label.ora_id == str(ora_id)))
            lab = Label(nome=titulo.strip(), cor=cor or "#9aa4b2", ora_id=None if usado else str(ora_id))
            self.db.add(lab)
            self.db.flush()
            self.labels_por_nome[chave] = lab
        return lab

    # -------------------------------------------------------------- anexos
    def anexo(self, ticket: Ticket, arquivo: Path, nome: str, mime: str | None, tamanho: int | None,
              autor: int | None, quando, ora_id: str) -> Anexo | None:
        if not arquivo.exists():
            self.avisos.append(f"#{ticket.numero}: arquivo não baixado: {nome}")
            return None
        mime = mime if mime and "/" in mime else (mimetypes.guess_type(nome)[0] or "application/octet-stream")
        ext = Path(nome).suffix.lower()[:12]
        if ext and not all(c.isalnum() or c == "." for c in ext):
            ext = ""
        rel = f"anexos/{ticket.projeto_id}/{ticket.id}/{uuid.uuid4().hex}{ext}"
        (self.upload_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(arquivo, self.upload_dir / rel)
        a = Anexo(ticket_id=ticket.id, nome_original=nome[:255], tipo_mime=mime,
                  tamanho=tamanho or arquivo.stat().st_size, caminho=rel, enviado_por=autor,
                  criado_em=quando, ora_id=ora_id)
        self.db.add(a)
        self.db.flush()
        return a

    @staticmethod
    def no_anexo(a: Anexo) -> dict:
        src = f"/api/anexos/{a.id}/arquivo"
        if a.tipo_mime.startswith("image/"):
            return {"type": "image", "attrs": {"src": src, "alt": a.nome_original, "anexoId": a.id}}
        if a.tipo_mime in VIDEO_TOCAVEL:
            return {"type": "video", "attrs": {"src": src, "anexoId": a.id, "nome": a.nome_original}}
        return {"type": "arquivo", "attrs": {"src": src, "anexoId": a.id, "nome": a.nome_original,
                                             "tamanho": a.tamanho, "mime": a.tipo_mime}}

    # ------------------------------------------------------------ projeto
    def remover_projeto_anterior(self, ora_pid: int) -> None:
        p = self.db.scalar(select(Projeto).where(Projeto.ora_id == str(ora_pid)))
        if p is None:
            return
        caminhos = self.db.scalars(select(Anexo.caminho).join(Ticket, Ticket.id == Anexo.ticket_id)
                                   .where(Ticket.projeto_id == p.id)).all()
        self.db.execute(delete(Projeto).where(Projeto.id == p.id))
        self.db.flush()
        for c in caminhos:
            (self.upload_dir / c).unlink(missing_ok=True)
        shutil.rmtree(self.upload_dir / "anexos" / str(p.id), ignore_errors=True)
        print(f"  projeto anterior (id {p.id}) removido para reimportar", flush=True)

    def importar(self, apelido: str) -> dict:
        base = PASTA / apelido
        arqs = base / "arquivos"
        bruto = json.loads((base / "projeto.json").read_text(encoding="utf-8"))
        d = bruto["data"]
        proj = d["project"]
        self.remover_projeto_anterior(proj["id"])

        # membros (com foto) e dono
        dono = proj.get("owner")
        for dev in d.get("developers") or []:
            info = {**dev, "is_owner": dev["dev_id"] == dono}
            self.usuario(dev["dev_id"], info, ativo=bool(dev.get("active", True)), avatar=arqs / f"avatar-{dev['dev_id']}")

        tickets_json = {}
        for arq in (base / "tickets").glob("*.json"):
            t = json.loads(arq.read_text(encoding="utf-8"))
            tickets_json[t["task_id"]] = t
            for m in t.get("mensagens") or []:  # autores que não são mais membros
                if isinstance(m.get("user"), dict) and m["user"].get("id"):
                    self.usuario(m["user"]["id"], m["user"])

        tarefas = [t for t in d["tasks"] if not t.get("deleted")]
        projeto = Projeto(
            nome=proj["title"].strip(), descricao=(proj.get("description") or "").strip(),
            proximo_numero=max([proj.get("tasks") or 0] + [t["second_id"] for t in d["tasks"]]) + 1,
            arquivado=bool(proj.get("archived")), criado_por=self.usuario(dono),
            criado_em=data(proj.get("created_at")) or datetime.now().astimezone(), ora_id=str(proj["id"]),
        )
        self.db.add(projeto)
        self.db.flush()

        listas = {lst["id"]: status_da_lista(lst["title"], lst.get("list_type")) for lst in d["lists"]}
        titulos_status = {lst["title"]: listas[lst["id"]] for lst in d["lists"]}
        tipos = {tt["id"]: self.categorias.get(CATEGORIA_POR_TIPO.get(tt["name"].strip().lower(), ""))
                 for tt in d.get("task_types") or []}
        labels_ora = {lab["id"]: self.label(lab["title"], lab.get("color"), lab["id"]) for lab in d.get("labels") or []}
        labels_do_ticket = defaultdict(list)
        for tl in d.get("tasks_labels") or []:
            if tl["label_id"] in labels_ora:
                labels_do_ticket[tl["task_id"]].append(labels_ora[tl["label_id"]])
        responsaveis = defaultdict(list)
        for td in sorted(d.get("tasks_developers") or [], key=lambda x: x.get("updated_at") or ""):
            responsaveis[td["task_id"]].append(td["dev_id"])

        # ordem dentro de cada coluna: pela posição do Ora (menor em cima)
        por_status = defaultdict(list)
        for t in tarefas:
            por_status[listas.get(t["list_id"], "pendente")].append(t)
        ordem = {}
        for st, lst in por_status.items():
            for i, t in enumerate(sorted(lst, key=lambda x: (x.get("position") or 0, -x["second_id"]))):
                ordem[t["id"]] = (i + 1) * 1024.0

        cont = Counter()
        agora_ = datetime.now().astimezone()
        for n, t in enumerate(sorted(tarefas, key=lambda x: x["second_id"]), 1):
            status = listas.get(t["list_id"], "pendente")
            resp = [r for r in responsaveis.get(t["id"], []) if r]
            exp = tickets_json.get(t["id"]) or {}
            detalhe = exp.get("detalhe") if isinstance(exp.get("detalhe"), dict) else {}

            # descrição: Markdown + checklists + outros responsáveis
            doc = para_doc(t.get("description")) or {"type": "doc", "content": []}
            checklists = [c for c in detalhe.get("checklists") or [] if not c.get("deleted")]
            grupos = sorted([c for c in checklists if not c.get("main_id")], key=lambda c: c.get("position") or 0)
            for g in grupos or [None]:
                itens = sorted([c for c in checklists if (c.get("main_id") == (g or {}).get("id")) and c.get("main_id")]
                               if g else [c for c in checklists if c.get("main_id") and c["main_id"] not in {x["id"] for x in grupos}],
                               key=lambda c: c.get("position") or 0)
                if not itens:
                    continue
                if g and g.get("title"):
                    doc["content"].append({"type": "paragraph", "content": [
                        {"type": "text", "text": g["title"], "marks": [{"type": "bold"}]}]})
                doc["content"].append({"type": "taskList", "content": [
                    {"type": "taskItem", "attrs": {"checked": bool(c.get("checked"))},
                     "content": [{"type": "paragraph", "content": [{"type": "text", "text": c.get("title") or "—"}]}]}
                    for c in itens]})
            if len(resp) > 1:
                outros = ", ".join(self.db.get(Usuario, self.usuario(r)).nome for r in resp[1:])
                doc["content"].append({"type": "paragraph", "content": [
                    {"type": "text", "text": f"Outros responsáveis no Ora: {outros}", "marks": [{"type": "italic"}]}]})
            doc = doc if doc["content"] else None

            ticket = Ticket(
                projeto_id=projeto.id, numero=t["second_id"], titulo=(t.get("title") or "(sem título)").strip()[:500],
                descricao=doc, descricao_texto=extrair_texto(doc) if doc else "", status=status,
                categoria_id=tipos.get(t.get("task_type")), responsavel_id=self.usuario(resp[0]) if resp else None,
                criado_por=self.usuario(t.get("creator")), ordem=ordem[t["id"]],
                criado_em=data(t.get("created_at")) or agora_,
                atualizado_em=data(t.get("updated_at")) or data(t.get("created_at")) or agora_,
                concluido_em=(data(t.get("complete_at")) or data(t.get("updated_at"))) if status == "completado" else None,
                excluido_em=data(t.get("updated_at")) if t.get("archived") else None, ora_id=str(t["id"]),
            )
            ticket.labels = list({lab.id: lab for lab in labels_do_ticket.get(t["id"], [])}.values())
            self.db.add(ticket)
            self.db.flush()
            cont["tickets"] += 1
            cont["arquivados"] += bool(t.get("archived"))

            # anexos do próprio ticket -> um comentário de quem enviou, na data do envio
            for f in sorted([f for f in detalhe.get("files") or [] if not f.get("deleted")],
                            key=lambda f: f.get("upload_date") or ""):
                autor = self.usuario(f.get("user_id"))
                quando = data(f.get("upload_date")) or ticket.criado_em
                if f.get("data_path"):
                    a = self.anexo(ticket, arqs / nome_local(f["data_path"]), f.get("file_title") or nome_local(f["data_path"]), f.get("file_type"),
                                   int(f["file_size"]) if str(f.get("file_size") or "").isdigit() else None,
                                   autor, quando, f"arq-{f['id']}")
                    nos = [self.no_anexo(a)] if a else []
                elif f.get("external_url"):
                    nos = [{"type": "paragraph", "content": [{"type": "text", "text": f.get("file_title") or f["external_url"],
                                                              "marks": [{"type": "link", "attrs": {"href": f["external_url"]}}]}]}]
                else:
                    nos = []
                if nos:
                    c = Comentario(ticket_id=ticket.id, autor_id=autor, conteudo={"type": "doc", "content": nos},
                                   texto=f.get("file_title") or "", criado_em=quando, ora_id=f"arq-{f['id']}")
                    self.db.add(c)
                    self.db.flush()
                    if nos[0]["type"] != "paragraph":
                        self.db.execute(text("UPDATE anexos SET comentario_id=:c WHERE id=:a"),
                                        {"c": c.id, "a": nos[0]["attrs"]["anexoId"]})
                    cont["comentarios"] += 1
                    cont["anexos"] += nos[0]["type"] != "paragraph"

            # comentários e histórico
            for m in sorted(exp.get("mensagens") or [], key=lambda m: m.get("created_at") or ""):
                autor = self.usuario(m.get("user_id"), m.get("user") if isinstance(m.get("user"), dict) else None)
                quando = data(m.get("created_at")) or ticket.criado_em
                eh_comentario = bool(m.get("discussion_thread")) or isinstance(m.get("text"), str) or bool(m.get("attachments"))
                if eh_comentario:
                    if m.get("deleted"):
                        continue
                    # monta o documento completo (texto + anexos) ANTES de gravar: o JSONB não percebe
                    # alterações feitas depois no mesmo objeto
                    cdoc = para_doc(m.get("text")) or {"type": "doc", "content": []}
                    anexos_msg = []
                    for at in m.get("attachments") or []:
                        a = self.anexo(ticket, arqs / nome_local(at["url"]), at.get("file_title") or nome_local(at["url"]),
                                       at.get("file_type"), at.get("file_size"), autor, quando, f"msg-{at['id']}")
                        if a:
                            anexos_msg.append(a)
                            cdoc["content"].append(self.no_anexo(a))
                    if not cdoc["content"]:
                        continue
                    c = Comentario(ticket_id=ticket.id, autor_id=autor, conteudo=cdoc, texto=extrair_texto(cdoc),
                                   criado_em=quando, editado_em=data(m.get("edited_at")), ora_id=str(m["id"]))
                    self.db.add(c)
                    self.db.flush()
                    for a in anexos_msg:
                        a.comentario_id = c.id
                    cont["comentarios"] += 1
                    cont["anexos"] += len(anexos_msg)
                    continue
                tipo, dados = None, {}
                tp = m.get("type")
                if tp == 1:
                    tipo = "criou"
                elif tp == 9 and m.get("new_title"):
                    tipo, dados = "titulo", {"de": m.get("old_title"), "para": m.get("new_title")}
                elif tp == 10:
                    tipo = "descricao"
                elif tp == 11:
                    de = titulos_status.get(m.get("category_old_title"), status_da_lista(m.get("category_old_title"), None))
                    para = titulos_status.get(m.get("category_new_title"), status_da_lista(m.get("category_new_title"), None))
                    if de != para:
                        tipo, dados = "moveu", {"de": de, "para": para}
                elif tp == 12:
                    tipo = "categoria"
                    dados = {"de": tipos.get(int(m["old_type"])) if str(m.get("old_type") or "").isdigit() else None,
                             "para": tipos.get(int(m["new_type"])) if str(m.get("new_type") or "").isdigit() else None}
                elif tp in (13, 14) and m.get("other_user_id"):  # 13 atribuiu alguém; 14 "joined this card"
                    tipo, dados = "responsavel", {"para": self.usuario(m["other_user_id"])}
                elif tp in (33, 34) and m.get("first_id") in labels_ora:
                    tipo, dados = ("label_add" if tp == 33 else "label_rem"), {"label_id": labels_ora[m["first_id"]].id}
                if tipo:
                    self.db.add(Atividade(ticket_id=ticket.id, usuario_id=autor, tipo=tipo, dados=dados, criado_em=quando))
                    cont["atividades"] += 1
            if not any(m.get("type") == 1 and not m.get("discussion_thread") and not isinstance(m.get("text"), str)
                       for m in exp.get("mensagens") or []):
                self.db.add(Atividade(ticket_id=ticket.id, usuario_id=ticket.criado_por, tipo="criou", dados={},
                                      criado_em=ticket.criado_em))
            self.db.flush()

            # progresso das listas de tarefas
            feitas, total = contar_tarefas(ticket.descricao)
            for (conteudo,) in self.db.execute(select(Comentario.conteudo).where(Comentario.ticket_id == ticket.id)):
                f2, t2 = contar_tarefas(conteudo)
                feitas, total = feitas + f2, total + t2
            ticket.tarefas_feitas, ticket.tarefas_total = feitas, total
            if n % 100 == 0:
                print(f"  {n}/{len(tarefas)} tickets", flush=True)
        self.db.flush()
        cont["labels_no_projeto"] = len(labels_ora)
        return {"projeto_id": projeto.id, "nome": projeto.nome, **cont}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--banco", choices=["sistema", "teste"], default="sistema")
    ap.add_argument("apelidos", nargs="*", default=["automacao", "mikrotik", "resolucao"])
    a = ap.parse_args()
    cfg = get_settings()
    upload_dir = Path(cfg.upload_dir)
    if a.banco == "teste":
        banco.configure(cfg.test_database_url)
        aplicar_migracoes()
        upload_dir = PASTA / "_uploads-teste"
        shutil.rmtree(upload_dir, ignore_errors=True)
        with banco.new_session() as s:  # banco de teste limpo, só com os dados padrão
            tabelas = s.execute(text("SELECT string_agg(quote_ident(tablename), ', ') FROM pg_tables "
                                     "WHERE schemaname='public' AND tablename <> 'schema_migrations'")).scalar()
            s.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
            semear(s)
            s.commit()
    else:
        banco.configure(cfg.database_url)
        aplicar_migracoes()
    upload_dir.mkdir(parents=True, exist_ok=True)
    with banco.new_session() as s:
        imp = Importador(s, upload_dir)
        resultados = []
        for apelido in a.apelidos:
            print(f"Importando {apelido}...", flush=True)
            resultados.append(imp.importar(apelido))
        s.commit()
    for r in resultados:
        print("OK", json.dumps(r, ensure_ascii=False))
    print(f"labels globais: {len(imp.labels_por_nome)}; usuários do Ora: {len(imp.usuarios)}")
    if imp.avisos:
        print(f"{len(imp.avisos)} avisos (primeiros):", *imp.avisos[:15], sep="\n  ")


if __name__ == "__main__":
    main()
