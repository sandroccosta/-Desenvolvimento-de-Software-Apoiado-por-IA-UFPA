import io
import json
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cliente_omdb import ErroOMDb, buscar_titulo, pesquisar_titulos
import agente
import tools


class RespostaFalsa(io.BytesIO):
    def __init__(self, dados):
        super().__init__(json.dumps(dados).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class TestClienteOMDb(unittest.TestCase):
    def test_rejeita_chave_ausente(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ErroOMDb, "Configure OMDB_API_KEY"):
                buscar_titulo("Dark")

    def test_normaliza_serie_e_omite_valor_indisponivel(self):
        resposta = {
            "Response": "True",
            "Title": "Dark",
            "Year": "2017–2020",
            "Type": "series",
            "Genre": "Crime, Drama, Mystery",
            "Director": "N/A",
            "imdbRating": "8.7",
            "totalSeasons": "3",
        }

        resultado = buscar_titulo(
            "Dark", api_key="chave-teste", abrir=lambda *_args, **_kwargs: RespostaFalsa(resposta)
        )

        self.assertEqual(
            resultado,
            {
                "titulo": "Dark",
                "ano": "2017–2020",
                "tipo": "series",
                "genero": "Crime, Drama, Mystery",
                "avaliacao_imdb": "8.7",
                "temporadas": "3",
            },
        )

    def test_pesquisa_limita_resultado_a_cinco_titulos(self):
        itens = [
            {
                "Title": f"Batman {numero}",
                "Year": str(2000 + numero),
                "imdbID": f"tt{numero:07d}",
                "Type": "movie",
                "Poster": "N/A",
            }
            for numero in range(1, 7)
        ]
        resposta = {"Search": itens, "totalResults": "6", "Response": "True"}

        resultado = pesquisar_titulos(
            "Batman", api_key="chave-teste", abrir=lambda *_args, **_kwargs: RespostaFalsa(resposta)
        )

        self.assertEqual(len(resultado), 5)
        self.assertEqual(
            resultado[0],
            {"titulo": "Batman 1", "ano": "2001", "id_imdb": "tt0000001", "tipo": "movie"},
        )

    def test_codifica_titulo_com_espacos_na_url(self):
        urls = []
        resposta = {"Response": "True", "Title": "Cidade de Deus", "Year": "2002", "Type": "movie"}

        def abrir(requisicao, **_kwargs):
            urls.append(requisicao.full_url)
            return RespostaFalsa(resposta)

        buscar_titulo("Cidade de Deus", api_key="chave-teste", abrir=abrir)

        self.assertIn("t=Cidade+de+Deus", urls[0])

    def test_traduz_titulo_inexistente(self):
        resposta = {"Response": "False", "Error": "Movie not found!"}

        with self.assertRaisesRegex(ErroOMDb, "Título não encontrado"):
            buscar_titulo(
                "Obra inexistente",
                api_key="chave-teste",
                abrir=lambda *_args, **_kwargs: RespostaFalsa(resposta),
            )

    def test_traduz_chave_invalida(self):
        resposta = {"Response": "False", "Error": "Invalid API key!"}

        with self.assertRaisesRegex(ErroOMDb, "Chave OMDb inválida"):
            buscar_titulo(
                "Dark", api_key="chave-invalida", abrir=lambda *_args, **_kwargs: RespostaFalsa(resposta)
            )

    def test_traduz_limite_diario(self):
        resposta = {"Response": "False", "Error": "Request limit reached!"}

        with self.assertRaisesRegex(ErroOMDb, "Limite diário"):
            buscar_titulo(
                "Dark", api_key="chave-teste", abrir=lambda *_args, **_kwargs: RespostaFalsa(resposta)
            )

    def test_traduz_falha_de_conexao_sem_expor_chave(self):
        def abrir(*_args, **_kwargs):
            raise urllib.error.URLError("falha envolvendo chave-secreta")

        with self.assertRaises(ErroOMDb) as contexto:
            buscar_titulo("Dark", api_key="chave-secreta", abrir=abrir)

        self.assertEqual(str(contexto.exception), "Não foi possível conectar à OMDb.")
        self.assertNotIn("chave-secreta", str(contexto.exception))

    def test_omite_avaliacao_indisponivel(self):
        resposta = {"Response": "True", "Title": "Exemplo", "Year": "2020", "Type": "movie", "imdbRating": "N/A"}

        resultado = buscar_titulo(
            "Exemplo", api_key="chave-teste", abrir=lambda *_args, **_kwargs: RespostaFalsa(resposta)
        )

        self.assertNotIn("avaliacao_imdb", resultado)

    def test_traduz_json_invalido(self):
        def abrir(*_args, **_kwargs):
            return io.BytesIO(b"nao e json")

        with self.assertRaisesRegex(ErroOMDb, "resposta inválida"):
            buscar_titulo("Dark", api_key="chave-teste", abrir=abrir)


class TestTools(unittest.TestCase):
    def test_wrappers_encaminham_argumentos_e_resultados(self):
        with patch.object(
            tools.cliente_omdb,
            "buscar_titulo",
            side_effect=lambda titulo, ano=None: {"titulo": titulo, "ano": ano},
        ):
            detalhe = tools.buscar_titulo("Dark", "2017")
        with patch.object(
            tools.cliente_omdb,
            "pesquisar_titulos",
            side_effect=lambda termo: [{"titulo": termo}],
        ):
            pesquisa = tools.pesquisar_titulos("Batman")

        self.assertEqual(detalhe, {"titulo": "Dark", "ano": "2017"})
        self.assertEqual(pesquisa, [{"titulo": "Batman"}])

    def test_declaracoes_formam_contrato_sem_ambiguidade(self):
        self.assertEqual(set(tools.FERRAMENTAS), {"buscar_titulo", "pesquisar_titulos"})
        declaracoes = {item["function"]["name"]: item["function"] for item in tools.DECLARACOES}

        busca = declaracoes["buscar_titulo"]
        pesquisa = declaracoes["pesquisar_titulos"]
        self.assertIn("título específico", busca["description"])
        self.assertIn("avaliação", busca["description"])
        self.assertEqual(busca["parameters"]["required"], ["titulo"])
        self.assertEqual(set(busca["parameters"]["properties"]), {"titulo", "ano"})
        self.assertIn("título aproximado", pesquisa["description"])
        self.assertIn("não retorna detalhes", pesquisa["description"])
        self.assertEqual(pesquisa["parameters"]["required"], ["termo"])


class TestAgente(unittest.TestCase):
    def test_system_prompt_evita_pesquisa_e_chamadas_redundantes(self):
        self.assertIn("não use pesquisar_titulos", agente.SISTEMA)
        self.assertIn("uma única vez", agente.SISTEMA)

    def test_solicita_novamente_quando_pergunta_esta_vazia(self):
        respostas = iter(["   ", "Quantas temporadas tem Dark?"])
        prompts = []

        with redirect_stdout(io.StringIO()):
            pergunta = agente.ler_pergunta(lambda prompt: prompts.append(prompt) or next(respostas))

        self.assertEqual(pergunta, "Quantas temporadas tem Dark?")
        self.assertEqual(len(prompts), 2)

    def test_valida_chave_antes_de_iniciar(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ErroOMDb, "Configure OMDB_API_KEY"):
                agente.validar_configuracao()

    def test_resposta_direta_encerra_em_um_passo(self):
        resposta, passos = agente.rodar(
            "Olá", chamar=lambda _mensagens, _declaracoes: {"role": "assistant", "content": "Olá!"}
        )

        self.assertEqual((resposta, passos), ("Olá!", 1))

    def test_tool_seguida_de_resposta_final_encerra_em_dois_passos(self):
        respostas = iter(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "buscar_titulo", "arguments": {"titulo": "Dark"}}}],
                },
                {"role": "assistant", "content": "Dark tem três temporadas."},
            ]
        )

        with patch.dict(agente.FERRAMENTAS, {"buscar_titulo": lambda titulo: {"titulo": titulo, "temporadas": "3"}}):
            resultado = agente.rodar("Quantas temporadas tem Dark?", chamar=lambda *_: next(respostas))

        self.assertEqual(resultado, ("Dark tem três temporadas.", 2))

    def test_registra_nome_da_tool_utilizada(self):
        respostas = iter(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "buscar_titulo", "arguments": {"titulo": "Dark"}}}],
                },
                {"role": "assistant", "content": "Dark tem três temporadas."},
            ]
        )

        with patch.dict(agente.FERRAMENTAS, {"buscar_titulo": lambda titulo: {"titulo": titulo}}):
            saida = io.StringIO()
            with redirect_stdout(saida):
                agente.rodar("Quantas temporadas tem Dark?", chamar=lambda *_: next(respostas))

        self.assertIn("Ferramenta usada: buscar_titulo", saida.getvalue())

    def test_descarta_argumento_extra_gerado_pelo_modelo(self):
        chamadas = 0

        def chamar(mensagens, _declaracoes):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 1:
                return {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "buscar_titulo",
                                "arguments": {"titulo": "Dark", "ano": "", "termo": "Dark"},
                            }
                        }
                    ],
                }
            resultado = json.loads(mensagens[-1]["content"])
            return {"role": "assistant", "content": "ok" if "erro" not in resultado else "erro"}

        with patch.dict(agente.FERRAMENTAS, {"buscar_titulo": lambda titulo, ano=None: {"titulo": titulo}}):
            resultado = agente.rodar("Detalhe Dark", chamar=chamar)

        self.assertEqual(resultado, ("ok", 2))

    def test_interrompe_chamadas_continuas_no_limite(self):
        chamada = {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "pesquisar_titulos", "arguments": {"termo": "Batman"}}}],
        }

        with patch.dict(agente.FERRAMENTAS, {"pesquisar_titulos": lambda termo: [{"titulo": termo}]}):
            resposta, passos = agente.rodar("Procure Batman", chamar=lambda *_: chamada.copy())

        self.assertEqual(passos, 6)
        self.assertIn("não concluiu", resposta)

    def test_pergunta_composta_permite_duas_tools_antes_da_resposta(self):
        respostas = iter(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "pesquisar_titulos", "arguments": {"termo": "Dark"}}}],
                },
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "buscar_titulo", "arguments": {"titulo": "Dark"}}}],
                },
                {"role": "assistant", "content": "Dark é uma série de 2017."},
            ]
        )
        funcoes = {
            "pesquisar_titulos": lambda termo: [{"titulo": termo, "ano": "2017"}],
            "buscar_titulo": lambda titulo: {"titulo": titulo, "ano": "2017", "tipo": "series"},
        }

        with patch.dict(agente.FERRAMENTAS, funcoes):
            resultado = agente.rodar("Encontre e detalhe Dark", chamar=lambda *_: next(respostas))

        self.assertEqual(resultado, ("Dark é uma série de 2017.", 3))


if __name__ == "__main__":
    unittest.main()
