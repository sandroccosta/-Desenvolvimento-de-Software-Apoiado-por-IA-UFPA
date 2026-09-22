# Aula 3 — Engenharia de contexto e decomposição de tarefas

Agente de terminal que usa o Ollama para escolher ferramentas e consultar filmes e séries na OMDb.

## Como funciona

O usuário digita uma pergunta em português. O modelo `llama3.2` escolhe entre buscar os detalhes de um título específico ou pesquisar até cinco títulos semelhantes. Nosso código executa a tool, devolve o resultado ao modelo e repete o laço até a resposta final ou o limite de seis passos.

```text
agente.py → tools.py → cliente_omdb.py → OMDb
     ↑             resultado             │
     └───────────────────────────────────┘
```

## Requisitos

- Python 3.11 ou superior.
- Ollama com o modelo `llama3.2`.
- Chave gratuita da OMDb.

## Configuração no PowerShell

```powershell
$env:OMDB_API_KEY="sua-chave"
ollama pull llama3.2
```

Não coloque a chave real no código, no `.env.example` nem nos commits.

Se a chave estiver em um arquivo local `.env`, carregue-a no terminal atual sem imprimi-la:

```powershell
$linha = Get-Content .env | Where-Object { $_ -match '^\s*OMDB_API_KEY\s*=' } | Select-Object -First 1
$env:OMDB_API_KEY = ($linha -split '=', 2)[1].Trim()
```

## Execução

```powershell
python aula3-engenharia-contexto/agente.py
```

Digite a pergunta quando aparecer o prompt. Exemplo: `Quantas temporadas tem a série Dark e qual é sua avaliação no IMDb?`

Durante a execução, o terminal registra cada tool acionada, por exemplo: `Ferramenta usada: buscar_titulo`.

## Testes

```powershell
python -m unittest discover -s aula3-engenharia-contexto/tests -v
```

Os testes não acessam a internet nem consomem requisições da OMDb.

## Erros tratados

- Chave ausente ou inválida.
- Limite diário atingido.
- Título inexistente.
- Falha de conexão ou timeout.
- Resposta JSON inválida.
- Pergunta vazia e limite de passos do agente.
