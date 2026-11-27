# HyBrazil Cases

Sistema interno de gestão de tickets/cases inspirado no Ora: projetos com quadro Kanban (Pendências → Doing → Completadas), tickets numerados por projeto, comentários com texto rico (cores, código com destaque, imagens, vídeos e arquivos), labels, categorias, filtros, login e grupos de permissões. Tudo roda localmente, com banco de dados interno.

## Como usar

Os scripts devem ser rodados no PowerShell, a partir da pasta do projeto.

**Iniciar** (banco + sistema):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\iniciar.ps1
```

Abra http://localhost:8000. Para liberar o acesso a outras máquinas da rede interna, use `-Rede` (o Firewall do Windows pode pedir permissão).

**Primeiro acesso:** login `admin`. A senha inicial está em `backend\.env`, na linha `ADMIN_INITIAL_PASSWORD`. O sistema obriga a trocar a senha no primeiro login. Depois disso, a linha pode ser apagada do arquivo.

Existe também um usuário `teste` (administrador) e um projeto **"Automação (demonstração)"** com dados de exemplo, criados por `backend\demo.py` para os testes. A senha do `teste` está em `DEV_TEST_PASSWORD` no mesmo `.env`. Esse usuário pode ser desativado em *Usuários*, e o projeto pode ser arquivado em *Projetos*.

**Parar o banco:** `scripts\db-stop.ps1`.

## O que está pronto

| Área | Recursos |
|---|---|
| Login | Usuário e senha (hash Argon2), "manter conectado", bloqueio de 5 min após 5 tentativas erradas, troca obrigatória da senha inicial, troca de senha e foto no perfil |
| Usuários | Criar (com senha inicial gerada), editar, desativar (o histórico é mantido), redefinir senha, último acesso |
| Grupos e permissões | Grupos editáveis com permissões; as permissões do usuário são a soma de todos os seus grupos. Grupos padrão: **Administradores** (tudo) e **Usuários** (excluir apenas o que é seu) |
| Projetos | Criar, editar, arquivar, favoritar (favoritos aparecem no topo da barra lateral) |
| Quadro | 3 colunas com contadores, criação rápida ("Novo ticket…"), arrastar e soltar entre colunas e dentro delas, checkbox para completar, carregamento de 50 em 50 |
| Ticket | Número `#N` por projeto, título editável, categoria, labels, responsável, descrição rica, linha do tempo (comentários + histórico de alterações, agrupados por dia), link copiável, exclusão conforme permissão |
| Texto rico | Negrito, itálico, sublinhado, riscado, **cor do texto**, títulos, listas, citação, código na linha, **blocos de código com destaque de sintaxe** (com escolha de linguagem), links, atalhos Markdown (`**`, `#`, ```` ``` ````, `>`, `-`), `#123` vira link para o ticket |
| Anexos | Pelo botão 📎, **colando (Ctrl+V)** ou **arrastando** para o editor. Imagens aparecem no texto, vídeos com player, PDF e outros arquivos como cartão para baixar |
| Filtros | Texto (título, descrição e comentários; sem acento; plurais; trechos de códigos como `52L`), labels (qualquer/todas), categoria, responsável ("Meus tickets", "Sem responsável") e ID. Os filtros ficam na URL, então o link filtrado pode ser compartilhado |
| Labels | Globais (compartilhadas entre projetos), criadas direto no ticket; tela para editar, **mesclar** duplicadas e excluir |
| Categorias | Tela de edição com nome, **ícone** (45 opções), **cor** e ordem. Uma categoria em uso é desativada em vez de excluída |
| Exclusões | Tickets e comentários excluídos saem da tela, mas continuam no banco (exclusão lógica) |
| Celular | Layout adaptado para telas pequenas |

## Estrutura

```
backend/            API em Python (FastAPI + SQLAlchemy + PostgreSQL)
  app/              código (routers/ = rotas da API)
  migrations/       esquema do banco em SQL, aplicado automaticamente ao iniciar
  tests/            testes automatizados (pytest)
  demo.py           cria o usuário de teste e o projeto de demonstração
  .env              configuração local com senhas (gerado; NÃO versionar)
frontend/           interface web (React + TypeScript + Vite)
  src/pages/        telas (Quadro, TicketModal, admin/…)
  src/editor/       editor de texto rico (TipTap) e o visualizador
runtime/            Node.js e PostgreSQL portáteis, dados do banco (pgdata) e anexos (uploads)
scripts/            iniciar, compilar, testes, banco
docs/               análises dos capítulos de especificação
```

### Detalhes técnicos

- **Banco:** PostgreSQL 18 portátil em `runtime\pgsql`, porta **5433**, dados em `runtime\pgdata`. Os bancos são `hyora` (sistema) e `hyora_test` (testes).
- **Anexos:** ficam em `runtime\uploads`; o banco guarda só os metadados. Arquivos HTML/SVG são sempre baixados, nunca abertos no navegador, por segurança.
- **Busca:** combina full-text em português (`tsvector` com `unaccent`) com busca por trecho (`pg_trgm`), as duas com índice.
- **Para cada mudança no esquema,** crie um novo arquivo `backend/migrations/002_….sql`. Ele é aplicado sozinho na próxima inicialização.
- **Backup:** `runtime\pgsql\bin\pg_dump.exe -h localhost -p 5433 -U hyora hyora > backup.sql`, mais uma cópia da pasta `runtime\uploads`.

## Desenvolvimento

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

Abre a API com recarga automática e a interface em http://localhost:5173, com recarga instantânea.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\testes.ps1
```

Roda os 20 testes automatizados do backend.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\compilar-frontend.ps1
```

Recompila a interface que o `iniciar.ps1` entrega.

## Próximos passos

1. **Migração do Ora via API.** O modelo de dados já tem `ora_id` em usuários, projetos, labels, tickets, comentários e anexos, para importar sem duplicar e manter os números originais.
2. **Instalação em servidor:** rodar como serviço do Windows (por exemplo com NSSM) e configurar HTTPS (com `COOKIE_SECURE=true` no `.env`).
3. **Possíveis melhorias:** notificações (e-mail ou no sistema), lixeira para restaurar excluídos, busca global em todos os projetos, menção `@pessoa`.
