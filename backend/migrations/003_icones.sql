-- Ícones de projeto.
-- projetos.icone: 'lucide:<nome>' (ícone padrão, colorido com icone_cor) ou 'lib:<id>' (imagem da biblioteca).
-- icones: biblioteca de ícones enviados (PNG, SVG, ICO, JPG, WebP, GIF), reaproveitáveis em vários projetos.
CREATE TABLE icones (
    id           serial PRIMARY KEY,
    nome         text NOT NULL,
    tipo_mime    text NOT NULL,
    tamanho      integer NOT NULL,
    caminho      text NOT NULL,
    enviado_por  integer REFERENCES usuarios(id),
    criado_em    timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE projetos
    ADD COLUMN icone     text,
    ADD COLUMN icone_cor text;
