# UdaPlay — AI Research Agent for Gaming Analytics

A Retrieval-Augmented Generation (RAG) agent that answers natural language questions about video games. Built as the capstone project for Udacity's *Building AI Agents* course.

---

## What is this?

UdaPlay is a two-part AI project:

**Part 1 — RAG Pipeline** (`Udaplay_01_solution_project.ipynb`)
Loads 25 game records into a ChromaDB vector store, embeds them with OpenAI, and demonstrates semantic search and question-answering over the dataset.

**Part 2 — Research Agent** (`Udaplay_02_solution_project.ipynb`)
A stateful AI agent that answers any gaming question by orchestrating three tools in sequence:

```
User query
    │
    ▼
retrieve_game          → searches internal ChromaDB (25 games, 2013–2023)
    │
evaluate_retrieval     → LLM scores confidence (0.0–1.0)
    │
    ├─ score ≥ 0.7 ──► answer with [Internal DB] citation
    │
    └─ score < 0.7 ──► game_web_search (Tavily) ──► answer with [Web Search] citation
```

The agent remembers conversation history per `session_id`, so follow-up questions resolve correctly across multiple turns.

---

## Why does it work this way?

| Design choice | Reason |
|---------------|--------|
| RAG before web search | Internal data is curated and fast; web search costs tokens and adds latency |
| Explicit confidence evaluation | Prevents hallucination — agent only falls back to web when it knows the internal data is insufficient |
| `session_id` memory | Enables multi-turn conversations without repeating context in every query |
| OpenAI tool-calling via `@tool` decorator | Auto-generates JSON schema from function signature — no manual schema writing |
| ChromaDB in-memory | Keeps the project self-contained; the 25-game dataset is small enough to re-embed on every run |

---

## How it works — technical stack

| Component | Technology |
|-----------|-----------|
| LLM (reasoning + answers) | OpenAI `gpt-4o-mini` via Vocareum proxy |
| Embeddings | OpenAI `text-embedding-ada-002` |
| Vector store | ChromaDB (in-memory) |
| Web search fallback | Tavily API |
| Agent framework | Course `lib/` — `Agent`, `StateMachine`, `@tool`, `ShortTermMemory` |
| Data | `games.json` — 25 hand-curated game records |

The `lib/` directory contains the course framework. Two files were extended for this project:
- `lib/loaders.py` — added `JSONGameLoader` to load game records as semantic documents
- `lib/vector_db.py` — added `api_base` proxy support and `CorpusLoaderService.load_json()`

---

## Project structure

```
udaplay/
├── Udaplay_01_solution_project.ipynb   # Part 1: RAG pipeline
├── Udaplay_02_solution_project.ipynb   # Part 2: Agent with tools
├── test_agent.py                       # CLI runner — pass any query
├── init.py                             # One-time environment setup
├── games.json                          # Dataset: 25 game records (2013–2023)
├── config.env.template                 # Copy → config.env, fill in API keys
├── requirements.txt                    # chromadb, openai, pydantic, dotenv, tavily
└── lib/                                # Course framework (Agent, RAG, StateMachine…)
```

---

## Setup and usage

### 1. Clone and initialise

```bash
git clone https://github.com/Freakling/Udacity_Building_agents1.git
cd Udacity_Building_agents1/udaplay
python init.py
```

### 2. Configure API keys

```bash
cp config.env.template config.env
# edit config.env and fill in OPENAI_API_KEY and TAVILY_API_KEY
```

Get a free Tavily key at [tavily.com](https://tavily.com).

### 3. Run the notebooks

Open `Udaplay_01_solution_project.ipynb` first, then `Udaplay_02_solution_project.ipynb`, and run all cells top to bottom.

### 4. Or use the CLI runner

```bash
# Default query (open world game research)
python test_agent.py

# Free text
python test_agent.py "Who developed Elden Ring and when was it released?"

# JSON — supports custom session_id for multi-turn memory
python test_agent.py '{"query": "What games has CD Projekt Red made?", "session_id": "cdpr"}'
python test_agent.py '{"query": "Which of their games has the most DLC?", "session_id": "cdpr"}'
```

---

## Dataset

25 games spanning 2013–2023 across genres: open world RPG, action-adventure, sports, shooters, battle royale, life simulation, and more. Each record includes title, developer, publisher, release date, platforms, genre, and description.

Notable titles: GTA V, The Witcher 3, Elden Ring, Cyberpunk 2077, Red Dead Redemption 2, Zelda: Breath of the Wild, Baldur's Gate 3, and 18 others.
