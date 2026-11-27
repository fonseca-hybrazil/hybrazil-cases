-- Listas de tarefas (caixas de marcar) na descrição e nos comentários.
-- O progresso fica guardado no ticket para o quadro mostrar "3/8" sem ler todos os comentários.
ALTER TABLE tickets
    ADD COLUMN tarefas_total  integer NOT NULL DEFAULT 0,
    ADD COLUMN tarefas_feitas integer NOT NULL DEFAULT 0;
