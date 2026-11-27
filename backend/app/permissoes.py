"""Catálogo de permissões atribuíveis a grupos."""

PERMISSOES: dict[str, str] = {
    "admin_usuarios": "Gerenciar usuários e grupos",
    "admin_projetos": "Criar, editar e arquivar projetos",
    "admin_categorias": "Gerenciar categorias",
    "admin_labels": "Editar, mesclar e excluir labels",
    "ticket_excluir": "Excluir qualquer ticket",
    "ticket_excluir_proprio": "Excluir tickets criados por mim",
    "comentario_editar": "Editar comentários de outras pessoas",
    "comentario_excluir": "Excluir qualquer comentário",
    "comentario_excluir_proprio": "Excluir meus próprios comentários",
}

GRUPOS_PADRAO = [
    {
        "nome": "Administradores",
        "descricao": "Acesso total, incluindo a administração do sistema.",
        "permissoes": list(PERMISSOES),
    },
    {
        "nome": "Usuários",
        "descricao": "Uso normal: criar e editar tickets, comentar e anexar.",
        "permissoes": ["ticket_excluir_proprio", "comentario_excluir_proprio"],
    },
]
