from ora.markdown import para_doc


def tipos(doc):
    return [b["type"] for b in doc["content"]]


def test_vazio():
    assert para_doc("") is None and para_doc("   \n ") is None and para_doc(None) is None


def test_paragrafos_e_quebras():
    d = para_doc("linha 1\nlinha 2\n\nsegundo parágrafo")
    assert tipos(d) == ["paragraph", "paragraph"]
    assert [n["type"] for n in d["content"][0]["content"]] == ["text", "hardBreak", "text"]


def test_codigo_com_linguagem():
    d = para_doc("Veja:\n```SQL\nSELECT 1;\nGO\n```\nfim")
    assert tipos(d) == ["paragraph", "codeBlock", "paragraph"]
    bloco = d["content"][1]
    assert bloco["attrs"]["language"] == "sql" and bloco["content"][0]["text"] == "SELECT 1;\nGO"
    assert para_doc("```\nx\n```")["content"][0]["attrs"]["language"] is None
    assert para_doc("```st\nIF x THEN\n```")["content"][0]["attrs"]["language"] == "st"


def test_marcacoes_inline():
    d = para_doc("comando **igoal/metername/command** e `52L1`, *nota*, ~~velho~~ "
                 "[doc](https://ex.com) https://ora.pm/x.")
    nos = d["content"][0]["content"]
    marcas = {n["text"]: [m["type"] for m in n.get("marks", [])] for n in nos}
    assert marcas["igoal/metername/command"] == ["bold"]
    assert marcas["52L1"] == ["code"]
    assert marcas["nota"] == ["italic"] and marcas["velho"] == ["strike"]
    assert marcas["doc"] == ["link"] and marcas["https://ora.pm/x"] == ["link"]
    assert nos[-1]["text"] == "."  # pontuação final fora do link


def test_listas_e_tarefas():
    d = para_doc("- um\n- dois\n\n1. a\n2. b\n\n- [x] feito\n- [ ] falta\n\n> citação\n\n## Título\n---")
    assert tipos(d) == ["bulletList", "orderedList", "taskList", "blockquote", "heading", "horizontalRule"]
    assert [i["attrs"]["checked"] for i in d["content"][2]["content"]] == [True, False]


def test_identificadores_com_sublinhado_nao_viram_italico():
    nos = para_doc("variável var_tag_1 e x*y*z")["content"][0]["content"]
    assert len(nos) == 1 and "marks" not in nos[0]
