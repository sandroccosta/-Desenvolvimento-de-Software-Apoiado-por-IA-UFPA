"""Tools que o modelo pode escolher durante o laço agêntico."""

import cliente_omdb


def buscar_titulo(titulo: str, ano: str | None = None) -> dict:
    """Busca detalhes como avaliação, temporadas e diretor quando o usuário informa um título específico."""
    return cliente_omdb.buscar_titulo(titulo, ano)


def pesquisar_titulos(termo: str) -> list[dict]:
    """Pesquisa opções para termo amplo ou título aproximado; não retorna detalhes, avaliação ou temporadas."""
    return cliente_omdb.pesquisar_titulos(termo)


FERRAMENTAS = {
    "buscar_titulo": buscar_titulo,
    "pesquisar_titulos": pesquisar_titulos,
}

DECLARACOES = [
    {
        "type": "function",
        "function": {
            "name": "buscar_titulo",
            "description": buscar_titulo.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Título exato do filme ou série."},
                    "ano": {"type": "string", "description": "Ano de lançamento, quando informado."},
                },
                "required": ["titulo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pesquisar_titulos",
            "description": pesquisar_titulos.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {"type": "string", "description": "Termo amplo ou título aproximado."},
                },
                "required": ["termo"],
            },
        },
    },
]
