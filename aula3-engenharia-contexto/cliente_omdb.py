"""Cliente HTTP enxuto para a OMDb."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

OMDB_URL = "https://www.omdbapi.com/"


class ErroOMDb(RuntimeError):
    """Erro compreensível ocorrido ao consultar a OMDb."""


def _consultar(parametros, api_key=None, abrir=None):
    chave = api_key or os.environ.get("OMDB_API_KEY")
    if not chave:
        raise ErroOMDb("Configure OMDB_API_KEY antes de executar.")
    consulta = {"apikey": chave, **parametros, "r": "json"}
    requisicao = urllib.request.Request(f"{OMDB_URL}?{urllib.parse.urlencode(consulta)}")
    abrir = abrir or urllib.request.urlopen
    try:
        with abrir(requisicao, timeout=10) as resposta:
            dados = json.load(resposta)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        raise ErroOMDb("Não foi possível conectar à OMDb.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ErroOMDb("A OMDb devolveu uma resposta inválida.") from None
    if dados.get("Response") == "False":
        mensagens = {
            "Movie not found!": "Título não encontrado na OMDb.",
            "Invalid API key!": "Chave OMDb inválida.",
            "Request limit reached!": "Limite diário da OMDb atingido.",
        }
        raise ErroOMDb(mensagens.get(dados.get("Error"), "A OMDb recusou a consulta."))
    return dados


def _normalizar(dados):
    campos = {
        "titulo": "Title",
        "ano": "Year",
        "tipo": "Type",
        "genero": "Genre",
        "diretor": "Director",
        "avaliacao_imdb": "imdbRating",
        "temporadas": "totalSeasons",
    }
    return {
        destino: dados[origem]
        for destino, origem in campos.items()
        if dados.get(origem) not in (None, "", "N/A")
    }


def buscar_titulo(titulo, ano=None, api_key=None, abrir=None) -> dict:
    """Busca uma obra por título e ano opcional e devolve campos normalizados."""
    parametros = {"t": titulo}
    if ano:
        parametros["y"] = ano
    return _normalizar(_consultar(parametros, api_key, abrir))


def pesquisar_titulos(termo, api_key=None, abrir=None) -> list[dict]:
    """Pesquisa obras por termo e devolve no máximo cinco resultados."""
    dados = _consultar({"s": termo}, api_key, abrir)
    campos = {"titulo": "Title", "ano": "Year", "id_imdb": "imdbID", "tipo": "Type"}
    return [
        {
            destino: item[origem]
            for destino, origem in campos.items()
            if item.get(origem) not in (None, "", "N/A")
        }
        for item in dados.get("Search", [])[:5]
    ]
