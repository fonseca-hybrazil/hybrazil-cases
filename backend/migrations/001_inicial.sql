-- Esquema inicial do HyBrazil Cases.
-- Requer as extensões unaccent e pg_trgm (criadas pelo superusuário em scripts/db-init.ps1).

-- ---------------------------------------------------------------------------
-- Busca: unaccent "imutável" e configuração de texto em português sem acentos
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;

CREATE TEXT SEARCH CONFIGURATION pt_unaccent (COPY = portuguese);
ALTER TEXT SEARCH CONFIGURATION pt_unaccent
    ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;

-- Texto normalizado para busca por trecho (minúsculas, sem acentos)
CREATE OR REPLACE FUNCTION f_norm(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$ SELECT lower(public.f_unaccent(coalesce($1, ''))) $$;

-- ---------------------------------------------------------------------------
-- Usuários, grupos e sessões
-- ---------------------------------------------------------------------------
CREATE TABLE usuarios (
    id                serial PRIMARY KEY,
    nome              text NOT NULL,
    login             text NOT NULL,
    email             text,
    avatar_caminho    text,
    senha_hash        text NOT NULL,
    trocar_senha      boolean NOT NULL DEFAULT false,
    ativo             boolean NOT NULL DEFAULT true,
    ultimo_acesso     timestamptz,
    tentativas_falhas integer NOT NULL DEFAULT 0,
    bloqueado_ate     timestamptz,
    criado_em         timestamptz NOT NULL DEFAULT now(),
    ora_id            text UNIQUE
);
CREATE UNIQUE INDEX usuarios_login_uq ON usuarios (lower(login));

CREATE TABLE grupos (
    id          serial PRIMARY KEY,
    nome        text NOT NULL,
    descricao   text NOT NULL DEFAULT '',
    permissoes  text[] NOT NULL DEFAULT '{}',
    sistema     boolean NOT NULL DEFAULT false,  -- grupo padrão, não pode ser excluído
    criado_em   timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX grupos_nome_uq ON grupos (lower(nome));

CREATE TABLE grupo_usuarios (
    grupo_id    integer NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    usuario_id  integer NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    PRIMARY KEY (grupo_id, usuario_id)
);
CREATE INDEX grupo_usuarios_usuario_idx ON grupo_usuarios (usuario_id);

CREATE TABLE sessoes (
    token_hash  text PRIMARY KEY,
    usuario_id  integer NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    criado_em   timestamptz NOT NULL DEFAULT now(),
    expira_em   timestamptz NOT NULL,
    ip          text,
    user_agent  text
);
CREATE INDEX sessoes_usuario_idx ON sessoes (usuario_id);

-- ---------------------------------------------------------------------------
-- Projetos, categorias e labels
-- ---------------------------------------------------------------------------
CREATE TABLE projetos (
    id              serial PRIMARY KEY,
    nome            text NOT NULL,
    descricao       text NOT NULL DEFAULT '',
    proximo_numero  integer NOT NULL DEFAULT 1,
    arquivado       boolean NOT NULL DEFAULT false,
    criado_por      integer REFERENCES usuarios(id),
    criado_em       timestamptz NOT NULL DEFAULT now(),
    ora_id          text UNIQUE
);

CREATE TABLE favoritos (
    usuario_id  integer NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    projeto_id  integer NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, projeto_id)
);

CREATE TABLE categorias (
    id      serial PRIMARY KEY,
    nome    text NOT NULL,
    icone   text NOT NULL,
    cor     text NOT NULL,
    ordem   integer NOT NULL DEFAULT 0,
    ativa   boolean NOT NULL DEFAULT true
);

CREATE TABLE labels (
    id         serial PRIMARY KEY,
    nome       text NOT NULL,
    cor        text NOT NULL,
    criado_em  timestamptz NOT NULL DEFAULT now(),
    ora_id     text UNIQUE
);
CREATE UNIQUE INDEX labels_nome_uq ON labels (lower(nome));

-- ---------------------------------------------------------------------------
-- Tickets
-- ---------------------------------------------------------------------------
CREATE TABLE tickets (
    id               serial PRIMARY KEY,
    projeto_id       integer NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    numero           integer NOT NULL,
    titulo           text NOT NULL,
    descricao        jsonb,
    descricao_texto  text NOT NULL DEFAULT '',
    status           text NOT NULL DEFAULT 'pendente'
                     CHECK (status IN ('pendente', 'andamento', 'completado')),
    categoria_id     integer REFERENCES categorias(id),
    responsavel_id   integer REFERENCES usuarios(id),
    criado_por       integer REFERENCES usuarios(id),
    ordem            double precision NOT NULL DEFAULT 0,
    criado_em        timestamptz NOT NULL DEFAULT now(),
    atualizado_em    timestamptz NOT NULL DEFAULT now(),
    concluido_em     timestamptz,
    excluido_em      timestamptz,
    excluido_por     integer REFERENCES usuarios(id),
    ora_id           text UNIQUE,
    busca            tsvector GENERATED ALWAYS AS (
                         setweight(to_tsvector('pt_unaccent'::regconfig, coalesce(titulo, '')), 'A') ||
                         setweight(to_tsvector('pt_unaccent'::regconfig, coalesce(descricao_texto, '')), 'B')
                     ) STORED,
    UNIQUE (projeto_id, numero)
);
CREATE INDEX tickets_quadro_idx ON tickets (projeto_id, status, ordem) WHERE excluido_em IS NULL;
CREATE INDEX tickets_categoria_idx ON tickets (projeto_id, categoria_id);
CREATE INDEX tickets_responsavel_idx ON tickets (projeto_id, responsavel_id);
CREATE INDEX tickets_busca_idx ON tickets USING gin (busca);
CREATE INDEX tickets_trgm_idx ON tickets USING gin ((f_norm(titulo) || ' ' || f_norm(descricao_texto)) gin_trgm_ops);

CREATE TABLE ticket_labels (
    ticket_id  integer NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    label_id   integer NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (ticket_id, label_id)
);
CREATE INDEX ticket_labels_label_idx ON ticket_labels (label_id, ticket_id);

-- ---------------------------------------------------------------------------
-- Comentários, anexos e atividades
-- ---------------------------------------------------------------------------
CREATE TABLE comentarios (
    id           serial PRIMARY KEY,
    ticket_id    integer NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    autor_id     integer REFERENCES usuarios(id),
    conteudo     jsonb NOT NULL,
    texto        text NOT NULL DEFAULT '',
    criado_em    timestamptz NOT NULL DEFAULT now(),
    editado_em   timestamptz,
    excluido_em  timestamptz,
    excluido_por integer REFERENCES usuarios(id),
    ora_id       text UNIQUE,
    busca        tsvector GENERATED ALWAYS AS (to_tsvector('pt_unaccent'::regconfig, coalesce(texto, ''))) STORED
);
CREATE INDEX comentarios_ticket_idx ON comentarios (ticket_id, criado_em);
CREATE INDEX comentarios_busca_idx ON comentarios USING gin (busca);
CREATE INDEX comentarios_trgm_idx ON comentarios USING gin (f_norm(texto) gin_trgm_ops);

CREATE TABLE anexos (
    id             serial PRIMARY KEY,
    ticket_id      integer REFERENCES tickets(id) ON DELETE CASCADE,
    comentario_id  integer REFERENCES comentarios(id) ON DELETE SET NULL,
    nome_original  text NOT NULL,
    tipo_mime      text NOT NULL,
    tamanho        bigint NOT NULL,
    caminho        text NOT NULL,
    enviado_por    integer REFERENCES usuarios(id),
    criado_em      timestamptz NOT NULL DEFAULT now(),
    ora_id         text UNIQUE
);
CREATE INDEX anexos_ticket_idx ON anexos (ticket_id);

CREATE TABLE atividades (
    id          bigserial PRIMARY KEY,
    ticket_id   integer NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    usuario_id  integer REFERENCES usuarios(id),
    tipo        text NOT NULL,
    dados       jsonb NOT NULL DEFAULT '{}',
    criado_em   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX atividades_ticket_idx ON atividades (ticket_id, criado_em);
