# Análise — Capítulo 1: Projetos, quadro e tickets

Fonte: `specs/capitulo1.txt`, `specs/image1.jpg` (quadro do projeto "Automação"), `specs/image2.jpg` (ticket #1652 aberto).

---

## 1. Visão geral

Sistema interno para registrar e acompanhar **tickets** (problemas, implementações, estudos etc.) da empresa. Cada ticket documenta o problema e o procedimento com texto rico, imagens, vídeos, arquivos e trechos de código. Os tickets são organizados por **projeto** em um quadro **Kanban** de três colunas.

---

## 2. Decisões confirmadas

| # | Tema | Decisão |
|---|---|---|
| D1 | Numeração `#` | **Por projeto**: cada projeto tem sua própria sequência (#1, #2, …). |
| D2 | Labels | **Globais**, compartilhadas entre todos os projetos. |
| D3 | Categorias | **Editáveis** numa tela de administração (nome, ícone, cor). As 6 atuais vêm pré-cadastradas. |
| D4 | Migração | **Obrigatória**: todos os tickets do Ora vêm para o sistema novo, **via API do Ora**. Fica **para depois**, quando o sistema estiver minimamente funcional. |
| D5 | Banco de dados | **PostgreSQL** (justificativa na seção 5). |
| D6 | Fora do escopo | Plan, Deadline, Milestone, Estimativa, Tracked Time, ticket pai/filho. |

---

## 3. Recursos identificados

### 3.1 Projetos (image1)
- Lista de projetos. Cada projeto é uma "área", por exemplo **Automação**.
- Cabeçalho do projeto: nome, botão de informações (ⓘ), menu "…", **favoritar** (★) e **Filtro**.
- Quadro com **3 colunas fixas**:

  | Coluna | Cor | Exemplo de contagem |
  |---|---|---|
  | Pendências | vermelho | 132 |
  | Doing (Em andamento) | laranja | 40 |
  | Completadas | verde | 1401 |

- Cada coluna mostra o **contador** de tickets, o campo **"New ticket…"** no topo para criação rápida e um menu "…".
- Os cards são **arrastáveis** entre colunas e dentro da coluna (ordem manual).

### 3.2 Card do ticket no quadro (image1)
Cada card mostra:
- **Checkbox**. Marcado = completado, com o título **riscado**.
- **Título**.
- **Labels** coloridas.
- **Identificador** `#1188`.
- **Ícone da categoria**.
- **Quantidade de comentários**.
- Ícone **≡**, indicando que o ticket tem descrição.
- **Avatar do responsável**, ou um ícone de "sem responsável".

### 3.3 Ticket aberto (image2)
- Cabeçalho: `#1652`, ícone da categoria e coluna atual (dropdown para mover).
- **Título** grande, com checkbox.
- **Labels**.
- **Responsável**.
- **Descrição** em texto rico.
- **Linha do tempo de atividades**, com separador por data:
  - eventos automáticos ("criou o ticket", "moveu para Doing", "atribuiu a …");
  - comentários com autor, avatar, data e hora.
- Caixa de comentário com anexo e emoji.

### 3.4 Regras
- `#123` escrito num comentário ou na descrição vira **link** para o ticket 123 **do mesmo projeto**.
- **Labels ilimitadas**, globais, com **texto + cor**.
- **Categorias** editáveis (nome, ícone, cor, ordem, ativa/inativa). Valores iniciais:
  Problema, Implementação, Modificação, Estudo, Verificação, Documentação.
- **Um responsável** por ticket.
- **Datas obrigatórias**: criação do ticket e de cada comentário.
- **Editor rico** na descrição e nos comentários:
  - estilo Markdown: negrito, itálico, citação, listas, títulos, links;
  - **cor do texto** em trechos selecionados;
  - **blocos de código com destaque de sintaxe**;
  - **anexos**: fotos (exibidas inline), vídeos (com player), PDFs e outros arquivos.

### 3.5 Telas de administração
- **Categorias**: lista, criar/editar (nome, seletor de ícone, seletor de cor), reordenar, desativar.
  Uma categoria em uso não é apagada, só desativada, para não quebrar tickets antigos.
- **Labels**: lista, criar/editar (nome, cor), mesclar duplicadas e excluir.
- **Projetos**: criar, renomear, arquivar.
- **Usuários**: depende da decisão de login (seção 7).

### 3.6 Estilo visual (decisão: seguir o estilo das imagens do Ora)
- **Fundo** do quadro em degradê azul → verde-água; cabeçalho do projeto em texto branco sobre o degradê.
- **Colunas** com fundo claro, cantos arredondados e cabeçalho colorido sólido (Pendências **vermelho**, Doing **laranja/amarelo**, Completadas **verde**). O contador fica num "pill" branco ao lado do nome.
- **Cards** brancos com cantos arredondados, sombra suave e espaçamento compacto. O rodapé do card é cinza-claro, com o `#número`, os ícones e o avatar à direita.
- **Labels** em "pills" pequenos com a cor da label de fundo e texto branco. O texto fica escuro quando a cor é clara (ex.: amarelo "Lagoa Grande").
- **Avatares** redondos.
- **Ticket aberto** em painel/modal branco sobre o quadro, com barra de ações no topo, título grande, botões em "pill" cinza (Assign), linha do tempo e caixa de comentário fixa no rodapé.
- **Tipografia** sem serifa e limpa, no estilo Lato/Inter.
- Nome, logo e ícones próprios da empresa. O layout segue o estilo, mas não copia a marca do Ora.

---

## 4. Modelo de dados

```
usuarios          id, nome, email, avatar, ativo, criado_em, ora_id

projetos          id, nome, descricao, proximo_numero, arquivado, criado_em, ora_id
favoritos         usuario_id, projeto_id                         PK (usuario_id, projeto_id)

categorias        id, nome, icone, cor, ordem, ativa
labels            id, nome, cor                                  UNIQUE (nome)

tickets           id, projeto_id, numero, titulo, descricao (jsonb),
                  status [pendente | andamento | completado],
                  categoria_id, responsavel_id, criado_por,
                  ordem, criado_em, atualizado_em, concluido_em,
                  busca (tsvector), ora_id
                  UNIQUE (projeto_id, numero)

ticket_labels     ticket_id, label_id                            PK (ticket_id, label_id)

comentarios       id, ticket_id, autor_id, conteudo (jsonb),
                  criado_em, editado_em, busca (tsvector), ora_id

anexos            id, ticket_id, comentario_id (opcional), nome_original,
                  tipo_mime, tamanho, caminho, enviado_por, criado_em

atividades        id, ticket_id, usuario_id, tipo, dados (jsonb), criado_em
```

Notas:
- **Numeração por projeto**: ao criar um ticket, o sistema faz `UPDATE projetos SET proximo_numero = proximo_numero + 1 ... RETURNING` na mesma transação. Assim dois usuários criando ao mesmo tempo nunca recebem o mesmo número.
- **`ora_id`**: guarda o identificador original do Ora. Serve para rodar a migração mais de uma vez sem duplicar dados e para rastrear a origem de cada registro.
- **Anexos** ficam em disco, numa pasta do servidor organizada por projeto/ticket. O banco guarda só os metadados.
- **Rich text** é salvo como JSON estruturado do editor, mais o texto puro extraído para a busca.
- **Índices**: `(projeto_id, status, ordem)` para montar o quadro rápido e índices GIN nas colunas `busca`.

---

## 5. Banco de dados recomendado: PostgreSQL

| Critério | PostgreSQL | SQL Server Express | SQLite |
|---|---|---|---|
| Custo | Gratuito, sem limites | Gratuito, mas limitado a 10 GB e 1 CPU | Gratuito |
| Vários usuários ao mesmo tempo | Excelente | Excelente | Fraco: só uma escrita por vez |
| Busca em texto em **português** (acentos, plurais) | Nativa (`tsvector`, dicionário `portuguese`, `unaccent`) | Full-text existe, mas é mais limitado no Express | FTS5, mais básico |
| Rich text / dados flexíveis | `jsonb` indexável | JSON como texto | JSON como texto |
| Roda em Windows Server e Linux | Sim | Só Windows/Linux com licença | Arquivo local |
| Backup | `pg_dump` simples, agendável | Sim | Copiar arquivo |

**Por que PostgreSQL:**
1. **Busca** é essencial com milhares de tickets e comentários técnicos. O Postgres busca "disjuntor" e encontra "disjuntores", ignorando acentos, sem precisar de outro serviço.
2. **`jsonb`** guarda o conteúdo do editor rico e os dados das atividades de forma eficiente.
3. É gratuito, sem limite de tamanho, e roda num servidor Windows da empresa.
4. É robusto para vários usuários editando ao mesmo tempo.

Se o TI da empresa **já padroniza SQL Server** com licença, o modelo acima funciona nele também, com pequenos ajustes. Fora esse caso, a recomendação é PostgreSQL.

---

## 6. Plano de migração do Ora (fase posterior)

> **Adiado**: será feito quando o sistema estiver minimamente funcional. O modelo de dados já prevê os campos `ora_id` para isso.

Fonte: a **API do Ora**. Como alternativa, o export JSON em Project Settings ([help.ora.pm/article/58-export-project](https://help.ora.pm/article/58-export-project)).

Etapas:
1. **Reconhecimento da API**: documentação, autenticação (token) e uma chamada de teste num projeto pequeno.
2. **Importador** (script) que, para cada projeto:
   - cria usuários (casados por nome/e-mail), labels (sem duplicar entre projetos), categorias e o projeto;
   - importa tickets **mantendo o número original** (`#1652` continua `#1652`), status, ordem, datas, autor e responsável;
   - importa comentários com autor e **data original**;
   - **baixa os anexos** (se o JSON trouxer links) para a pasta do servidor;
   - converte o texto do Ora para o formato do editor novo;
   - ajusta `proximo_numero` do projeto para o maior número importado + 1.
3. **Ensaio**: rodar num banco de teste e conferir contagens (Automação: 132 / 40 / 1401) e alguns tickets por amostragem.
4. **Migração final**: congelar o Ora, exportar todos os projetos, importar e liberar o sistema novo.

---

## 7. Dúvidas em aberto

1. ~~Exportação de amostra~~: adiado junto com a migração (via API).
2. **Referência entre projetos**: `#123` aponta para o mesmo projeto. Precisa referenciar ticket de **outro** projeto? Se sim, proposta: `AUT#123`, com uma sigla por projeto.
3. **Categorias no Ora**: o Ora tem categorias nativas, ou isso é algum campo específico de vocês? Isso define como a migração as reconhece.
4. **Colunas**: são sempre as mesmas 3 em todos os projetos?
5. **Comentários**: pode **editar/excluir** depois de enviado?
6. ~~Filtro do quadro~~: definido no capítulo 2 ([analise-capitulo2.md](analise-capitulo2.md)).
7. **Infraestrutura**: existe um servidor interno (Windows ou Linux) onde o sistema e o PostgreSQL vão rodar?
8. ~~Login~~: sistema próprio com gestão de usuários (capítulo 2).
9. **Usuários**: quantas pessoas vão usar?
