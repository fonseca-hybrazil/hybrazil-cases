# API do Ora: documentação e plano de migração

## O que está nesta pasta

| Arquivo | Conteúdo |
|---|---|
| [`swagger.json`](swagger.json) | Especificação **completa** da API pública do Ora (Swagger 2.0, "Ora API 1.0"): 68 endereços, 110 operações e 58 modelos de dados |
| [`referencia.md`](referencia.md) | A mesma especificação em formato legível: cada operação com parâmetros e respostas, e cada modelo com os campos (descrições originais em inglês) |

**Origem:** o `swagger.json` publicado em `https://api.ora.pm/swagger.json`. O servidor `api.ora.pm` não responde (em 27/11/2026 o DNS resolvia para 45.33.42.135, mas as conexões expiravam; `app.ora.pm` funcionava normalmente). A cópia veio do Internet Archive, capturada em **04/02/2026**:
https://web.archive.org/web/20260204233546/https://api.ora.pm/swagger.json

A página de introdução oficial é https://ora.pm/docs/getting-started-with-ora-public-api, e há um exemplo de login OAuth em Python em https://github.com/codemotionapps/flask-api-example.

## Como acessar a API

1. No Ora, vá em **<sua organização> › Preferences › Applications › Create an app**. Anote o `client_id` e o `client_secret`.
2. **Login OAuth2 (authorization code):**
   - Abra `https://app.ora.pm/authorize?response_type=code&client_id=…&redirect_uri=…&state=…`
   - O usuário autoriza, e o Ora redireciona para o `redirect_uri` com `code` e `state`.
   - Faça um `POST https://api.ora.pm/oauth/token` com o JSON `{client_id, client_secret, code, redirect_uri, grant_type: "authorization_code"}`. A resposta traz `access_token` e `refresh_token`.
3. Envie `Authorization: Bearer <access_token>` em todas as chamadas. Quando o token expirar, peça outro com `grant_type: "refresh_token"`.

## Equivalência Ora → HyBrazil Cases

| Ora | Endereço da API | HyBrazil Cases |
|---|---|---|
| Organization | `GET /organizations` | (não existe; tudo é de uma organização só) |
| Project | `GET /projects` ou `GET /organizations/{id}/projects` | `projetos` (`title`, `description`, `archived`) |
| Project.`tasks` (contador) | — | `projetos.proximo_numero` |
| List (coluna) | `GET /projects/{id}/lists` | Coluna, pelo `list_type`: 1 Open → **Pendências**; 3 Review → **Doing** (a confirmar); 2 Closed → **Completadas**; 4 Frozen → a decidir |
| Task | `GET /projects/{id}/tasks` (paginado) ou `…/lists/{list_id}/tasks` | `tickets` |
| Task.`second_id` | — | `tickets.numero` (o `#123` que aparece no Ora) |
| Task.`title` / `description` | — | `titulo` / `descricao` |
| Task.`task_type` + Task Type (`name`, `icon`, `color`) | `GET /projects/{id}/tasks/types` | `categorias` (Problema, Implementação…) |
| Task.`creator`, `created_at` | — | `criado_por`, `criado_em` |
| Task.`state` / `archived` | — | status (1 Frozen, 2 Open, 3 Review, 4 Closed) |
| Label (`title`, `color`) | `GET /projects/{id}/labels` | `labels`. No Ora as labels são **por projeto**; aqui são compartilhadas, então labels de mesmo nome são unidas |
| Task Label | `GET /projects/{id}/tasks/{task_id}/labels` | `ticket_labels` |
| Task Member (assignee) | `GET /projects/{id}/tasks/{task_id}/members` | `responsavel_id`. O Ora aceita vários responsáveis; aqui é um só, então fica o primeiro e os demais vão para um comentário |
| Project/Organization Member (`full_name`, `email`, `profile_picture`) | `GET /projects/{id}/members`, `GET /organizations/{id}/members` | `usuarios` (criados desativados ou com senha a definir) |
| Task Comment (`comment`, `created_at`, `public`) | `GET /projects/{id}/tasks/{task_id}/comments` | `comentarios` |
| Task Attachment (`data_path`, `external_url`, `file_title`, `file_size`, `file_type`, `activity_id`) | `GET /projects/{id}/tasks/{task_id}/attachments` | `anexos`: baixar o arquivo e gravar em `UPLOAD_DIR`. O `activity_id` provavelmente liga o anexo ao comentário |
| Task Checklist (`title`, `checked`, `main_id`) | `GET …/tasks/{task_id}/checklists` e `…/items` | Lista de tarefas (`[ ]`) no fim da descrição |
| Atividade (histórico) | `GET /projects/{id}/tasks/{task_id}/activity` | `atividades`. A resposta **não é documentada** na especificação; descobrir com uma chamada real |

O banco já tem a coluna `ora_id` em usuários, projetos, labels, tickets, comentários e anexos. Com ela, a importação pode ser rodada de novo sem duplicar nada.

## Pontos a confirmar com a API no ar

1. **Formato do texto** de `description` e `comment`: HTML, Markdown ou texto simples. A especificação diz apenas `string`. É preciso converter para o formato do editor (JSON do TipTap) mantendo negrito, listas, código e imagens.
2. **`id` dos objetos:** os modelos da especificação não listam o campo `id`, mas as rotas usam `task_id`, `label_id` etc. Na prática ele vem na resposta.
3. **Paginação e limites de requisições:** qual o `limit` máximo, e se a API limita o número de chamadas por minuto.
4. **Download dos anexos:** se `data_path` é uma URL direta (por exemplo, Amazon S3) ou se precisa do token.
5. **Quais listas** correspondem a Pendências, Doing e Completadas em cada projeto de vocês, já que os nomes e tipos podem variar.

## Se a api.ora.pm continuar fora do ar

- **Primeiro:** confirmar com o suporte do Ora (hi@ora.pm) se a API pública foi desativada ou se é uma queda temporária.
- **Alternativa 1:** o próprio site `app.ora.pm` funciona, e ele conversa com algum servidor para carregar os dados. Esse caminho pode ser usado com a sessão do usuário logado, mas é preciso investigar.
- **Alternativa 2:** exportação manual pelo próprio Ora, se ele oferecer exportação de projetos.
