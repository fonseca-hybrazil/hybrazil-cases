# Análise — Capítulo 2: Filtros e login

Fonte: `specs/capitulo2.txt`. Complementa [analise-capitulo1.md](analise-capitulo1.md).

---

## 1. Filtros do quadro

O botão **Filtro** no cabeçalho do projeto (image1) abre um painel com os filtros abaixo. Ao aplicar:
- as **3 colunas** mostram só os tickets que atendem aos filtros;
- os **contadores** das colunas refletem o resultado filtrado (ex.: "Completadas 12 de 1401");
- há um indicador visível de "filtro ativo" e um botão **Limpar filtros**;
- os filtros ficam na **URL**, então dá para compartilhar um link já filtrado ou voltar a ele.

| Filtro | Comportamento proposto |
|---|---|
| **Label** | Seleção múltipla. Padrão: o ticket tem **qualquer uma** das labels escolhidas. Opção para exigir **todas**. |
| **Texto** | Procura no **título**, na **descrição** e nos **comentários** do ticket. Ignora maiúsculas/minúsculas e acentos ("modificacao" acha "Modificação"). |
| **Categoria** | Seleção múltipla. O ticket tem qualquer uma das categorias escolhidas. |
| **ID** | Digitar `1652` ou `#1652` encontra o ticket #1652 do projeto. |

- Filtros diferentes se **combinam com E**. Por exemplo: label "PLC" **e** categoria "Problema" **e** texto "Kron".
- Na busca por texto, o resultado indica **onde** o termo apareceu (título, descrição ou "em 3 comentários") e destaca o trecho.

### Detalhe técnico: busca por texto
Os tickets têm muitos termos técnicos e códigos (`52L1`, `1J4`, `UHLM`, `QDCA`, `LEOC`). Só a busca "linguística" do PostgreSQL (que entende plurais) não é suficiente para esses casos. Por isso, a busca combina duas técnicas:
1. **Full-text em português** (`tsvector` + `unaccent`): "disjuntor" encontra "disjuntores".
2. **Busca por trecho** (`pg_trgm`): "52L" encontra "52L1"; "Kro" encontra "Kron".

As duas usam índices, então continuam rápidas com dezenas de milhares de comentários.

---

## 2. Login e gestão de usuários

### 2.1 Acesso
- Todo acesso exige **login** (e-mail ou nome de usuário + senha). Sem login, nenhuma página ou anexo fica acessível.
- **Sessão** com validade configurável e opção "manter conectado".
- **Logout**.
- Bloqueio temporário após várias tentativas de senha erradas.
- Senhas guardadas com **hash** (Argon2), nunca em texto puro.

### 2.2 Gestão de usuários (tela de administração)
- Listar usuários: nome, e-mail, papel, ativo, último acesso.
- **Criar** usuário: nome, e-mail/login, papel e senha inicial (o usuário troca a senha no primeiro acesso).
- **Editar**: nome, e-mail, papel e avatar.
- **Redefinir senha** de um usuário (feito pelo administrador).
- **Desativar/reativar**. Usuários **não são apagados**, porque são autores de tickets e comentários. Um desativado não consegue logar e não aparece na lista de responsáveis, mas o histórico continua mostrando o nome dele.

### 2.3 Perfil do próprio usuário
- Trocar a própria senha.
- Alterar nome e avatar (a foto que aparece nos cards e comentários).

### 2.4 Grupos e permissões (decidido e implementado)
Em vez de papéis fixos, há **grupos editáveis**. Cada grupo tem um conjunto de permissões, e as permissões de um usuário são a soma das de todos os seus grupos. Todos os usuários logados veem todos os projetos, criam e editam tickets, comentam, anexam e criam labels.

| Permissão | Descrição |
|---|---|
| `admin_usuarios` | Gerenciar usuários e grupos |
| `admin_projetos` | Criar, editar e arquivar projetos |
| `admin_categorias` | Gerenciar categorias |
| `admin_labels` | Editar, mesclar e excluir labels |
| `ticket_excluir` / `ticket_excluir_proprio` | Excluir qualquer ticket / só os que eu criei |
| `comentario_editar` | Editar comentários de outras pessoas (o autor sempre edita o seu) |
| `comentario_excluir` / `comentario_excluir_proprio` | Excluir qualquer comentário / só os meus |

Grupos padrão: **Administradores** (todas as permissões, fixo) e **Usuários** (excluir só o que é seu).

---

## 3. Alterações no modelo de dados

```
usuarios     + login (único), senha_hash, papel [admin | usuario],
               trocar_senha (bool), ultimo_acesso, tentativas_falhas, bloqueado_ate
sessoes      id (token), usuario_id, criado_em, expira_em, ip, user_agent
```

Índices para os filtros:
- `ticket_labels (label_id, ticket_id)` para o filtro por label;
- `tickets (projeto_id, categoria_id)` para o filtro por categoria;
- `tickets (projeto_id, numero)`, que já é único, para o filtro por ID;
- GIN (`tsvector` + `pg_trgm`) em `tickets.titulo`, `tickets.descricao` e `comentarios.conteudo` para o texto.

---

## 4. Decisões e dúvidas

Decidido:
- Todos os usuários veem todos os projetos (por enquanto).
- A exclusão é controlada por **grupos de permissões** (seção 2.4). Tickets e comentários excluídos ficam guardados no banco (exclusão lógica).
- **Filtro por responsável** incluído, com "Meus tickets" e "Sem responsável".
- O texto também é buscado na **descrição** do ticket, além do título e dos comentários.

Em aberto:
1. **Busca global**: quer uma busca que procure em **todos os projetos** de uma vez?
2. **Esqueci minha senha**: hoje o administrador redefine. Enviar por e-mail exige um servidor SMTP da empresa.
3. **Só leitura**: precisa de um grupo que só visualiza, sem criar nem comentar?
