"""Agente de terminal que consulta filmes e séries na OMDb."""

import json
import inspect
import os
import sys
import urllib.request

from cliente_omdb import ErroOMDb
from tools import DECLARACOES, FERRAMENTAS

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODELO = "llama3.2"
MAX_PASSOS = 6
SISTEMA = (
    "Responda em português. Use as ferramentas para obter fatos sobre filmes e séries. "
    "Não invente dados ausentes e explique erros de forma clara. "
    "Quando o título estiver claro e o usuário pedir avaliação, temporadas, gênero ou diretor, "
    "use buscar_titulo uma única vez e não use pesquisar_titulos. "
    "Use pesquisar_titulos somente para listas, termos amplos ou títulos incertos."
)


def validar_configuracao():
    """Interrompe cedo quando a chave da OMDb não está configurada."""
    if not os.environ.get("OMDB_API_KEY"):
        raise ErroOMDb("Configure OMDB_API_KEY antes de executar.")


def ler_pergunta(entrada=input) -> str:
    """Lê até receber uma pergunta não vazia."""
    while True:
        pergunta = entrada("Digite sua pergunta sobre um filme ou série: ").strip()
        if pergunta:
            return pergunta
        print("A pergunta não pode ficar vazia.")


def chamar_modelo(mensagens, declaracoes):
    """Envia o histórico e as tools ao Ollama."""
    corpo = {
        "model": MODELO,
        "messages": mensagens,
        "tools": declaracoes,
        "stream": False,
        "options": {"temperature": 0},
    }
    requisicao = urllib.request.Request(
        OLLAMA_URL,
        json.dumps(corpo).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(requisicao, timeout=600) as resposta:
        return json.load(resposta)["message"]


def rodar(pergunta, chamar=None) -> tuple[str, int]:
    """Executa o laço até a resposta final ou o limite de passos."""
    chamar = chamar or chamar_modelo
    mensagens = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": pergunta}]
    for passo in range(1, MAX_PASSOS + 1):
        mensagem = chamar(mensagens, DECLARACOES)
        mensagens.append(mensagem)
        chamadas = mensagem.get("tool_calls") or []
        if not chamadas:
            return mensagem.get("content", "").strip(), passo
        for chamada in chamadas:
            nome = chamada["function"]["name"]
            print(f"Ferramenta usada: {nome}")
            argumentos = chamada["function"].get("arguments") or {}
            try:
                funcao = FERRAMENTAS[nome]
                parametros = inspect.signature(funcao).parameters
                argumentos_validos = {chave: valor for chave, valor in argumentos.items() if chave in parametros}
                resultado = funcao(**argumentos_validos)
            except (ErroOMDb, KeyError, TypeError) as erro:
                resultado = {"erro": str(erro)}
            mensagens.append(
                {"role": "tool", "tool_name": nome, "content": json.dumps(resultado, ensure_ascii=False)}
            )
    return f"O agente não concluiu após {MAX_PASSOS} passos.", MAX_PASSOS


def main():
    """Valida a configuração e executa uma pergunta interativa."""
    validar_configuracao()
    pergunta = ler_pergunta()
    resposta, passos = rodar(pergunta)
    print(f"\nResposta: {resposta}")
    print(f"Passos: {passos}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except ErroOMDb as erro:
        print(f"Erro: {erro}")
