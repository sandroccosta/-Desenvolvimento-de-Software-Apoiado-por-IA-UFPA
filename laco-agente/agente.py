"""Agente de filmes e séries: laço de function calling com Ollama local."""
import json
import sys
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODELO = "llama3.2"
MAX_PASSOS = 6
PERGUNTA = "Quantas temporadas tem a série Dark e qual nota a dupla deu para ela?"
SISTEMA = (
    "Você é o assistente do catálogo de filmes e séries da dupla. "
    "Use as ferramentas para obter os dados e nunca invente informações."
)
DESCRICAO_VAGA = "faz uma consulta"

CATALOGO = {
    "Breaking Bad": {"tipo": "série", "ano": 2008, "genero": "drama", "temporadas": 5, "nota_da_dupla": 9.5},
    "Dark": {"tipo": "série", "ano": 2017, "genero": "ficção científica", "temporadas": 3, "nota_da_dupla": 9.0},
    "Stranger Things": {"tipo": "série", "ano": 2016, "genero": "terror", "temporadas": 5, "nota_da_dupla": 8.0},
    "Interestelar": {"tipo": "filme", "ano": 2014, "genero": "ficção científica", "duracao_min": 169, "nota_da_dupla": 9.2},
    "Cidade de Deus": {"tipo": "filme", "ano": 2002, "genero": "crime", "duracao_min": 130, "nota_da_dupla": 9.4},
    "O Auto da Compadecida": {"tipo": "filme", "ano": 2000, "genero": "comédia", "duracao_min": 104, "nota_da_dupla": 9.8},
}


def listar_catalogo() -> list[str]:
    """Lista os títulos de filmes e séries cadastrados no catálogo da dupla."""
    return list(CATALOGO)


def detalhes_titulo(titulo: str) -> dict:
    """Retorna tipo, ano, gênero, duração ou número de temporadas e a nota da dupla de um filme ou série do catálogo."""
    for nome, dados in CATALOGO.items():
        if nome.casefold() == titulo.strip().casefold():
            return {"titulo": nome, **dados}
    return {"erro": f"'{titulo}' não está no catálogo. Use listar_catalogo para ver os títulos."}


FERRAMENTAS = {f.__name__: f for f in (listar_catalogo, detalhes_titulo)}


def declarar(func, descricao=None) -> dict:
    """Monta a declaração da tool no formato de function calling a partir da assinatura e da docstring."""
    params = {nome: {"type": "string"} for nome in func.__annotations__ if nome != "return"}
    return {"type": "function", "function": {
        "name": func.__name__,
        "description": descricao or func.__doc__,
        "parameters": {"type": "object", "properties": params, "required": list(params)},
    }}


def chamar_modelo(mensagens: list[dict], tools: list[dict]) -> dict:
    corpo = {"model": MODELO, "messages": mensagens, "tools": tools, "stream": False,
             "options": {"temperature": 0, "seed": 42}}
    requisicao = urllib.request.Request(OLLAMA_URL, json.dumps(corpo).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(requisicao, timeout=600) as resposta:
        return json.load(resposta)["message"]


def rodar(modo: str) -> int | None:
    """Executa o laço e devolve quantos passos levou, ou None se estourou MAX_PASSOS."""
    tools = [declarar(listar_catalogo), declarar(detalhes_titulo, DESCRICAO_VAGA if modo == "vaga" else None)]
    mensagens = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": PERGUNTA}]
    print(f"\n=== Descrição {modo}: {tools[1]['function']['description']!r}")
    for passo in range(1, MAX_PASSOS + 1):
        mensagem = chamar_modelo(mensagens, tools)
        mensagens.append(mensagem)
        chamadas = mensagem.get("tool_calls") or []
        if not chamadas:
            print(f"[passo {passo}] resposta final: {mensagem.get('content', '').strip()}")
            return passo
        for chamada in chamadas:
            nome, args = chamada["function"]["name"], chamada["function"].get("arguments") or {}
            try:
                resultado = FERRAMENTAS[nome](**args)
            except (KeyError, TypeError) as erro:
                resultado = {"erro": f"chamada inválida: {erro}"}
            print(f"[passo {passo}] tool {nome}({args}) -> {resultado}")
            mensagens.append({"role": "tool", "tool_name": nome, "content": json.dumps(resultado, ensure_ascii=False)})
    print(f"Limite de {MAX_PASSOS} passos atingido sem resposta final.")
    return None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    modos = sys.argv[1:] or ["boa", "vaga"]
    print(f"Modelo: {MODELO} | Pergunta: {PERGUNTA}")
    passos = {modo: rodar(modo) for modo in modos}
    print("\nResumo:", ", ".join(f"descrição {m} = {p or 'sem resposta'} passo(s)" for m, p in passos.items()))
