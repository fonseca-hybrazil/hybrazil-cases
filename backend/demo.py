"""Cria um usuário de teste e um projeto de demonstração (rodar uma vez, opcional).

Uso: .venv\\Scripts\\python.exe demo.py
A senha do usuário "teste" fica em DEV_TEST_PASSWORD no backend/.env.
"""
import secrets
from pathlib import Path

from sqlalchemy import select

from app import db
from app.main import inicializar_banco
from app.models import Categoria, Comentario, Grupo, Label, Projeto, Ticket, Usuario, Atividade
from app.richtext import extrair_texto
from app.security import hash_senha

ENV = Path(__file__).parent / ".env"


def senha_teste() -> str:
    linhas = ENV.read_text(encoding="utf-8").splitlines()
    for l in linhas:
        if l.startswith("DEV_TEST_PASSWORD="):
            return l.split("=", 1)[1]
    s = secrets.token_urlsafe(10)
    ENV.write_text("\n".join(linhas) + f"\n# Usuario 'teste' criado por demo.py\nDEV_TEST_PASSWORD={s}\n", encoding="utf-8")
    return s


def p(texto, marks=None):
    n = {"type": "text", "text": texto}
    if marks:
        n["marks"] = marks
    return n


def main():
    inicializar_banco()
    s = db.new_session()
    if s.scalar(select(Projeto).where(Projeto.nome == "Automação (demonstração)")):
        print("Demonstração já existe.")
        return
    admins = s.scalar(select(Grupo).where(Grupo.nome == "Administradores"))
    usuarios_g = s.scalar(select(Grupo).where(Grupo.nome == "Usuários"))
    teste = s.scalar(select(Usuario).where(Usuario.login == "teste"))
    if teste is None:
        teste = Usuario(nome="Usuário de Teste", login="teste", senha_hash=hash_senha(senha_teste()))
        teste.grupos = [admins]
        s.add(teste)
    marina = Usuario(nome="Marina Costa", login="marina", senha_hash=hash_senha(secrets.token_urlsafe(16)),
                     trocar_senha=True)
    marina.grupos = [usuarios_g]
    s.add(marina)
    s.flush()

    cores = {"PLC": "#05a2c2", "IHM": "#0091ff", "Elipse E3": "#3e63dd", "Lagoa Grande": "#f5d90a",
             "UFV Guanambi": "#f76b15", "Solar": "#e5484d", "Pardo": "#8e4ec6", "Medidor Kron": "#e93d82"}
    labels = {}
    for nome, cor in cores.items():
        l = s.scalar(select(Label).where(Label.nome == nome)) or Label(nome=nome, cor=cor)
        s.add(l)
        labels[nome] = l
    cats = {c.nome: c for c in s.scalars(select(Categoria))}
    proj = Projeto(nome="Automação (demonstração)", descricao="Projeto de exemplo criado automaticamente.",
                   criado_por=teste.id)
    s.add(proj)
    s.flush()

    dados = [
        ("pendente", "Válvula elétrica UHLM sem resposta", ["PLC", "IHM", "Elipse E3"], "Problema", None),
        ("pendente", "Modificar os telegramas Modbus devido à substituição do multimedidor para o modelo Kron",
         ["PLC", "Medidor Kron"], "Modificação", teste),
        ("pendente", "Falha no fechamento do disjuntor 52L1", ["Lagoa Grande"], "Problema", marina),
        ("pendente", "Estudar proteção de sobrecorrente de excitação (LEOC) na UG1", [], "Estudo", None),
        ("andamento", "Implementação da lógica de acionamento do GMG de Pardo", ["Elipse E3", "PLC", "Pardo"],
         "Implementação", teste),
        ("andamento", "Procedimento de cadastro de novo alarme / trip e onde eles são analisados", ["Lagoa Grande"],
         "Documentação", teste),
        ("andamento", "Trocar sensor ultrassônico por sonda na usina de Pardo", ["PLC", "Pardo"], "Modificação", marina),
        ("completado", "Configurar IP no multimedidor Kron em Guanambi", ["Medidor Kron", "Solar", "UFV Guanambi"],
         "Verificação", teste),
        ("completado", "Inserir Guanambi no sistema supervisório", ["UFV Guanambi", "Solar", "Elipse E3"],
         "Implementação", marina),
    ]
    for i, (status, titulo, labs, cat, resp) in enumerate(dados):
        t = Ticket(projeto_id=proj.id, numero=i + 1, titulo=titulo, status=status, categoria_id=cats[cat].id,
                   responsavel_id=resp.id if resp else None, criado_por=teste.id, ordem=i * 1024.0)
        t.labels = [labels[l] for l in labs]
        s.add(t)
        s.flush()
        s.add(Atividade(ticket_id=t.id, usuario_id=teste.id, tipo="criou", dados={}))
        if i == 5:
            t.descricao = {"type": "doc", "content": [
                {"type": "paragraph", "content": [p("Registrar onde os eventos de "), p("trip", [{"type": "bold"}]),
                                                  p(" são gravados e como analisá-los. Relacionado ao "), p("#3"), p(".")]}]}
            t.descricao_texto = extrair_texto(t.descricao)
            conteudo = {"type": "doc", "content": [
                {"type": "paragraph", "content": [
                    p("Primeiramente, os arrays de Ocorrências são gravados em "),
                    p("Gera FB → Ocorrências", [{"type": "code"}]), p(".")]},
                {"type": "paragraph", "content": [
                    p("Atenção: ", [{"type": "bold"}, {"type": "textStyle", "attrs": {"color": "#e5484d"}}]),
                    p("o tipo de parada é definido na declaração da variável em globals.")]},
                {"type": "codeBlock", "attrs": {"language": "python"}, "content": [p(
                    "def tipo_parada(evento):\n    # 86M, 86E ou 86H\n    return evento.ctrl and evento.tipoparada")]},
            ]}
            s.add(Comentario(ticket_id=t.id, autor_id=teste.id, conteudo=conteudo, texto=extrair_texto(conteudo)))
    proj.proximo_numero = len(dados) + 1
    s.commit()
    print("Demonstração criada. Usuário: teste (senha em DEV_TEST_PASSWORD no backend/.env)")


if __name__ == "__main__":
    main()
