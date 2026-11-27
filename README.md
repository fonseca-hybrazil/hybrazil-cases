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

O banco é o PostgreSQL instalado como serviço do Windows, que já inicia sozinho com o computador (veja *Detalhes técnicos*).

### Site sempre no ar

```powershell
powershell -ExecutionPolicy Bypass -File scripts\instalar-servico.ps1
```

Registra a tarefa agendada **"HyBrazil Cases"**, que inicia o site escondido toda vez que você entra no Windows, e já o inicia. O site fica em http://localhost:8000. Use `-Rede` para liberar o acesso pela rede interna.

- **Supervisor:** `scripts\servico.ps1` mantém o servidor rodando e o reinicia sozinho se ele cair.
- **Logs:** ficam em `runtime\logs` (`servico.log`, `servidor.log`, `servidor-erros.log`).
- **Parar:** `instalar-servico.ps1 -Parar`. Para tirar do início automático, use `-Remover`.

**Publicar mudanças no site:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\atualizar.ps1 -Testes
```

- Compila a interface numa pasta separada e confere o backend. Com `-Testes`, também roda os testes.
- Só depois disso reinicia o servidor com a versão nova. Leva menos de um minuto, e o site fica fora do ar por poucos segundos.
- Se algo falhar, nada é trocado e o site continua na versão anterior.
- As mudanças no banco (`backend/migrations`) são aplicadas sozinhas quando o servidor reinicia.

## O que está pronto

| Área | Recursos |
|---|---|
| Login | Usuário e senha (hash Argon2), "manter conectado", bloqueio de 5 min após 5 tentativas erradas, troca obrigatória da senha inicial, troca de senha e foto no perfil |
| Usuários | Criar (com senha inicial gerada), editar (inclusive a **foto**), desativar (o histórico é mantido), redefinir senha, último acesso. Fotos são reduzidas no navegador para 512 px antes do envio |
| Grupos e permissões | Grupos editáveis com permissões; as permissões do usuário são a soma de todos os seus grupos. Grupos padrão: **Administradores** (tudo) e **Usuários** (excluir apenas o que é seu) |
| Projetos | Criar, editar, arquivar, favoritar (favoritos aparecem no topo da barra lateral) |
| Quadro | 3 colunas com contadores, criação rápida ("Novo ticket…"), arrastar e soltar entre colunas e dentro delas, checkbox para completar, carregamento de 50 em 50 |
| Ticket | Número `#N` por projeto, título editável, categoria, labels, responsável, descrição rica, linha do tempo (comentários + histórico de alterações, agrupados por dia), link copiável, exclusão conforme permissão |
| Texto rico | Negrito, itálico, sublinhado, riscado, **cor do texto**, títulos, listas, citação, código na linha, **blocos de código com destaque de sintaxe** (com escolha de linguagem), links, atalhos Markdown (`**`, `#`, ```` ``` ````, `>`, `-`), `#123` vira link para o ticket |
| Linguagens de código | Escolha na lista do bloco ou digite ```` ``` ```` + nome + espaço (ex.: ```` ```st ````). Inclui **Texto Estruturado** (`st`, CODESYS V2.3 e V3.5: palavras-chave, tipos, `T#5S`, `16#FF`, `%IX0.0`, pragmas `{attribute ...}`, TON/R_TRIG etc.) e **VBScript do Elipse E3** (`elipse`: objetos `Application`/`Screen`/`Parent`, funções E3Globals como `OPCIsGood` e métodos como `GetObject`/`WriteEx`), além de Python, C#, SQL, JSON, XML e outras. No modo *Automático* a linguagem é detectada entre as da lista |
| Anexos | Pelo botão 📎, **colando (Ctrl+V)** ou **arrastando** para o editor (até 1 GB por arquivo). Imagens aparecem no texto; vídeos que o navegador toca (MP4/H.264, WebM) ganham player com avanço/retrocesso e link para baixar; AVI, MKV, PDF e outros viram cartão para baixar |
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

- **Banco:** o sistema usa o **PostgreSQL 18 instalado no Windows** (serviço `postgresql-x64-18`, porta **5432**). Os bancos são `hyora` (sistema) e `hyora_test` (testes), com o usuário `hyora`. A conexão fica no `backend\.env`.
  - Para apontar para outro PostgreSQL instalado, rode `scripts\usar-postgres-instalado.ps1`. Ele pede a senha de um usuário com permissão de criar usuários e bancos (não precisa ser superusuário), cria os bancos, copia os dados e atualiza o `.env`.
  - Também existe um PostgreSQL **portátil** em `runtime\pgsql` (porta 5433, dados em `runtime\pgdata`), usado na primeira versão. O `db-start.ps1` só o liga quando o `.env` aponta para a porta 5433; as linhas antigas estão comentadas no `.env` para voltar a ele.
- **Anexos:** ficam em `runtime\uploads`; o banco guarda só os metadados. Arquivos HTML/SVG são sempre baixados, nunca abertos no navegador, por segurança.
- **Busca:** combina full-text em português (`tsvector` com `unaccent`) com busca por trecho (`pg_trgm`), as duas com índice.
- **Para cada mudança no esquema,** crie um novo arquivo `backend/migrations/002_….sql`. Ele é aplicado sozinho na próxima inicialização.
- **Backup:** `& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h localhost -p 5432 -U hyora -Fc -f backup.dump hyora`, mais uma cópia da pasta `runtime\uploads`. A senha do `hyora` está no `DATABASE_URL` do `.env`.

## Desenvolvimento

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

Abre a API com recarga automática e a interface em http://localhost:5173, com recarga instantânea.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\testes.ps1
```

Roda os testes automatizados do backend.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\compilar-frontend.ps1
```

Recompila a interface que o `iniciar.ps1` entrega.

## Próximos passos

1. **Migração do Ora via API.** O modelo de dados já tem `ora_id` em usuários, projetos, labels, tickets, comentários e anexos, para importar sem duplicar e manter os números originais.
2. **Instalação em servidor:** rodar como serviço do Windows (por exemplo com NSSM) e configurar HTTPS (com `COOKIE_SECURE=true` no `.env`).
3. **Possíveis melhorias:** notificações (e-mail ou no sistema), lixeira para restaurar excluídos, busca global em todos os projetos, menção `@pessoa`.
