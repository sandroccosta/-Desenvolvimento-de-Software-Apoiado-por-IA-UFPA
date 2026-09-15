# Desenvolvimento de Software Apoiado por IA — UFPA

Repositório da dupla **Alexsandro Costa** e **Jhonathan Fagundes** na disciplina Desenvolvimento de Software Apoiado por IA (UFPA, 2026.4).

## Estrutura

```text
.
├── diario/          # registro de cada atividade, em diario/AAAA-MM-DD.md
└── laco-agente/     # exercício de 03/09: agente com function calling
```

## Diário

| Data | Atividade |
|---|---|
| [03/09/2026](diario/2026-09-03.md) | Construam o laço: agente de filmes e séries e experimento com a descrição da tool |

## Como rodar o agente

Requisitos: Python 3.10+ e [Ollama](https://ollama.com) com um modelo que suporte tool calling.

```bash
ollama pull llama3.2
python laco-agente/agente.py          # roda a descrição boa e depois a vaga
python laco-agente/agente.py vaga     # roda só um dos cenários
```

O script não tem dependências externas: fala com a API do Ollama em `http://127.0.0.1:11434` usando `urllib`.
