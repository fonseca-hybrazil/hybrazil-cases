# Migração do Ora

Como os tickets do Ora (app.ora.pm) foram trazidos para o HyBrazil Cases, e como repetir.

## Por que não pela API oficial

A API pública (`api.ora.pm`, documentada em [ora-api/](ora-api/README.md)) não responde mais. O site `app.ora.pm` continua funcionando e carrega os dados por uma conexão WebSocket (`wss://ws.ora.pm/ws`). Cada mensagem é um JSON com uma "intenção", e as respostas grandes vêm compactadas com zlib dentro de uma string. A exportação usa esse mesmo canal, **só para leitura**, de dentro de uma aba do Ora com o usuário logado. O token de sessão nunca sai do navegador.

| Intenção | Parâmetros | O que traz |
|---|---|---|
| `get_organization_projects` | `organization_id` | Lista de projetos (id, uuid, título) |
| `project_all` | `project_uuid`, `version: 4` | O projeto inteiro: tickets (`tasks`, com título, descrição, `second_id` = número #, `list_id`, `task_type`, `position`, `archived`), listas, labels, `tasks_labels`, `tasks_developers` (responsáveis), `task_types` (categorias) e membros (`developers`) |
| `all_task_data` | `project_id`, `task_id` | Detalhes do ticket: `discussionThread` (a conversa), `files` (anexos do ticket) e `checklists` |
| `get_channel_messages` | `discussion_thread`, `project_id`, `version: 2` | Todas as mensagens do ticket: comentários (`text` em Markdown, `attachments`, `edited_at`) e eventos do histórico (`type`: 1 criou, 9 título, 10 descrição, 11 moveu de lista, 12 tipo, 13/14 responsável…) |

Arquivos: `https://ora-attachments.s3.amazonaws.com/<data_path>` para anexos do ticket e `https://message-attachments.s3.amazonaws.com/<url>` para anexos de comentário. São endereços públicos, sem login.

## Passo a passo

1. **Exportar.** Com o Ora aberto e logado no navegador do app, um script colado na aba percorre os projetos (3 pedidos por vez, com pausas) e guarda cada ticket no IndexedDB do navegador. Assim a exportação sobrevive se a página recarregar e retoma de onde parou. No fim, cada projeto é compactado (gzip + base64) e entregue como texto, que vira arquivo em disco.
2. **Montar em disco:** `python ora/receber.py <arquivos com os pacotes>`. Grava `runtime/ora-export/<projeto>/projeto.json` e `tickets/<id>.json`.
3. **Baixar os arquivos:** `python ora/baixar_arquivos.py automacao mikrotik resolucao`. Grava em `runtime/ora-export/<projeto>/arquivos/`. Pode rodar de novo, porque pula o que já baixou.
4. **Testar:** `python ora/importar.py --banco teste automacao mikrotik resolucao`. Importa no banco `hyora_test`, que é zerado antes, e grava os anexos numa pasta à parte.
5. **Importar de verdade:** `python ora/importar.py automacao mikrotik resolucao`. Depois, rode `scripts/atualizar.ps1` para o site recarregar.

Rodar a importação de novo é seguro: o projeto que já foi importado (mesmo `ora_id`) é apagado, junto com seus anexos, e importado outra vez. Mas o que tiver sido feito **no HyBrazil Cases** nesses projetos depois da importação se perde.

## Regras de conversão

| Ora | HyBrazil Cases |
|---|---|
| Projeto | Projeto com o mesmo nome. O próximo número continua a numeração do Ora |
| `second_id` | Número do ticket (`#123`) |
| Lista "Pendências" / "Doing" / "Completadas" | Status pendente / andamento / completado (pelo nome da lista) |
| `position` | Ordem dentro da coluna (a mesma do Ora) |
| Ticket arquivado | Importado como excluído: fica no banco, mas não aparece |
| Labels (por projeto no Ora) | **Globais**: labels com o mesmo nome em projetos diferentes viram uma só. Uma label criada antes aqui com o mesmo nome adota a cor do Ora |
| Tipo de tarefa | Categoria: Problem, bug e fix → Problema; Add e feature → Implementação; Modification e chore → Modificação; Study → Estudo; Check e test → Verificação; docs → Documentação |
| Responsáveis | O primeiro vira o responsável; os demais são citados no fim da descrição |
| Descrição e comentários (Markdown) | Texto rico: código com linguagem, negrito, listas, links etc. (`ora/markdown.py`) |
| Checklists | Lista de tarefas no fim da descrição, com o título do checklist e as caixas marcadas |
| Anexos de comentário | Imagens, vídeos e arquivos dentro do próprio comentário |
| Anexos do ticket | Um comentário de quem enviou, na data do envio |
| Membros | Usuários com o mesmo login, nome, e-mail e foto, e **senha bloqueada**. O administrador libera o acesso em *Usuários › Redefinir senha*. O dono do projeto com e-mail @hybrazil.com entra como administrador |
| Eventos do histórico | Linha do tempo: criou, título, descrição, moveu, categoria, responsável |

## Diferenças conhecidas

- **Contador de comentários:** o contador do Ora inclui comentários já apagados. Por exemplo, o #222 mostra "12", mas o próprio Ora exibe só 3, e esses 3 foram importados.
- **Itens que não existem aqui:** timers, prazos, reações e quem segue cada ticket não são importados.
