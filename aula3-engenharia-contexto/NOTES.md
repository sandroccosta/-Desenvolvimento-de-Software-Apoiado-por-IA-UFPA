# Notas de engenharia de contexto

## Exploração inicial

- A Aula 2 concentra catálogo, declarações de tools, chamada HTTP ao Ollama e laço agêntico em `aula2-laco-agentico/agente.py`.
- A Aula 3 preservará esse exercício e separará a integração externa, as tools e a orquestração em arquivos com responsabilidades distintas.
- A OMDb usa o parâmetro `t` para buscar uma obra por título e `s` para pesquisar títulos semelhantes.
- A chave será lida de `OMDB_API_KEY` e não poderá entrar no histórico do agente, nos logs ou no Git.
- Os testes substituirão apenas as fronteiras externas: HTTP da OMDb e chamada ao Ollama.

## Decisões

- Usar somente a biblioteca padrão do Python.
- Retornar no máximo cinco itens na pesquisa.
- Manter `MAX_PASSOS = 6`.
- Normalizar os nomes dos campos da OMDb para português antes de entregá-los ao modelo.

## Problemas abertos

- Nenhum problema funcional permanece aberto após a validação real de 22/09/2026.

## Cliente OMDb concluído

- A URL é montada com `urllib.parse.urlencode`, inclusive para títulos com espaços e acentos.
- A busca exata normaliza somente campos disponíveis; valores `N/A` são omitidos.
- A pesquisa retorna título, ano, identificador IMDb e tipo dos cinco primeiros resultados.
- Erros de chave, limite, título inexistente, conexão e JSON inválido são convertidos para mensagens em português.
- As mensagens de erro não incluem a URL completa nem a chave da API.

## Tools concluídas

- `buscar_titulo` atende perguntas sobre uma obra específica e aceita ano opcional.
- `pesquisar_titulos` atende termos amplos ou títulos aproximados e retorna alternativas.
- As descrições evitam sobreposição: uma tool detalha uma obra; a outra descobre possíveis obras.
- Os esquemas tornam obrigatórios somente `titulo` ou `termo`, deixando `ano` opcional.

## Laço agêntico concluído

- A pergunta vazia é rejeitada antes de qualquer chamada ao modelo.
- O histórico mantém system prompt, pergunta, pedidos de tools e resultados necessários para a próxima decisão.
- Erros de tool retornam ao modelo como dados, permitindo que ele explique a falha em português.
- Uma resposta sem `tool_calls` encerra o laço; chamadas contínuas param em `MAX_PASSOS = 6`.
- Os testes comprovaram uma resposta direta em um passo, uma tool em dois passos e duas tools em três passos.
- Não foi necessária correção manual fora do ciclo teste falhando, implementação mínima e teste passando.

## Evidências automatizadas

- Cliente, tools, entrada e laço foram exercitados sem internet.
- Os cenários simulados do laço terminaram em um passo sem tool, dois passos com uma tool e três passos com duas tools.
- O cenário que nunca conclui parou corretamente no sexto passo.
- A saída extra do teste de pergunta vazia foi removida redirecionando apenas a saída do teste.

## Validação real e correções

- A consulta direta à OMDb retornou Dark com 3 temporadas e avaliação IMDb 8.7.
- Na primeira execução completa, o modelo usou somente `pesquisar_titulos` e inventou 4 temporadas e nota 8.1.
- As descrições das tools foram ajustadas para informar que pesquisa não devolve detalhes e que avaliação ou temporadas exigem `buscar_titulo`.
- O system prompt passou a proibir pesquisa quando o título já está claro e a pedir uma única busca exata.
- O modelo ainda acrescentou o argumento indevido `termo` à busca exata; o dispatcher passou a filtrar argumentos pela assinatura da função.
- Na execução final, o agente chamou `buscar_titulo`, recebeu 3 temporadas e nota 8.7 e respondeu corretamente em 2 passos.
