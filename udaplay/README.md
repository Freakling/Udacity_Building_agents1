# UdaPlay

RAG pipeline and stateful tool-calling agent over a 210-game dataset. Udacity *Building AI Agents* capstone - two notebooks.

## Decision flow

```
retrieve_game
    +- ChromaDB semantic search over 210 game records (in-memory, rebuilt per session)
evaluate_retrieval
    +- LLM returns JSON: { confidence_score, is_sufficient, reasoning }
    |- score >= 0.7: compose answer, cite [Internal DB]
    +- score < 0.7: game_web_search -> Tavily -> compose answer, cite [Web Search]
```

## Components

| File | Role |
|------|------|
| `Udaplay_01_solution_project.ipynb` | RAG pipeline: embed, store, search, answer |
| `Udaplay_02_solution_project.ipynb` | Agent: tool orchestration, session memory |
| `test_agent.py` | CLI runner, accepts free text or JSON |
| `init.py` | Installs deps, validates API keys |
| `save.py` | Executes all notebooks in-place and saves outputs |
| `games.json` | 210 game records, 1978-2024 |
| `lib/loaders.py` | Extended: `JSONGameLoader` |
| `lib/vector_db.py` | Extended: `api_base` proxy support, `load_json()` |
| `lib/llm_claude.py` | Anthropic backend: drop-in `LLM` replacement |

## Setup

```bash
python init.py
cp config.env.template config.env
```

`config.env` keys:

| Key | Source |
|-----|--------|
| `OPENAI_API_KEY` | Udacity workspace (Vocareum) or platform.openai.com |
| `TAVILY_API_KEY` | tavily.com - free tier, 1000 req/month |
| `OPENAI_BASE_URL` | `https://openai.vocareum.com/v1` (workspace) or `https://api.openai.com/v1` (direct) |
| `ANTHROPIC_API_KEY` | console.anthropic.com - fallback when no OpenAI key |

Backend priority: OpenAI if `OPENAI_API_KEY` is set; Claude if only `ANTHROPIC_API_KEY` is set.

## Embeddings

| Mode | Trigger | Requires |
|------|---------|---------|
| OpenAI `text-embedding-ada-002` | `OPENAI_API_KEY` set | Vocareum or direct OpenAI key |
| Local `onnxruntime` MiniLM-L6-v2 | Claude mode or no OpenAI key | `pip install onnxruntime` |

## CLI

```bash
python test_agent.py
python test_agent.py "Who developed Elden Ring?"
python test_agent.py '{"query": "What has CD Projekt Red made?", "session_id": "cdpr"}'
python test_agent.py '{"query": "Which of their games has the most DLC?", "session_id": "cdpr"}'
```

## Dataset

210 records, 1978-2024. Sources: Wikipedia best-sellers, Metacritic/OpenCritic top-rated, Steam peak player counts. Genres: action RPG, platformer, FPS, MOBA, survival, roguelike, fighting, JRPG, RTS, life sim.

Schema: `id`, `title`, `developer`, `publisher`, `release_date`, `platforms[]`, `genre`, `description`.
