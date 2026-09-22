# Orientações da Aula 3

- Use Python 3.11 e somente a biblioteca padrão.
- Execute os testes com `python -m unittest discover -s aula3-engenharia-contexto/tests -v`.
- Leia `NOTES.md` antes de alterar os arquivos desta pasta.
- Atualize `NOTES.md` ao concluir cada etapa.
- Nunca grave nem versione a chave da OMDb. Leia-a exclusivamente de `OMDB_API_KEY`.
- Limite pesquisas da OMDb aos cinco primeiros resultados.
- Mantenha `MAX_PASSOS = 6` no laço agêntico.
- Responda ao usuário em português e não invente informações ausentes na API.

## Critério de conclusão

Os testes automatizados devem passar sem internet. A validação final deve incluir uma consulta real à OMDb, uma execução completa com Ollama e a atualização de `../diario/2026-09-15.md`.
